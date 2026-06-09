# 설계 명세서: SCP World Visual 및 로컬 마이그레이션

본 문서는 SCPWorld 챗봇 데모를 GCP 서버리스 아키텍처에서 완전한 로컬 구동 환경으로 마이그레이션하고, 애니메이션 도트(픽셀 아트) 캐릭터와 동적 배경을 결합한 반응형 분할 화면 사용자 인터페이스를 도입하기 위한 설계 방향을 정의합니다.

---

## 1. 목표 및 범위

**SCPWorldVisual** 프로젝트의 핵심 목표는 다음과 같습니다.
1. **로컬 실행 환경 구축**: GCP 서비스 의존성(Cloud Run vLLM, Firestore Native Vector Search, Firebase Auth, Google Sign-In)을 완전히 제거하여 개발자가 로컬 환경(Ollama, Python SQLite, 로컬 Flutter Web)에서 최소한의 의존성만으로 전체 시스템을 구동할 수 있도록 합니다.
2. **시각적 몰입감 극대화**: 채팅 인터페이스를 반응형 좌우 분할 화면(Split-Screen) 레이아웃으로 변경합니다. 왼쪽 영역에는 선택된 페르소나의 격리실 또는 사무실을 표현하는 애니메이션 도트 그래픽 배경과 캐릭터를 배치하고, 오른쪽 영역에는 기존의 레트로 터미널 채팅창을 구성합니다.

---

## 2. 시스템 아키텍처 구성도

```mermaid
graph TD
    subgraph Frontend (Flutter Web)
        A[LoginScreen - 레트로 ID 입력] --> B[PersonaSelectScreen]
        B --> C[ChatScreen - 분할 레이아웃]
        C --> D[VisualMonitor - 좌측 영역]
        C --> E[ChatInterface - 우측 영역]
    end

    subgraph Backend (FastAPI)
        E --> F[API 라우터]
        F --> G[RAG 서비스]
        F --> H[저장소 서비스]
        G --> I[SentenceTransformers - GPU 가속 BGE-M3]
        G --> J[NumPy 행렬 곱 기반 벡터 유사도 검색]
        H --> K[(로컬 SQLite DB)]
        F --> L[Ollama 서비스 클라이언트]
    end

    subgraph External (Localhost)
        L --> M[Ollama 서버 - http://localhost:11434]
        M --> N[(로컬 LLM - qwen2.5:7b)]
    end
```

---

## 3. 상세 설계 내용

### 3.1. 프론트엔드 UI 및 시각 컴포넌트 (Flutter Web)

* **반응형 분할 화면 레이아웃**:
  * Flutter의 `LayoutBuilder`를 사용하여 화면 너비가 $800\text{px}$ 이상일 때는 좌우 분할 모드로 배치합니다 (좌측 40% `VisualMonitor`, 우측 60% 대화 영역).
  * 화면 너비가 $800\text{px}$ 미만(모바일/태블릿 등)일 때는 상하 배치 모드로 전환됩니다 (상단 220px 고정 `VisualMonitor`, 하단 남은 영역 전체 대화 영역).

* **`VisualMonitor` 위젯 다층(Layered) 구조**:
  * **Layer 1: 페르소나별 도트 배경 에셋**: `assets/images/backgrounds/`에 저장된 16비트 도트 스타일 배경 이미지.
    * *연구원*: 서류 더미와 분석용 모니터가 있는 연구실 사무실 환경.
    * *요원*: CCTV 모니터 벽과 작전 지도가 띄워진 지하 통제실 환경.
    * *SCP-079*: 구형 컴퓨터 단말, 케이블, 서버 랙들이 있는 강철 격리실 환경.
  * **Layer 2: 환경 특수 효과 (VFX) 오버레이**: 플러터 코드로 구동되는 동적 그래픽 애니메이션.
    * *연구원*: 깜빡이는 분석 장비 불빛 연출.
    * *요원*: 회전하고 깜빡이는 붉은 경보등 연출 (`RadialGradient` 애니메이션).
    * *SCP-079*: 화면 상단에서 흘러내리는 구식 녹색 문자열 비(Matrix Rain) 효과 및 가끔 치는 지글거림(CRT Glitch).
  * **Layer 3: 페르소나 도트 캐릭터 스프라이트**: 플러터를 통해 구현하는 동적 움직임.
    * *대기 상태 (Idle)*: `TweenAnimationBuilder`를 통해 부드럽게 상하 크기가 미세하게 변하는 숨쉬기(Breathing) 효과.
    * *대화 생성 상태 (LLM 스트리밍 중)*: 캐릭터의 들썩거림(Bobbing), 타이핑 중인 손동작 스프라이트로 교체, 또는 요원의 무전기 통신 램프 점멸 등 적용.
    * *SCP-079 노이즈 상태*: 대화 생성 중에 기괴한 노이즈 필터, 위치 오프셋 글리치 효과 실시간 렌더링.
  * **Layer 4: CRT 모니터 프레임 및 스캔라인 (Scanline)**:
    * 레트로 모니터 베젤 그래픽 프레임.
    * 반투명하게 가로지르는 주사선(Scanline) 및 화면 깜빡임 효과 오버레이.
    * 좌측 상단에 실시간 상태와 동기화되는 터미널 로그 텍스트 (예: `MONITORING: ACTIVE`, `STATUS: GENERATING RESPONSE...` 등) 표시.

