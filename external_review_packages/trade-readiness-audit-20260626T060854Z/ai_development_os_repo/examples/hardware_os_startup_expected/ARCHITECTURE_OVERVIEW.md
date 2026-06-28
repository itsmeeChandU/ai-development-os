# Architecture Overview

## Product

Offline-first edge device OS and operator console for sensor collection, local
inference, and delayed sync.

## Components

| Component | Responsibility | Inputs | Outputs | Owner Lane |
|---|---|---|---|---|
| hardware target | sensors, CPU/MCU/SoC, power, connectivity | product constraints | candidate boards | hardware-os |
| embedded OS | boot, drivers, processes/tasks, updates | hardware target | device runtime | firmware-os |
| local inference runtime | model execution | sensor data | inference events | backend-control-plane |
| sync service | offline queue and network sync | local events | remote records | backend-control-plane |
| operator console | status, configuration, logs | device/backend state | operator actions | UI-operator-console |
| simulation harness | run before hardware arrives | mocked sensors/device model | proof logs | simulation-bench |

## Likely OS Path

Start with Zephyr for MCU/RTOS targets or Buildroot/Yocto for Linux-capable edge
targets. Do not choose a custom kernel until evidence proves existing RTOS or
embedded Linux cannot satisfy the product.

