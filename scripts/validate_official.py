#!/usr/bin/env python3
"""Validate one generated XTX against a supplied official NTA root XSD."""

from __future__ import annotations

import argparse
from pathlib import Path

from app.errors import XtxValidationError
from app.validator import validate_xtx


def main() -> None:
    """Parse arguments and validate the requested XTX document."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xtx", type=Path, help="Generated .xtx file")
    parser.add_argument(
        "--schema",
        required=True,
        type=Path,
        help="Official RKO0010-250.xsd path inside the extracted e-tax19 tree",
    )
    args = parser.parse_args()
    try:
        validate_xtx(args.xtx.read_bytes(), args.schema)
    except XtxValidationError as exc:
        for error in exc.errors:
            print(error)
        raise SystemExit(1) from exc
    print(f"VALID: {args.xtx} against {args.schema}")


if __name__ == "__main__":
    main()
