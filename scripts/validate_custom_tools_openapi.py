#!/usr/bin/env python3
"""Validate a Custom Tools OpenAPI artifact against the SDK's supported profile."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from tamarind_codegen.custom_tools.profile import validate_profile


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("spec", type=Path)
    args = parser.parse_args()
    validate_profile(json.loads(args.spec.read_text(encoding="utf-8")))


if __name__ == "__main__":
    main()
