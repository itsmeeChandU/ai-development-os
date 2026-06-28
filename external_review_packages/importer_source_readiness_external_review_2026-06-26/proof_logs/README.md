# Proof Logs

These logs were generated from the source snapshots inside this package.

Use them as convenience evidence, not as a substitute for rerunning the commands
in your own environment.

Recommended rerun order:

```bash
cd sources/importer-source-readiness-copilot
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/check_product.py

cd ../ai-development-os
python3 scripts/product_project_check.py
python3 scripts/ai_dev_os_check.py
python3 scripts/workflow_manifest_check.py
```
