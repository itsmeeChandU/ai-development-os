# Package Audit

The package audit verifies that a review package is inspectable and does not
leak local machine details.

## Command

```bash
python3 scripts/audit_external_package.py --root .
```

To inspect a zip:

```bash
python3 scripts/audit_external_package.py --zip path/to/package.zip
```

## Required Result

```text
External package audit: PASS
```

## Checks

- no path traversal entries in zip files
- no `/Users/` or `file:///Users/` references
- no obvious secret markers
- `SOURCE_OF_TRUTH.md` exists
- `RUN_RESULTS.md` exists
- `REDACTION_REPORT.md` exists
- `REVIEW_USE_TERMS.md` exists
- canonical generated reports exist
