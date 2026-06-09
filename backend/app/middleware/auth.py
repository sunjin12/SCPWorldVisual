"""Operator ID local authentication middleware.

Used as a FastAPI Dependency on all /api/* routes except /api/auth/verify.
Extracts the Bearer token from the Authorization header and returns
the authenticated user info (Operator ID based, no external OAuth).
"""

import logging

from fastapi import Depends, HTTPException, Header
from app.config import settings
from app.models.schemas import AuthUser

logger = logging.getLogger(__name__)


async def verify_google_token(
    authorization: str = Header(..., description="Bearer <operator_id>"),
) -> AuthUser:
    """
    FastAPI Dependency that extracts and returns the local Operator ID.

    Usage:
        @router.get("/api/protected")
        async def protected(user: AuthUser = Depends(verify_google_token)):
            ...
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Authorization header must start with 'Bearer '",
        )

    token = authorization[7:].strip()  # Strip "Bearer "
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Operator ID is required",
        )

    return AuthUser(
        user_id=token,
        email=f"{token}@scp.foundation",
        name=token,
        picture="",
    )
