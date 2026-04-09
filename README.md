# lunch_recommend_agent

## 프로젝트 소개

음성 입력(STT) -> LLM 응답 생성 -> 음성 출력(TTS) 흐름으로 동작하는 점심 메뉴 추천 에이전트입니다.

- CLI 실행 지원
- Streamlit 대시보드 지원
- CSV 기반 추천 지원
- 카카오 로컬 API 기반 위치 추천 지원

## 파일 구성

- `stt.py`: 마이크 녹음 및 음성 전사
- `tts.py`: TTS 생성 및 재생
- `llm.py`: 추천 프롬프트와 LLM 호출
- `menu_db.py`: CSV 가게 데이터 처리
- `kakao_api.py`: 카카오 로컬 API 호출
- `location_rag.py`: 위치 기반 추천 후보 컨텍스트 생성
- `llm_main.py`: CLI 진입점
- `streamlit_app.py`: Streamlit 진입점

## 설치

```bash
uv venv
uv add openai python-dotenv gTTS sounddevice scipy streamlit
```

## 환경 변수

프로젝트 루트의 `.env` 파일에 아래처럼 넣으면 됩니다.

```env
OPENAI_API_KEY=your_key_here
```

위치 기반 추천을 쓰려면 `.env`에 카카오 REST API 키를 추가합니다.

```env
KAKAO_REST_API_KEY=your_kakao_rest_api_key
```

## 실행

마이크 입력:

```bash
uv run python llm_main.py
```

텍스트 입력:

```bash
uv run python llm_main.py --text "점심 메뉴 추천해줘"
```

위치 기반 추천 예시:

```bash
uv run python llm_main.py --text "오늘 점심 메뉴 추천해주는데 울산 송정동 송정테라스에서 도보 5분거리로 추천해줘"
uv run python llm_main.py --text "내 위치 기반 반경 500m 안에 있는 가게 추천해줘" --latitude 35.645 --longitude 129.355
```

Streamlit 실행:

```bash
uv run streamlit run streamlit_app.py
```

## 데이터 파일

기본 CSV 파일은 아래 경로를 사용합니다.

```text
restaurants.csv
```

다른 파일을 쓰고 싶으면 `--menu-csv` 옵션으로 넘기면 됩니다.

## 참고

- TTS는 `gTTS`를 사용하므로 인터넷 연결이 필요합니다.
- 카카오 로컬 API는 한국 주소/장소 검색 정확도가 높아서 국내 위치 추천에 더 적합합니다.
