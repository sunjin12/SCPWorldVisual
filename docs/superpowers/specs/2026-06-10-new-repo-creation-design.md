# Design Spec: New Repository Creation (SCPWorldVisual)

**Date**: 2026-06-10  
**Topic**: Initialize New Git Repo and Upload to GitHub via gh CLI  

---

## 1. Goal
기존 `SCPWorld` Git 레포지토리의 이력을 끊고, 현재의 로컬 상태(마이그레이션 및 비주얼 개선이 반영된 최신 소스 코드)를 최초 커밋(Initial Commit)으로 하는 새로운 `SCPWorldVisual` 깃허브 저장소를 생성하여 업로드합니다.

---

## 2. Technical Approach & Workflow

### **[Phase 1] Git History Isolation**
*   로컬 디렉토리 `d:/vscodeprojects/SCPWorldVisual/.git` 폴더명을 `.git_old`로 리네임하여 백업 및 격리합니다.

### **[Phase 2] Git Re-initialization**
*   `git init` 수행.
*   기본 브랜치를 `main`으로 지정: `git branch -m main`
*   모든 파일 스테이징: `git add .`  
    *   이때 `.gitignore`에 지정된 캐시 폴더(`.hf_cache`), 로컬 DB(`*.db`), 가상 환경(`.venv`) 등은 자동 제외됩니다.
*   최초 커밋 생성: `git commit -m "feat: Initial commit for SCPWorldVisual"`

### **[Phase 3] Create GitHub Repository & Push**
*   Github CLI (`gh`) 명령어를 활용하여 원격 저장소를 생성하고 소스를 업로드합니다.
*   명령어: `gh repo create SCPWorldVisual --public --source=. --remote=origin --push`
*   생성되는 저장소: `https://github.com/sunjin12/SCPWorldVisual`

---

## 3. Verification Plan
*   **Git Status Check**: `git status`를 조회하여 `.gitignore` 규칙이 정상 작동하여 보안이 필요한 로컬 파일들이 스테이징에서 잘 빠졌는지 확인합니다.
*   **Remote Verification**: 깃허브 원격 저장소가 올바르게 생성되었는지 `gh repo view sunjin12/SCPWorldVisual` 또는 브라우저 링크로 최종 조회가 가능한지 검증합니다.
