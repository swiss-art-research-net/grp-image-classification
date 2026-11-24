#!/usr/bin/env python3
"""Package a JSON-LD provenance graph as a TriG file with a single named graph.

Uses pyoxigraph (Rust) for parsing and serialization. pyoxigraph's JSON-LD parser
does not fetch remote contexts, so the ``@context`` of the input is resolved here
(downloaded once, cached on disk) and inlined into the stream fed to the parser.
The input file itself is never modified or loaded fully into memory by Python.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_GRAPH_BASE = "http://data.gta.arch.ethz.ch/provolone/grp-image-classification"
DEFAULT_CACHE_DIR = Path(".cache/jsonld-contexts")
HEADER_BYTES = 1 << 20  # the top-level @context must start within the first MiB


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Package JSON-LD provenance as a TriG named graph ready for ingestion."
    )
    parser.add_argument("--input", type=Path, required=True, help="Input JSON-LD file.")
    parser.add_argument("--output", type=Path, required=True, help="Output TriG file.")
    parser.add_argument(
        "--graph-base",
        default=DEFAULT_GRAPH_BASE,
        help="Base URL of the named graph (default: %(default)s).",
    )
    parser.add_argument(
        "--graph-name",
        default="",
        help="Optional name appended to the base URL (BASE/NAME). "
        "If empty, the base URL itself is the graph IRI.",
    )
    parser.add_argument(
        "--context-cache",
        type=Path,
        default=DEFAULT_CACHE_DIR,
        help="Directory where downloaded JSON-LD contexts are cached (default: %(default)s).",
    )
    parser.add_argument(
        "--no-prune-context",
        action="store_true",
        help="Keep unused term definitions in the context (much slower, same output).",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip re-parsing the generated TriG for validation.",
    )
    return parser.parse_args()


def graph_iri(base: str, name: str) -> str:
    base = base.strip().rstrip("/")
    name = name.strip().strip("/")
    if not base:
        raise ValueError("Graph base URL must not be empty.")
    if not base.startswith(("http://", "https://")):
        raise ValueError(f"Graph base URL must be an absolute http(s) URL: {base!r}")
    return f"{base}/{name}" if name else base


# --------------------------------------------------------------------------- #
# Context resolution
# --------------------------------------------------------------------------- #
def fetch_context(url: str, cache_dir: Path) -> Any:
    """Return the ``@context`` value of a remote JSON-LD context document (cached)."""
    cache_file = cache_dir / (hashlib.sha1(url.encode()).hexdigest() + ".json")
    if cache_file.exists():
        document = json.loads(cache_file.read_text(encoding="utf-8"))
    else:
        request = urllib.request.Request(
            url,
            headers={"Accept": "application/ld+json, application/json;q=0.9"},
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            document = json.loads(response.read().decode("utf-8"))
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(document), encoding="utf-8")
    if not isinstance(document, dict) or "@context" not in document:
        raise ValueError(f"Remote context {url} has no top-level @context.")
    return document["@context"]


def inline_context(context: Any, cache_dir: Path) -> Any:
    """Replace remote context URLs (recursively) with their downloaded content."""
    if isinstance(context, str):
        return inline_context(fetch_context(context, cache_dir), cache_dir)
    if isinstance(context, list):
        return [inline_context(item, cache_dir) for item in context]
    return context


def collect_prefixes(context: Any) -> dict[str, str]:
    """Namespace prefixes declared as plain ``prefix -> IRI ending in / or #``."""
    prefixes: dict[str, str] = {}
    if isinstance(context, list):
        for item in context:
            prefixes.update(collect_prefixes(item))
    elif isinstance(context, dict):
        for key, value in context.items():
            if (
                not key.startswith("@")
                and isinstance(value, str)
                and value.startswith(("http://", "https://"))
                and value.endswith(("/", "#"))
            ):
                prefixes[key] = value
    return prefixes


_KEY_RE = re.compile(rb'"([^"\\\n]+)"\s*:')
_TYPE_RE = re.compile(rb'"(?:type|@type)"\s*:\s*"([^"\\\n]+)"')
_SCAN_BLOCK = 16 << 20


def scan_used_terms(path: Path) -> set[str]:
    """Collect every JSON key and ``type`` value that occurs in the file (superset of used terms)."""
    used: set[bytes] = set()
    with path.open("rb") as handle:
        carry = b""
        while True:
            block = handle.read(_SCAN_BLOCK)
            data = carry + block
            if not block:
                cut = len(data)
            else:
                cut = data.rfind(b"\n") + 1  # never split a token across blocks
                if cut == 0:
                    carry = data
                    continue
            used.update(_KEY_RE.findall(data[:cut]))
            used.update(_TYPE_RE.findall(data[:cut]))
            carry = data[cut:]
            if not block:
                break
    return {term.decode("utf-8", errors="ignore") for term in used}


