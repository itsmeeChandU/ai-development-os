# Tool Decision Record

- product_gap: simulation and OS path before hardware selection
- selected_tool: QEMU/Renode plus Zephyr or Buildroot/Yocto
- stage_supported: feasibility and simulation
- decision: adopt_when_fit_proven

## Fit

- QEMU: full-system OS emulation when target architecture/machine is supported
- Renode: embedded device and multi-node simulation
- Zephyr: RTOS path for resource-constrained devices
- Buildroot: fast embedded Linux prototype
- Yocto: production embedded Linux distribution path
- OpenOCD: later bench debugging and flashing

## Next Valid Move

Create hardware candidate table with CPU/MCU/SoC, interfaces, OS support, cost,
availability, sensor compatibility, and simulation path.

