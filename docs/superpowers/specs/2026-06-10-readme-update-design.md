# Design Spec: README.md Update (Visual-First & Local Migration)

**Date**: 2026-06-10  
**Topic**: README.md Update to Reflect Local Migration & Visual Enhancements  

---

## 1. Goal & Context
최근 SCP World 프로젝트는 Firebase/Cloud Run 등의 기존 클라우드 인프라에서 로컬 환경(SQLite + NumPy 로컬 벡터 검색 + Ollama LLM + 로컬 인증)으로 성공적으로 마이그레이션되었으며, 프론트엔드의 비주얼(스플릿 스크린, VisualMonitor, 스프라이트 동작 애니메이션)이 크게 강화되었습니다.

본 설계의 목표는 이러한 변화에 맞춰 프로젝트의 깃허브 메인 문서인 `README.md`를 **이미지 중심**으로 매력적이고 직관적으로 개편하는 것입니다. 방문자가 프로젝트의 목적과 비주얼을 바로 이해할 수 있도록 구성하며, 기능 및 기술 명세는 최소화하고 실행 가이드는 접이식 메뉴로 숨깁니다.

---

## 2. README.md Layout Design

### **[Section 1] Header & Main Visual**
*   **타이틀**: `SCP World Visual`
*   **소개**: "SCP 재단 위키 데이터를 기반으로 한 로컬 RAG 인터랙티브 페르소나 챗봇"
*   **대표 이미지**: `docs/images/screens/로그인화면.PNG`를 헤더 바로 아래 중앙에 배치하여 오퍼레이터 인증 UI의 독특한 비주얼을 강조.

### **[Section 2] UI & Visual Showcase (Gallery)**
방문자가 실제 UI를 즉시 볼 수 있도록 마크다운 표를 사용해 갤러리를 형성합니다.

| 🔐 로컬 오퍼레이터 로그인 | 👥 페르소나 선택 |
| :---: | :---: |
| ![로그인화면](docs/images/screens/로그인화면.PNG) | ![연구원선택](docs/images/screens/연구원선택.PNG) |

| 🧪 연구원 대화 세션 | 🕵️ 에이전트 대화 세션 | 🤖 SCP-079 대화 세션 |
| :---: | :---: | :---: |
| ![연구원대화](docs/images/screens/연구원대화.PNG) | ![에이전트대화](docs/images/screens/에이전트대화.PNG) | ![SCP-079대화](docs/images/screens/SCP-079대화.PNG) |

### **[Section 3] Key Features (간단 요약)**
각 기능을 간결한 카드 스타일(아이콘 + 한 줄 설명)로 배치합니다.
*   **Local RAG Engine**: SQLite 및 NumPy 벡터 검색을 이용한 100% 오프라인 정보 검색.
*   **Persona Dialogue**: 3인의 재단 페르소나(연구원, 에이전트, SCP-079)별 고유한 대화 톤 및 실시간 Stream 답변.
*   **Visual Monitor & Sprites**: 반응형 스플릿 스크린 UI와 대화 진행에 따라 동적으로 반응하는 캐릭터 스프라이트 애니메이션.
*   **Operator Authentication**: Local ID 기반의 안전한 세션 인증 및 암호화 보관.

### **[Section 4] Quick Start (로컬 실행 가이드 - Foldable)**
`<details>` 태그를 활용하여 개발자용 설치 가이드를 정리합니다.
*   **Prerequisites**: Ollama 설치 및 임베딩/LLM 모델 다운로드 안내.
*   **Data Pipeline**: SCP 위키 데이터 수집 및 로컬 SQLite DB 구축 스크립트 실행법.
*   **Backend & Frontend Run**: `fastapi dev` 및 `flutter run` 실행 명령어.

---

## 3. Verification Plan
*   **Visual Check**: VS Code 마크다운 렌더링 기능을 활용하여 이미지 경로 및 갤러리 레이아웃이 정상적으로 표현되는지 검증합니다.
*   **Link Check**: 마크다운 파일 내의 상대 경로(이미지 경로 등)가 정확히 맞는지 확인합니다.
