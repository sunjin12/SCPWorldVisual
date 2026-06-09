# SCP World 아키텍처 비교: GKE vs. Serverless

기존 GKE 기반의 복잡한 인프라에서 Cloud Run과 Firestore를 사용하는 비용 효율적인 서버리스 아키텍처로의 전환 과정을 정리했습니다.

---

## 1. 시스템 구성도 (System Architecture)

### [Before] GKE 기반 (고정비 발생형)
기존 아키텍처는 GKE 클러스터 내에서 모든 구성 요소를 파드(Pod) 형태로 관리했습니다. CPU와 메모리 점유로 인해 인스턴스가 24시간 가동되어야 하므로 고정 비용이 높았습니다.

```mermaid
graph TD
    subgraph "GCP Resource (GKE Cluster)"
        FE[Frontend Pod - Flutter]
        BE[Backend Pod - FastAPI]
        QD[Qdrant - Vector DB]
        RD[Redis - Session Cache]
        VLLM["vLLM Pod (GPU L4)"]
    end

    User --> FE
    FE --> BE
    BE --> QD
    BE --> RD
    BE --> VLLM
```

### [After] Serverless 환경 (비용 최적화형)
수정 후 아키텍처는 관리형 서비스를 사용하여 유휴 상태일 때 비용이 발생하지 않거나(0원), 처리량에 비례하여 비용을 지불하는 구조입니다.

```mermaid
graph TD
    subgraph "GCP Serverless Ecosystem"
        FH[Firebase Hosting - Flutter]
        CRB["Cloud Run (Backend CPU)"]
        FS[("Firestore (Native Mode)")]
        CRG["Cloud Run (vLLM GPU L4)"]
    end

    User --> FH
    FH --> CRB
    CRB --> FS
    CRB --> CRG
    
    note_fs["<b>Firestore 통합</b><br/>Vector Search + History"]
    FS --- note_fs
```

---

## 2. 데이터 흐름도 (Data Flow)

### [Before] 파편화된 데이터 관리
데이터가 검색(Qdrant), 세션(Redis), 영구 저장(DB)으로 파편화되어 있어 로직이 복잡했습니다.

```mermaid
sequenceDiagram
    participant User
    participant BE as Backend (FastAPI)
    participant QD as Qdrant
    participant RD as Redis
    participant VLLM as vLLM (GPU)

    User->>BE: 질문 전송
    BE->>RD: 세션 이력 조회 (Session ID)
    RD-->>BE: 문맥 데이터 반환
    BE->>QD: 벡터 검색 (Similarity Search)
    QD-->>BE: 관련 SCP 문서 반환
    BE->>VLLM: 프롬프트 전송 (Persona + History + Docs)
    VLLM-->>BE: 답변 생성 (Streaming)
    BE->>User: SSE 응답 전송
    BE->>RD: 새로운 대화 턴 저장
```

### [After] Firestore 중심의 단일화된 흐름
Firestore가 벡터 검색과 세션 관리를 모두 수행하므로 데이터 흐름이 단순해지고 인프라 의존성이 줄어듭니다.

```mermaid
sequenceDiagram
    participant User
    participant BE as Cloud Run (Backend)
    participant FS as Firestore (Unified DB)
    participant VLLM as Cloud Run (vLLM GPU)

    User->>BE: 질문 전송
    BE->>FS: 세션 이력 조회 (sessions 컬렉션)
    FS-->>BE: 문맥 데이터 반환
    BE->>FS: 벡터 검색 (find_nearest)
    FS-->>BE: 관련 SCP 문서 반환 (scp_documents)
    BE->>VLLM: 프롬프트 전송
    VLLM-->>BE: 답변 생성 (Streaming)
    BE->>User: SSE 응답 전송
    BE->>FS: 새로운 대화 턴 저장 (save_history)
```

---

## 💡 주요 변경 포인트
1.  **단일 DB 전략**: Qdrant와 Redis를 **Firestore 하나로 통합**하여 관리 포인트를 획기적으로 줄였습니다.
2.  **GPU 서버리스화**: GKE 노드 풀 대신 **Cloud Run GPU**를 사용하여 사용한 시간(초 단위)만큼만 GPU 비용을 지불합니다.
3.  **정적 웹 호스팅**: 기존 Nginx 파드 대신 **Firebase Hosting**을 사용하여 글로벌 CDN을 통한 빠른 배포와 0원 수준의 유지비를 달성합니다.
