# Security Policy

## Scope

This repository is a process/tooling kit. Security reports should focus on:

- scripts in this repo
- generated project-starter behavior
- documentation that could cause secret leakage
- agent instructions that encourage unsafe external actions
- workflows that mishandle credentials, private data, or licensing claims

Derivative products built with this toolkit are outside this repository's
responsibility. Report vulnerabilities in derivative products to those product
owners.

## Do Not Submit Secrets

Never submit:

- API keys
- access tokens
- passwords
- private customer data
- proprietary datasets
- private prompts or logs containing sensitive information

## Reporting

If GitHub private vulnerability reporting is available, use it. Otherwise,
open a public issue only if the report can be written without exposing secrets,
exploits, private data, or live credentials.

## Agent Rule

If an agent finds a likely secret, it must:

1. stop printing the value
2. record only a redacted path/type
3. recommend rotation if exposure is possible
4. avoid committing the secret
5. add a blocker row with `next_valid_move`
