# Architecture

## 시스템 다이어그램

```
┌──────────────────────────────────────────────────────────────────┐
│  USER  (브라우저)                                                 │
└──────────────────────┬───────────────────────────────────────────┘
                       │  HTTPS
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│  FRONTEND  Flutter Web                                           │
│  Firebase Hosting   (scpworld.web.app)                           │
│  - Riverpod 상태관리 / go_router                                  │
│  - SSE 클라이언트 (chat_provider.dart)                            │
│  - google_sign_in (Web button)                                   │
└────────┬──────────────────────────────────────────┬──────────────┘
         │                                          │
   ① Google ID Token 발급                       ② API 호출
         ▼                                          │  Authorization: Bearer <id_token>
┌──────────────────┐                                ▼
│  GOOGLE OAUTH    │       ┌────────────────────────────────────────────┐
│  (공개 키)       │◄─────│  BACKEND  FastAPI on Cloud Run (CPU)        │
└──────────────────┘ ③검증 │  asia-southeast1 / scp-backend              │
                          │                                              │
                          │  Routers                                     │
                          │   /api/auth/verify                           │
                          │   /api/personas      (인증 필요)             │
                          │   /api/chat         (인증 필요, 동기)        │
                          │   /api/chat/stream  (인증 필요, SSE) ★메인  │
                          │   /health, /ready                            │
                          │                                              │
                          │  Services                                    │
                          │   MemoryService  ─┐                          │
                          │   RAGService     ─┤                          │
                          │   EmbeddingSvc   ─┤  (BGE-M3 in-process)     │
                          │   PromptService  ─┤                          │
                          │   LLMService     ─┘                          │
                          └──┬────────────────────┬──────────────────┬───┘
                             │                    │                  │
                             │ ④ Vector Search    │ ⑤ ID Token 발급  │ ⑥ /v1/chat/completions
                             │   (find_nearest)   │   (metadata)     │   (SSE stream)
                             ▼                    ▼                  ▼
                ┌────────────────────┐  ┌──────────────────┐  ┌────────────────────┐
                │  FIRESTORE         │  │  Cloud Run       │  │  Cloud Run GPU      │
                │  (Native Mode)     │  │  Metadata Server │  │  vllm-server-v3     │
                │                    │  │  (Auth Audience) │  │  Qwen2.5-7B / L4    │
                │  scp_documents     │  └──────────────────┘  │  scale-to-zero      │
                │   (1024-d vector)  │                        │  ⏱ 콜드스타트 3~5분 │
                │  sessions          │                        └────────────────────┘
                │  users             │
                └────────────────────┘
```

## 컴포넌트 책임

### Frontend (Flutter Web)
- 라우트 가드: `routerProvider` (lib/app.dart) — 비로그인 시 보호 라우트 접근 자동 차단
- 인증: `authProvider` — Google Sign-In v7 API, ID Token 보관
- 채팅: `chatProvider` — `http.Client().send()` 으로 SSE 수신, 토큰 누적, 스테이지 추적
- 페르소나: `selectedPersonaProvider` — 3종 하드코딩 (Persona 모델), 선택 상태 보관
- UI: `MessageBubble` — `[REDACTED]` 박스 스타일링, 깜빡이는 커서, 스테이지 라벨 (한국어)

### Backend (FastAPI)
| 모듈 | 역할 |
|------|------|
| `app/main.py` | FastAPI 인스턴스, CORS, 라우터 등록, lifespan |
| `app/config.py` | Pydantic Settings — Firestore/vLLM/OAuth 설정 |
| `app/dependencies.py` | DI 컨테이너 — Firestore 클라이언트, vLLM httpx 클라이언트, Embedding 모델, ID Token 캐시(50분) 싱글톤 |
| `app/middleware/auth.py` | `verify_google_token` Dependency |
| `app/routers/chat.py` | `/api/chat/stream` SSE, `/api/chat` 동기 |
| `app/routers/auth.py` | `/api/auth/verify` |
| `app/routers/personas.py` | `/api/personas` |
| `app/routers/health.py` | `/health`, `/ready` |
| `app/services/memory_service.py` | 슬라이딩 윈도우 대화 히스토리 (Firestore `sessions`, 페르소나별 격리) |
| `app/services/rag_service.py` | SCP 번호 자동 추출 + Firestore `find_nearest` 호출 |
| `app/services/embedding_service.py` | BAAI/bge-m3 CPU 임베딩, asyncio executor |
| `app/services/prompt_service.py` | persona system + RAG context + history + user msg 조립 |
| `app/services/llm_service.py` | vLLM `/v1/chat/completions` SSE 스트림 |
| `app/services/storage_service.py` | Firestore 통합 (vector_search / get_history / save_history / save_user) |
| `app/services/response_filter.py` | LLM 출력 후처리 (한자·가나 제거, 페르소나별 영문 화이트리스트, `>>>` 토큰·마크다운 볼드 스트립) |
| `app/core/personas.py` | 3개 페르소나(연구원/에이전트/SCP-079)의 system prompt, closing directive, few-shot, 샘플링 파라미터 |

### Cloud Run vLLM
- 이미지: `vllm/vllm-openai:latest`
- 모델: `Qwen/Qwen2.5-7B-Instruct`, `--max-model-len=8192`, `--dtype=bfloat16`, `--enforce-eager`
- GPU: NVIDIA L4 ×1, CPU 8 / Memory 32Gi
- 인증: Cloud Run IAM (Bearer ID Token 필수)
- 스케일: 0 → on-demand. 콜드 스타트 3~5분 (의도된 정책)

### Firestore 컬렉션

