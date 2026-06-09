"""Tests for auth middleware and auth-related schemas."""

import pytest
from app.models.schemas import AuthUser, AuthRequest, ChatRequest


class TestAuthSchemas:
    def test_auth_user_creation(self):
        user = AuthUser(user_id="123", email="test@example.com", name="Test")
        assert user.user_id == "123"
        assert user.email == "test@example.com"

    def test_auth_request(self):
        req = AuthRequest(id_token="test-token")
        assert req.id_token == "test-token"


class TestChatRequestValidation:
    def test_valid_request(self):
        req = ChatRequest(message="Hello", session_id="sess1", persona_id="researcher")
        assert req.message == "Hello"

    def test_default_values(self):
        req = ChatRequest(message="Hello")
        assert req.session_id == "default"
        assert req.persona_id == "researcher"

    def test_empty_message_rejected(self):
        with pytest.raises(Exception):
            ChatRequest(message="")

    def test_max_length_respected(self):
        req = ChatRequest(message="x" * 4000)
        assert len(req.message) == 4000

        with pytest.raises(Exception):
            ChatRequest(message="x" * 4001)
