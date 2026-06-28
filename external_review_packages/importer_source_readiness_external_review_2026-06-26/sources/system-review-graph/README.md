# System Review Graph

<p align="center">
  <a href="https://github.com/itsmeeChandU/system-review-graph">
    <img src="https://raw.githubusercontent.com/itsmeeChandU/system-review-graph/main/assets/system-review-graph-mark.svg" alt="System Review Graph mark" width="96">
  </a>
</p>

<p align="center">
  <a href="https://pypi.org/project/system-review-graph/"><img alt="PyPI version" src="https://img.shields.io/pypi/v/system-review-graph.svg?color=1456cc"></a>
  <a href="https://github.com/itsmeeChandU/system-review-graph/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/itsmeeChandU/system-review-graph/actions/workflows/ci.yml/badge.svg"></a>
  <img alt="Python 3.10+" src="https://img.shields.io/badge/python-3.10%2B-234b6d.svg">
  <a href="https://github.com/itsmeeChandU/system-review-graph/blob/main/LICENSE"><img alt="License MIT" src="https://img.shields.io/badge/license-MIT-2f855a.svg"></a>
  <a href="https://github.com/itsmeeChandU/system-review-graph/blob/main/docs/MCP.md"><img alt="MCP server" src="https://img.shields.io/badge/MCP-agent--ready-176b78.svg"></a>
</p>

<p align="center">
  <a href="https://github.com/itsmeeChandU/system-review-graph/blob/main/docs/METHODOLOGY.md"><img alt="System map" src="https://img.shields.io/badge/maps-system%20%3E%20code-176b78.svg"></a>
  <a href="#language-and-project-surface-support"><img alt="Mixed language scanner" src="https://img.shields.io/badge/scanner-mixed--language-d7a441.svg"></a>
  <a href="#depth-levels"><img alt="Blueprint depth" src="https://img.shields.io/badge/depth-blueprint-172033.svg"></a>
  <a href="https://github.com/itsmeeChandU/system-review-graph/blob/main/examples/actual_repos/linux_kernel/reports/system_review_graph.md"><img alt="Linux atlas example" src="https://img.shields.io/badge/example-Linux%20atlas-2f855a.svg"></a>
</p>

Turn any repo into a system-level review map:
what it does, what it trusts, what it blocks, and what reviewers should inspect next.

## 30-second demo

```bash
pip install system-review-graph
system-review-graph scan --repo ./my-repo --out system_review_manifest.json
system-review-graph build --manifest system_review_manifest.json --out-dir reports --html
```

<img src="https://raw.githubusercontent.com/itsmeeChandU/system-review-graph/main/assets/social-preview.svg" alt="System Review Graph demo" width="800">

## See generated reports

