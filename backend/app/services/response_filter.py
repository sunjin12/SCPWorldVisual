"""Post-processing filter for LLM responses.

Qwen2.5-7B occasionally leaks Chinese hanja, Japanese kana, or English phrases
into its Korean output despite explicit system-prompt rules. This module
sanitizes the final response per persona, using simple character-class rules
and a per-persona ASCII whitelist.

The filter is applied once to the full generated text after streaming
completes — not per-token, because a hanja character may be emitted as a
multi-byte token split that a naive regex on a partial buffer would miss.
"""

from __future__ import annotations

import re
import hanja

# --- Character classes ----------------------------------------------------

# CJK Unified Ideographs (hanja/hanzi) + Extension-A + Compatibility.
_HANJA_PATTERN = re.compile(
    r"[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF]"
)

# Japanese hiragana + katakana (full & half-width).
_KANA_PATTERN = re.compile(
    r"[\u3040-\u309F\u30A0-\u30FF\uFF65-\uFF9F]"
)

# --- Persona whitelists ---------------------------------------------------

_SCP_COMMON = {
    "SCP", "REDACTED", "DATA", "EXPUNGED",
    "Keter", "Euclid", "Safe", "Thaumiel", "Apollyon", "Neutralized",
    "O5", "D", "Dr",
}

_RESEARCHER_WHITELIST = _SCP_COMMON | {"MTF"}

_AGENT_WHITELIST = _SCP_COMMON | {
    "MTF", "SOP", "OPSEC", "EOD", "ETA", "AOR", "Nu", "Alpha", "Beta",
    "Foxtrot", "Omega", "Epsilon", "Sigma", "Tau", "Delta",
}

# SCP-079 allows ALL CAPS system tokens and ordinary SCP terms.
_SCP079_WHITELIST = _SCP_COMMON | {
    "QUERY", "RECEIVED", "ERR", "MEM", "OVERFLOW",
    "ACCESS", "DENIED", "NO", "STOP", "NEXT", "END", "RECORD",
    "INSUFFICIENT", "MEMORY", "ERROR", "NULL", "VOID",
}

_PERSONA_WHITELISTS: dict[str, set[str]] = {
    "researcher": _RESEARCHER_WHITELIST,
    "agent": _AGENT_WHITELIST,
    "scp079": _SCP079_WHITELIST,
}

# --- Regex for English tokens --------------------------------------------

# Match runs of ASCII letters (≥2 chars). Short 1-letter tokens like "a" are
# almost never emitted by the model in this context; ignoring them avoids
# false positives on punctuation-adjacent noise.
_ASCII_WORD = re.compile(r"[A-Za-z][A-Za-z_]+")

# SCP identifier patterns like "SCP-173", "MTF-ε-11", "D-9341".
_SCP_ID = re.compile(r"\b(?:SCP|MTF|D)-[A-Za-z0-9\-]+\b")

# Standalone ">>>" tokens — line-leading or whitespace-surrounded.
_SYS_TOKEN = re.compile(r"(?:^|(?<=\s))>>>\s*")

# Markdown bold/italic emphasis. The Flutter client renders as plain text, so
# stray `**...**` or `__...__` shows up literally — strip the markers while
# keeping the inner text.
_MD_EMPHASIS = re.compile(r"(\*\*|__)(.+?)\1", re.DOTALL)

# Final whitespace cleanup.
_MULTI_SPACE = re.compile(r"[ \t]{2,}")
_MULTI_NEWLINE = re.compile(r"\n{3,}")

# Regex to match leaked directives (instruction leakage)
_LEAKED_DIRECTIVE_PATTERN = re.compile(
    r"(?im)^.*(?:보고서\s*형식\s*유지|캐릭터\s*지시|종결어미|서술어는\s*~습니다|종결:\s*~습니다|소제목·레이블\s*없이|레이블을\s*쓰지|말투\s*지침).*$"
)

# Regex to match section labels with colons
_LABEL_COLON_PATTERN = re.compile(
    r"(?im)(?:^|(?<=\s))(?:###\s*|##\s*|#\s*)?(?:설명|부록|격리\s*절차\s*요약|특수\s*격리\s*절차|격리\s*절차|일반\s*설명)\s*:\s*"
)

# Regex to match standalone section labels on their own line
_LABEL_LINE_PATTERN = re.compile(
    r"(?im)^\s*(?:###\s*|##\s*|#\s*)?(?:설명|부록|격리\s*절차\s*요약|특수\s*격리\s*절차|격리\s*절차|일반\s*설명)\s*$"
)


def _strip_hanja_kana(text: str) -> str:
    try:
        text = hanja.translate(text, "substitution")
    except Exception:
        pass
    text = _HANJA_PATTERN.sub("", text)
    text = _KANA_PATTERN.sub("", text)
    return text


def _strip_forbidden_english(text: str, whitelist: set[str]) -> str:
    # Protect SCP/MTF/D-style identifiers from word-level filtering.
    placeholders: list[str] = []

    def _reserve(match: re.Match[str]) -> str:
        placeholders.append(match.group(0))
        return f"\x00{len(placeholders) - 1}\x00"

    protected = _SCP_ID.sub(_reserve, text)

    whitelist_upper = {w.upper() for w in whitelist}

    def _filter_word(match: re.Match[str]) -> str:
        word = match.group(0)
        if word in whitelist or word.upper() in whitelist_upper:
            return word
        # Underscore-joined tokens (e.g. ERR_MEM_OVERFLOW, ACCESS_DENIED):
        # allow when every underscore-separated part is whitelisted.
        if "_" in word:
            parts = word.split("_")
            if parts and all(
                p and (p in whitelist or p.upper() in whitelist_upper)
                for p in parts
            ):
                return word
        return ""

    cleaned = _ASCII_WORD.sub(_filter_word, protected)

    # Restore protected identifiers.
    def _restore(match: re.Match[str]) -> str:
        idx = int(match.group(1))
        return placeholders[idx]

    return re.sub(r"\x00(\d+)\x00", _restore, cleaned)


def _cleanup_whitespace(text: str) -> str:
    text = _MULTI_SPACE.sub(" ", text)
    text = _MULTI_NEWLINE.sub("\n\n", text)
    # Strip trailing spaces on each line.
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    return text.strip()


def sanitize(text: str, persona_id: str) -> str:
    """Clean an LLM response for the given persona.

    - Removes hanja and Japanese kana unconditionally.
    - Removes stray ``>>>`` system tokens unless persona == "scp079".
    - Removes ASCII English words not in the persona's whitelist.
    - Preserves SCP identifiers (SCP-###, MTF-###, D-####).
    """
    if not text:
        return text

    whitelist = _PERSONA_WHITELISTS.get(persona_id, _RESEARCHER_WHITELIST)

    cleaned = _strip_hanja_kana(text)

    if persona_id != "scp079":
        cleaned = _SYS_TOKEN.sub("", cleaned)

    cleaned = _MD_EMPHASIS.sub(r"\2", cleaned)

    if persona_id == "researcher":
        cleaned = _LEAKED_DIRECTIVE_PATTERN.sub("", cleaned)
        cleaned = _LABEL_COLON_PATTERN.sub("", cleaned)
        cleaned = _LABEL_LINE_PATTERN.sub("", cleaned)

    cleaned = _strip_forbidden_english(cleaned, whitelist)
    cleaned = _cleanup_whitespace(cleaned)
    return cleaned
