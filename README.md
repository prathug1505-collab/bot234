# 🧠 AI Gateway — FastAPI Scaffold

A production-ready, scalable API gateway for your Python AI system.

## Project Structure

```
ai_gateway/
├── app/
│   ├── main.py                  # FastAPI app, middleware, router registration
│   ├── routers/
│   │   ├── inference.py         # POST /v1/inference/complete + /stream
│   │   ├── models.py            # GET  /v1/models
│   │   └── health.py            # GET  /health
│   ├── middleware/
│   │   ├── auth.py              # JWT Bearer token validation
│   │   └── rate_limit.py        # Redis sliding-window rate limiter (60 req/min)
│   ├── services/
│   │   ├── inference_engine.py  # Wraps OpenAI / vLLM — swap providers easily
│   │   ├── cache.py             # SHA-256 semantic cache backed by Redis
│   │   └── redis_client.py      # Async Redis singleton
│   └── models/
│       └── schemas.py           # Pydantic request/response models
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## Quick Start

### 1. Install dependencies
```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env — add your OPENAI_API_KEY and JWT_SECRET
```

### 3. Start Redis (Docker)
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

### 4. Run the server
```bash
uvicorn app.main:app --reload
```

### 5. Or run everything with Docker Compose
```bash
docker-compose up --build
```

### 6. Visit the auto-generated API docs
```
http://localhost:8000/docs
```

---

## Key Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check (Redis + inference status) |
| GET | /v1/models | List available AI models |
| POST | /v1/inference/complete | Standard completion (with cache) |
| POST | /v1/inference/stream | Streaming SSE completion |

---

## Example Request

```bash
# Get a JWT token first (implement a /auth/login endpoint)
TOKEN="your-jwt-token"

curl -X POST http://localhost:8000/v1/inference/complete \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain neural networks in 3 sentences.",
    "model": "gpt-4o",
    "max_tokens": 256,
    "temperature": 0.7
  }'
```

---

## Scaling Up

- **More workers**: Increase `--workers` in the Dockerfile CMD
- **More instances**: Put behind a load balancer (AWS ALB / Nginx)
- **GPU workers**: Point `AI_PROVIDER=vllm` to a vLLM server on a GPU node
- **Kubernetes**: Use HPA to auto-scale based on CPU/GPU queue depth

---

## Next Steps

1. Add a `POST /auth/login` endpoint that returns a JWT
2. Add PostgreSQL (SQLAlchemy) for storing conversation history
3. Upgrade cache to vector similarity (Pinecone / pgvector)
4. Add Prometheus metrics middleware
5. Deploy to Kubernetes with GPU node pool
