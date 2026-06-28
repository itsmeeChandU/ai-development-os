# Security Policy

System Review Graph is a documentation and analysis helper. It should never
require secrets, production credentials, private customer data, or raw internal
databases.

## Supported Versions

Security reports are accepted for the current `main` branch and latest release.

## Reporting A Vulnerability

Please open a private security advisory on GitHub if available, or create an
issue with a minimal description that does not expose secrets or exploit details.

Good reports include:

- affected version or commit,
- command used,
- manifest snippet with private data removed,
- expected behavior,
- actual behavior,
- impact.

## Safe Manifest Rule

Do not publish manifests containing:

- API keys or credentials,
- personal data,
- customer data,
- proprietary source payloads,
- private prompts,
- private model weights,
- internal hostnames that should not be public.

Use logical names, schema-only contracts, counts, and fake examples instead.
