"""``python -m tamarind.finetune predict``: serve a trained artifact once. See ``predict.py``."""

from __future__ import annotations

import sys

from tamarind.finetune.predict import main

if __name__ == "__main__":
    sys.exit(main())
