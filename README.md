# Model-API
A lightweight FastAPI wrapper around Ollama that provides secure and scalable AI inference endpoints with support for streaming, authentication, and custom prompt workflows.

## Local run (Docker Compose)

```bash
docker compose up --build
```

- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

## Use this service from an *external* docker-compose.yml

Because this repo includes a `Dockerfile` at the project root, another repo can build it by pointing `build.context` at this folder.

Example external compose snippet:

```yaml
services:
  model_api:
    build:
      context: ../Model-API
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
```
