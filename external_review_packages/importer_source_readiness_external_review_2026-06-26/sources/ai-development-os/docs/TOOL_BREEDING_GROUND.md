# Tool Breeding Ground

Complex products need an environment where ideas can mature into verified
systems. That environment is a tool breeding ground: a curated set of tools,
sources, checks, and proof paths that help agents move from uncertainty to
working product.

## Tool Layers

Do not start by installing everything. Start by mapping the product to these
layers, then adopt tools only when they close a proven gap.

| Layer | Purpose | Examples |
|---|---|---|
| Agent runtime | code, review, handoff, orchestration | Codex, Agents SDK, LangGraph, MCP |
| Repo and project control | issues, branches, CI, releases | GitHub, GitHub MCP, pre-commit |
| Research and docs | current API/hardware/standards truth | official docs, datasheets, specs, web search |
| Product strategy | user, market, build-vs-buy, wedge | JTBD, Wardley maps, Shape Up, Toyota Kata |
| Data and source mesh | datasets, freshness, lineage, rights | DuckDB, DVC, dbt, Great Expectations |
| UI and browser proof | app behavior and screenshots | Playwright, browser automation, accessibility checks |
| Firmware and embedded OS | RTOS/Linux images/drivers | Zephyr, Yocto, Buildroot, OpenOCD |
| Emulation and simulation | proof before hardware arrives | QEMU, Renode, Verilator, cocotb, ngspice |
| Hardware design | electronics and mechanical design | KiCad, FreeCAD, OpenSCAD |
| Lab and bench | measurement and hardware-in-loop | pytest fixtures, lab logs, OpenOCD, pyVISA |
| Security and supply chain | secrets, vulnerabilities, SBOM | gitleaks, Trivy, Semgrep, Syft, Grype, OSV |
| Observability | traces, metrics, product telemetry | OpenTelemetry, Grafana, Prometheus, Loki |
| Compliance and governance | licenses, notices, safety, responsibility | SPDX, REUSE, CycloneDX, governance docs |

## Stage-Gated Adoption

| Stage | Tool Need | Proof |
|---|---|---|
| idea | strategy, examples, comparable products | research record |
| feasibility | official docs, hardware/API options, license fit | decision record |
| simulation | emulator, mocks, fixtures, digital twin | reproducible simulation run |
| prototype | app/backend/firmware/UI stack | working local flow |
| bench | hardware-in-loop, lab equipment, measurement | bench log and repeatable command |
| integration | full data/control path | integration test/report |
| launch | deployment, monitoring, rollback | launch readiness artifact |
| operations | telemetry, incident, support, updates | operator dashboard and runbook |

## Tool Decision Rule

Every adopted tool needs:

- product gap it closes
- source URL
- license
- install command or access method
- proof command
- owner lane
- risk
- fallback

If a tool cannot name its product gap, it stays in `watch`.

## Hardware/OS Toolchain Starter Set

For a product like "build an operating system for specific hardware", start
with:

- hardware research: datasheets, reference manuals, vendor SDK/BSP, procurement links
- OS choice: Zephyr for RTOS, Yocto or Buildroot for embedded Linux
- emulation: QEMU for machine/OS emulation, Renode for embedded device simulation
- debugging: OpenOCD plus GDB for JTAG/SWD targets
- board design: KiCad for electronics, FreeCAD/OpenSCAD for mechanical parts
- circuit simulation: ngspice
- RTL/FPGA path: Yosys, Verilator, cocotb
- security/supply chain: gitleaks, Trivy, Syft/Grype, OSV-Scanner
- observability: OpenTelemetry, Grafana/Prometheus/Loki

## Tool Breeding Ground Prompt

```text
Build the tool breeding ground for this product. Map the product to agent,
research, data, UI, firmware/OS, simulation, hardware, lab, security,
observability, compliance, and governance layers. For each layer, select tools
only when they close a proven gap. Produce a tool decision record, install/use
commands, proof commands, fallback options, and blockers for unavailable
hardware, paid APIs, credentials, lab equipment, or standards access.
```

