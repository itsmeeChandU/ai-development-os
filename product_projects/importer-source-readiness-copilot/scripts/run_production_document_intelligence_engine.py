#!/usr/bin/env python3
"""Generate production document intelligence artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness.production_document_intelligence_engine import (
    build_production_document_intelligence_engine,
    ensure_parser_qa_documents,
    write_production_document_intelligence_engine_artifacts,
)


def main() -> int:
    ensure_parser_qa_documents(ROOT)
    payload = build_production_document_intelligence_engine(ROOT)
    paths = write_production_document_intelligence_engine_artifacts(payload, ROOT)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "pipeline_stage_count": payload["pipeline_stage_count"],
                "document_record_count": payload["document_record_count"],
                "official_sample_document_count": payload["official_sample_document_count"],
                "source_route_only_sample_count": payload["source_route_only_sample_count"],
                "synthetic_parser_fixture_count": payload["synthetic_parser_fixture_count"],
                "extracted_field_count": payload["extracted_field_count"],
                "parser_qa_status": payload["parser_qa_status"],
                "parser_qa_passed_count": payload["parser_qa_passed_count"],
                "parser_qa_needs_rule_count": payload["parser_qa_needs_rule_count"],
                "sample_library_status": payload["sample_library_status"],
                "sample_library_count": payload["sample_library_count"],
                "sample_library_official_pdf_count": payload["sample_library_official_pdf_count"],
                "sample_library_source_route_only_count": payload["sample_library_source_route_only_count"],
                "claims_opened": payload["claims_opened"],
                "external_effects_created": payload["external_effects_created"],
                "manifest": str(paths["manifest"].relative_to(ROOT)),
                "pipeline": str(paths["pipeline"].relative_to(ROOT)),
                "fields": str(paths["fields"].relative_to(ROOT)),
                "parser_qa": str(paths["parser_qa"].relative_to(ROOT)),
                "sample_library": str(paths["sample_library"].relative_to(ROOT)),
                "doc": str(paths["doc"].relative_to(ROOT)),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
