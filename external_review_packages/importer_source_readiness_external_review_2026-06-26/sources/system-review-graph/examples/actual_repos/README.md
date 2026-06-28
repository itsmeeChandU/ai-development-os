# Actual Public Repo Examples

These examples are public-review manifests for real open-source repositories.
They are not official audits from the maintainers. They are hand-authored maps
based on public repo surfaces and public documentation.

The goal is to show how System Review Graph can be used across different
architecture shapes:

| Example | Repo | Architecture shape |
|---|---|---|
| FastAPI | `fastapi/fastapi` | Python web/API framework |
| DuckDB | `duckdb/duckdb` | Embedded analytical database engine |
| OpenTelemetry Collector | `open-telemetry/opentelemetry-collector` | Go telemetry pipeline and component framework |
| Linux Kernel Atlas | `torvalds/linux` | Large source-tree atlas with child maps and blueprint flows |

Generated reports include coverage, evidence, gap, and action registers. Use
those registers first when reviewing an example: they show what the report
covers, what evidence is declared, what remains open, and what the next review
actions are.

Build one report:

```bash
system-review-graph build \
  --manifest examples/actual_repos/fastapi/system_review_manifest.json \
  --out-dir examples/actual_repos/fastapi/reports
```

Copy one example as a starting point:

```bash
system-review-graph init-example \
  --example actual_repos/opentelemetry_collector \
  --out-dir /tmp/my-system-review \
  --force
```

## Public-Safe Rule

For actual repos, keep the examples limited to:

- public source paths,
- public docs,
- architecture interpretation,
- public interfaces and contracts,
- reviewer questions.

Do not add private deployment details, production data, non-public customer
information, secrets, or maintainer-only operational assumptions.
