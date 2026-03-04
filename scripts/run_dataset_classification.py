#!/usr/bin/env python3
"""Run YOLO classification inference on a full image dataset."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Iterable

OUTPUT_COLUMNS = [
    "absolute_image_path",
    "image_file_name",
    "top1_class",
    "top1_confidence",
    "top2_class",
    "top2_confidence",
    "top3_class",
    "top3_confidence",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Apply a trained YOLO classification model to a dataset."
    )
    parser.add_argument(
        "--model",
        type=Path,
        default=Path("./yolo11n-cls-grp.pt"),
        help="Path to YOLO classification model (.pt).",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("./clip_data"),
        help="Dataset directory (uses <data-dir>/images when present).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("./classification_predictions.csv"),
        help="Output file (.csv or .parquet).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=64,
        help="Batch size used for model inference.",
    )
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        help="Inference device (e.g. cpu, 0, mps).",
    )
    parser.add_argument(
        "--save-every-batches",
        type=int,
        default=10,
        help="How often to flush predictions to disk.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        choices=[1, 2, 3],
        help="Number of top classes to store.",
    )
    parser.add_argument(
        "--extensions",
        type=str,
        default=".jpg,.jpeg,.png,.bmp,.webp,.tif,.tiff",
        help="Comma-separated image file extensions.",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Start from scratch even if output already exists.",
    )
    parser.add_argument(
        "--max-images",
        type=int,
        default=None,
        help="Optional cap on number of discovered images (useful for testing).",
    )
    return parser.parse_args()


def resolve_images_dir(data_dir: Path) -> Path:
    images_dir = data_dir / "images"
    return images_dir if images_dir.exists() else data_dir


def list_images(images_dir: Path, extensions: set[str]) -> list[Path]:
    paths = [
        path.resolve()
        for path in images_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in extensions
    ]
    paths.sort()
    return paths


def load_processed_paths_from_csv(csv_path: Path) -> set[str]:
    processed: set[str] = set()
    if not csv_path.exists():
        return processed

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            image_path = row.get("absolute_image_path")
            if image_path:
                processed.add(image_path)
    return processed


def load_processed_paths_from_parquet(parquet_path: Path) -> set[str]:
    if not parquet_path.exists():
        return set()
    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError(
            "pandas is required when using parquet output. Install it with: pip install pandas pyarrow"
        ) from exc

    df = pd.read_parquet(parquet_path, columns=["absolute_image_path"])
    return set(df["absolute_image_path"].astype(str).tolist())


def append_rows_to_csv(output_path: Path, rows: list[dict[str, object]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = output_path.exists()
    with output_path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)


def append_rows_to_journal(journal_path: Path, rows: list[dict[str, object]]) -> None:
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = journal_path.exists()
    with journal_path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)


def sync_parquet_from_journal(journal_path: Path, parquet_path: Path) -> None:
    if not journal_path.exists():
        return
    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError(
            "pandas is required when using parquet output. Install it with: pip install pandas pyarrow"
        ) from exc

    df = pd.read_csv(journal_path)
    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(parquet_path, index=False)


def chunked(items: list[Path], size: int) -> Iterable[list[Path]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def get_topk_prediction(result, top_k: int) -> list[tuple[str | None, float | None]]:
    probs = getattr(result, "probs", None)
    if probs is None:
        return [(None, None)] * top_k

    names = result.names
    top_indices = list(getattr(probs, "top5", []))[:top_k]
    top_confs = list(getattr(probs, "top5conf", []))[:top_k]

    output: list[tuple[str | None, float | None]] = []
    for idx, conf in zip(top_indices, top_confs):
        cls_idx = int(idx)
        cls_name = names[cls_idx] if isinstance(names, dict) else names[cls_idx]
        output.append((str(cls_name), float(conf)))

    while len(output) < top_k:
        output.append((None, None))
    return output


def build_rows(batch_paths: list[Path], results, top_k: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for image_path, result in zip(batch_paths, results):
        predictions = get_topk_prediction(result, top_k=top_k)

        row = {
            "absolute_image_path": str(image_path),
            "image_file_name": image_path.name,
            "top1_class": predictions[0][0] if top_k >= 1 else None,
            "top1_confidence": predictions[0][1] if top_k >= 1 else None,
            "top2_class": predictions[1][0] if top_k >= 2 else None,
            "top2_confidence": predictions[1][1] if top_k >= 2 else None,
            "top3_class": predictions[2][0] if top_k >= 3 else None,
            "top3_confidence": predictions[2][1] if top_k >= 3 else None,
        }
        rows.append(row)
    return rows


def clear_resume_state(output_path: Path) -> None:
    if output_path.exists():
        output_path.unlink()
    journal_path = Path(str(output_path) + ".journal.csv")
    if journal_path.exists():
        journal_path.unlink()
    skipped_path = Path(str(output_path) + ".skipped.csv")
    if skipped_path.exists():
        skipped_path.unlink()


def load_skipped_paths(skipped_path: Path) -> set[str]:
    skipped: set[str] = set()
    if not skipped_path.exists():
        return skipped

    with skipped_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            image_path = row.get("absolute_image_path")
            if image_path:
                skipped.add(image_path)
    return skipped


def append_skipped_rows(
    skipped_path: Path, skipped_rows: list[dict[str, str]], seen_skipped: set[str]
) -> None:
    if not skipped_rows:
        return

    deduped_rows: list[dict[str, str]] = []
    for row in skipped_rows:
        image_path = row["absolute_image_path"]
        if image_path in seen_skipped:
            continue
        seen_skipped.add(image_path)
        deduped_rows.append(row)

    if not deduped_rows:
        return

    skipped_path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = skipped_path.exists()
    with skipped_path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["absolute_image_path", "error"])
        if not file_exists:
            writer.writeheader()
        writer.writerows(deduped_rows)


def predict_with_fault_tolerance(model, batch_paths: list[Path], device: str | None):
    """Predict for a batch; if decode errors occur, isolate and skip bad images."""
    if not batch_paths:
        return [], []

    try:
        results = model.predict(
            source=[str(path) for path in batch_paths],
            verbose=False,
            device=device,
        )
        return list(zip(batch_paths, results)), []
    except OSError as exc:
        if len(batch_paths) == 1:
            return [], [
                {
                    "absolute_image_path": str(batch_paths[0]),
                    "error": str(exc),
                }
            ]

        mid = len(batch_paths) // 2
        left_pairs, left_skipped = predict_with_fault_tolerance(model, batch_paths[:mid], device)
        right_pairs, right_skipped = predict_with_fault_tolerance(model, batch_paths[mid:], device)
        return left_pairs + right_pairs, left_skipped + right_skipped


def main() -> int:
    args = parse_args()
    output_path = args.output.resolve()
    images_dir = resolve_images_dir(args.data_dir.resolve())
    extensions = {
        ext.strip().lower() if ext.strip().startswith(".") else f".{ext.strip().lower()}"
        for ext in args.extensions.split(",")
        if ext.strip()
    }

    if args.batch_size <= 0:
        raise ValueError("--batch-size must be > 0")
    if args.save_every_batches <= 0:
        raise ValueError("--save-every-batches must be > 0")
    if not args.model.exists():
        raise FileNotFoundError(f"Model not found: {args.model}")
    if not images_dir.exists():
        raise FileNotFoundError(f"Images directory not found: {images_dir}")

    if args.no_resume:
        clear_resume_state(output_path)

    suffix = output_path.suffix.lower()
    if suffix not in {".csv", ".parquet"}:
        raise ValueError("--output must end with .csv or .parquet")

    image_paths = list_images(images_dir, extensions)
    if not image_paths:
        raise RuntimeError(f"No images found in {images_dir} with extensions: {sorted(extensions)}")
    if args.max_images is not None:
        if args.max_images <= 0:
            raise ValueError("--max-images must be > 0 when provided")
        image_paths = image_paths[: args.max_images]

    journal_path = Path(str(output_path) + ".journal.csv")
    if suffix == ".csv":
        processed_paths = load_processed_paths_from_csv(output_path)
    else:
        processed_paths = load_processed_paths_from_csv(journal_path)
        if not processed_paths and output_path.exists():
            processed_paths = load_processed_paths_from_parquet(output_path)
    skipped_path = Path(str(output_path) + ".skipped.csv")
    skipped_paths = load_skipped_paths(skipped_path)

    to_process = [
        path
        for path in image_paths
        if str(path) not in processed_paths and str(path) not in skipped_paths
    ]
    already_done = len(image_paths) - len(to_process)

    print(f"Model: {args.model.resolve()}")
    print(f"Images directory: {images_dir}")
    print(f"Total images found: {len(image_paths)}")
    print(f"Already processed: {already_done}")
    print(f"Remaining: {len(to_process)}")
    print(f"Output: {output_path}")
    if suffix == ".parquet":
        print(f"Parquet journal: {journal_path}")
    print(f"Skipped-log: {skipped_path}")

    if not to_process:
        if suffix == ".parquet":
            sync_parquet_from_journal(journal_path, output_path)
        print("Nothing to do.")
        return 0

    try:
        from tqdm import tqdm
    except ImportError as exc:
        raise RuntimeError("tqdm is required. Install it with: pip install tqdm") from exc
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise RuntimeError("ultralytics is required. Install it with: pip install ultralytics") from exc

    model = YOLO(str(args.model.resolve()))
    pending_rows: list[dict[str, object]] = []
    pending_skipped_rows: list[dict[str, str]] = []

    pbar = tqdm(total=len(image_paths), initial=already_done, unit="img", desc="Classifying")
    try:
        for batch_idx, batch_paths in enumerate(chunked(to_process, args.batch_size), start=1):
            paired_results, skipped_rows = predict_with_fault_tolerance(
                model, batch_paths, args.device
            )
            if skipped_rows:
                pending_skipped_rows.extend(skipped_rows)
                print(f"Skipped {len(skipped_rows)} unreadable image(s) in current batch.")

            if paired_results:
                good_paths, good_results = zip(*paired_results)
                pending_rows.extend(build_rows(list(good_paths), list(good_results), top_k=args.top_k))
            pbar.update(len(batch_paths))

            if batch_idx % args.save_every_batches == 0 and pending_rows:
                if suffix == ".csv":
                    append_rows_to_csv(output_path, pending_rows)
                else:
                    append_rows_to_journal(journal_path, pending_rows)
                pending_rows.clear()
            if batch_idx % args.save_every_batches == 0 and pending_skipped_rows:
                append_skipped_rows(skipped_path, pending_skipped_rows, skipped_paths)
                pending_skipped_rows.clear()

        if pending_rows:
            if suffix == ".csv":
                append_rows_to_csv(output_path, pending_rows)
            else:
                append_rows_to_journal(journal_path, pending_rows)
            pending_rows.clear()
        if pending_skipped_rows:
            append_skipped_rows(skipped_path, pending_skipped_rows, skipped_paths)
            pending_skipped_rows.clear()
    except KeyboardInterrupt:
        print("\nInterrupted. Flushing pending predictions to disk before exit...")
        if pending_rows:
            if suffix == ".csv":
                append_rows_to_csv(output_path, pending_rows)
            else:
                append_rows_to_journal(journal_path, pending_rows)
        if pending_skipped_rows:
            append_skipped_rows(skipped_path, pending_skipped_rows, skipped_paths)
        if suffix == ".parquet":
            sync_parquet_from_journal(journal_path, output_path)
        print("Resume by running the same command again.")
        return 130
    finally:
        pbar.close()

    if suffix == ".parquet":
        print("Converting journal to parquet...")
        sync_parquet_from_journal(journal_path, output_path)

    print("Done.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pylint: disable=broad-exception-caught
        print(f"Error: {exc}", file=sys.stderr)
        raise
