# SCP World Visual

SCP Foundation 위키 콘텐츠를 기반으로 한 페르소나 챗봇 데모

---

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

---

## ✨ Key Features (핵심 기능)

*   **Persona Dialogue & Stream**: 3인의 재단 페르소나(연구원 Dr. [REDACTED], 요원 Agent [REDACTED], SCP-079 Old AI)별 독창적인 대화 페르소나를 구현하였으며, SSE 스트리밍 답변을 제공합니다.
*   **Visual Monitor & Dynamic Sprites**: 반응형 스플릿 스크린 UI 구조를 채택하여 실시간 상태 로그를 모니터링할 수 있으며, 대화 진행에 따라 동적으로 반응하는 캐릭터 스프라이트 애니메이션이 탑재되어 있습니다.

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

---

## 📄 License & Credits

*   **Source Code**: 본 저장소의 모든 소스 코드는 [MIT License](LICENSE)를 따릅니다.
*   **SCP Foundation Content**: RAG 데이터셋에 포함된 모든 SCP 위키 텍스트는 [Creative Commons Attribution-ShareAlike 3.0 (CC-BY-SA 3.0)](https://creativecommons.org/licenses/by-sa/3.0/) 라이선스를 준수하며, 출처는 [SCP Foundation Wiki](https://scp-wiki.wikidot.com/)에 있습니다.
*   **Credits**: 본 프로젝트는 개발 생산성 극대화를 위해 Gemini / Claude Code 등의 AI 에이전트 도구를 적극 활용하여 구축되었습니다.
