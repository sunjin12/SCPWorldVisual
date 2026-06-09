# Frontend Screens

라우터 정의: [frontend/lib/app.dart](../frontend/lib/app.dart) — `routerProvider` (go_router).
모든 라우트는 `authProvider` 의 로그인 상태에 따라 redirect 됩니다.

## `/splash` — 스플래시
- **진입**: 앱 시작 시 자동 (`initialLocation`)
- **표시**: SCP 로고, "SECURE. CONTAIN. PROTECT.", 페이드 인/아웃 애니메이션, 스피너
- **사용자 액션**: 없음. 2초 후 `/login` 으로 자동 이동.

## `/login` — 로그인
- **진입**: 스플래시 후, 또는 비로그인 상태에서 보호 라우트 접근 시
- **표시**: SCP 로고, "LEVEL 2 CLEARANCE REQUIRED" 경고, Google 로그인 버튼, CC-BY-SA 풋터
- **사용자 액션**:
  - **Google로 로그인**: `authProvider.signIn()` → `GoogleSignIn.instance.authenticate()` 호출. 성공 시 `/personas` 로 자동 이동.
  - **로그인 실패**: 빨간색 에러 메시지 표시.

## `/personas` — 페르소나 선택
- **진입**: 로그인 성공 후, 또는 채팅 화면에서 뒤로가기
- **표시**: AppBar "SELECT PERSONA" + 3개 카드:
  - **Dr. [REDACTED]** (researcher) — 수석 연구원, `[DEFAULT]` 배지. **존댓말**(하십시오체) 임상 보고서 톤.
  - **Agent [REDACTED]** (agent) — 현장 요원. **반말**(해라체) 전술 브리핑 톤.
  - **SCP-079** (scp079) — 구식 AI. **특수 단편 모드** — `>>>` 시스템 토큰, 8어절 이하 짧은 문장, 체언·명사구 종결.
- **페르소나별 대화 이력은 백엔드에서 완전히 분리** (Firestore 문서 키에 `persona_id` 포함). 페르소나 전환 시 이전 페르소나 대화가 노출되지 않음.
- **사용자 액션**:
  - **카드 탭**: `selectedPersonaProvider.select(persona)` — 선택 표시 갱신
  - **"BEGIN BRIEFING"**: 미선택 시 `researcher` 기본값 적용, `/chat` 으로 이동

## `/chat` — 채팅 (메인)

### AppBar
- **뒤로가기 (←)**: `/personas` 로 이동
- **페르소나 이름**: 현재 선택된 페르소나 (예: "Dr. [REDACTED]")
- **새 세션 (＋)**: `chatProvider.newSession()` — 새 `session_id` 발급, 메시지 초기화
- **사용자 아바타** (이름 첫 글자):
  - 탭 시 PopupMenu 표시:
    - 사용자 이름 + 이메일 (정보용, 비활성)
    - **"LOG OUT"** — 빨간색. 탭 시 `authProvider.signOut()` + `chatProvider.newSession()` → 가드가 자동으로 `/login` 으로 보냄.

### Body — 메시지 영역
- **빈 상태**: "SCP DATABASE TERMINAL" + "Enter your query to access SCP records."
- **메시지 있음**: `MessageBubble` 위젯으로 각 메시지 표시
  - 사용자 메시지: 우측 정렬, 빨간색 톤
  - AI 메시지: 좌측 정렬 + 아바타, "SCP FOUNDATION" 라벨
  - **`[REDACTED]`, `[DATA EXPUNGED]`** 패턴: 검은색 박스로 스타일링
  - **스트리밍 중**: 깜빡이는 빨간색 커서

### Body — 스테이지 인디케이터 (스트리밍 시작 ~ 첫 토큰 도착 사이)
| stage | 한국어 라벨 |
|-------|-----------|
| `null` (서버 연결 전) | 서버 연결 중... |
| `history` | 세션 기록 불러오는 중... |
| `rag` | 연구 일지 조회 중... |
| `prompt` | 문서 분석 중... |
| `llm` | 답변 생성 중... |
| `persist` | 기록 저장 중... |

### 스트리밍 완료 처리
스트림의 마지막 SSE 이벤트(`{"done": true, ...}`)에는 백엔드가 후처리 필터(`response_filter.sanitize`)를
적용한 `final_text` 필드가 포함됩니다. 클라이언트는 이를 수신하면 그동안 토큰 단위로 누적해
화면에 보여주던 본문을 `final_text` 로 교체합니다. 결과적으로 한자·비허용 영문·`>>>` 누출 등
스트리밍 중에 일시적으로 표시됐을 수 있는 불순물이 최종 화면에서는 제거됩니다.

### Input Bar
- **TextField**:
  - 1줄 → 5줄 자동 확장
  - **Enter** (단독): 메시지 전송
  - **Shift+Enter**: 줄바꿈
  - 로딩 중: 비활성화, "Processing query..." 힌트
- **Send 버튼** (✈):
  - 일반: 빨간색
  - 로딩 중: 회색 + 스피너

### Footer
- CC-BY-SA 3.0 라이선스 표기 (SCP Foundation Wiki 콘텐츠)

## 사용자 액션 → API 매핑

| 액션 | API 호출 |
|------|----------|
| 로그인 | (백엔드 호출 없음 — Google 직접) → 후속 API 호출에 ID Token 첨부 |
| 메시지 전송 | `POST /api/chat/stream` (SSE, Bearer ID Token) |
| 새 세션 | (백엔드 호출 없음, 클라이언트 상태만 리셋) |
| 로그아웃 | (백엔드 호출 없음 — `GoogleSignIn.signOut()`) |

`/api/auth/verify`, `/api/personas`, `/api/chat` (동기) 는 백엔드에는 존재하지만 현재 클라이언트가 호출하지 않습니다 (페르소나는 하드코딩, 인증은 후속 요청의 Bearer 토큰으로 매번 검증).
