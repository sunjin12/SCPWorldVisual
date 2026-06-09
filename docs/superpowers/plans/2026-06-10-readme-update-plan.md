# README.md Visual & Local Migration Update Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 로컬 마이그레이션 및 비주얼 기능 강화가 완료된 SCP World 프로젝트의 깃허브 README.md 파일을 이미지 중심으로 개편하여 프로젝트의 매력도와 명확성을 향상시킵니다.

**Architecture:** 기존 클라우드 기반 아키텍처 정보를 완전히 제거하고, 갤러리 형태로 주요 스크린샷들을 격자 배치하며, 상세한 로컬 실행 방법은 접이식(Foldable Details) 메뉴로 제공합니다.

**Tech Stack:** Markdown, Git

---

### Task 1: 백업 및 기존 내용 제거

**Files:**
- Modify: `d:/vscodeprojects/SCPWorldVisual/README.md`

- [ ] **Step 1: 기존 README.md 내용을 백업 및 클리어**
  - 기존 `d:/vscodeprojects/SCPWorldVisual/README.md` 파일의 기존 내용을 안전하게 백업(메모리 또는 스크래치 파일에 기록)하고, 파일 내용을 새로 작성하기 위해 준비합니다.
  - 실행: 기존 내용을 완전히 지우고 아래의 기본 뼈대를 작성합니다.
  
  ```markdown
  # SCP World Visual

  SCP Foundation 위키 콘텐츠를 기반으로 한 로컬 RAG 인터랙티브 페르소나 챗봇 데모.
  본 프로젝트는 서버리스 환경에서 **100% 로컬 환경(SQLite + NumPy 로컬 벡터 검색 + Ollama LLM + 로컬 인증)**으로 마이그레이션되었으며, 프론트엔드의 비주얼과 애니메이션이 대폭 강화되었습니다.
  ```

- [ ] **Step 2: 로컬 상태 확인 및 뼈대 커밋**
  - 실행: `git diff d:/vscodeprojects/SCPWorldVisual/README.md`
  - Expected: 이전 내용이 삭제되고 새로운 소개글이 들어갔는지 확인합니다.
  - 커밋 실행:
  ```bash
  git add d:/vscodeprojects/SCPWorldVisual/README.md
  git commit -m "docs: clean up and write initial shell for README.md"
  ```

---

### Task 2: 비주얼 쇼케이스 갤러리 및 핵심 기능 작성

**Files:**
- Modify: `d:/vscodeprojects/SCPWorldVisual/README.md`

- [ ] **Step 1: 메인 헤더 아래 대표 이미지 및 갤러리 마크다운 작성**
  - `README.md`에 로그인 화면 및 캐릭터별 대화 화면 갤러리를 작성합니다. 플레이스홀더 없이 실제 경로를 매핑합니다.
  
  ```markdown
  ---

  ## 📸 Visual Showcase

  ### 🔐 로컬 오퍼레이터 로그인
  ![로그인화면](docs/images/screens/로그인화면.PNG)

  ### 👥 페르소나 선택 및 대화 세션
  | 🧪 연구원 선택 및 대화 | 🕵️ 에이전트 선택 및 대화 | 🤖 SCP-079 선택 및 대화 |
  | :---: | :---: | :---: |
  | ![연구원선택](docs/images/screens/연구원선택.PNG) | ![에이전트선택](docs/images/screens/에이전트선택.PNG) | ![SCP-079선택](docs/images/screens/SCP-079선택.PNG) |
  | ![연구원대화](docs/images/screens/연구원대화.PNG) | ![에이전트대화](docs/images/screens/에이전트대화.PNG) | ![SCP-079대화](docs/images/screens/SCP-079대화.PNG) |

  ---
  ```

- [ ] **Step 2: 간단한 핵심 기능 설명 섹션 작성**
  - 아래의 기능 요약 텍스트를 마크다운 파일에 추가합니다.
  
  ```markdown
  ## ✨ Key Features (핵심 기능)

  *   **Local RAG Engine**: SQLite 및 NumPy 벡터 검색을 활용하여 네트워크 연결 없이도 SCP 위키 문서를 검색하고 답변의 정확한 출처(SCP 번호 및 원문 URL)를 제시합니다.
  *   **Persona Dialogue & Stream**: 3인의 재단 페르소나(연구원 Dr. [REDACTED], 요원 Agent [REDACTED], SCP-079 Old AI)별 독창적인 대화 페르소나를 구현하였으며, SSE 스트리밍 답변을 제공합니다.
  *   **Visual Monitor & Dynamic Sprites**: 반응형 스플릿 스크린 UI 구조를 채택하여 실시간 상태 로그를 모니터링할 수 있으며, 대화 진행에 따라 동적으로 반응하는 캐릭터 스프라이트 애니메이션이 탑재되어 있습니다.
  *   **Operator Authentication**: 로컬 Operator ID 기반의 안전한 세션 인증 방식을 적용하였습니다.
  *   **Hanja-to-Hangul Translation**: 데이터 파이프라인에서 한자가 섞인 문서를 한글로 자동 변역 및 정제하여 임베딩 및 답변의 가독성을 최적화했습니다.
  ```

