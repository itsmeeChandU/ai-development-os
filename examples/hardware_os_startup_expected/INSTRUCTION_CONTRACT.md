# Instruction Contract

## Goal

Create a startup product plan and first execution path for a custom operating
system on a low-cost edge device with sensor ingestion, local inference,
offline-first behavior, sync, and an operator console.

## Current-State Claims

| Claim | Source | Verification Status | Evidence |
|---|---|---|---|
| exact hardware is unknown | prompt | proven | prompt text |
| custom OS is required | prompt | unsupported | must compare RTOS, embedded Linux, and custom OS options |
| local inference is required | prompt | partial | needs model/runtime/hardware constraints |

## First Concrete Action

Build a simulation-first architecture and tool decision record using QEMU or
Renode, then create hardware research rows for candidate devices.

