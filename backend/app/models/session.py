"""Data models for conversation session and messages."""

from pydantic import BaseModel, Field


class Message(BaseModel):
    """A single message in a conversation."""
    role: str = Field(..., description="'user' or 'assistant'")
    content: str