- [FastAPI system review](https://github.com/itsmeeChandU/system-review-graph/blob/main/examples/actual_repos/fastapi/reports/system_review_graph.md)
- [DuckDB system review](https://github.com/itsmeeChandU/system-review-graph/blob/main/examples/actual_repos/duckdb/reports/system_review_graph.md)
- [OpenTelemetry Collector system review](https://github.com/itsmeeChandU/system-review-graph/blob/main/examples/actual_repos/opentelemetry_collector/reports/system_review_graph.md)
- [Linux Kernel atlas](https://github.com/itsmeeChandU/system-review-graph/blob/main/examples/actual_repos/linux_kernel/reports/system_review_graph.md)

It turns a public or sanitized manifest into:

- a system-level graph,
- a reverse-engineering report,
- architecture and workflow maps,
- decision-gate documentation,
- coverage, evidence, gap, and action registers,
- schema and artifact references,
- walkthrough examples for reviewers, maintainers, and AI agents.
- optional HTML and Graphviz DOT outputs.
- optional map-of-maps atlases for huge repositories.
- blueprint-depth reports with source evidence, flows, control points, and known gaps.
- documentation knowledge graph support for repo file catalogs, concept/file/status nodes, cleanup links, and bounded MCP context slices.
- an MCP server so agents can scan, build, validate, and load atlas context.

This project is meant for open-source maintainers, platform teams, audit teams, AI coding agents, and new engineers who need to understand a repo as an operating system rather than a pile of files.

## Why This Exists

Most repo maps stop at modules, classes, functions, imports, and calls. That is useful, but it does not answer the questions a real reviewer asks:

- What does this system do?
- What are the decision gates?
- What data or artifacts feed each stage?
- What actions can happen downstream?
- What is blocked by human/legal/security review?
- What is covered, proven, open, and actionable?
- What can be shared publicly when the database is private?
- How could someone rebuild the system from the report?

System Review Graph is the opposite side of a code-review graph:

| Map | Answers |
|---|---|
| Code-review graph | What code exists and how it connects. |
| System Review Graph | What the system does, how it moves, what it trusts, and what it blocks. |

## How It Figures Out What A System Does

System Review Graph does **not** pretend that a call graph alone proves system
behavior.

The method is:

```text
sources -> artifacts -> schemas -> systems -> workflows -> gates -> outcomes -> review questions
```

Code shows what can happen. A system review asks what actually moves through
the system, what contracts shape it, what gates control it, what artifacts prove
it, and what the reviewer should inspect next.

The report is built from a manifest because many real systems cannot safely
publish raw databases, production data, credentials, model weights, or private
service internals. The manifest can be generated by humans, scripts, AI agents,
or future repo scanners.

Use code as evidence, but not the only evidence:

- source directories,
- function and module surfaces,
- CLI entry points,
- APIs and route files,
- schemas and migrations,
- configs,
- tests,
- docs,
- queues, reports, dashboards, and logs,
- human/legal/security gates.

Read more in
[`docs/METHODOLOGY.md`](https://github.com/itsmeeChandU/system-review-graph/blob/main/docs/METHODOLOGY.md).

## What It Looks Like

Lifecycle map:

```mermaid
flowchart LR
  source["Source / repo surface"]
  artifact["Artifact"]
  schema["Schema / contract"]
  system["System / subsystem"]
  workflow["Workflow step"]
  gate{"Decision gate"}
  output["Output / report"]
  question["Review question"]
  source --> artifact --> schema --> system --> workflow --> gate --> output --> question
```

Artifact and schema expansion:

```mermaid
flowchart LR
  frontend["Frontend System"] --> route["Route/API Artifact"]
  backend["Backend Service"] --> queue["Queue Artifact"]
  data["Data Layer"] --> table["Table/View Artifact"]
  route --> request["Request Contract"]
  queue --> event["Event Contract"]
  table --> fact["Fact Contract"]
```

Gate map:

```mermaid
flowchart LR
  confidence{"Confidence Gate"} --> advance["advance"]
  confidence --> wait["wait"]
  confidence --> reject["reject"]
  human{"Human Review Gate"} --> approve["approved"]
  human --> block["blocked"]
  human --> review["needs review"]
```

Map of maps for huge repositories:

```mermaid
flowchart TD
  atlas["Root system atlas"]
  drivers["drivers/ child map"]
  net["net/ child map"]
  fs["fs/ child map"]
  mm["mm/ child map"]
  atlas --> drivers
  atlas --> net
  atlas --> fs
  atlas --> mm
  drivers --> ccpp["C / C++ source surfaces"]
  net --> workflow["network workflows to refine"]
```

## Quick Start

```bash
pip install system-review-graph
system-review-graph list-examples
system-review-graph validate --manifest examples/fictional_ai_ops/system_review_manifest.json
system-review-graph doctor --manifest examples/fictional_ai_ops/system_review_manifest.json
system-review-graph build \
  --manifest examples/fictional_ai_ops/system_review_manifest.json \
  --out-dir examples/fictional_ai_ops/reports \
  --depth deep \
  --html \
  --dot
```

Open:

```text
examples/fictional_ai_ops/reports/system_review_graph.md
```

Try an actual public repo example:

```bash
system-review-graph build \
  --manifest examples/actual_repos/fastapi/system_review_manifest.json \
  --out-dir examples/actual_repos/fastapi/reports
```

Copy a bundled starter manifest:

```bash
system-review-graph init-example \
  --example actual_repos/duckdb \
  --out-dir /tmp/duckdb-system-review \
  --force
```

Generate a starter manifest from any local repo:

```bash
system-review-graph scan \
  --repo /path/to/repo \
  --out /tmp/system_review_manifest.json \
  --title "My Project System Review Graph"
```

Load a compact slice from a generated documentation knowledge graph:

```bash
system-review-graph load-documentation-graph-context \
  --nodes /path/to/documentation_knowledge_graph_nodes.jsonl \
  --edges /path/to/documentation_knowledge_graph_edges.jsonl \
  --start-node concept:stock_selection
```

The generated documentation artifacts are agent/LLM surfaces first. Use stable
node IDs, typed edges, bounded context slices, and explicit proof boundaries so
agents can audit or hand off work without rereading an entire repository.

Load a full agent context bundle that combines an SRG manifest, optional
documentation graph slice, optional code-review graph contract, and optional
AI Development OS execution manifest:

```bash
system-review-graph load-repo-context-bundle \
  --manifest /path/to/system_review_manifest.json \
  --documentation-nodes /path/to/documentation_knowledge_graph_nodes.jsonl \
  --documentation-edges /path/to/documentation_knowledge_graph_edges.jsonl \
  --code-review-graph /path/to/code_review_graph_contract.json \
  --agentic-workflow /path/to/agentic_execution_manifest.json \
  --start-node concept:stock_selection
```

The bundle is designed for AI Development OS style workers: stable IDs,
bounded context, typed sections, lane coordination references, and explicit
proof boundaries before a lane is assigned.

The scanner supports mixed-language repositories. It detects starter surfaces
for C, C++, Java, C#, Python, JavaScript/TypeScript, Go, Rust, docs, tests, and
common build/config files. Scanner output is intentionally marked as inferred;
it is a starting map, not proof of runtime behavior.

## Language And Project Surface Support

System Review Graph has two levels of language support:

- The manifest/report model is language-neutral. You can describe any stack if
  you provide systems, artifacts, schemas, workflows, gates, and boundaries.
- The automatic `scan` command detects starter surfaces for the languages and
  project markers below. It creates a first-pass map that humans or agents
  should refine.

| Surface | Detected From | What The Scanner Creates |
|---|---|---|
| Python | `.py`, `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements.txt` | Python source/build surface |
| JavaScript / TypeScript | `.js`, `.jsx`, `.ts`, `.tsx`, `.mjs`, `.cjs`, `package.json`, `tsconfig.json`, Vite/Next config | JavaScript/TypeScript source/build surface |
| C / C++ | `.c`, `.cc`, `.cpp`, `.cxx`, `.h`, `.hpp`, `.hh`, `CMakeLists.txt`, `Makefile`, `configure.ac` | C/C++ source/build surface |
| Java / Kotlin | `.java`, `.kt`, `pom.xml`, Gradle files | Java/Kotlin source/build surface |
| C# / .NET | `.cs`, `.csproj`, `.sln`, `Directory.Build.props`, `global.json` | C#/.NET source/build surface |
| Go | `.go`, `go.mod`, `go.sum` | Go source/build surface |
| Rust | `.rs`, `Cargo.toml`, `Cargo.lock` | Rust source/build surface |
| Docs | `docs/`, `doc/`, `Documentation/` | Documentation artifact surface |
| Tests | `test/`, `tests/`, `spec/`, `specs/`, `__tests__/` | Test artifact surface |
| Build/config | Docker, Compose, Make, CMake, Python, Node, Maven, Go, and Cargo markers | Config/build artifact surface |

For languages not detected automatically yet, use the manifest directly. The
report renderer, HTML output, Mermaid maps, registers, MCP server, atlas mode,
and blueprint sections do not care what language the system is written in.

For a huge repository, generate an atlas instead of one giant flat graph:

```bash
system-review-graph scan \
  --repo /path/to/large/repo \
  --atlas \
  --out /tmp/system-review-atlas \
  --max-subsystems 24 \
  --build-reports \
  --depth overview
```

That writes:

```text
/tmp/system-review-atlas/system_review_manifest.json
/tmp/system-review-atlas/reports/system_review_graph.md
/tmp/system-review-atlas/subsystems/*/system_review_manifest.json
```

The root manifest includes `child_maps`, so a reviewer or AI agent can load one
map and discover the linked subsystem maps.

Every generated report also includes open-source-style audit registers:

| Register | Answers |
|---|---|
| Coverage Register | Which systems, artifacts, schemas, gates, workflows, child maps, and blueprint sections are represented? |
| Evidence Register | Which source links, artifact paths, schema contracts, and blueprint evidence rows support the map? |
| Gap Register | Which boundaries, missing proof points, and optional deepening areas remain open? |
| Action Register | Which review questions, rebuild phases, and gap-closing tasks should happen next? |

Expose SRG to MCP-capable agents:

```bash
system-review-graph-mcp
```

Example MCP client entry:

```json
{
  "mcpServers": {
    "system-review-graph": {
      "command": "system-review-graph-mcp"
    }
  }
}
```

See
[`docs/MCP.md`](https://github.com/itsmeeChandU/system-review-graph/blob/main/docs/MCP.md).

## Example Gallery

| Example | What It Teaches | Generated Report |
|---|---|---|
| Fictional AI Ops | End-to-end `source -> fact -> decision -> action -> outcome -> lesson` flow | `examples/fictional_ai_ops/reports/system_review_graph.md` |
| FastAPI | Framework/API runtime mapping | `examples/actual_repos/fastapi/reports/system_review_graph.md` |
| DuckDB | Database/query-engine mapping | `examples/actual_repos/duckdb/reports/system_review_graph.md` |
| OpenTelemetry Collector | Component pipeline and API-only review mapping | `examples/actual_repos/opentelemetry_collector/reports/system_review_graph.md` |
| Linux Kernel Atlas | Large-repo map-of-maps stress test | `examples/actual_repos/linux_kernel/reports/system_review_graph.md` |

The actual-repo examples are educational public-review maps, not official
maintainer audits.

## Depth Levels

Reports are generated with `--depth deep` by default.

| Depth | Use When | Includes |
|---|---|---|
| `overview` | You need the fastest orientation. | Current truth, source links, report registers, lifecycle map, expansion index, systems, architecture patterns, walkthroughs, review questions. |
| `standard` | You want a normal audit handoff. | Overview plus artifact/schema map, gate map, system details, artifacts, schemas, gates, and workflows. |
| `deep` | You want blueprint-level inspection. | Standard plus relationship graph, schema examples, and per-system artifact/gate/workflow drill-downs. |
| `blueprint` | You want a wall-map view of how the system works. | Deep plus blueprint sections with source evidence, operational flow, control points, review questions, known gaps, and full report registers. |

```bash
system-review-graph build \
  --manifest examples/actual_repos/duckdb/system_review_manifest.json \
  --out-dir /tmp/duckdb-system-review \
  --depth deep
```

Linux-scale blueprint example:

```bash
system-review-graph build \
  --manifest examples/actual_repos/linux_kernel/system_review_manifest.json \
  --out-dir examples/actual_repos/linux_kernel/reports \
  --depth blueprint \
  --html \
  --dot
```

## Manifest-First Design

The tool is intentionally manifest-first. A project can expose a safe system map without exposing private tables, production data, model weights, vendor contracts, or internal credentials.

That matters for:

- public open-source projects,
- enterprise services with private databases,
- data platforms,
- ML systems,
- agent systems,
- microservice platforms,
- embedded or hardware-adjacent systems,
- regulated or security-sensitive environments.

## What You Describe

A manifest describes:

- systems,
- artifacts,
- schemas,
- decision gates,
- workflows,
- graph edges,
- child maps for large-repo atlases,
- blueprint sections for source-evidence-backed system flows,
- source links,
- current truth,
- architecture patterns,
- walkthroughs,
- review questions,
- rebuild recipe,
- known boundaries.

Example system row:

```json
{
  "system_id": "action_engine",
  "name": "Action Engine",
  "purpose": "Turns approved recommendations into bounded action intents.",
  "architecture_style": "event-driven service",
  "language_stack": ["Python", "PostgreSQL", "OpenAPI"],
  "truth_boundary": "Can propose actions, but cannot execute restricted actions without a human gate.",
  "ideal_target": "Every action has an outcome and lesson."
}
```

## Public-Safe Reviews

Companies often cannot publish database schemas, architecture details, or source data. This tool supports sanitized reporting:

- publish interface schemas instead of raw tables,
- publish field names without sample values,
- publish evidence counts instead of records,
- publish redacted artifact paths,
- publish decision rules without secrets,
- publish risk boundaries and human gates.

The goal is not to leak the system. The goal is to explain the system.

## Outputs

`build` always writes:

```text
system_review_graph.json
system_review_graph.md
```

Optional:

```bash
system-review-graph build --manifest system_review_manifest.json --out-dir reports --html
system-review-graph build --manifest system_review_manifest.json --out-dir reports --dot
```

Optional files:

```text
system_review_graph.html
system_review_graph.dot
```

`scan --atlas --build-reports` writes the same report files for the root atlas
and each child subsystem map.

## Repository Layout

```text
src/system_review_graph/
  builder.py      # manifest -> graph object
  render.py       # Markdown and Mermaid rendering
  cli.py          # system-review-graph CLI
  models.py       # typed graph structures
  example_manifests/
docs/
  METHODOLOGY.md
  WALKTHROUGH.md
  SCHEMA.md
  ARCHITECTURE_PATTERNS.md
  OPEN_SOURCE_LAUNCH.md
  PYPI_RELEASE.md
examples/
  fictional_ai_ops/
    system_review_manifest.json
    reports/system_review_graph.md
  actual_repos/
    fastapi/
    duckdb/
    opentelemetry_collector/
    linux_kernel/
```

## Project Docs

| Document | Purpose |
|---|---|
| [`docs/METHODOLOGY.md`](https://github.com/itsmeeChandU/system-review-graph/blob/main/docs/METHODOLOGY.md) | Explains code map vs system map and the review methodology. |
| [`docs/WALKTHROUGH.md`](https://github.com/itsmeeChandU/system-review-graph/blob/main/docs/WALKTHROUGH.md) | Step-by-step usage walkthrough. |
| [`docs/SCHEMA.md`](https://github.com/itsmeeChandU/system-review-graph/blob/main/docs/SCHEMA.md) | Manifest fields and depth options. |
| [`docs/MCP.md`](https://github.com/itsmeeChandU/system-review-graph/blob/main/docs/MCP.md) | MCP stdio server setup and tools. |
| [`docs/schema/system_review_manifest.schema.json`](https://github.com/itsmeeChandU/system-review-graph/blob/main/docs/schema/system_review_manifest.schema.json) | JSON Schema for editor/tool validation. |
| [`docs/ARCHITECTURE_PATTERNS.md`](https://github.com/itsmeeChandU/system-review-graph/blob/main/docs/ARCHITECTURE_PATTERNS.md) | How different system shapes map into the manifest. |
| [`docs/OPEN_SOURCE_LAUNCH.md`](https://github.com/itsmeeChandU/system-review-graph/blob/main/docs/OPEN_SOURCE_LAUNCH.md) | How to make the repo findable and launch it publicly. |
| [`docs/PYPI_RELEASE.md`](https://github.com/itsmeeChandU/system-review-graph/blob/main/docs/PYPI_RELEASE.md) | Build, verify, and publish package instructions. |
| [`ROADMAP.md`](https://github.com/itsmeeChandU/system-review-graph/blob/main/ROADMAP.md) | Future work. |
| [`CHANGELOG.md`](https://github.com/itsmeeChandU/system-review-graph/blob/main/CHANGELOG.md) | Release history. |

## Development

```bash
python -m pip install -e .
python -m pytest
python -m ruff check .
```

GitHub Actions workflows are committed under `.github/workflows/`:

- `ci.yml` runs lint, tests, package builds, wheel smoke tests, example report
  builds, and merge-time atlas generation.
- `publish.yml` builds, validates, smoke-tests, and publishes to PyPI through
  Trusted Publishing.

## Packaging

The project is configured as a Python package with the console command:

```bash
system-review-graph
system-review-graph-mcp
```

Build and check locally:

```bash
python -m pip install --upgrade build twine
python -m build
python -m twine check dist/*
```

See
[`docs/PYPI_RELEASE.md`](https://github.com/itsmeeChandU/system-review-graph/blob/main/docs/PYPI_RELEASE.md)
before publishing.

Release automation:

- CI runs lint, tests, package builds, wheel smoke tests, example report builds,
  and atlas generation on pushes and pull requests.
- PyPI publishing is wired through GitHub Actions and PyPI Trusted Publishing
  with the `pypi` environment. See
  [`docs/PYPI_RELEASE.md`](https://github.com/itsmeeChandU/system-review-graph/blob/main/docs/PYPI_RELEASE.md).

## Credit, Citation, And License

System Review Graph was created by Sai Chandra Madduri and is released under the
[`MIT License`](https://github.com/itsmeeChandU/system-review-graph/blob/main/LICENSE).
MIT keeps the project easy to use while requiring the
copyright and license notice to be preserved in copies or substantial portions
of the software.

For attribution, use:

```text
System Review Graph by Sai Chandra Madduri and contributors
https://github.com/itsmeeChandU/system-review-graph
```

For research, talks, public examples, benchmarks, or audits, use
[`CITATION.cff`](https://github.com/itsmeeChandU/system-review-graph/blob/main/CITATION.cff).
GitHub reads this file and shows a
`Cite this repository` entry on the repository page.

Credit files:

- [`AUTHORS.md`](https://github.com/itsmeeChandU/system-review-graph/blob/main/AUTHORS.md)
- [`NOTICE.md`](https://github.com/itsmeeChandU/system-review-graph/blob/main/NOTICE.md)
- [`CITATION.cff`](https://github.com/itsmeeChandU/system-review-graph/blob/main/CITATION.cff)

Visual assets:

- [`assets/system-review-graph-mark.svg`](https://github.com/itsmeeChandU/system-review-graph/blob/main/assets/system-review-graph-mark.svg)
- [`assets/social-preview.svg`](https://github.com/itsmeeChandU/system-review-graph/blob/main/assets/social-preview.svg)

Package links:

- [PyPI package](https://pypi.org/project/system-review-graph/)

## Discoverability

Suggested GitHub topics:

```text
architecture audit code-review documentation developer-tools mermaid reverse-engineering software-architecture system-design system-review
```

## Philosophy

Knowledge is not enough. A useful system map should show how knowledge becomes:

```text
source -> fact -> candidate -> decision -> action -> outcome -> lesson
```

That is the path from information to operational wisdom.
