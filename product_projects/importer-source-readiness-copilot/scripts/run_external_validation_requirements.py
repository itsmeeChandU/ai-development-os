#!/usr/bin/env python3
"""Generate the external validation requirements pack."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness.external_validation_research import write_external_validation_requirements


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate external validation and go-live input requirements.")
    parser.add_argument("--input-dir", default="", help="Directory containing returned real-person input JSON files.")
    args = parser.parse_args()
    input_dir = Path(args.input_dir).resolve() if args.input_dir else None
    result = write_external_validation_requirements(ROOT, input_dir=input_dir)
    print(f"external_validation_status={result['status']}")
    print(f"gate_count={result['gate_count']}")
    print(f"source_count={result['source_count']}")
    print(f"evidence_requirement_count={result['evidence_requirement_count']}")
    print(f"required_data_category_count={result['required_data_category_count']}")
    print(f"go_live_input_status={result['go_live_input_status']}")
    print(f"ready_input_count={result['ready_input_count']}")
    print(f"missing_input_count={result['missing_input_count']}")
    print(f"public_launch_ready={result['public_launch_ready']}")
    print(f"hosted_private_beta_ready={result['hosted_private_beta_ready']}")
    print(f"live_payment_ready={result['live_payment_ready']}")
    print(f"pdf_path={result['pdf_path']}")
    print(f"brief_pdf_path={result['brief_pdf_path']}")
    print(f"input_pdf_path={result['input_pdf_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
