# lunch_recommend_agent

## 프로젝트 소개

음성 입력(STT) -> LLM 응답 생성 -> 음성 출력(TTS) 흐름으로 동작하는 점심 메뉴 추천 에이전트입니다.  
CLI 실행과 Streamlit 대시보드 실행을 모두 지원합니다.

## 폴더 구조

- `db/`: 가게 CSV/DB 데이터와 DB 관련 코드
- `llm/`: LLM, STT, TTS, CLI 실행 코드
- `streamlit_ui/`: Streamlit 화면 코드
- `llm_main.py`: CLI 실행용 진입 파일
- `streamlit_app.py`: Streamlit 실행용 진입 파일

## 개발 환경 설정

`uv`로 가상환경을 만들고 필요한 라이브러리를 설치합니다.

```bash
uv venv
uv add openai python-dotenv gTTS sounddevice scipy streamlit
```

## API 키 설정

프로젝트 루트에 `.env` 파일을 두고 아래처럼 작성하면 됩니다.

```env
OPENAI_API_KEY=your_key_here
```

또는 환경 변수로 직접 설정해도 됩니다.

```bash
set OPENAI_API_KEY=your_key_here
```

## 실행 방법

### 1. 마이크 입력으로 실행

```bash
uv run python llm_main.py
```

### 2. 텍스트로 바로 실행

```bash
uv run python llm_main.py --text "점심 메뉴 추천해줘"
```

### 3. Streamlit 대시보드 실행

```bash
uv run streamlit run streamlit_app.py
```

## 주요 기능

- STT -> LLM -> TTS 전체 흐름 지원
- 점심 메뉴 추천 결과를 TTS로 자동 재생
- TTS on/off 토글 지원
- 대화 리셋 버튼 지원
- CSV에 있는 가게만 추천하도록 제한
- Streamlit 채팅 UI + 메뉴 대시보드 지원

## CSV 데이터 위치

기본 CSV 파일 경로는 아래입니다.

```text
db/restaurants.csv
```

다른 CSV 파일을 쓰고 싶으면 CLI 실행 시 `--menu-csv` 옵션으로 경로를 넘기면 됩니다.

```bash
uv run python llm_main.py --menu-csv your_file.csv
```

## 참고

- TTS는 `gTTS`를 사용하므로 인터넷 연결이 필요합니다.
- TTS 재생용 텍스트에서는 `[ ]`, `*`, `/` 같은 문자를 제거합니다.
