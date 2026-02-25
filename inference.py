"""
Inference Router
Handles AI completion requests — both standard and streaming.
"""

import time
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.models.schemas import InferenceRequest, InferenceResponse
from app.services.cache import SemanticCache
from app.services.inference_engine import InferenceEngine
from app.middleware.auth import get_current_user

router = APIRouter()
cache = SemanticCache()
engine = InferenceEngine()


@router.post("/complete", response_model=InferenceResponse)
async def complete(
    request: InferenceRequest,
    user: dict = Depends(get_current_user),
):
    """
    Standard (non-streaming) AI completion endpoint.
    Checks semantic cache first to avoid redundant inference.
    """
    request_id = str(uuid.uuid4())
    start = time.time()

    # 1. Check semantic cache
    cached = await cache.get(request.prompt)
    if cached:
        return InferenceResponse(
            id=request_id,
            text=cached,
            cached=True,
            latency_ms=round((time.time() - start) * 1000, 2),
            model=request.model,
        )

    # 2. Run inference
    try:
        result = await engine.generate(
            prompt=request.prompt,
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Inference failed: {str(e)}")

    # 3. Store in cache
    await cache.set(request.prompt, result)

    return InferenceResponse(
        id=request_id,
        text=result,
        cached=False,
        latency_ms=round((time.time() - start) * 1000, 2),
        model=request.model,
    )


@router.post("/stream")
async def stream(
    request: InferenceRequest,
    user: dict = Depends(get_current_user),
):
    """
    Streaming AI completion — returns Server-Sent Events.
    Use this for chat UIs where you want token-by-token output.

    Client usage:
        const es = new EventSource('/v1/inference/stream');
        es.onmessage = (e) => console.log(e.data);
    """

    async def token_generator() -> AsyncGenerator[str, None]:
        async for token in engine.stream(
            prompt=request.prompt,
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        ):
            yield f"data: {token}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        token_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable Nginx buffering
        },
    )
