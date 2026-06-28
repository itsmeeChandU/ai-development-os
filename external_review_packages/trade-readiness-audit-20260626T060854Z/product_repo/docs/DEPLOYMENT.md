# Deployment

## Local App

Run the product locally:

```bash
python3 scripts/check_product.py
python3 scripts/serve_operator_app.py --host 127.0.0.1 --port 8765
```

Health checks:

- `GET /healthz`
- `GET /readyz`
- `GET /api/system-health`

## Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

The app serves on `http://127.0.0.1:8765` by default. Generated runtime artifacts are mounted from `system_review_graph/`.

## Production Boundary

The repository includes a hostable local stack and deployment readiness report. It does not claim a live production environment has been provisioned.

Before public hosting:

- use a managed database and object storage
- replace demo sessions with production auth
- configure TLS and secure cookies
- use a secrets manager
- add malware scanning for uploaded files
- test backup and restore
- configure error tracking and monitoring
- complete qualified security, privacy, legal, and compliance review
