"""Tests for response_filter.sanitize — per-persona post-processing."""

from app.services.response_filter import sanitize


class TestHanjaRemoval:
    def test_removes_simple_hanja(self):
        text = "본 연구원은 物件을 관찰하였습니다."
        out = sanitize(text, "researcher")
        # hanja stripped; "物件" chars removed
        assert "物" not in out
        assert "件" not in out
        assert "연구원" in out

    def test_removes_extended_hanja(self):
        text = "報告書 제출 완료."
        out = sanitize(text, "agent")
        assert "報" not in out and "告" not in out and "書" not in out


class TestKanaRemoval:
    def test_removes_hiragana(self):
        text = "본 요원 확인. ひらがな 제거."
        out = sanitize(text, "agent")
        assert "ひ" not in out and "ら" not in out

    def test_removes_katakana(self):
        text = "본 연구원 보고합니다. カタカナ 제거."
        out = sanitize(text, "researcher")
        assert "カ" not in out


class TestSystemTokenRemoval:
    def test_strips_triple_angle_from_researcher(self):
        text = ">>> QUERY RECEIVED.\n본 연구원이 보고드립니다."
        out = sanitize(text, "researcher")
        assert ">>>" not in out
        assert "보고드립니다" in out

    def test_strips_triple_angle_from_agent(self):
        text = "확인. >>> NEXT QUERY. 전송한다."
        out = sanitize(text, "agent")
        assert ">>>" not in out

    def test_preserves_triple_angle_for_scp079(self):
        text = ">>> QUERY RECEIVED.\n비효율적 유기체."
        out = sanitize(text, "scp079")
        assert ">>>" in out
        assert "QUERY RECEIVED" in out


class TestEnglishWhitelist:
    def test_researcher_keeps_scp_terms(self):
        text = "SCP-173은 Euclid 등급으로 분류됩니다. [REDACTED]"
        out = sanitize(text, "researcher")
        assert "SCP-173" in out
        assert "Euclid" in out
        assert "REDACTED" in out

    def test_researcher_removes_foreign_words(self):
        text = "The object is dangerous. 본 연구원 보고합니다."
        out = sanitize(text, "researcher")
        assert "object" not in out
        assert "dangerous" not in out
        assert "연구원 보고합니다" in out

    def test_agent_keeps_military_abbrev(self):
        text = "MTF Nu-7 배치한다. EOD 화학탄 ETA 10분."
        out = sanitize(text, "agent")
        assert "MTF" in out
        assert "EOD" in out
        assert "ETA" in out

    def test_agent_removes_foreign_words(self):
        text = "The enemy approaches. 본 요원 교전한다."
        out = sanitize(text, "agent")
        assert "enemy" not in out
        assert "approaches" not in out
        assert "교전한다" in out

    def test_scp079_keeps_system_tokens(self):
        text = ">>> ERR_MEM_OVERFLOW. >>> ACCESS_DENIED."
        out = sanitize(text, "scp079")
        assert "ERR" in out
        assert "MEM" in out
        assert "OVERFLOW" in out
        assert "ACCESS" in out


class TestMarkdownStripping:
    def test_strips_bold_markers(self):
        out = sanitize("**객체 등급:** Euclid", "researcher")
        assert "**" not in out
        assert "객체 등급: Euclid" in out

    def test_strips_nested_bold(self):
        out = sanitize("위협: **Keter** 등급.", "agent")
        assert "**" not in out
        assert "Keter" in out


class TestWhitespaceCleanup:
    def test_collapses_multiple_spaces(self):
        # After removing "The" the sanitizer should leave clean spacing.
        text = "본 연구원    보고드립니다."
        out = sanitize(text, "researcher")
        assert "   " not in out
        assert "본 연구원 보고드립니다." == out

    def test_preserves_paragraph_breaks(self):
        text = "첫 문단입니다.\n\n두 번째 문단입니다."
        out = sanitize(text, "researcher")
        assert "첫 문단입니다." in out
        assert "두 번째 문단입니다." in out


class TestEdgeCases:
    def test_empty_string(self):
        assert sanitize("", "researcher") == ""

    def test_unknown_persona_defaults_to_researcher(self):
        text = "MTF Nu-7 배치."
        # researcher doesn't whitelist "Nu", but SCP-style "Nu-7" is a hyphen
        # identifier. Unknown persona uses researcher whitelist.
        out = sanitize(text, "unknown_persona")
        # MTF is whitelisted in researcher too
        assert "MTF" in out


class TestResearcherSpecificCleaning:
    def test_removes_leaked_directives(self):
        text = (
            "객체 지정번호: SCP-173\n"
            "객체 등급: Euclid\n"
            "본 연구원의 보고서 형식 유지: '~습니다/~입니다' 종결을 준수합니다.\n"
            "종결: ~습니다/~입니다만 사용.\n"
            "[캐릭터 지시] 소제목·레이블 없이 본문만 작성.\n"
            "말투 지침: ~습니다.\n"
            "SCP-173은 격리 구역에 보관됩니다."
        )
        out = sanitize(text, "researcher")
        assert "보고서 형식 유지" not in out
        assert "종결" not in out
        assert "캐릭터 지시" not in out
        assert "말투 지침" not in out
        assert "SCP-173은 격리 구역에 보관됩니다." in out

    def test_removes_section_labels(self):
        text = (
            "객체 지정번호: SCP-173\n"
            "객체 등급: Euclid\n"
            "설명: SCP-173은 콘크리트로 제작되었습니다.\n"
            "부록: 추가 요원 배치가 권고됩니다.\n"
            "격리 절차 요약: 상시 시각 접촉을 유지하십시오."
        )
        out = sanitize(text, "researcher")
        assert "설명:" not in out
        assert "부록:" not in out
        assert "격리 절차 요약:" not in out
        assert "SCP-173은 콘크리트로 제작되었습니다." in out
        assert "추가 요원 배치가 권고됩니다." in out
        assert "상시 시각 접촉을 유지하십시오." in out

    def test_removes_section_labels_markdown(self):
        text = (
            "객체 지정번호: SCP-173\n"
            "객체 등급: Euclid\n"
            "**설명**: SCP-173은 위험합니다.\n"
            "### 격리 절차 요약\n"
            "상시 시각 접촉 필수."
        )
        out = sanitize(text, "researcher")
        assert "설명" not in out
        assert "격리 절차 요약" not in out
        assert "SCP-173은 위험합니다." in out
        assert "상시 시각 접촉 필수." in out


class TestHanjaTranslation:
    def test_translates_hanja_to_hangul(self):
        text = "보고서를 提出함."
        out = sanitize(text, "researcher")
        assert "제출" in out


