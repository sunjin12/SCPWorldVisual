"""Tests for prompt service — prompt assembly and constraint compliance."""

from app.services.prompt_service import build_prompt, extract_sources
from app.core.personas import get_persona
from app.models.session import Message


def _rag_result(
    item_number="SCP-173",
    section="description",
    text="Test text",
    url="https://scp-wiki.wikidot.com/scp-173",
):
    return {
        "item_number": item_number,
        "section_type": section,
        "text": text,
        "url": url,
    }


class TestBuildPrompt:
    def test_basic_structure(self):
        persona = get_persona("researcher")
        messages = build_prompt(persona, [], [], "Hello")
        # 1 system + 2N few-shot (user/assistant) + 1 final user
        expected = 2 + 2 * len(persona.few_shot_examples)
        assert len(messages) == expected
        assert messages[0]["role"] == "system"
        assert messages[-1]["role"] == "user"
        # Final user message starts with the raw input (closing_directive appended).
        assert messages[-1]["content"].startswith("Hello")

    def test_includes_rag_context(self):
        persona = get_persona("researcher")
        messages = build_prompt(persona, [_rag_result()], [], "About SCP-173")
        expected = 2 + 2 * len(persona.few_shot_examples) + 1  # +1 RAG system
        assert len(messages) == expected
        rag_msg = next(
            m for m in messages if "Retrieved SCP Documents" in m["content"]
        )
        assert rag_msg["role"] == "system"
        assert "SCP-173" in rag_msg["content"]

    def test_includes_history(self):
        persona = get_persona("researcher")
        history = [
            Message(role="user", content="prev question"),
            Message(role="assistant", content="prev answer"),
        ]
        messages = build_prompt(persona, [], history, "Follow up")
        # system + few-shots + history(2) + final user
        expected = 2 + 2 * len(persona.few_shot_examples) + 2
        assert len(messages) == expected
        # History should be present before the final user message.
        contents = [m["content"] for m in messages]
        assert "prev question" in contents
        assert "prev answer" in contents

    def test_system_prompt_no_lore(self):
        """System prompt must define tone only, not SCP lore.

        Length is a proxy check — keep it bounded so it can't silently balloon
        with worldbuilding content. The cap is generous to accommodate the
        explicit language/termination rules added for Qwen2.5-7B drift control.
        """
        persona = get_persona("researcher")
        messages = build_prompt(persona, [], [], "test")
        # No SCP-specific lore (containment procedure descriptions, foundation
        # history) should appear in the system prompt itself. SCP IDs used as
        # syntax examples (e.g. 'SCP-173') are permitted.
        system_content = messages[0]["content"]
        assert "격리실" not in system_content
        assert "격납 조치" not in system_content
        assert len(system_content) < 2000


class TestExtractSources:
    def test_extracts_urls(self):
        results = [
            _rag_result(url="https://scp-wiki.wikidot.com/scp-173"),
            _rag_result(url="https://scp-wiki.wikidot.com/scp-682"),
        ]
        assert len(extract_sources(results)) == 2

    def test_deduplicates(self):
        results = [
            _rag_result(url="https://scp-wiki.wikidot.com/scp-173"),
            _rag_result(url="https://scp-wiki.wikidot.com/scp-173"),
        ]
        assert len(extract_sources(results)) == 1
