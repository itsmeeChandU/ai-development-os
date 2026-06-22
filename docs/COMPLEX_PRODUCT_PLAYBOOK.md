# Complex Product Playbook

AI Development OS must handle more than web apps. It should support products
that involve hardware, operating systems, embedded firmware, regulated domains,
scientific systems, robotics, manufacturing, finance, health, and other
multi-domain work.

## Core Rule

Do not pretend a complex product is simple. Expand the state model until it
matches reality.

## Complex Product Dimensions

When a prompt mentions hardware, operating systems, devices, sensors, robotics,
medical, finance, legal, manufacturing, or deployment into the physical world,
add these dimensions to the system review graph:

- hardware bill of materials
- hardware availability and procurement
- firmware and boot chain
- operating-system constraints
- driver and kernel support
- electrical, thermal, mechanical, and enclosure constraints
- lab equipment and measurement plan
- simulation, emulator, or digital twin
- manufacturing and supply chain
- certification, compliance, and safety standards
- field update and rollback path
- observability and diagnostics
- security and secure boot
- privacy and data retention
- operator training and support
- vendor/source rights and licensing
- failure modes and hazard analysis

## Hardware/OS Intake Questions

- What exact hardware target exists or is being considered?
- What CPU/MCU/SoC architecture is used?
- What bootloader, firmware, kernel, drivers, and board support package exist?
- What interfaces are required: GPIO, I2C, SPI, UART, USB, PCIe, CAN, BLE, Wi-Fi, Ethernet?
- What real-time requirements exist?
- What sensors, actuators, displays, batteries, and enclosures are needed?
- What operating system is appropriate: Linux, RTOS, bare metal, Android, custom?
- What parts are available, affordable, and replaceable?
- What can be simulated before hardware arrives?
- What lab equipment is required?
- What certification or safety rules apply?
- What cannot be tested remotely?

## Research Before Build

Research must answer:

- available hardware options
- official datasheets and reference manuals
- SDKs, BSPs, kernel support, and driver status
- open-source examples and licenses
- supply availability and cost
- compliance constraints
- test equipment needs
- known failure modes
- alternatives if the first hardware choice fails

## Completion Ladder

Complex products need staged proof:

1. Concept proof: user, outcome, constraints, hazard boundaries.
2. Feasibility proof: hardware/software/tooling options and blockers.
3. Simulation proof: emulator, mocked device, digital twin, or fixture.
4. Bench proof: hardware-in-loop or lab measurement.
5. Integration proof: firmware/OS/app/data path works together.
6. Reliability proof: repeated runs, failure recovery, logs, diagnostics.
7. Compliance proof: standards, review, or certification plan.
8. Field proof: controlled deployment with rollback and support.

## Agent Lane Split

For complex products, use lanes like:

- systems-engineering
- hardware-research
- firmware-os
- backend-control-plane
- UI-operator-console
- data-telemetry
- simulation-test
- compliance-safety
- procurement-vendor
- qa-integration

Each lane still needs owned files, forbidden files, proof commands, artifacts,
blockers, and handoff.

Use `docs/TOOL_BREEDING_GROUND.md` to select the actual toolchain for each
lane. Complex products need tool decisions, not tool shopping.

## Prompt

```text
Treat this as a complex product, not a simple app. Build a state model that
includes hardware, firmware/OS, data, UI, simulation, lab validation,
procurement, compliance, security, and field operation. Research official
hardware/software sources before selecting components. Implement the smallest
verifiable slice that can run locally or in simulation, and write blockers for
anything requiring physical hardware, certification, or external procurement.
```
