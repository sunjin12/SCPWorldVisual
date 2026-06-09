"""Pydantic schemas for request/response models."""

from pydantic import BaseModel, Field


# --- Auth ---

class AuthRequest(BaseModel):
    """Operator ID authentication request."""
    id_token: str


class AuthUser(BaseModel):
    """Authenticated user info extracted from Google ID token."""
    user_id: str
    email: str
    name: str = ""
    picture: str = ""


class AuthResponse(BaseModel):
    """Response after successful token verification."""
    user: AuthUser
    status: str = "verified"


# --- Chat ---

class ChatRequest(BaseModel):
    """Chat message request."""
    session_id: str = Field(default="default", description="Conversation session ID")
    message: str = Field(..., min_length=1, max_length=4000, description="User message")
    persona_id: str = Field(default="researcher", description="Persona character ID")


class ChatResponse(BaseModel):
    """Non-streaming chat response."""
    session_id: str
    message: str
    persona_id: str
    sources: list[str] = Field(default_factory=list, description="SCP source URLs")


# --- Persona ---

class PersonaInfo(BaseModel):
    """Persona display info for API response."""
    id: str
    name: str
    description: str
    avatar: str
    is_default: bool = False


# --- Health ---

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    database: str = "unknown"
    ollama_llm: str = "unknown"
    embedding: str = "unknown"
