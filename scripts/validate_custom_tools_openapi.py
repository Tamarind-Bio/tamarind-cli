#!/usr/bin/env python3
"""Validate a Custom Tools OpenAPI artifact against the SDK's supported profile."""

from __future__ import annotations

import argparse
from pathlib import Path

from tamarind_codegen.custom_tools.json_loader import load_json_document
from tamarind_codegen.custom_tools.profile import validate_profile
from tamarind_codegen.custom_tools.project import project_custom_tools


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("spec", type=Path)
    args = parser.parse_args()
    validate_profile(project_custom_tools(load_json_document(args.spec.read_bytes())))


if __name__ == "__main__":
    main()
