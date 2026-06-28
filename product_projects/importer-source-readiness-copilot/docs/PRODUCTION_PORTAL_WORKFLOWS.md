# Production Portal Workflow Engine

Status: `production_portal_workflow_engine_ready_routes_gated_business_owner_ux`

The portal workflow engine maps the existing UI/API routes to complete
business-owner, reviewer, operator, admin, and enterprise workflows.

## Portals

- Public portal: business owner exploring a trade lane (covered)
- Exporter portal: foreign exporter preparing a Canada-facing packet (covered)
- Importer portal: Canadian importer checking source, supplier, and responsibility questions (covered)
- Expert reviewer portal: scoped external reviewer (covered)
- Operator and admin portal: internal operator or admin (covered)
- Enterprise portal: broker, advisor, or team managing multiple packets (covered)

## Default First Screen

- Explore a market: `/opportunities` (route present)
- Prepare a buyer packet: `/tools/buyer-broker-packet` (route present)
- Check my documents: `/tools/document-check` (route present)
- Prepare for broker/expert review: `/expert-network` (route present)

## Business-Owner UX Checks

- first screen has four default choices: passed
- first screen routes exist: passed
- all portal routes covered: passed
- plain business language required: passed
- mobile review required: passed
- accessibility review required: passed
- blocked vs approved confusion testing required: passed

## Gate Boundary

- Public launch ready: false
- Live payment ready: false
- Unrestricted uploads enabled: false
- Claims opened: false

The product can guide users through preparation workflows. It still needs real
business-owner UX feedback, accessibility signoff, mobile review, hosted proof,
live payment approval, unrestricted upload approval, and public launch approval
before those gates can open.