```
scp_documents          # RAG 벡터 저장소
  ├ item_number        (e.g. "SCP-173")
  ├ object_class       (e.g. "Euclid")
  ├ section_type       (containment_procedures | description | full)
  ├ tags               (string[])
  ├ text               (string)
  ├ url                (string)
  └ embedding          (Vector<1024>, normalized, COSINE)

sessions/{user_id}__{persona_id}__{session_id}
  ├ messages           (Message[]: role, content)
  ├ user_id            (string)
  ├ persona_id         (string: "researcher" | "agent" | "scp079")
  ├ session_id         (string)
  └ updated_at         (TIMESTAMP)
  # 문서 키에 persona_id 를 포함시켜 페르소나 전환 시 이력이 교차 오염되지 않도록 분리.

users/{user_id}
  ├ user_id, email, name, picture
  └ last_login         (TIMESTAMP)
```

## 데이터 흐름

### 챗 SSE (`POST /api/chat/stream`)

```
[USER]
  │ "SCP-173에 대해 알려줘"
  ▼
[Frontend chat_provider.dart]
  ├─ POST /api/chat/stream  Authorization: Bearer <google_id_token>
  │  body { session_id, message, persona_id }
  ▼
[Backend chat.py event_generator()]
  │
  │ ─►  SSE: {"stage":"history"}    MemoryService.get_history()
  │ ─►  SSE: {"stage":"rag"}        RAGService.hybrid_search()
  │      ├─ extract_scp_number → "SCP-173"
  │      ├─ EmbeddingService.encode → [1024-d]
  │      └─ Firestore find_nearest (COSINE, top_k=5)
  │ ─►  SSE: {"stage":"prompt"}     get_persona + build_prompt
  │ ─►  SSE: {"stage":"llm"}        LLMService.generate_stream
  │      └─ httpx → vLLM /v1/chat/completions (Bearer Cloud Run ID Token)
  │ ◄── 토큰별 SSE: {"token":"...","done":false}
  │
  │     stage="sanitize" → ResponseFilter.sanitize(full_response, persona_id)
  │       ├─ 한자(CJK)·일본어 가나 제거
  │       ├─ 페르소나별 영문 화이트리스트로 비허용 영문 단어 제거
  │       ├─ `>>>` 시스템 토큰 제거 (SCP-079 제외)
  │       └─ 마크다운 볼드(`**…**`) 마커 제거
  │     stage="persist" → MemoryService.add_turn(persona_id, …) → Firestore sessions.set
  │
  │ ─►  SSE: {"token":"","done":true,"sources":[urls...],"final_text":"<정제본>"}
  │       └─ 클라이언트는 final_text 로 누적 버퍼 최종 교체 (스트리밍 중엔 원본 표시)
  ▼
[Frontend MessageBubble]
  - stage 별 한국어 라벨 + 스피너 (콜드스타트 안내 포함)
  - token 누적 → 실시간 스트리밍
  - done 시 종료
```

### 데이터 파이프라인 (오프라인, 1회성)

```
SCP Wiki  ──► scrape_scp.py        ──► data/scp_raw_documents.json
              (rate limit 2초)

              preprocess.py        ──► data/scp_chunks.json
              (Wikidot 마크업 제거,
               512 tok 청킹, overlap 64)

              upload_to_firestore  ──► Firestore scp_documents
              (BGE-M3 임베딩, batch 100,
               Vector(1024) 정규화)

              validate_firestore   (count/sample/find_nearest 테스트)
```

## 인증 흐름

```
[Frontend]  google_sign_in.authenticate()
              ├─ Google OAuth Server (popup/redirect)
              └─ ID Token (JWT, aud=GOOGLE_CLIENT_ID, exp=1h)

[Frontend → Backend]  Authorization: Bearer <id_token>
[Backend middleware/auth.py]
  └─ google.oauth2.id_token.verify_oauth2_token(token, GOOGLE_CLIENT_ID)
       └─ Google 공개키 서명 검증
       └─ AuthUser(user_id=sub, email, name, picture)

[Backend → vLLM]  Authorization: Bearer <cloud_run_id_token>
[Backend dependencies.get_vllm_id_token()]
  └─ google.oauth2.id_token.fetch_id_token(audience=vLLM_URL)
       ├─ Cloud Run metadata server 호출
       └─ 50분 in-process 캐시
```

## 주요 설계 결정

- **vLLM scale-to-zero 유지** — L4 GPU 24/7 비용(~$500/월) 회피. 콜드스타트는 UI 라벨로 안내.
- **임베딩은 백엔드 in-process** — 별도 임베딩 서비스를 두지 않고 BGE-M3을 백엔드 컨테이너에서 직접 실행. 4Gi 메모리면 충분.
- **클라이언트는 Firestore 직접 접근 안 함** — 모든 데이터는 백엔드를 경유. firestore.rules는 deny-all.
- **백엔드는 `--allow-unauthenticated`** — 인프라 레벨 차단이 아닌 앱 레벨 OAuth로 보호. CORS preflight를 막지 않기 위함.
- **페르소나별 이력 격리** — Firestore 문서 키에 `persona_id`를 포함시켜 저장소 레벨에서 교차 참조 불가. 프론트엔드의 메모리 분리만으로는 동일 `session_id` 재사용·앱 재시작 시 취약하기 때문.
- **출력 후처리 필터** — Qwen2.5-7B는 중국어·일본어·영문이 섞여 나오는 경향이 있어 system prompt만으로는 억제가 어려움. 생성이 끝난 전체 응답에 일회성 `sanitize()` 적용(토큰 단위 검열은 멀티바이트 토큰 분할로 누락 위험). SCP-079만 `>>>` 시스템 토큰을 허용하고 다른 페르소나의 누출은 제거.
