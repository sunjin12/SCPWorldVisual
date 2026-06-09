# SCP World - 포트폴리오

---

## 1. TL;DR

**SCP World** — SCP Foundation 위키 콘텐츠를 임베딩하여 Firestore Vector에 저장하고, RAG를 활용하여 재단 페르소나(연구원 / 요원 / SCP-079) 중 하나로 답변하는 챗봇 시스템입니다. 100% 서버리스(Cloud Run + Firebase Hosting + Firestore)로 운영됩니다.

### 기술 스택

| 레이어 | 기술 |
|--------|------|
| Frontend | Flutter Web, Riverpod, go_router, Google Sign-In v7 |
| Backend API | FastAPI, Uvicorn, Python 3.11 |
| LLM Serving | vLLM (Qwen2.5-7B-Instruct), NVIDIA L4 GPU |
| Embedding | BAAI/bge-m3 (1024차원) |
| Vector DB | Firestore Native Vector Search (find_nearest, COSINE) |
| Infra | Cloud Run (Scale-to-Zero), Firebase Hosting, Firestore |
| Auth | Google OAuth 2.0, ID Token 검증 |


---

## 2. Overview: 프로젝트 개요

### 기획 배경 및 목표

세계관을 탐구할 때, 단순히 위키를 읽는 것이 아니라 하나의 페르소나를 가진 캐릭터와 대화하며 알아가면 재밌을 것 같다고 생각했습니다. 방대한 자료와 오픈된 라이선스(CC BY-SA 3.0)를 가진 SCP 위키를 기반으로, 3가지 캐릭터를 통해 SCP 세계관에 대해 탐구할 수 있는 챗봇을 만들었습니다.

### 핵심 기능

| 기능 | 설명 |
|------|------|
| 페르소나 선택 | 연구원(Dr. [REDACTED]), 요원(Agent [REDACTED]), SCP-079(Old AI) 중 선택 |
| RAG 기반 대화 | SCP 위키 문서를 벡터 검색하여 근거 있는 답변 생성 |
| SSE 스트리밍 | 토큰 단위 실시간 스트리밍으로 자연스러운 대화 경험 |
| 페르소나별 격리 | 캐릭터마다 독립된 대화 세션 유지 |
| Google 로그인 | OAuth 2.0 기반 인증, ID Token으로 모든 API 보호 |
| 출처 표시 | 답변에 사용된 SCP 위키 원문 URL 제공 |

---

## 3. System Architecture

### 시스템 구성도

![시스템 구성도](images/SCPWorld시스템구성도.png)

### 데이터 흐름도

**데이터 수집 파이프라인 (오프라인)**

![데이터 수집 파이프라인](images/SCPWorld데이터수집파이프라인.png)

**실시간 질의 파이프라인 (온라인)**

![실시간 질의 파이프라인](images/SCPWorld실시간질의파이프라인.png)

---

## 4. Analyze & Action: 기술적 가치

### 4-1. 트러블슈팅 및 인프라 최적화

#### Problem 1: 단일 GPU에 임베딩 모델과 LLM 동시 탑재 시 OOM

**문제 상황**

초기 설계에서는 하나의 GPU 인스턴스에 임베딩 모델(BAAI/bge-m3)과 LLM(Qwen2.5-7B)을 함께 올려 운영하려 했습니다. NVIDIA L4 GPU의 VRAM은 24GB인데, LLM 단독으로도 bfloat16 기준 약 14GB의 VRAM을 점유하고, 임베딩 모델까지 GPU에 올리면 가용 메모리가 부족해져 OOM(Out of Memory)이 빈번하게 발생했습니다.

**원인 분석**

- vLLM은 KV Cache를 위해 남는 GPU 메모리를 최대한 확보하려 하므로, 다른 모델과 GPU를 공유하는 구조에 적합하지 않음
- 임베딩 모델과 LLM이 동시에 메모리를 점유하면 KV Cache 공간이 부족해져 max-model-len을 극단적으로 줄여야 함
- 이는 RAG 컨텍스트 + 대화 히스토리를 충분히 담을 수 없는 결과를 초래

**해결 과정**

임베딩 모델을 GPU에서 분리하여 **CPU에서 추론**하도록 변경했습니다. BGE-M3는 인코딩 속도가 CPU에서도 충분히 빠르고(쿼리 1건당 수십 ms), 실시간 대량 처리가 아닌 쿼리 단위 인코딩이므로 GPU가 필수적이지 않았습니다. 이를 통해 L4 GPU 24GB 전체를 vLLM에 할당할 수 있게 되었고, `gpu-memory-utilization=0.8`, `max-model-len=8192`로 안정적으로 운영할 수 있게 되었습니다.

