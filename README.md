# GRP Image Classification

This repository implements a supervised image-classification pipeline for the [Graphische Sammlung (GRP)](https://resource.swissartresearch.net/) at the GTA Archive, ETH Zurich. The pipeline classifies digitised cultural-heritage images into eight visual-type categories and is developed as part of the [Swiss Art Research Infrastructure (SARI)](https://swissartresearch.net/) project.

## Classification taxonomy

Every image is assigned to one of the following classes:

| Class | Description |
|---|---|
| collage | Composite images made from multiple sources |
| drawing | Hand-drawn works (sketches, plans, illustrations) |
| handwritten document | Manuscripts and handwritten texts |
| machine-produced document | Typed or printed textual documents |
| painting | Painted artworks |
| photograph | Photographic images |
| print | Printed graphic works (engravings, lithographs, etc.) |
| unknown | Images that do not clearly fit any other category |

Annotation guidelines and edge-case discussions are documented in [this presentation](https://docs.google.com/presentation/d/17C8LQP0_mMth9kH3_mz7iJAH4nqMckNmvulq1g-tIYk/).

## Pipeline overview

The pipeline consists of four sequential steps:

1. **Image download** — Fetch images from the GTA IIIF server
2. **Labelling** — Annotate a representative sample on Roboflow
3. **Model training** — Fine-tune a YOLO11n-cls model on the annotated data
4. **Prediction** — Classify the full dataset with the trained model

### 1. Image download

Images are downloaded from the GTA Archive IIIF server (`iiif.gta.arch.ethz.ch`) using the [sari-iiif-clip-search](https://github.com/swiss-art-research-net/sari-iiif-clip-search) tool. The file `images-20231206.csv` (a [snapshot](https://raw.githubusercontent.com/swiss-art-research-net/sari-iiif-clip-search/46e07f7c31487c37954165218ad70be2bfb01a89/precomputedFeatures/grp/images.csv) of ~117k records) serves as the image index. Each image is stored locally in `clip_data/images/` under a hash-based filename derived from the `localIdentifier` column.

Since the original download, some IIIF URLs were renamed by the GTA Archive. To resolve current URLs from older filenames, look up the `iiif_url` base name in `rename-iiif/rename-alias-map.yml`.

### 2. Labelling

A sample of 2,183 images was annotated by student assistants on the [Roboflow](https://roboflow.com) platform (workspace: `sariimageannotation`, project: [`grp-image-classification`](https://universe.roboflow.com/sariimageannotation/grp-image-classification)). The annotation project was created on 2025-01-29 and the dataset (version 2) was exported on 2026-02-13 in folder format. The exported data lives in `grp-image-classification-dataset-v2/` and is split as follows:

| Split | Images |
|---|---:|
| Train | 1,515 |
| Validation | 367 |
| Test | 301 |
| **Total** | **2,183** |

The dataset is licensed under CC BY 4.0.

### 3. Model training

A pretrained [YOLO11n-cls](https://docs.ultralytics.com/models/yolo11/) model (`models/yolo11n-cls.pt`, from the Ultralytics model hub) was fine-tuned on the annotated dataset. Training was carried out in the notebook `notebooks/train_yolo_classification_model.ipynb` using Ultralytics 8.3.40, PyTorch 2.9.1, and Apple MPS acceleration.

Key training settings (full configuration in `runs/classify/train42/args.yaml`):

- Image size: 640 × 640
- Batch size: 16
- Max epochs: 100 (early stopping with patience 20)
- Optimizer: auto (SGD)
- Seed: 0, deterministic mode enabled

Training stopped at epoch 44 after ~25 minutes. The best checkpoint was saved as `models/yolo11n-cls-grp.pt` (1.5M parameters, 3.2 GFLOPs).

**Evaluation on the held-out test split:**

| Metric | Score |
|---|---:|
| Top-1 accuracy | 93.69% |
| Top-5 accuracy | 99.67% |

Per-epoch metrics are recorded in `runs/classify/train42/results.csv`.

### 4. Prediction

The script `scripts/run_dataset_classification.py` applies the trained model to the full image dataset. It processes images in configurable batches, displays a progress bar, and supports interruption with graceful resume.

**Basic usage:**

```bash
python scripts/run_dataset_classification.py \
    --model ./models/yolo11n-cls-grp.pt \
    --data-dir ./clip_data \
    --output ./predictions.csv
```

The output CSV contains one row per image with the following columns:

| Column | Description |
|---|---|
| `absolute_image_path` | Full path to the source image |
| `image_file_name` | Filename (hash-based identifier) |
| `top1_class` / `top1_confidence` | Most likely class and its confidence |
| `top2_class` / `top2_confidence` | Second most likely class and its confidence |
| `top3_class` / `top3_confidence` | Third most likely class and its confidence |

Images that fail to decode (e.g. truncated files) are logged to a separate `*.skipped.csv` file rather than halting the run. A complete run over ~131k images produced `predictions_test.csv`, with only 2 images skipped due to corruption.

**Selected CLI options:**

| Flag | Default | Description |
|---|---|---|
| `--batch-size` | 64 | Images per inference batch |
| `--device` | auto | Inference device (`cpu`, `0`, `mps`) |
| `--top-k` | 3 | Number of top predictions to store (1–3) |
| `--no-resume` | off | Discard previous progress and start fresh |
| `--max-images` | all | Cap on images to process (useful for testing) |
| `--output` | `classification_predictions.csv` | Output path (`.csv` or `.parquet`) |

## Repository structure

```
.
├── README.md
├── pipeline_provenance_questionnaire.md       # Detailed provenance documentation
├── images-20231206.csv                        # Image index (IIIF URLs + identifiers)
├── predictions_test.csv                       # Classification output (~131k images)
├── scripts/
│   └── run_dataset_classification.py          # Batch inference script
├── notebooks/
│   ├── train_yolo_classification_model.ipynb  # Training & evaluation notebook
│   └── explore_images.ipynb                   # Utility notebook for image lookup
├── models/
│   ├── yolo11n-cls.pt                         # Pretrained YOLO11n-cls weights
│   └── yolo11n-cls-grp.pt                     # Fine-tuned model (best checkpoint)
├── grp-image-classification-dataset-v2/       # Annotated dataset from Roboflow
├── runs/classify/train42/                     # Training artifacts (metrics, config)
├── rename-iiif/                               # IIIF URL renaming map and scripts
└── clip_data/                                 # Downloaded images (gitignored)
```

## Requirements

- Python 3.12+
- [Ultralytics](https://github.com/ultralytics/ultralytics) (tested with 8.3.40)
- PyTorch (tested with 2.9.1)
- tqdm
- For training/dataset export: [Roboflow SDK](https://github.com/roboflow/roboflow-python) and a `ROBOFLOW_API_KEY` in `.env`

## Provenance

Full provenance documentation — covering data sources, annotation details, software versions, model configuration, and responsible actors — is available in [`pipeline_provenance_questionnaire.md`](pipeline_provenance_questionnaire.md).

## License

The annotated dataset is released under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
