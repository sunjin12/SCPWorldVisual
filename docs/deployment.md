# Deployment

전체 시스템은 Cloud Run + Firebase Hosting + Firestore로 구성됩니다.

## 사전 조건

```bash
# Google Cloud SDK 인증
gcloud auth login
gcloud config set project scpworld
gcloud auth application-default login

# Firebase CLI
npm install -g firebase-tools
firebase login
firebase use scpworld
```

## 1. vLLM (LLM 서비스, GPU)

```bash
bash infra/deploy-vllm-cloudrun.sh
```

- 기존 서비스 삭제 → 120초 대기 → L4 GPU 할당량 확보 → 새로 배포
- 서비스명: `vllm-server-v3`, 리전: `asia-southeast1`
- 모델: Qwen2.5-7B-Instruct, scale-to-zero 유지
- PowerShell: `infra/deploy-vllm-cloudrun.ps1`

## 2. 백엔드 (FastAPI)

```bash
bash infra/deploy-backend-cloudrun.sh
```

- `--source backend/` 로 Buildpacks가 backend/Dockerfile 을 사용해 이미지 빌드
- 환경변수는 스크립트에 하드코딩 (공개값만 — GCP 프로젝트 ID, OAuth Client ID, vLLM URL)
- 민감값(서비스 계정 키, HF 토큰 등)은 저장소에 포함하지 않음. 필요 시 `--update-secrets` 또는 Cloud Run 콘솔에서 시크릿 매니저 연동으로 주입.
- 서비스명: `scp-backend`, 리전: `asia-southeast1`
- PowerShell: `infra/deploy-backend-cloudrun.ps1`

배포 후 smoke:
```bash
curl -s https://scp-backend-1087559947666.asia-southeast1.run.app/health
```

### 백엔드 IAM 요구사항

Compute service account (`<PROJECT_NUM>-compute@developer.gserviceaccount.com`)에 다음 권한 필요:
- `roles/datastore.user` — Firestore 읽기/쓰기
- `roles/run.invoker` (vLLM 서비스에 대해) — vLLM 호출용 ID Token 발급

Cloud Run 환경에서는 메타데이터 서버가 자동으로 ID Token을 발급하므로 키 파일이 필요 없습니다.
로컬 개발에서 동일 vLLM을 호출하려면 `gcloud auth application-default login`으로는 부족하고 (`fetch_id_token`이
서비스 계정 자격 증명을 요구), 서비스 계정 impersonation 또는 vLLM을 `--allow-unauthenticated`로
일시 전환하는 방법을 사용합니다. 자세한 내용은 해당 이슈 트래킹을 참조하세요.

## 3. 프론트엔드 (Flutter Web)

```bash
cd frontend
flutter build web --release \
  --dart-define=API_BASE_URL=https://scp-backend-1087559947666.asia-southeast1.run.app \
  --dart-define=GOOGLE_CLIENT_ID=1087559947666-uuelrdfelo0c76nm837e4v9epv5er3sa.apps.googleusercontent.com
firebase deploy --only hosting
```

- 산출물: `frontend/build/web/`
- Firebase Hosting 설정: [firebase.json](../firebase.json)

## 4. Firestore 보안 규칙

```bash
firebase deploy --only firestore:rules
```

- 정책: deny-all (클라이언트 직접 접근 차단). 백엔드는 Admin SDK로 우회.
- 파일: [firestore.rules](../firestore.rules)

## 5. Firestore 벡터 인덱스

`scp_documents` 컬렉션의 `embedding` 필드(1024-d)에 벡터 인덱스 필요:

```bash
gcloud firestore indexes composite create \
  --project=scpworld \
  --collection-group=scp_documents \
  --query-scope=COLLECTION \
  --field-config=vector-config='{"dimension":"1024","flat":{}}',field-path=embedding
```

상태 확인:
```bash
gcloud firestore indexes composite list --project=scpworld
# 또는
cd data-pipeline && uv run python scripts/validate_firestore.py
```

## 6. 데이터 파이프라인 (1회성)

```bash
cd data-pipeline
uv sync
uv run python scripts/scrape_scp.py        # SCP Wiki 크롤 (rate limit 2초)
uv run python scripts/preprocess.py        # 정제 + 512토큰 청킹
uv run python scripts/upload_to_firestore.py  # BGE-M3 임베딩 + Firestore 업로드
uv run python scripts/validate_firestore.py   # 카운트 + find_nearest 테스트
```

또는 Docker로:
```bash
cd data-pipeline
docker build -t scp-pipeline .
docker run --rm \
  -v ~/.config/gcloud:/root/.config/gcloud:ro \
  scp-pipeline   # CMD 기본값: upload_to_firestore.py
```

## 환경별 주의사항

- **vLLM 첫 요청**: 콜드 스타트 3~5분 (L4 GPU + 7B 모델 로드). UI에 안내 문구 표시됨.
- **vLLM URL 변경 시**: `infra/deploy-backend-cloudrun.sh` 의 `VLLM_LLM_URL` 갱신 후 백엔드 재배포.
- **OAuth 클라이언트 ID 변경 시**: 백엔드 스크립트 + `frontend/web/index.html` + `frontend/lib/config/constants.dart` 의 default value 모두 갱신.