```python
# backend/app/services/embedding_service.py
model = SentenceTransformer("BAAI/bge-m3", device="cpu")
embedding = await loop.run_in_executor(
    None, lambda: model.encode(text, normalize_embeddings=True).tolist()
)
```

---

#### Problem 2: 로컬 GPU 부족 → GKE 전환 → 비용 폭증 → 서버리스 전환

**문제 상황**

로컬 환경에는 LLM 추론에 적합한 GPU가 없었기 때문에, Google Kubernetes Engine(GKE) 환경으로 전환하여 L4 GPU 노드를 할당받으려 했습니다. 그러나 두 가지 문제가 동시에 발생했습니다:

1. **GPU 쿼터 부족**: Google Cloud의 GPU 할당량 정책에 의해 L4 GPU 노드를 원하는 리전에서 확보하기 어려웠고, 노드 할당이 불안정했습니다.
2. **고정 비용 폭증**: GKE는 노드가 항상 실행 상태를 유지하므로, 실제 요청이 없는 시간에도 GPU 인스턴스 비용이 발생했습니다. **3일 만에 약 10만 원**의 비용이 청구되었고, 월 기준으로는 100만 원 이상이 될 수 있는 구조였습니다.

**원인 분석**

- GKE의 GPU 노드풀은 Scale-to-Zero를 기본 지원하지 않으며, 노드가 존재하는 한 과금됨
- 개인 프로젝트 / 포트폴리오 용도로 상시 GPU를 유지하는 것은 비용 대비 효율이 극히 낮음
- GPU 쿼터 신청 및 승인 과정이 수일 이상 소요되어 개발 일정에도 영향

**해결 과정**

GKE를 포기하고 **Cloud Run GPU (Scale-to-Zero)** 아키텍처로 전환했습니다. Cloud Run은 요청이 없으면 인스턴스를 0으로 줄이고, 요청이 들어올 때만 GPU 인스턴스를 할당합니다. 이를 통해 **사용한 만큼만 과금**되는 구조를 만들었고, 비용을 90% 이상 절감할 수 있었습니다.

```bash
# infra/deploy-vllm-cloudrun.sh
gcloud run deploy vllm-server-v3 \
  --gpu=1 --gpu-type=nvidia-l4 \
  --cpu=8 --memory=32Gi \
  --min-instances=0 \         # Scale-to-Zero 핵심
  --timeout=3600 \
  --no-allow-unauthenticated
```

트레이드오프로 콜드 스타트(약 3~5분)가 발생하지만, 상시 운영이 아닌 포트폴리오/데모 목적에서는 수용 가능한 수준이었습니다.

---

#### Problem 3: 프론트엔드를 Cloud Run에서 Firebase Hosting으로 전환

**문제 상황**

초기에는 프론트엔드(Flutter Web 빌드 결과물)도 Cloud Run 위에 Nginx 컨테이너로 배포했습니다. 그러나 정적 파일 서빙에 컨테이너 인스턴스를 사용하는 것은 불필요한 비용과 콜드 스타트를 유발했습니다.

**해결 과정**

Flutter Web은 빌드 후 순수 정적 파일(HTML/JS/CSS)만 생성되므로, **Firebase Hosting**으로 전환했습니다. CDN 기반으로 글로벌 배포되어 응답 속도가 빨라졌고, Cloud Run 인스턴스 비용이 절감되었습니다. SPA 라우팅을 위한 rewrite 규칙만 추가하면 되었습니다.

```json
// firebase.json
{
  "hosting": {
    "public": "frontend/build/web",
    "rewrites": [{ "source": "**", "destination": "/index.html" }]
  }
}
```

---

#### Problem 4: Qdrant + Redis에서 Firestore로 전환

**문제 상황**

초기 아키텍처에서는 벡터 검색을 위해 Qdrant, 세션/캐싱을 위해 Redis를 별도로 운영했습니다. 이는 각각의 서버를 관리해야 하고, 서버리스 아키텍처와 맞지 않는 상시 운영 비용이 발생하는 구조였습니다.

**원인 분석**

- Qdrant와 Redis는 자체 서버 인스턴스가 필요하여 Scale-to-Zero가 불가능
- 서버리스로 전환한 취지(필요할 때만 비용 발생)와 모순
- 서비스가 늘어날수록 관리 포인트가 증가하고 서비스 간 네트워크 설정, 인증, 권한 문제가 복잡해짐

**해결 과정**

Firestore가 **Native Vector Search**(find_nearest)를 지원한다는 점을 활용하여, 벡터 스토어, 세션 스토어, 사용자 프로필 저장소를 **Firestore 하나로 통합**했습니다. 관리형 서비스이므로 서버 관리가 불필요하고, 사용량 기반 과금이며, 벡터 검색·문서 저장·세션 관리를 단일 서비스에서 처리할 수 있게 되었습니다.

