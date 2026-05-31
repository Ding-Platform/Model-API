# Model-API
A lightweight FastAPI wrapper around Ollama that provides secure and scalable AI inference endpoints with support for streaming, authentication, and custom prompt workflows.

## Local run (Docker Compose)

```bash
docker compose up --build
```

Copy `.env.example` to `.env` and use the dev `DATABASE_URL` / `REDIS_URL` (host ports `5433` / `6380`).

- API: `http://localhost:8000`
- Docs (DEBUG=true): `http://localhost:8000/api/docs`
- Health: `http://localhost:8000/api/v1/health`

## Production (Docker)

On the server, configure `.env` with Docker service hostnames (`postgres`, `redis`), `ENVIRONMENT=production`, `DEBUG=false`, and the same `JWT_SECRET` as Ding-Platform-Backend.

```bash
./scripts/deploy.sh
# or from backend repo:
# DEPLOY_MODEL_API=1 ./scripts/deploy.sh
```

- Loopback API: `http://127.0.0.1:8000/api/v1`
- Public (via host Nginx): `http://<server>/model-api/` (e.g. `/model-api/chat/sessions`)

Chat routes require `Authorization: Bearer <platform JWT>` and `X-API-Key: <SERVICE_API_KEY>`.

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
