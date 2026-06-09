"""Auth router — Operator ID local authentication."""

import logging

from fastapi import APIRouter, HTTPException
from app.dependencies import get_storage_service
from app.models.schemas import AuthRequest, AuthResponse, AuthUser

logger = logging.getLogger(__name__)
router = APIRouter(tags=["auth"])


@router.post("/api/auth/verify", response_model=AuthResponse)
async def verify_login(request: AuthRequest):
    """
    Verify a local Operator Clearance ID.

    Returns user info. The client should store the Operator ID
    and include it as a Bearer token in subsequent API calls.
    """
    operator_id = request.id_token.strip()
    if not operator_id:
        raise HTTPException(status_code=400, detail="Invalid Operator ID")

    user = AuthUser(
        user_id=operator_id,
        email=f"{operator_id}@scp.foundation",
        name=operator_id,
        picture="",
    )

    storage_service = get_storage_service()
    await storage_service.save_user(user.model_dump())

    logger.info("Operator ID access authorized: %s", operator_id)
    return AuthResponse(user=user, status="verified")
