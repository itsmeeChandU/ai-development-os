# Redaction Report

The review package and generated artifacts must not expose local machine paths
or reviewer-confusing file URLs.

## Blocked Patterns

```text
/Users/
file:///Users/
```

## Required Checks

```bash
python3 scripts/audit_external_package.py --root .
```

The package audit also checks for path traversal entries in zip files, obvious
secret markers, canonical report documentation, run results, and review terms.
