#!/usr/bin/env python3
"""Convert a JSON-LD file to RDF/XML and validate the output triples."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert JSON-LD provenance data to RDF/XML and validate triples."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("./provenance/pipeline_provenance.jsonld"),
        help="Path to input JSON-LD file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("./provenance/pipeline_provenance.rdf"),
        help="Path to output RDF/XML file.",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip re-parsing the generated RDF/XML for validation.",
    )
    return parser.parse_args()


def convert_jsonld_to_rdfxml(input_path: Path, output_path: Path) -> int:
    try:
        from rdflib import Graph
    except ImportError as exc:
        raise RuntimeError(
            "rdflib is required. Install it with: pip install rdflib rdflib-jsonld"
        ) from exc

    graph = Graph()
    graph.parse(str(input_path.resolve()), format="json-ld")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=str(output_path.resolve()), format="xml")
    return len(graph)


def validate_rdfxml(output_path: Path, expected_triples: int) -> int:
    try:
        from rdflib import Graph
    except ImportError as exc:
        raise RuntimeError(
            "rdflib is required. Install it with: pip install rdflib rdflib-jsonld"
        ) from exc

    validation_graph = Graph()
    validation_graph.parse(str(output_path.resolve()), format="xml")
    parsed_triples = len(validation_graph)

    if parsed_triples != expected_triples:
        raise RuntimeError(
            "Validation failed: triple count mismatch "
            f"(source={expected_triples}, rdfxml={parsed_triples})."
        )

    return parsed_triples


def main() -> int:
    args = parse_args()
    input_path = args.input.resolve()
    output_path = args.output.resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"Input JSON-LD file not found: {input_path}")

    print(f"Input JSON-LD: {input_path}")
    print(f"Output RDF/XML: {output_path}")

    source_triples = convert_jsonld_to_rdfxml(input_path=input_path, output_path=output_path)
    print(f"Conversion complete. Source triples: {source_triples}")

    if args.skip_validation:
        print("Validation skipped (--skip-validation).")
        return 0

    parsed_triples = validate_rdfxml(output_path=output_path, expected_triples=source_triples)
    print(f"Validation passed. Parsed RDF/XML triples: {parsed_triples}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pylint: disable=broad-exception-caught
        print(f"Error: {exc}", file=sys.stderr)
        raise
