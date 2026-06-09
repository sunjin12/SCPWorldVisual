"""Personas router — list available personas."""

from fastapi import APIRouter, Depends

from app.core.personas import list_personas
from app.middleware.auth import verify_google_token
from app.models.schemas import AuthUser, PersonaInfo

router = APIRouter(tags=["personas"])


@router.get("/api/personas", response_model=list[PersonaInfo])
async def get_personas(user: AuthUser = Depends(verify_google_token)):
    """Return all available persona characters."""
    return [
        PersonaInfo(
            id=p.id,
            name=p.name,
            description=p.description,
            avatar=p.avatar,
            is_default=p.is_default,
        )
        for p in list_personas()
    ]
