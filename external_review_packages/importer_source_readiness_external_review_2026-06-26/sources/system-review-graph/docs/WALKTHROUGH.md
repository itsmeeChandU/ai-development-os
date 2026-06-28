# Walkthrough

This walkthrough uses the bundled fictional example.

## 1. Validate The Manifest

```bash
system-review-graph validate --manifest examples/fictional_ai_ops/system_review_manifest.json
```

Expected:

```text
manifest valid
```

## 2. Build The Report

```bash
system-review-graph build \
  --manifest examples/fictional_ai_ops/system_review_manifest.json \
  --out-dir examples/fictional_ai_ops/reports \
  --depth deep
```

Outputs:

```text
examples/fictional_ai_ops/reports/system_review_graph.json
examples/fictional_ai_ops/reports/system_review_graph.md
```

Depth options:

- `overview`: fastest orientation.
- `standard`: normal audit handoff.
- `deep`: blueprint-level report with relationship graph and per-system drill-downs.
- `blueprint`: deepest report with source evidence, operational flows, control points, and gaps.

## 3. Read The Report Like A Reviewer

Start with:

- Bigger Picture
- Current Truth
- System Graph
- Systems
- Decision Gates
- Workflows
- Walkthroughs

The report should answer:

- What does the system do?
- What are the major subsystems?
- What artifacts prove each subsystem exists?
- Which gates block unsafe action?
- What can be shared publicly?
- What is still unproven?

## 4. Apply To Your Project

Create your own manifest:

```bash
system-review-graph init-example --out-dir /tmp/my-system-review --force
```

Then edit:

```text
/tmp/my-system-review/system_review_manifest.json
```

Replace the fictional systems with your own:

- web app,
- API,
- database,
- data pipeline,
- ML model,
- event bus,
- admin UI,
- approval workflow,
- reporting layer.

## 5. For Private Systems

If you cannot expose internals:

- use sanitized schemas,
- remove raw sample values,
- replace database paths with logical names,
- publish counts instead of records,
- describe gates and redaction boundaries,
- include examples with fake data only.

The report should teach the architecture without leaking the company.

## 6. Check Report Quality

Run:

```bash
system-review-graph doctor --manifest examples/fictional_ai_ops/system_review_manifest.json
```

The doctor command reports missing boundaries, shallow workflows, unresolved
references, and missing review/audit surfaces.

## 7. Generate HTML Or DOT

```bash
system-review-graph build \
  --manifest examples/actual_repos/fastapi/system_review_manifest.json \
  --out-dir /tmp/fastapi-system-review \
  --depth deep \
  --html \
  --dot
```

Outputs:

```text
system_review_graph.md
system_review_graph.json
system_review_graph.html
system_review_graph.dot
```

## 8. Scan A Mixed-Language Repo

```bash
system-review-graph scan \
  --repo /path/to/repo \
  --out /tmp/system_review_manifest.json
```

The manifest/report model is language-neutral. The automatic scanner currently
detects starter surfaces for C, C++, Java/Kotlin, C#/.NET, Python,
JavaScript/TypeScript, Go, Rust, docs, tests, and common build/config files.
It is a starting point, not a proof of runtime behavior. For a language or
architecture the scanner does not detect yet, write the manifest directly and
set `language_stack`, `code_surfaces`, artifacts, workflows, gates, and
boundaries yourself.

## 9. Try Actual Public Repos

The `examples/actual_repos/` folder contains public-review manifests for real
open-source repositories. They are educational maps, not official maintainer
audits.

```bash
system-review-graph build \
  --manifest examples/actual_repos/duckdb/system_review_manifest.json \
  --out-dir examples/actual_repos/duckdb/reports \
  --depth deep
```

Use these examples to learn how different architecture shapes map into the same
review grammar:

- framework repo,
- database engine,
- component pipeline.

## 10. Generate A Map-Of-Maps Atlas

For very large repositories, use atlas mode:

```bash
system-review-graph scan \
  --repo /path/to/linux-or-monorepo \
  --atlas \
  --out /tmp/system-review-atlas \
  --max-subsystems 24 \
  --build-reports \
  --depth overview
```

Outputs:

```text
/tmp/system-review-atlas/system_review_manifest.json
/tmp/system-review-atlas/reports/system_review_graph.md
/tmp/system-review-atlas/subsystems/<subsystem>/system_review_manifest.json
/tmp/system-review-atlas/subsystems/<subsystem>/reports/system_review_graph.md
```

Read the root report first. It shows the current truth, a map-of-maps diagram,
and a child-map table. Then open the subsystem that changed, failed review, or
needs deeper analysis.

Atlas mode is also useful in CI:

```bash
system-review-graph scan \
  --repo . \
  --atlas \
  --out reports/system-review-atlas \
  --max-subsystems 16 \
  --build-reports
```

The generated report can be attached to pull requests or compared after merges
to spot architecture drift, missing gates, and new subsystem surfaces.

## 11. Read A Blueprint Report

When a project needs a true blueprint, add `blueprint_sections` and render with
`--depth blueprint`:

```bash
system-review-graph build \
  --manifest examples/actual_repos/linux_kernel/system_review_manifest.json \
  --out-dir examples/actual_repos/linux_kernel/reports \
  --depth blueprint \
  --html \
  --dot
```

Read it like this:

- Start with `Current Truth` to know the proof boundary.
- Use `Map Of Maps` to choose a subsystem.
- Use `Blueprint Map` to choose an end-to-end flow.
- Use `Blueprint Sections` to inspect source evidence, flow steps, control
  points, review questions, and known gaps.

A blueprint section is how SRG turns code evidence into system meaning. It does
not merely say that two functions connect. It says what operational path those
functions represent and how confidently that path is proven.