- [ ] **Step 3: 변경사항 저장 및 커밋**
  - 커밋 실행:
  ```bash
  git add d:/vscodeprojects/SCPWorldVisual/README.md
  git commit -m "docs: add visual showcase and key features to README.md"
  ```

---

### Task 3: 퀵스타트(Foldable) 및 라이선스 안내 작성

**Files:**
- Modify: `d:/vscodeprojects/SCPWorldVisual/README.md`

- [ ] **Step 1: 접이식 실행 가이드(Quick Start) 작성**
  - `<details>`와 `<summary>` 태그를 활용해 접어둘 수 있는 로컬 구동 가이드를 작성합니다.
  
  ```markdown
  ---

  ## 🚀 Quick Start (로컬 실행 가이드)

  <details>
  <summary>💻 Local Development Setup (클릭하여 펼치기)</summary>

  ### 1. Prerequisites (사전 준비)
  *   **Ollama**: 로컬 LLM 서빙을 위해 [Ollama](https://ollama.com/)를 설치합니다.
  *   **Models**: 대화용 LLM과 임베딩 모델을 다운로드합니다.
      ```bash
      ollama pull qwen2.5:7b-instruct
      # 임베딩용 bge-m3 등 로컬 GPU 가속 환경 구성
      ```

  ### 2. Data Pipeline (데이터 파이프라인)
  SCP 위키 문서를 스크래핑하고 임베딩하여 로컬 SQLite DB로 구축합니다.
  ```bash
  cd data-pipeline
  # 의존성 설치 (uv 사용)
  uv sync
  # 데이터 스크래핑 및 전처리(한자 번역 포함)
  uv run scripts/scrape_scp.py
  uv run scripts/preprocess.py
  # 로컬 SQLite DB 구축 및 임베딩 적재
  uv run scripts/upload_to_sqlite.py
  ```

  ### 3. Backend Run (백엔드 실행)
  ```bash
  cd backend
  uv sync
  # .env 설정 (.env.example 참고)
  # 백엔드 서버 구동
  uv run fastapi dev app/main.py
  ```

  ### 4. Frontend Run (프론트엔드 실행)
  ```bash
  cd frontend
  flutter pub get
  # Flutter Web 실행
  flutter run -d chrome
  ```

  </details>
  ```

- [ ] **Step 2: 라이선스 및 크레딧 정보 작성**
  - 아래의 라이선스 정보를 추가하여 최종 파일을 완성합니다.
  
  ```markdown
  ---

  ## 📄 License & Credits

  *   **Source Code**: 본 저장소의 모든 소스 코드는 [MIT License](LICENSE)를 따릅니다.
  *   **SCP Foundation Content**: RAG 데이터셋에 포함된 모든 SCP 위키 텍스트는 [Creative Commons Attribution-ShareAlike 3.0 (CC-BY-SA 3.0)](https://creativecommons.org/licenses/by-sa/3.0/) 라이선스를 준수하며, 출처는 [SCP Foundation Wiki](https://scp-wiki.wikidot.com/)에 있습니다.
  *   **Credits**: 본 프로젝트는 개발 생산성 극대화를 위해 Gemini / Claude Code 등의 AI 에이전트 도구를 적극 활용하여 구축되었습니다.
  ```

- [ ] **Step 3: 변경사항 저장 및 커밋**
  - 커밋 실행:
  ```bash
  git add d:/vscodeprojects/SCPWorldVisual/README.md
  git commit -m "docs: add foldable setup guide and license info to README.md"
  ```

---

### Task 4: 최종 검증 및 테스트

**Files:**
- Modify: `d:/vscodeprojects/SCPWorldVisual/README.md`

- [ ] **Step 1: 마크다운 파일 무결성 검증**
  - 작성된 마크다운 내의 로컬 이미지 경로 (`docs/images/screens/...`) 파일들이 실제로 존재하는지 한 번 더 확인합니다.
  - 실행: `git status`를 확인하여 누락되거나 스테이징되지 않은 사항이 없는지 확인합니다.

- [ ] **Step 2: 최종 풀 푸시 및 병합 준비**
  - 깃 브랜치의 커밋 로그를 확인하여 모든 변경이 깔끔하게 커밋되었는지 검증합니다.
  - 실행: `git log -n 3`
