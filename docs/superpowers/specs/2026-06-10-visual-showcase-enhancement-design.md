# Design Spec: Visual Showcase Enhancement (Background + Character Persona Visuals)

**Date**: 2026-06-10  
**Topic**: Generate Combined Background+Character Images & Update README.md Visual Showcase  

---

## 1. Goal
프로젝트의 깃허브 README.md 문서 내 'Visual Showcase' 섹션을 강화합니다. 페르소나별 배경과 캐릭터가 자연스럽게 합성된 일러스트 프리뷰 이미지 3종을 새로 제작하여 수록하고, 실제 구동 화면과 캐릭터 콘셉트를 직관적으로 비교할 수 있게 마크다운 레이아웃을 개편합니다.

---

## 2. Technical Approach & Design Details

### **[Step 1] Generate Combined Images via AI**
`generate_image` 툴을 사용해 캐릭터 이미지와 배경 이미지를 병합한 새로운 고화질 프리뷰 이미지를 `docs/images/screens/` 폴더에 생성합니다.

1.  **연구원 프리뷰 (`researcher_preview.png`)**
    *   배경: `frontend/assets/images/backgrounds/research_lab.png`
    *   캐릭터: `frontend/assets/images/characters/researcher/researcher_standing.png`
    *   컨셉: 비밀 과학 실험실 배경 중앙에 지적이고 연구원 다운 포즈의 캐릭터가 오버레이된 합성 이미지.
2.  **요원 프리뷰 (`agent_preview.png`)**
    *   배경: `frontend/assets/images/backgrounds/tactical_bunker.png`
    *   캐릭터: `frontend/assets/images/characters/agent/agent_standing.png`
    *   컨셉: 어두운 군사 전술 벙커 배경 중앙에 특수 부대 요원 포즈의 캐릭터가 오버레이된 합성 이미지.
3.  **SCP-079 프리뷰 (`scp079_preview.png`)**
    *   배경: `frontend/assets/images/backgrounds/server_chamber.png`
    *   캐릭터: `frontend/assets/images/characters/scp079/scp-079_standing.png`
    *   컨셉: 음산한 구형 서버실 배경 중앙에 낡은 CRT 모니터 캐릭터가 자연스럽게 배치된 합성 이미지.

### **[Step 2] README.md Showcase Layout Restructuring**
README.md의 `Visual Showcase` 섹션을 아래와 같이 3단계 그리드로 재배치합니다.

1.  **로그인 및 기본 화면**
    *   `🔐 로컬 오퍼레이터 로그인`
2.  **페르소나 비주얼 프로필 (신규 이미지 적용)**
    *   `👥 페르소나 비주얼 프로필 (배경 + 캐릭터 스프라이트)`
    *   | 🧪 연구원 프로필 | 🕵️ 에이전트 프로필 | 🤖 SCP-079 프로필 |
    *   | `researcher_preview.png` | `agent_preview.png` | `scp079_preview.png` |
3.  **실제 대화 구동 갤러리**
    *   | 🧪 연구원 대화 | 🕵️ 에이전트 대화 | 🤖 SCP-079 대화 |
    *   | `연구원대화.PNG` | `에이전트대화.PNG` | `SCP-079대화.PNG` |

---

## 3. Verification Plan
*   **Visual Layout Checking**: README.md의 상대 경로 이미지들이 마크다운 프리뷰 상에서 가로세로 비율 깨짐 없이 정렬되어 표시되는지 검증합니다.
*   **Push Verification**: 생성된 이미지 3종과 README.md 변경사항이 `sunjin12/SCPWorldVisual` 깃허브 저장소에 정상적으로 업로드 및 렌더링되는지 브라우저에서 최종 확인합니다.
