"""Tests for RAG service — SCP number extraction and search logic."""

import pytest
from app.services.rag_service import extract_scp_number


class TestExtractSCPNumber:
    """Test SCP number auto-detection from user queries."""

    def test_standard_format(self):
        assert extract_scp_number("Tell me about SCP-173") == "SCP-173"

    def test_lowercase(self):
        assert extract_scp_number("describe scp-682") == "SCP-682"

    def test_with_space(self):
        assert extract_scp_number("what is SCP 049?") == "SCP-049"

    def test_four_digit(self):
        assert extract_scp_number("SCP-3008 is interesting") == "SCP-3008"

    def test_no_scp_number(self):
        assert extract_scp_number("Tell me about the foundation") is None

    def test_embedded_in_text(self):
        result = extract_scp_number("I read about SCP-999 yesterday and it was cute")
        assert result == "SCP-999"

    def test_zero_padded(self):
        assert extract_scp_number("SCP-001") == "SCP-001"

    def test_multiple_returns_first(self):
        result = extract_scp_number("Compare SCP-173 and SCP-682")
        assert result == "SCP-173"
