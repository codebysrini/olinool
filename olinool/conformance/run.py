#!/usr/bin/env python3
"""Run the conformance corpus against the reference verifier.

    python3 conformance/run.py                      # shipped corpus (the truth)
    python3 conformance/run.py path/to/vectors/     # an external vector dir

The corpus lives inside the package (`olinool/conformance/vectors/`) so the
built wheel is self-testing: `python -m olinool.conformance`. This wrapper adds
the repo-checkout sys.path shim and an optional external-directory mode for
certifying vectors that are not (yet) shipped.
"""
from __future__ import annotations

import json
import pathlib
import sys

for _sib in ("python", "../moolam/python", "../olinool/python"):
    sys.path.insert(0, str((pathlib.Path(__file__).resolve().parent.parent / _sib).resolve()))

from olinool.conformance import certify, run_vector  # noqa: E402


def main() -> None:
    if len(sys.argv) > 1:
        vectors = sorted(pathlib.Path(sys.argv[1]).glob("*.json"))
        if not vectors:
            print(f"no vectors found in {sys.argv[1]}")
            sys.exit(2)
        results = [run_vector(json.loads(p.read_text())) for p in vectors]
        print(f"\n{sum(results)}/{len(results)} vectors passed")
        sys.exit(0 if all(results) else 1)
    sys.exit(certify())


if __name__ == "__main__":
    main()
