FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY . /app
RUN python -m py_compile src/importer_source_readiness/*.py scripts/*.py

EXPOSE 8765
CMD ["python", "scripts/serve_operator_app.py", "--host", "0.0.0.0", "--port", "8765", "--skip-refresh", "--no-open"]