def prune_context(context: Any, used: set[str]) -> Any:
    """Drop term definitions the data never uses.

    The linked-art context defines hundreds of terms (plus type-scoped contexts), and
    Oxigraph's JSON-LD parser re-processes it for every typed node, which makes parsing
    ~10x slower. Removing unused definitions cannot change the triples produced.
    Kept: keywords, prefix declarations, keyword aliases (``id``, ``type``...), and
    any term that occurs in the data as a key or ``type`` value.
    """
    if isinstance(context, list):
        return [prune_context(item, used) for item in context]
    if not isinstance(context, dict):
        return context
    pruned = {}
    for key, value in context.items():
        alias_of_keyword = (isinstance(value, str) and value.startswith("@")) or (
            isinstance(value, dict) and str(value.get("@id", "")).startswith("@")
        )
        is_prefix = isinstance(value, str) and value.endswith(("/", "#"))
        if key.startswith("@") or key in used or alias_of_keyword or is_prefix:
            pruned[key] = value
    return pruned


class ChainReader(io.RawIOBase):
    """Read-only binary stream: ``prefix`` bytes followed by the rest of ``tail``."""

    def __init__(self, prefix: bytes, tail: io.BufferedReader) -> None:
        self._prefix = memoryview(prefix)
        self._tail = tail

    def readable(self) -> bool:
        return True

    def readinto(self, buffer) -> int:  # type: ignore[no-untyped-def]
        if len(self._prefix):
            n = min(len(buffer), len(self._prefix))
            buffer[:n] = self._prefix[:n]
            self._prefix = self._prefix[n:]
            return n
        return self._tail.readinto(buffer)

    def close(self) -> None:
        self._tail.close()
        super().close()


def open_with_inlined_context(
    path: Path, cache_dir: Path, prune: bool = True
) -> tuple[io.BufferedReader, dict[str, str]]:
    """Open ``path`` as a byte stream whose top-level @context has no remote references."""
    handle = path.open("rb")
    head = handle.read(HEADER_BYTES)
    text = head.decode("utf-8", errors="ignore")
    key = text.find('"@context"')
    if key < 0:
        handle.seek(0)
        return handle, {}
    colon = text.find(":", key + len('"@context"'))
    start = colon + 1
    while text[start].isspace():
        start += 1
    context, end = json.JSONDecoder().raw_decode(text, start)

    resolved = inline_context(context, cache_dir)
    prefixes = collect_prefixes(resolved)
    if prune:
        resolved = prune_context(resolved, scan_used_terms(path))

    # Everything before the context value is `{ "@context":` (whitespace aside);
    # keep that text, swap the value, then continue with the unread remainder.
    new_head = text[:start] + json.dumps(resolved) + text[end:]
    stream = ChainReader(new_head.encode("utf-8"), handle)
    return io.BufferedReader(stream, buffer_size=1 << 20), prefixes


# --------------------------------------------------------------------------- #
def main() -> int:
    args = parse_args()

    try:
        import pyoxigraph as ox
    except ImportError as exc:
        raise RuntimeError("pyoxigraph is required. Install it with: pip install pyoxigraph") from exc

    input_path = args.input.resolve()
    output_path = args.output.resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Input JSON-LD file not found: {input_path}")

    iri = graph_iri(args.graph_base, args.graph_name)
    print(f"Input JSON-LD: {input_path}")
    print(f"Output TriG:   {output_path}")
    print(f"Named graph:   {iri}")

    started = time.perf_counter()
    graph_name = ox.NamedNode(iri)

    # In-memory store de-duplicates triples (RDF set semantics) and relocates
    # them from the default graph into the named graph.
    store = ox.Store()
    stream, prefixes = open_with_inlined_context(
        input_path, args.context_cache, prune=not args.no_prune_context
    )
    with stream:
        store.bulk_load(stream, format=ox.RdfFormat.JSON_LD, to_graph=graph_name)
    triples = len(store)
    print(f"Parsed {triples} triples in {time.perf_counter() - started:.1f}s")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as out:
        ox.serialize(
            store.quads_for_pattern(None, None, None, graph_name),
            out,
            format=ox.RdfFormat.TRIG,
            prefixes=prefixes,
        )
    print(f"Wrote TriG in {time.perf_counter() - started:.1f}s")

    if args.skip_validation:
        print("Validation skipped (--skip-validation).")
        return 0

    check = ox.Store()
    check.bulk_load(path=str(output_path), format=ox.RdfFormat.TRIG)
    graphs = [g for g in check.named_graphs() if isinstance(g, ox.NamedNode)]
    if len(check) != triples or [g.value for g in graphs] != [iri]:
        raise RuntimeError(
            "Validation failed: "
            f"expected {triples} triples in <{iri}>, found {len(check)} quads "
            f"in graphs {[g.value for g in graphs]}."
        )
    print(f"Validation passed. Named graph <{iri}> has {triples} triples.")
    print(f"Total {time.perf_counter() - started:.1f}s")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pylint: disable=broad-exception-caught
        print(f"Error: {exc}", file=sys.stderr)
        raise
