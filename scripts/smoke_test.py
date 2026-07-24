#!/usr/bin/env python3
"""Run a small end-to-end API smoke test against a running service."""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from pathlib import Path


def _request(url: str, *, method: str = "GET", body: bytes | None = None) -> bytes:
    """Send one HTTP request and return its response bytes.

    Args:
        url: Absolute endpoint URL.
        method: HTTP method.
        body: Optional JSON request bytes.

    Returns:
        Response body.

    Raises:
        SystemExit: If the service returns an HTTP or connection error.
    """
    headers = {"Content-Type": "application/json"} if body is not None else {}
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.read()
    except (urllib.error.HTTPError, urllib.error.URLError) as exc:
        raise SystemExit(f"Smoke test request failed: {exc}") from exc


def main() -> None:
    """Generate and download one XTX from a running local API."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--request", type=Path, default=Path("examples/request.json"))
    parser.add_argument("--output", type=Path, default=Path("data/generated/smoke-test.xtx"))
    args = parser.parse_args()

    health = json.loads(_request(f"{args.base_url}/health"))
    if health != {"status": "ok"}:
        raise SystemExit(f"Unexpected health response: {health}")

    payload = args.request.read_bytes()
    generated = json.loads(_request(f"{args.base_url}/v1/xtx", method="POST", body=payload))
    document = _request(generated["download_url"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(document)
    print(f"PASS: generated and downloaded {args.output}")


if __name__ == "__main__":
    main()