```python
# backend/app/services/storage_service.py
results = collection.find_nearest(
    vector_field="embedding",
    query_vector=Vector(query_vector),
    distance_measure=DistanceMeasure.COSINE,
    limit=top_k,
)
```

---

### 4-2. 기술 스택 선정 이유 (Trade-off 분석)

#### LLM: Qwen2.5-7B-Instruct 선택

L4 GPU 1대(VRAM 24GB)라는 물리적 한계 안에서 모델을 선택해야 했습니다.

| 후보 | 탈락/선택 이유 |
|------|---------------|
| Gemma 4 | vLLM에서의 지원이 불안정하여 서빙 시 오류 빈발. 최신 모델일수록 서드파티 도구 호환성이 보장되지 않음을 경험 |
| Qwen2.5-3B | 가볍지만 한국어 페르소나 유지 품질이 부족 |
| **Qwen2.5-7B-Instruct** | vLLM 지원 안정적, 한국어 성능 우수, bfloat16으로 L4 24GB에 안정 탑재 가능 |

```bash
--model=Qwen/Qwen2.5-7B-Instruct \
--max-model-len=8192 \
--dtype=bfloat16 \
--gpu-memory-utilization=0.8
```

- **bfloat16**: FP16 대비 수치 안정성이 높고, L4 GPU에서 네이티브 지원
- **max-model-len=8192**: RAG 컨텍스트(~2K) + 대화 히스토리(~3K) + 응답(~2K)을 커버하는 최적값
- **gpu-memory-utilization=0.8**: OOM 방지를 위해 20% 여유 확보

#### 임베딩: BAAI/bge-m3

- 다국어(한국어+영어 혼합) SCP 문서에 적합
- 1024차원으로 검색 정밀도와 저장 효율의 균형
- Firestore Vector Search와 호환

---

### 4-3. 프롬프트 엔지니어링 전략

#### 프롬프트 구조 (Recency-Bias 최적화)

LLM은 프롬프트의 **처음과 끝에 위치한 내용**에 더 강하게 반응하는 경향이 있습니다. 이 특성을 활용하여 다음과 같은 순서로 프롬프트를 조립했습니다:

```
1. System Prompt ──────── 페르소나 말투/형식 규칙 (첫 번째 위치)
2. Few-shot Examples ──── 페르소나 목소리 앵커링 (user/assistant 쌍)
3. RAG Context Block ──── 검색된 SCP 문서 (중간 위치)
4. Conversation History ── 최근 10턴 슬라이딩 윈도우
5. Closing Directive ──── 페르소나 강제 리마인더 (마지막 위치)
```

처음(System Prompt)과 끝(Closing Directive) 모두에 페르소나 규칙을 배치하여, 중간의 RAG 컨텍스트가 길어져도 페르소나가 무너지지 않도록 했습니다.

#### 페르소나별 세밀한 파라미터 튜닝

각 페르소나의 성격에 맞게 생성 파라미터를 차별화했습니다:

| 페르소나 | temperature | top_p | frequency_penalty | 의도 |
|---------|------------|-------|-------------------|------|
| 연구원 | 0.35 | 0.9 | 0.2 | 정형화된 보고서 톤, 낮은 창의성 |
| 요원 | 0.55 | 0.92 | 0.4 | 간결한 전술 브리핑, 반복 억제 |
| SCP-079 | 0.7 | 0.92 | 0.5 | 기계적이지만 예측 불가능한 AI 톤 |

#### 환각(Hallucination) 제어: 다층 방어

1. **지식 소스 제한**: 시스템 프롬프트에는 말투 규칙만 포함하고, SCP 관련 사실은 100% RAG 검색 결과에 의존하도록 설계
2. **Closing Directive**: 프롬프트 마지막에 "제공된 자료에 없는 내용은 '[데이터 말소]'로 처리" 지시
3. **후처리 필터** (`response_filter.py`):
   - 한자(CJK Unified Ideographs), 일본어 히라가나/가타카나 자동 제거
   - 페르소나별 허용 영단어 화이트리스트 적용 (SCP, REDACTED, MTF 등만 허용)
   - SCP 식별자(SCP-173, MTF-Nu-7, D-9341 등) 보호
   - 마크다운 볼드(`**...**`) 제거 (Flutter에서 플레인 텍스트로 렌더링)

```python
# backend/app/services/response_filter.py
# 1단계: 한자/가나 제거
text = re.sub(r'[\u3400-\u9FFF]', '', text)       # CJK
text = re.sub(r'[\u3040-\u30FF]', '', text)       # 히라가나/가타카나

# 2단계: 페르소나별 영단어 화이트리스트
RESEARCHER_ALLOWED = {"SCP", "REDACTED", "DATA EXPUNGED", "Keter", "Euclid", ...}
```

