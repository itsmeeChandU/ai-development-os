# Offline Reproduction

The current product proof can run without live external calls, paid APIs,
credentials, or production deployment.

## Steps

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/check_product.py
python3 scripts/audit_external_package.py --root .
python3 scripts/serve_operator_app.py
```

Open:

```text
http://127.0.0.1:8765/
http://127.0.0.1:8765/source-packets
http://127.0.0.1:8765/source-packets/new
```

## Boundary

Offline reproduction proves local workflow behavior only. It does not prove
current official-source freshness, customer demand, legal/compliance approval,
supplier readiness, buyer validation, hosted security, or production launch.
