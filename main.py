"""
AI Gateway - Main FastAPI Application
Scalable entry point for your Python AI system.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.middleware.auth import AuthMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.routers import inference, health, models
from app.services.redis_client import redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup & shutdown lifecycle."""
    await redis_client.connect()
    print("✅ Redis connected")
    yield
    await redis_client.disconnect()
    print("🛑 Redis disconnected")


app = FastAPI(
    title="AI Gateway",
    description="Scalable FastAPI gateway for your Python AI system",
    version="1.0.0",
    lifespan=lifespan,
)

# --- Middleware (order matters: last added = first executed) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production!
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuthMiddleware)

# --- Routers ---
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(inference.router, prefix="/v1/inference", tags=["Inference"])
app.include_router(models.router, prefix="/v1/models", tags=["Models"])
