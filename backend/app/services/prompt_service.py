"""Prompt service — assembles the final prompt from persona, RAG, and history.

qwen3 모델은 enable_thinking=False로 정상 동작하므로 role="system" 사용.
"""

from app.core.personas import Persona
from app.models.session import Message

# qwen3.5:2b 최적화: RAG 컨텍스트 최대 토큰 (근사치: 한글 1토큰 ≈ 2~3자)
_MAX_RAG_CHARS = 3500


def _truncate_rag_text(text: str, max_chars: int = _MAX_RAG_CHARS) -> str:
    """RAG 컨텍스트가 너무 길면 마지막 완전한 문단에서 자릅니다."""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    # 마지막 개행 기준으로 자르기 (문단 단위)
    last_newline = truncated.rfind("\n")
    if last_newline > max_chars // 2:
        return truncated[:last_newline] + "\n[...후략]"
    return truncated + "[...후략]"


def build_prompt(
    persona: Persona,
    rag_results: list[dict],
    conversation_history: list[Message],
    user_message: str,
) -> list[dict]:
    """Assemble the final prompt for Ollama chat/completions."""
    messages: list[dict] = []

    messages.append({"role": "system", "content": persona.system_prompt})

    for example_user, example_assistant in persona.few_shot_examples:
        messages.append({"role": "user", "content": example_user})
        messages.append({"role": "assistant", "content": example_assistant})

    if rag_results:
        context_blocks = []
        for r in rag_results:
            item = r.get("item_number", "Unknown")
            section = r.get("section_type", "unknown")
            text = r.get("text", "")
            context_blocks.append(f"[{item}] ({section})\n{text}")

        context_text = "\n\n---\n\n".join(context_blocks)
        context_text = _truncate_rag_text(context_text)
        messages.append({
            "role": "system",
            "content": f"# Retrieved SCP Documents:\n{context_text}",
        })

    for msg in conversation_history:
        messages.append({"role": msg.role, "content": msg.content})

    final_user_content = user_message
    if persona.closing_directive:
        final_user_content = (
            f"{user_message}\n\n---\n[캐릭터 지시] {persona.closing_directive}"
        )
    messages.append({"role": "user", "content": final_user_content})

    return messages


def extract_sources(rag_results: list[dict]) -> list[str]:
    """Extract unique source URLs from RAG results."""
    urls: set[str] = set()
    for r in rag_results:
        url = r.get("url")
        if url:
            urls.add(url)
    return sorted(urls)
