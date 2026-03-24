#!/usr/bin/env python3
"""Generate a Mermaid diagram tracing the provenance of a single classification."""

from __future__ import annotations

import argparse
import json
import textwrap
from pathlib import Path
from typing import Any


def load_graph(path: Path) -> tuple[dict[str, str], list[dict]]:
    """Return (prefix_map, nodes) from a JSON-LD file."""
    data = json.loads(path.read_text())

    prefixes: dict[str, str] = {}
    for ctx in data.get("@context", []):
        if isinstance(ctx, dict):
            prefixes.update(ctx)

    return prefixes, data.get("@graph", [])


def expand_id(raw_id: str, prefixes: dict[str, str]) -> str:
    """Expand prefixed IDs like ``ex:foo`` using *prefixes*."""
    for pfx, uri in prefixes.items():
        if raw_id.startswith(f"{pfx}:"):
            return uri + raw_id[len(pfx) + 1 :]
    return raw_id


def build_index(nodes: list[dict]) -> dict[str, dict]:
    """Map every node ``id`` to its full dict."""
    return {n["id"]: n for n in nodes if "id" in n}


def _get_label(node: dict) -> str:
    """Best human-readable label for *node*."""
    if "_label" in node:
        return node["_label"]
    for ident in _as_list(node.get("identified_by", [])):
        if ident.get("type") == "Name":
            return ident.get("content", "")
    return node.get("id", "?")


def _get_description(node: dict) -> str:
    refs = node.get("referred_to_by")
    if refs is None:
        return ""
    if isinstance(refs, dict):
        refs = [refs]
    for r in refs:
        if r.get("type") == "LinguisticObject":
            return r.get("content", "")
    return ""


def _as_list(v: Any) -> list:
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def _safe_node_id(raw: str) -> str:
    """Mermaid-safe node identifier (alphanumeric + underscores)."""
    return "".join(c if c.isalnum() else "_" for c in raw)


def _wrap(text: str, width: int = 38) -> str:
    return "<br/>".join(textwrap.wrap(text, width))


# ── Shape helpers ────────────────────────────────────────────────────
SHAPE = {
    "DigitalReading": ("([", "])", "stadium"),       # rounded / stadium
    "Software": ("[[", "]]", "subroutine"),           # subroutine
    "DigitalObject": ("[(", ")]", "cylinder"),         # cylinder / database
    "Project": ("{{", "}}", "hexagon"),                # hexagon
    "ZE4_Classificatory_Status": ("[/", "\\]", "trap"),  # trapezoid
}


def _shape(node_type: str) -> tuple[str, str]:
    """Return (open_bracket, close_bracket) for a Mermaid shape."""
    for key, (opn, cls, _) in SHAPE.items():
        if key in node_type:
            return opn, cls
    return "[", "]"


# ── Diagram builder ─────────────────────────────────────────────────

def trace_provenance(
    target_id: str,
    index: dict[str, dict],
    prefixes: dict[str, str],
) -> str:
    """Return a Mermaid flowchart string for *target_id* and its upstream."""

    visited: set[str] = set()
    node_defs: list[str] = []
    edges: list[str] = []
    styles: list[str] = []

    def _resolve(ref: dict | str) -> dict | None:
        rid = ref if isinstance(ref, str) else ref.get("id", "")
        return index.get(rid) or index.get(expand_id(rid, prefixes))

    def visit(node_id: str) -> str | None:
        """Recursively visit *node_id*, returning its Mermaid node id."""
        if node_id in visited:
            return _safe_node_id(node_id)
        visited.add(node_id)

        node = index.get(node_id)
        if node is None:
            return None

        mid = _safe_node_id(node_id)
        ntype = node.get("type", "")
        opn, cls = _shape(ntype)

        label = _get_label(node)

        # Classificatory status: enrich with confidence + class
        if "Classificatory_Status" in ntype:
            cls_as = node.get("classified_as", {})
            cls_label = cls_as.get("_label", "")
            conf_node = node.get("confidence", {})
            conf_val = conf_node.get("value")
            parts = [f"<b>{label}</b>"]
            if cls_label:
                parts.append(f"Class: <i>{cls_label}</i>")
            if conf_val is not None:
                parts.append(f"Confidence: {conf_val:.4f}")
            inner = "<br/>".join(parts)
        elif ntype == "DigitalReading":
            desc = _get_description(node)
            inner = f"<b>{label}</b>"
            if desc:
                inner += f"<br/>{_wrap(desc, 42)}"
        else:
            desc = _get_description(node)
            inner = f"<b>{label}</b>"
            if desc:
                inner += f"<br/>{_wrap(desc, 42)}"

        node_defs.append(f"    {mid}{opn}\"{inner}\"{cls}")

        # ── Follow provenance edges ──────────────────────────────
        edge_props = [
            ("is_produced_by", "produced by"),
            ("model", "model"),
            ("code", "code"),
            ("input", "input"),
            ("output", "output"),
            ("part_of", "part of"),
            ("log_file", "log"),
        ]

        for prop, arrow_label in edge_props:
            for ref in _as_list(node.get(prop)):
                target = _resolve(ref)
                if target is None:
                    continue
                child_mid = visit(target["id"])
                if child_mid:
                    edges.append(f"    {mid} -->|{arrow_label}| {child_mid}")

        # Follow output backwards: if another DigitalReading produced
        # this node as its output, find that step.
        for other in index.values():
            for out_ref in _as_list(other.get("output")):
                out_node = _resolve(out_ref)
                if out_node and out_node["id"] == node_id:
                    if other.get("type") == "DigitalReading":
                        parent_mid = visit(other["id"])
                        if parent_mid:
                            edges.append(
                                f"    {mid} -.->|produced by| {parent_mid}"
                            )

        return mid

    root_mid = visit(target_id)
    if root_mid:
        styles.append(f"    style {root_mid} stroke:#e74c3c,stroke-width:3px")

    lines = ["graph LR"]
    lines.extend(node_defs)
    lines.append("")
    lines.extend(sorted(set(edges)))
    if styles:
        lines.append("")
        lines.extend(styles)

    return "\n".join(lines)


# ── CLI ──────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a Mermaid provenance diagram for a classification entity."
    )
    parser.add_argument(
        "jsonld",
        type=Path,
        help="Path to the pipeline_provenance.jsonld file.",
    )
    parser.add_argument(
        "entity_id",
        help="Full or prefixed ID of the target entity "
        "(e.g. ex:classificatorystatus/000494d4bcdac0c48d80be8e43b375ef26026aff).",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Write the diagram to this file (default: stdout).",
    )
    parser.add_argument(
        "--wrap-md",
        action="store_true",
        help="Wrap output in a Markdown fenced code block.",
    )
    args = parser.parse_args()

    prefixes, nodes = load_graph(args.jsonld)
    index = build_index(nodes)

    entity_id = args.entity_id
    if entity_id not in index:
        expanded = expand_id(entity_id, prefixes)
        if expanded in index:
            entity_id = expanded
        else:
            avail = [k for k in index if "classificatorystatus" in k.lower()]
            raise SystemExit(
                f"Entity '{args.entity_id}' not found in graph.\n"
                f"Example classificatory-status IDs:\n  "
                + "\n  ".join(avail[:5])
            )

    diagram = trace_provenance(entity_id, index, prefixes)

    if args.wrap_md:
        diagram = f"```mermaid\n{diagram}\n```"

    if args.output:
        args.output.write_text(diagram + "\n")
        print(f"Wrote diagram to {args.output}")
    else:
        print(diagram)


if __name__ == "__main__":
    main()
