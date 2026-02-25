"""
Inference Engine Service
Abstracts your AI model calls. Swap out the provider easily.
Currently supports: OpenAI, vLLM (self-hosted), HuggingFace.
"""

import os
from typing import AsyncGenerator

import httpx
from openai import AsyncOpenAI

# --- Provider config ---
PROVIDER = os.getenv("AI_PROVIDER", "openai")   # "openai" | "vllm" | "huggingface"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")


class InferenceEngine:
    def __init__(self):
        if PROVIDER == "openai":
            self._client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        elif PROVIDER == "vllm":
            # vLLM exposes an OpenAI-compatible API — just point the base URL
            self._client = AsyncOpenAI(
                api_key="vllm",   # vLLM doesn't require a real key
                base_url=VLLM_BASE_URL,
            )
        else:
            raise ValueError(f"Unknown AI_PROVIDER: {PROVIDER}")

    async def generate(
        self,
        prompt: str,
        model: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        """Non-streaming completion."""
        response = await self._client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
            stream=False,
        )
        return response.choices[0].message.content

    async def stream(
        self,
        prompt: str,
        model: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """Token-by-token streaming completion."""
        response = await self._client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
        )
        async for chunk in response:
            token = chunk.choices[0].delta.content
            if token:
                yield token
