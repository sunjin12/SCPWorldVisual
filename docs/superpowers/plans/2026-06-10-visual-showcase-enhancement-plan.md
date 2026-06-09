# Visual Showcase Enhancement (Background + Character) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 로컬의 배경 이미지 자원과 캐릭터 스탠딩 스프라이트를 합성하여 고품질 페르소나 프리뷰 이미지 3종을 생성하고, 이를 적용하여 README.md의 비주얼 쇼케이스 갤러리 구성을 대폭 개편합니다.

**Architecture:** `generate_image` 도구를 활용해 이미지 자원을 합성하여 `docs/images/screens/`에 적재하고, README.md에 비주얼 그리드 테이블 구조를 개편 적용한 후 원격 저장소에 업로드합니다.

**Tech Stack:** Git, Python, Markdown, AI Image Generation

---

### Task 1: 페르소나 프리뷰 이미지 합성 및 생성

**Files:**
- Create: `d:/vscodeprojects/SCPWorldVisual/docs/images/screens/researcher_preview.png`
- Create: `d:/vscodeprojects/SCPWorldVisual/docs/images/screens/agent_preview.png`
- Create: `d:/vscodeprojects/SCPWorldVisual/docs/images/screens/scp079_preview.png`

- [ ] **Step 1: 연구원 프리뷰 이미지 생성**
  - 배경: `d:/vscodeprojects/SCPWorldVisual/frontend/assets/images/backgrounds/research_lab.png`
  - 캐릭터: `d:/vscodeprojects/SCPWorldVisual/frontend/assets/images/characters/researcher/researcher_standing.png`
  - 합성 작업: AI 생성 도구를 활용하여 실험실 배경에 캐릭터를 보기 좋게 오버레이합니다.
  - 저장 경로: `d:/vscodeprojects/SCPWorldVisual/docs/images/screens/researcher_preview.png`

- [ ] **Step 2: 요원 프리뷰 이미지 생성**
  - 배경: `d:/vscodeprojects/SCPWorldVisual/frontend/assets/images/backgrounds/tactical_bunker.png`
  - 캐릭터: `d:/vscodeprojects/SCPWorldVisual/frontend/assets/images/characters/agent/agent_standing.png`
  - 합성 작업: 어두운 전술 벙커 배경 중앙에 특수 부대 요원 스프라이트를 오버레이합니다.
  - 저장 경로: `d:/vscodeprojects/SCPWorldVisual/docs/images/screens/agent_preview.png`

- [ ] **Step 3: SCP-079 프리뷰 이미지 생성**
  - 배경: `d:/vscodeprojects/SCPWorldVisual/frontend/assets/images/backgrounds/server_chamber.png`
  - 캐릭터: `d:/vscodeprojects/SCPWorldVisual/frontend/assets/images/characters/scp079/scp-079_standing.png`
  - 합성 작업: 서버실 배경에 CRT 모니터 캐릭터를 어색하지 않게 투영시킵니다.
  - 저장 경로: `d:/vscodeprojects/SCPWorldVisual/docs/images/screens/scp079_preview.png`

---

### Task 2: README.md 비주얼 쇼케이스 레이아웃 업데이트

**Files:**
- Modify: `d:/vscodeprojects/SCPWorldVisual/README.md`

- [ ] **Step 1: README.md의 '📸 Visual Showcase' 섹션 수정**
  - 아래 마크다운 템플릿에 맞추어 `README.md` 파일의 로그인 이미지 및 대화 갤러리 구조를 업데이트합니다. 새로 생성한 프리뷰 이미지 3종을 중간 행에 갤러리 테이블로 추가 삽입합니다.
  
  ```markdown
  ## 📸 Visual Showcase

  ### 🔐 로컬 오퍼레이터 로그인 & 캐릭터 선택
  | 🔐 로컬 오퍼레이터 로그인 | 👥 캐릭터 선택 화면 |
  | :---: | :---: |
  | ![로그인화면](docs/images/screens/로그인화면.PNG) | ![연구원선택](docs/images/screens/연구원선택.PNG) |

  ### 👥 페르소나 비주얼 프로필 (배경 + 캐릭터)
  | 🧪 연구원 프로필 | 🕵️ 에이전트 프로필 | 🤖 SCP-079 프로필 |
  | :---: | :---: | :---: |
  | ![연구원프로필](docs/images/screens/researcher_preview.png) | ![에이전트프로필](docs/images/screens/agent_preview.png) | ![SCP-079프로필](docs/images/screens/scp079_preview.png) |

  ### 💬 실시간 대화 세션 (실행 화면)
  | 🧪 연구원 대화 | 🕵️ 에이전트 대화 | 🤖 SCP-079 대화 |
  | :---: | :---: | :---: |
  | ![연구원대화](docs/images/screens/연구원대화.PNG) | ![에이전트대화](docs/images/screens/에이전트대화.PNG) | ![SCP-079대화](docs/images/screens/SCP-079대화.PNG) |
  ```

---

### Task 3: 최종 검증 및 깃 푸시

**Files:**
- Modify: Git configuration & Remote Repository

- [ ] **Step 1: 생성된 파일 무결성 점검 및 커밋**
  - 새로 생성된 이미지 3종(`researcher_preview.png`, `agent_preview.png`, `scp079_preview.png`)과 수정된 `README.md`, `.gitignore` 상태를 확인하고 한꺼번에 커밋합니다.
  - 실행:
  ```bash
  git add docs/images/screens/*_preview.png README.md
  git commit -m "docs: add background+character preview images and update README.md showcase gallery"
  ```

- [ ] **Step 2: GitHub 원격 저장소 푸시**
  - 실행:
  ```bash
  git push origin main
  ```
  - Expected: 생성된 이미지와 변경된 리드미가 깃허브 상에 정상 반영됩니다.
