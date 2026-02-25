"""
Auth Middleware
JWT-based authentication. Validates Bearer tokens on every request.
"""

import os
from typing import Optional

import jwt
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware

SECRET_KEY = os.getenv("JWT_SECRET", "change-me-in-production")
ALGORITHM = "HS256"

# Paths that skip auth
PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}

security = HTTPBearer()


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        token = _extract_token(request)
        if not token:
            return _unauthorized("Missing Authorization header")

        payload = _verify_token(token)
        if not payload:
            return _unauthorized("Invalid or expired token")

        # Attach user info to request state
        request.state.user = payload
        return await call_next(request)


def _extract_token(request: Request) -> Optional[str]:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return None


def _verify_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def _unauthorized(detail: str):
    from starlette.responses import JSONResponse
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": detail},
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(request: Request) -> dict:
    """Dependency injection — use in route handlers."""
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def create_token(user_id: str, role: str = "user") -> str:
    """Utility to generate a JWT — use in your login endpoint."""
    import datetime
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