---

### 4-4. 한계점 및 개선 방향

#### 콜드 스타트 지연

Scale-to-Zero 아키텍처의 트레이드오프로, vLLM GPU 인스턴스의 콜드 스타트에 약 3~5분이 소요됩니다. 첫 요청 시 사용자 경험이 저하되는 문제가 있습니다.

**개선 방안**: 자체 GPU 서버를 구축하거나, `min-instances=1`로 최소 1대를 상시 유지하는 전략으로 전환하면 비용은 증가하지만 콜드 스타트를 해소할 수 있습니다. 또는 Cloud Scheduler로 주기적 워밍업 요청을 보내는 방법도 고려할 수 있습니다.

---

## 5. Conclusion

### 프로젝트 회고 (Lessons Learned)

**클라우드 인프라 비용의 현실**

클라우드에 GPU 서비스를 고정으로 띄우는 것이 3일 만에 10만 원이 나갈 정도로 엄청난 비용을 수반한다는 것을 체감했습니다. GKE에서 Cloud Run Scale-to-Zero로 전환하는 과정을 통해, 아키텍처 설계 단계에서 비용 구조를 반드시 고려해야 한다는 것을 배웠습니다.

**GPU 자원 할당의 제약**

Google Cloud Platform의 GPU 할당량은 Google 방침에 의해 제약을 받아 자유롭게 할당받을 수 없는 경우가 있습니다. 리전별 가용성, 쿼터 승인 대기 등 물리적·정책적 제약이 개발 일정에 영향을 줄 수 있으므로, 사전에 대안을 준비해두어야 합니다.

**단일 GPU에서의 모델 공존 문제**

하나의 GPU 서버에 임베딩 모델과 LLM을 동시에 탑재하는 전략은 OOM을 유발하는 위험이 있음을 배웠습니다. vLLM처럼 가용 VRAM을 최대한 활용하는 서빙 프레임워크에서는 특히 GPU 메모리를 단일 모델에 독점시키는 것이 안정적입니다.

**최신 모델의 서드파티 호환성 문제**

Gemma 4와 같은 최신 모델은 vLLM 등의 서드파티 서빙 프레임워크에서 충분히 검증되지 않아 서비스에 지장을 줄 수 있음을 배웠습니다. 안정성이 중요한 프로덕션 환경에서는 커뮤니티에서 충분히 검증된 모델을 선택하는 것이 중요합니다.

**한국어 모델 성능의 편차**

벤치마크 상 비슷한 성능의 모델이라도 한국어 생성 품질에는 큰 차이가 날 수 있음을 경험했습니다. 특히 페르소나 말투 유지, 존댓말/반말 구분 등 한국어 특유의 요구사항에서 모델 간 격차가 두드러졌습니다.

**로컬 테스팅 환경의 중요성**

클라우드 환경 배포에는 빌드·푸시·프로비저닝까지 상당한 시간이 소요되므로, 로컬에서 테스팅할 수 있는 환경을 갖추는 것이 개발 속도 향상에 큰 도움이 됩니다. 배포 한 번에 수십 분이 걸리는 GPU 서비스의 경우 특히 그렇습니다.

**GCP 서비스 간 권한 문제**

Cloud Run, Firestore, Firebase Hosting, Google OAuth 2.0 등 여러 서비스를 연동할 때, 서비스 간 IAM 권한 설정에서 많은 오류가 발생했습니다. 서비스 계정 권한, API 활성화, OAuth 동의 화면 구성 등 사람이 직접 통제해야 하는 부분에 예상보다 많은 시간이 소요됩니다.

**Google Cloud Platform과 Firebase에 대한 이해도 향상**

프로젝트 전반을 통해 GCP와 Firebase 생태계에 대한 실무적 이해도가 크게 높아졌습니다. Cloud Run 배포, Firestore 벡터 검색, Firebase Hosting, IAM 권한 관리, OAuth 2.0 연동 등 서버리스 풀스택 아키텍처를 설계하고 운영하는 역량을 갖추게 되었습니다.

---

### 향후 발전 계획 (Future Works)

| 항목 | 설명 |
|------|------|
| 콜드 스타트 해결 | Cloud Scheduler 워밍업 또는 min-instances=1 전략 적용 |
| 다양한 로그인 방법 추가 | Apple, GitHub, 이메일/패스워드 등 Firebase Auth 연동 확대 |
| 커스텀 페르소나 구현 | 사용자가 직접 페르소나 성격·말투·전문 분야를 정의할 수 있는 기능 |
| 챗봇 이외의 콘텐츠 | SCP 도감, 격리 시뮬레이션, 퀴즈 등 세계관 탐구 콘텐츠 확장 |
