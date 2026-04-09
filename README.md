# lunch_recommend_agent

## 프로젝트 소개

이 저장소는 음성 입력(STT)을 받아 LLM으로 점심 메뉴 추천을 생성하고, 결과를 음성(TTS)으로 재생하는 에이전트입니다. CLI 실행과 Streamlit 기반 대시보드를 지원합니다.

## 중요 변경 — 데이터 소스

이 프로젝트는 이제 로컬 CSV/DB 대신 **Kakao Local API (지도 검색)** 를 기본 데이터 소스로 사용합니다. 즉, 저장된 CSV가 있더라도 추천은 실시간으로 Kakao 지도 검색 결과만 참고하도록 설계되어 있습니다. Kakao API 키(`KAKAO_REST_API_KEY`)를 `.env`에 설정해야 합니다.

## 폴더 구조 (요약)

- `llm/`: LLM, STT, TTS, CLI 실행 코드
- `streamlit_ui/`: Streamlit 화면 코드 (대시보드)
- `kakao_api.py`, `location_rag.py`: Kakao 지도/위치 관련 헬퍼
- `llm_main.py`: CLI 실행 진입점
- `streamlit_app.py`: Streamlit 실행 진입점 (프로젝트 루트 호환 wrapper)

## 개발 환경 설정

Python 3.11 이상에서 동작하며, 의존성은 `pyproject.toml`의 `dependencies`를 참고하세요. 간단 설치 예:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt  # 또는 pyproject.toml 기반 설치
```

필요한 주요 패키지: `openai`, `python-dotenv`, `streamlit`, `gtts`, `sounddevice`, `scipy`, `requests`.

## 환경 변수 설정

프로젝트 루트에 `.env` 파일을 만들고 다음 항목을 설정하세요:

```env
OPENAI_API_KEY=your_openai_key
KAKAO_REST_API_KEY=your_kakao_rest_api_key
```

Windows PowerShell에서 환경 변수 설정 예:

```powershell
setx OPENAI_API_KEY "your_openai_key"
setx KAKAO_REST_API_KEY "your_kakao_rest_api_key"
```

## 실행 방법

### 1) CLI (텍스트 입력)

```bash
python llm_main.py --text "송정테라스 근처 점심 추천해줘" --origin-query "울산 송정동" --radius-m 500
```

### 2) Streamlit 대시보드

```bash
streamlit run streamlit_app.py
```

대시보드에서 기준 위치와 반경을 입력하면 우측에 Kakao 기반 후보들이 지도와 카드로 표시됩니다.

## 동작 원칙

- 추천은 반드시 Kakao API로부터 받아온 후보 데이터를 기반으로 생성됩니다. (LLM이 임의로 가게명을 생성하지 않도록 제한)
- 현재 위치 기반 추천을 사용하려면 위도/경도를 제공하거나 브라우저에서 위치 권한을 허용해야 합니다.

## 문제 발생 시

- Kakao API 에러(401/403 등)가 발생하면 `.env` 설정과 Kakao Developers 설정(지도 API 활성화)을 확인하세요.
- Streamlit에서 지도가 표시되지 않으면 `pandas` 설치 여부를 확인해 주세요 (`pip install pandas`).

---

필요하시면 제가 `README.md`에 더 추가할 내용(예: 데모 스크린샷, 로컬 개발 팁 등)을 반영해 드릴게요.
