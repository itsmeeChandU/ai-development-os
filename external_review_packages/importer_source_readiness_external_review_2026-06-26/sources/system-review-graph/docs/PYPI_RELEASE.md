# PyPI Release Guide

System Review Graph is PyPI-ready. Prefer PyPI Trusted Publishing through
GitHub Actions so the project does not need a long-lived PyPI token.

Official packaging flow, in plain language:

1. Keep package metadata in `pyproject.toml`.
2. Build a source distribution and wheel.
3. Check the package metadata.
4. Upload to TestPyPI first.
5. Upload to PyPI after verifying install.

## Build Locally

```bash
python -m pip install --upgrade build twine
python -m build
python -m twine check dist/*
```

## Test The Wheel

```bash
python -m venv /tmp/srg-test
source /tmp/srg-test/bin/activate
python -m pip install dist/system_review_graph-*.whl
system-review-graph list-examples
system-review-graph init-example --example fictional_ai_ops --out-dir /tmp/srg-example --force
system-review-graph build --manifest /tmp/srg-example/system_review_manifest.json --out-dir /tmp/srg-report
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"smoke","version":"1"}}}' | system-review-graph-mcp
```

## One-Time Trusted Publishing Setup

For a new PyPI project, create a pending publisher from your PyPI account:

```text
PyPI account settings -> Publishing -> Add a new pending publisher
```

Use these exact fields:

| Field | Value |
|---|---|
| PyPI project name | `system-review-graph` |
| Owner | `itsmeeChandU` |
| Repository name | `system-review-graph` |
| Workflow filename | `publish.yml` |
| Environment name | `pypi` |

Then open the GitHub repository settings and create an environment named
`pypi`. For extra safety, require manual approval on that environment before
publishing.

The publish workflow is:

```text
.github/workflows/publish.yml
```

It builds distributions, validates metadata, smoke-tests the wheel, and then
publishes through `pypa/gh-action-pypi-publish` using GitHub OIDC. No PyPI
password or API token is stored in the repository.

## Publish Through GitHub Actions

After the pending publisher and GitHub `pypi` environment are configured,
publish by creating a GitHub release for a new tag, or run the `Publish`
workflow manually and type:

```text
publish
```

The current release artifacts are already attached to GitHub releases, but
PyPI publishing should happen through the workflow after PyPI trusts this
repository.

## Manual Upload Fallback

If Trusted Publishing is not configured yet, use an API token manually. Do not
commit the token and do not paste it into chat.

Use TestPyPI first if desired:

```bash
python -m twine upload --repository testpypi dist/*
```

Then PyPI:

```bash
python -m twine upload dist/*
```

When prompted by `twine`, use:

```text
username: __token__
password: <paste the full pypi-... token locally>
```

After the first upload, create a project-scoped token for future emergency
manual uploads. The normal release path should still be Trusted Publishing.

## References

- Python Packaging User Guide: https://packaging.python.org/en/latest/flow/
- PyPI project metadata docs: https://docs.pypi.org/project_metadata/
- Twine: https://pypi.org/project/twine/
