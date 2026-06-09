# New Repository Creation (SCPWorldVisual) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 로컬의 마이그레이션된 전체 프로젝트 상태를 최초 커밋으로 하는 새로운 `SCPWorldVisual` 깃허브 저장소를 생성하여 소스코드를 안전하게 업로드합니다.

**Architecture:** 기존 `.git` 폴더를 격리하고, `git init`을 새로 수행하여 꼬인 이력을 청소한 뒤, GitHub CLI를 통해 퍼블릭 원격 레포지토리를 만들고 푸시합니다.

**Tech Stack:** Git, GitHub CLI (gh)

---

### Task 1: 기존 Git 격리 및 백업

**Files:**
- Modify: `d:/vscodeprojects/SCPWorldVisual/.git` (이름 변경)

- [ ] **Step 1: 기존 .git 폴더 백업**
  - 프로젝트 루트 경로(`d:/vscodeprojects/SCPWorldVisual`) 내의 `.git` 디렉토리명을 `.git_old`로 리네임하여 격리합니다.
  - 실행: 파워쉘 또는 CMD 명령어로 수행합니다.
  ```powershell
  Rename-Item -Path "d:\vscodeprojects\SCPWorldVisual\.git" -NewName ".git_old"
  ```
  - Expected: `.git` 폴더가 더 이상 루트에 보이지 않고 `.git_old`로 변경되어야 합니다.

---

### Task 2: 로컬 Git 초기화 및 최초 커밋

**Files:**
- Create: `d:/vscodeprojects/SCPWorldVisual/.git` (새로 생성됨)

- [ ] **Step 1: 신규 git init 수행 및 main 브랜치 설정**
  - 실행: 
  ```bash
  git init
  git branch -m main
  ```
  - Expected: `Initialized empty Git repository...` 메시지가 뜨고 기본 브랜치가 `main`이 됩니다.

- [ ] **Step 2: 스테이징 전 배제 파일 교차 검증**
  - 실행: `git status`
  - Expected: `.gitignore`가 정상 작동하여 아래 파일들이 Untracked 상태로 표시되지 않아야 합니다. (만약 표시된다면 스테이징 전에 즉시 중단)
    *   `backend/.env`, `backend/scp_database.db`
    *   `.hf_cache/`
    *   `.venv/` (가상환경)

- [ ] **Step 3: 전체 파일 추가 및 최초 커밋 실행**
  - 실행:
  ```bash
  git add .
  git commit -m "feat: Initial commit for SCPWorldVisual"
  ```
  - Expected: 모든 필수 프로젝트 파일들이 성공적으로 최초 커밋으로 묶여 저장됩니다.

---

### Task 3: GitHub 저장소 생성 및 푸시

**Files:**
- Modify: Git Remote Config (`.git/config`)

- [ ] **Step 1: gh CLI를 통한 GitHub 원격 저장소 생성 및 푸시**
  - 실행:
  ```bash
  gh repo create SCPWorldVisual --public --source=. --remote=origin --push
  ```
  - Expected: 깃허브 상에 `sunjin12/SCPWorldVisual` 퍼블릭 저장소가 생성되고, 로컬의 `main` 브랜치가 자동으로 원격의 `main`으로 업로드됩니다.

- [ ] **Step 2: 원격 업로드 상태 검증**
  - 실행:
  ```bash
  gh repo view sunjin12/SCPWorldVisual
  ```
  - Expected: 생성된 레포지토리 정보와 리드미 파일이 터미널 화면에 정상 출력됩니다.
