#!/usr/bin/env python3
"""Generate the CLI's v1 operation manifest from the vendored v1 contract.

The v1 contract (``openapi/api-v1.yaml``, vendored from tamarind-website) names,
for every operation, its CLI command in ``x-clients.cli``. The CLI builds its v1
commands from this manifest: path parameters become positional arguments, query
parameters options, and a request body ``--input``/``--set``. Reading a compact
JSON file keeps CLI startup fast; this script keeps it in step with the contract.

    uv run python scripts/gen_v1_cli_manifest.py          # rewrite the manifest
    uv run python scripts/gen_v1_cli_manifest.py --check  # fail if it is stale

``tests/test_v1_cli_parity.py`` runs the same check in CI, and also fails when an
operation's CLI command does not exist.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "openapi" / "api-v1.yaml"
MANIFEST = ROOT / "src" / "tamarind" / "cli" / "v1" / "_operations.json"
METHODS = ("get", "post", "put", "patch", "delete")
# Options every generic command defines itself; a query parameter with one of
# these names would be shadowed.
RESERVED_OPTIONS = {"input", "set", "idempotency-key", "if-match", "all", "help"}


def _first_paragraph(text: str | None, limit: int = 600) -> str:
    if not text:
        return ""
    para = text.strip().split("\n\n", 1)[0]
    para = " ".join(para.split())
    return para if len(para) <= limit else para[: limit - 1].rstrip() + "…"


def _first_sentence(text: str | None, limit: int = 240) -> str:
    para = _first_paragraph(text, 2000)
    # "e.g." and "i.e." end no sentence.
    match = re.match(r"(.+?(?<!\be\.g)(?<!\bi\.e)[.!?])(\s|$)", para)
    sentence = match.group(1) if match else para
    return sentence if len(sentence) <= limit else sentence[: limit - 1].rstrip() + "…"


class Contract:
    def __init__(self, doc: dict[str, Any]) -> None:
        self.doc = doc

    def resolve(self, node: Any) -> Any:
        seen = 0
        while isinstance(node, dict) and "$ref" in node:
            target: Any = self.doc
            for part in node["$ref"].lstrip("#/").split("/"):
                target = target[part]
            node = target
            seen += 1
            if seen > 20:
                raise ValueError("reference cycle")
        return node

    def scalar(self, schema: Any) -> dict[str, Any]:
        """The JSON type, enum and default of a parameter schema."""
        schema = self.resolve(schema or {})
        for key in ("anyOf", "oneOf"):
            if key in schema:
                options = [self.resolve(s) for s in schema[key]]
                options = [s for s in options if s.get("type") != "null"]
                if len(options) == 1:
                    merged = dict(options[0])
                    merged.setdefault("default", schema.get("default"))
                    schema = merged
        kind = schema.get("type")
        if isinstance(kind, list):
            kind = next((k for k in kind if k != "null"), None)
        out: dict[str, Any] = {"type": kind or "string"}
        if kind == "array":
            items = self.resolve(schema.get("items") or {})
            out["items"] = items.get("type") or "string"
            if items.get("enum"):
                out["enum"] = [str(v) for v in items["enum"]]
        elif schema.get("enum"):
            out["enum"] = [str(v) for v in schema["enum"]]
        if "default" in schema and schema["default"] is not None:
            out["default"] = schema["default"]
        return out


def build(doc: dict[str, Any]) -> dict[str, Any]:
    contract = Contract(doc)
    operations = []
    for path, item in doc["paths"].items():
        shared = item.get("parameters", [])
        for method in METHODS:
            op = item.get(method)
            if not op:
                continue
            clients = op.get("x-clients") or {}
            params = [contract.resolve(p) for p in [*shared, *op.get("parameters", [])]]
            path_params = [p for p in params if p.get("in") == "path"]
            order = re.findall(r"{([^}]+)}", path)
            path_params.sort(key=lambda p: order.index(p["name"]))
            query = []
            for p in params:
                if p.get("in") != "query":
                    continue
                entry = {
                    "name": p["name"],
                    "description": _first_sentence(p.get("description")),
                    "required": bool(p.get("required")),
                    **contract.scalar(p.get("schema")),
                }
                option = re.sub(r"(?<!^)(?=[A-Z])", "-", p["name"]).lower()
                if option in RESERVED_OPTIONS:
                    raise SystemExit(f"{op['operationId']}: query parameter {p['name']!r} clashes")
                entry["option"] = option
                query.append(entry)
            headers = sorted(p["name"] for p in params if p.get("in") == "header")
            body = None
            if op.get("requestBody"):
                rb = contract.resolve(op["requestBody"])
                body = {
                    "required": bool(rb.get("required")),
                    "contentTypes": sorted(rb.get("content", {})),
                    "description": _first_sentence(rb.get("description")),
                }
            success = {}
            for code, resp in op.get("responses", {}).items():
                if not str(code).startswith("2"):
                    continue
                resp = contract.resolve(resp)
                success[str(code)] = sorted(resp.get("content", {}))
            operations.append(
                {
                    "operationId": op["operationId"],
                    "tag": (op.get("tags") or [None])[0],
                    "method": method.upper(),
                    "path": path,
                    "cli": clients.get("cli"),
                    "sdk": clients.get("sdk"),
                    "summary": _first_sentence(op.get("summary") or op.get("description"), 120),
                    "description": _first_paragraph(op.get("description")),
                    "pathParams": [
                        {"name": p["name"], "description": _first_sentence(p.get("description"))}
                        for p in path_params
                    ],
                    "query": query,
                    "headers": [h for h in headers if h in ("Idempotency-Key", "If-Match")],
                    "body": body,
                    "success": success,
                }
            )
    return {
        "source": "openapi/api-v1.yaml",
        "info": {"title": doc.get("info", {}).get("title"), "version": doc.get("info", {}).get("version")},
        "tags": {t["name"]: _first_sentence(t.get("description")) for t in doc.get("tags", [])},
        "operations": operations,
    }


def render(manifest: dict[str, Any]) -> str:
    return json.dumps(manifest, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="Fail if the manifest is stale.")
    args = parser.parse_args(argv)
    expected = render(build(yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))))
    if args.check:
        current = MANIFEST.read_text(encoding="utf-8") if MANIFEST.exists() else ""
        if current != expected:
            print(f"{MANIFEST.relative_to(ROOT)} is stale; run scripts/gen_v1_cli_manifest.py", file=sys.stderr)
            return 1
        return 0
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(expected, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