---

### 3.2. 백엔드 RAG 및 로컬 DB 아키텍처 (FastAPI + SQLite + NumPy)

* **데이터베이스 엔진**: 백엔드 폴더 내 파일 기반 SQLite (`scp_database.db`) 사용.
* **데이터베이스 스키마 구성**:
  ```sql
  CREATE TABLE scp_documents (
      id TEXT PRIMARY KEY,
      item_number TEXT,
      object_class TEXT,
      section_type TEXT,
      tags TEXT, -- JSON 문자열
      text TEXT,
      url TEXT,
      embedding BLOB -- 1024차원 float32 리스트 (4096바이트 raw binary)
  );

  CREATE TABLE chat_sessions (
      session_key TEXT PRIMARY KEY, -- {user_id}__{persona_id}__{session_id}
      user_id TEXT,
      persona_id TEXT,
      session_id TEXT,
      messages TEXT, -- 메시지 딕셔너리 리스트의 JSON 문자열
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );

  CREATE TABLE users (
      user_id TEXT PRIMARY KEY,
      name TEXT,
      last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );
  ```

* **로컬 임베딩 생성 및 벡터 검색 구현**:
  * **임베딩 모델**: CUDA 가속(`device="cuda"`)을 우선 사용하되, GPU가 없을 경우 CPU(`"cpu"`)로 자동 폴백하는 `SentenceTransformer("BAAI/bge-m3")` 로드.
  * **벡터 검색 로직**:
    1. 사용자의 쿼리에 대해 1024차원 임베딩 벡터 $Q \in \mathbb{R}^{1024}$를 생성합니다.
    2. SQLite 데이터베이스에서 특정 `item_number = ?` 메타데이터에 일치하는 문서 조각을 불러옵니다.
    3. 로드된 임베딩(BLOB)들을 NumPy 2D 행렬 $M \in \mathbb{R}^{N \times 1024}$로 로드합니다.
    4. 코사인 유사도를 연산합니다. 쿼리 벡터와 DB 벡터가 이미 L2 정규화되어 있으므로, 코사인 유사도는 NumPy의 **행렬 곱(Dot Product)** 연산으로 처리됩니다.
       ```python
       similarities = np.dot(embeddings_matrix, query_vector)
       ```
    5. 유사도가 높은 상위 $K$개의 인덱스를 추출하여 해당 원문 문서 본문 조각을 RAG 컨텍스트로 프롬프트에 동적으로 바인딩합니다.

* **Ollama API 클라이언트 연동**:
  * FastAPI 백엔드가 `http://localhost:11434/v1/chat/completions` 주소를 바라보도록 설정합니다.
  * Google OAuth 인증 검증(Bearer Google ID Token)을 거치지 않으므로 HTTP 헤더 생성 로직을 간소화합니다.
  * 백엔드 환경 변수(`.env`) 설정을 통해 구동할 LLM 모델명(기본값: `qwen2.5:7b`)을 자유롭게 변경할 수 있도록 합니다.

---

### 3.3. 사원 ID 로컬 인증 체계

* **로그인 UI**: Google 인증 버튼을 제거하고, "사원 ID 보안 터미널 로그인" 인터페이스를 배치합니다.
* **동작 프로세스**:
  * 사용자가 사원 식별자 ID(예: `OP-104`, `Dr. Clef` 등)를 입력하여 접속을 수행합니다.
  * 입력받은 사원 ID를 `SharedPreferences`를 활용해 브라우저에 캐싱하여 새로고침 시에도 로그인 상태를 영구 유지합니다.
  * 모든 API 요청 시 `Authorization: Bearer <사원_ID>` 헤더를 주입해 통신합니다.
  * 백엔드 보안 종단점(`dependencies.py`)은 Google Token 파싱 대신 단순히 전달된 사원 ID 값을 추출하여 유효한 사용자로 간주하고 이를 `user_id` 세션 키로 식별하여 RAG와 채팅 저장소에 사용합니다.

---

## 4. 검증 계획

### 4.1. 자동화 테스트 계획
* 데이터베이스 초기화 및 데이터 주입용 마이그레이션 스크립트(`init_db.py`) 구동 테스트.
* 목업 데이터 및 실제 RAG 청크 벡터를 이용한 NumPy 코사인 유사도 연산 성능 및 매칭률 독립 테스트.
* 로컬 Ollama API 서버(`http://localhost:11434/v1`) 연결 및 스트리밍 응답 지연 시간 유효성 확인용 스크립트 작성 및 실행.

### 4.2. 수동 검증 계획
* 백엔드를 로컬에서 구동하여 SQLite 데이터베이스 및 테이블 자동 생성 확인.
* 다양한 이름의 사원 ID로 로그인 테스트 후 세션이 개별적으로 독립되어 유지되는지 확인.
* 특정 SCP 정보(예: "SCP-173에 대해 알려줘") 질문 시, SQLite RAG를 거쳐 정확한 출처 URL 및 본문이 답변에 표시되는지 검증.
* 모니터 화면 크기 조절 시 좌우 분할에서 상하 분할로 자연스럽게 레이아웃이 깨지지 않고 갱신되는지 확인.
