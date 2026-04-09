"""Streamlit UI for the lunch recommendation agent."""

from __future__ import annotations

import base64
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from openai import APIConnectionError, OpenAI

from llm import extract_place_count, extract_search_keyword, generate_response, generate_response_with_places
from kakao_map import build_map_html, search_places
from db.menu_db import (
    DEFAULT_MENU_CSV,
    KOREAN_WEEKDAYS,
    build_menu_context_for_day,
    current_korean_weekday,
    filter_open_rows,
    load_menu_rows,
)
from llm.tts import synthesize_speech


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(255, 214, 165, 0.28), transparent 30%),
                radial-gradient(circle at top right, rgba(255, 183, 94, 0.22), transparent 24%),
                linear-gradient(180deg, #fffaf1 0%, #fffefb 38%, #f4efe6 100%);
            color: #1f2937;
        }
        .hero-card {
            border: 1px solid rgba(122, 92, 61, 0.18);
            border-radius: 24px;
            padding: 1.15rem 1.25rem;
            background: linear-gradient(135deg, rgba(255,255,255,0.88), rgba(255,248,236,0.95));
            box-shadow: 0 20px 50px rgba(80, 53, 20, 0.10);
            min-height: 220px;
            height: 220px;
        }
        .hero-kicker {
            letter-spacing: 0.08em;
            font-size: 0.75rem;
            color: #b45309;
            font-weight: 700;
            margin-bottom: 0.45rem;
        }
        .hero-title {
            font-size: 2rem;
            font-weight: 800;
            line-height: 1.05;
            margin: 0;
            color: #111827;
        }
        .hero-copy {
            margin-top: 0.6rem;
            color: #4b5563;
            font-size: 0.95rem;
            max-width: 48ch;
        }
        .section-title {
            font-size: 1.15rem;
            font-weight: 800;
            color: #111827;
            margin: 0;
        }
        .chat-block {
            margin-top: 1.2rem;
        }
        .restaurant-card {
            border: 1px solid rgba(17, 24, 39, 0.08);
            border-radius: 18px;
            padding: 1rem;
            background: rgba(255,255,255,0.85);
            box-shadow: 0 12px 30px rgba(17, 24, 39, 0.05);
            margin-bottom: 0.85rem;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            height: 160px;
        }
        .restaurant-thumb {
            width: 76px;
            height: 76px;
            border-radius: 18px;
            object-fit: cover;
            flex: 0 0 auto;
            box-shadow: 0 8px 16px rgba(17, 24, 39, 0.10);
        }
        .restaurant-name {
            font-size: 1.02rem;
            font-weight: 800;
            color: #111827;
            margin-bottom: 0.3rem;
        }
        .restaurant-meta {
            font-size: 0.92rem;
            color: #6b7280;
            line-height: 1.5;
        }
        .stat-grid {
            display: flex;
            gap: 1rem;
            margin: 0.75rem 0 1.25rem 0;
        }
        .stat-card {
            flex: 1;
            border-radius: 20px;
            padding: 1.1rem 1.3rem;
            background: linear-gradient(135deg, rgba(255,255,255,0.92), rgba(255,248,236,0.97));
            border: 1px solid rgba(122, 92, 61, 0.14);
            box-shadow: 0 10px 28px rgba(80, 53, 20, 0.08);
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }
        .stat-card-label {
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.07em;
            color: #b45309;
            text-transform: uppercase;
        }
        .stat-card-value {
            font-size: 2.4rem;
            font-weight: 900;
            color: #111827;
            line-height: 1;
        }
        .stat-card-sub {
            font-size: 0.82rem;
            color: #6b7280;
            margin-top: 0.15rem;
        }
        .stat-card.open .stat-card-value { color: #16a34a; }
        .stat-card.closed .stat-card-value { color: #dc2626; }
        .summary-panel {
            border-radius: 20px;
            padding: 1rem 1.1rem;
            background: linear-gradient(180deg, rgba(255,255,255,0.90), rgba(255,250,241,0.96));
            border: 1px solid rgba(17, 24, 39, 0.08);
            box-shadow: 0 12px 30px rgba(17, 24, 39, 0.05);
        }
        [data-testid="stChatMessage"] {
            border-radius: 18px;
        }
        .stChatFloatingInputContainer {
            backdrop-filter: blur(10px);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero_svg() -> str:
    svg = """
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 420" width="640" height="420">
      <defs>
        <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#fff2d9"/>
          <stop offset="100%" stop-color="#ffe1ad"/>
        </linearGradient>
        <linearGradient id="plate" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#ffffff"/>
          <stop offset="100%" stop-color="#f4f5f7"/>
        </linearGradient>
      </defs>
      <rect width="640" height="420" rx="36" fill="url(#bg)"/>
      <circle cx="510" cy="82" r="44" fill="#ffbf69" opacity="0.45"/>
      <circle cx="120" cy="78" r="28" fill="#f59e0b" opacity="0.22"/>
      <rect x="78" y="72" width="484" height="276" rx="30" fill="rgba(255,255,255,0.28)" stroke="rgba(120,70,20,0.14)"/>
      <ellipse cx="322" cy="232" rx="158" ry="78" fill="url(#plate)"/>
      <ellipse cx="322" cy="219" rx="114" ry="38" fill="#f7c948" opacity="0.86"/>
      <circle cx="278" cy="216" r="18" fill="#ef4444"/>
      <circle cx="318" cy="202" r="14" fill="#f97316"/>
      <circle cx="350" cy="220" r="16" fill="#f59e0b"/>
      <circle cx="382" cy="207" r="12" fill="#16a34a"/>
      <path d="M186 292c32-35 77-49 136-49 63 0 111 14 142 49" fill="none" stroke="#9a6b2f" stroke-width="9" stroke-linecap="round"/>
      <path d="M195 118h45c16 0 29 13 29 29v40H166v-40c0-16 13-29 29-29z" fill="#b45309" opacity="0.92"/>
      <rect x="220" y="102" width="16" height="38" rx="8" fill="#fb923c"/>
      <rect x="235" y="93" width="16" height="47" rx="8" fill="#fdba74"/>
      <rect x="250" y="104" width="16" height="36" rx="8" fill="#f97316"/>
      <path d="M438 126h32l-10 90h-12z" fill="#7c4a1e"/>
      <path d="M452 170c16-18 28-31 40-38" stroke="#7c4a1e" stroke-width="6" stroke-linecap="round"/>
      <text x="92" y="338" font-family="Arial, sans-serif" font-size="26" font-weight="700" fill="#7c4a1e">점심 보드</text>
    </svg>
    """
    return base64.b64encode(svg.encode("utf-8")).decode("ascii")


def init_state() -> None:
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("latest_audio_bytes", None)
    st.session_state.setdefault("tts_enabled", True)
    st.session_state.setdefault("quick_question", None)
    st.session_state.setdefault("kakao_places", [])
    st.session_state.setdefault("kakao_map_html", "")


def reset_conversation() -> None:
    st.session_state["messages"] = []
    st.session_state["latest_audio_bytes"] = None
    st.session_state["kakao_places"] = []
    st.session_state["kakao_map_html"] = ""


def sidebar_controls(csv_path: Path) -> str:
    st.sidebar.title("메뉴 보드")
    st.session_state["tts_enabled"] = st.sidebar.toggle(
        "TTS 재생",
        value=st.session_state["tts_enabled"],
        help="추천 답변을 음성으로 바로 재생합니다.",
    )

    weekday_options = ["오늘", *KOREAN_WEEKDAYS]
    selected_weekday = st.sidebar.selectbox("요일", weekday_options, index=0)

    st.sidebar.divider()
    st.sidebar.markdown(
        """
        <div style="font-size:0.78rem; font-weight:700; letter-spacing:0.07em;
                    color:#b45309; text-transform:uppercase; margin-bottom:0.5rem;">
          ⚡ 빠른 질문
        </div>
        """,
        unsafe_allow_html=True,
    )
    quick_questions = [
        "오늘 점심 추천해줘",
        "국물 있는 거 추천해줘",
        "빨리 먹을 수 있는 곳 알려줘",
        "혼밥하기 좋은 곳 있어?",
        "어제랑 안 겹치게 추천해줘",
    ]
    for q in quick_questions:
        if st.sidebar.button(q, use_container_width=True, key=f"qq_{q}"):
            st.session_state["quick_question"] = q

    effective_weekday = (
        current_korean_weekday() if selected_weekday == "오늘" else selected_weekday
    )
    return effective_weekday


def render_chat_section() -> None:
    st.markdown('<div class="chat-block">', unsafe_allow_html=True)
    title_col, button_col = st.columns([0.84, 0.16])
    with title_col:
        st.markdown('<div class="section-title">대화</div>', unsafe_allow_html=True)
        st.caption("카카오맵에서 실시간으로 검색한 가게를 추천합니다.")
    with button_col:
        st.write("")
        if st.button("대화 리셋", use_container_width=True):
            reset_conversation()
            st.rerun()

    if st.session_state["latest_audio_bytes"]:
        st.audio(st.session_state["latest_audio_bytes"], format="audio/mp3", autoplay=True)

    # 최신 메시지가 위에 오도록 역순으로 표시
    for message in reversed(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    st.markdown("</div>", unsafe_allow_html=True)


def render_dashboard(csv_path: Path, weekday: str) -> str:
    rows = load_menu_rows(csv_path)
    if not rows:
        st.info("`restaurants.csv` 파일을 찾지 못했습니다.")
        return ""

    open_rows = filter_open_rows(rows, weekday)
    closed_count = len(rows) - len(open_rows)

    st.markdown('<div class="section-title">메뉴 대시보드</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="stat-grid">
          <div class="stat-card">
            <div class="stat-card-label">전체 가게</div>
            <div class="stat-card-value">{len(rows)}</div>
            <div class="stat-card-sub">등록된 가게 수</div>
          </div>
          <div class="stat-card open">
            <div class="stat-card-label">영업중</div>
            <div class="stat-card-value">{len(open_rows)}</div>
            <div class="stat-card-sub">오늘 방문 가능</div>
          </div>
          <div class="stat-card closed">
            <div class="stat-card-label">휴무</div>
            <div class="stat-card-value">{closed_count}</div>
            <div class="stat-card-sub">오늘 휴무인 가게</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    open_context = build_menu_context_for_day(csv_path, weekday)

    return open_context


def render_summary_panel() -> None:
    st.markdown('<div class="section-title">추천 요약</div>', unsafe_allow_html=True)
    with st.container(border=True):
        if st.session_state.messages:
            last_assistant = next(
                (
                    msg["content"]
                    for msg in reversed(st.session_state.messages)
                    if msg["role"] == "assistant"
                ),
                None,
            )
            if last_assistant:
                st.markdown(
                    f'<div class="summary-panel">{last_assistant}</div>',
                    unsafe_allow_html=True,
                )
                return
        st.caption("가장 최근 추천 결과가 여기에 표시됩니다.")


def create_tts_audio(answer: str) -> bytes | None:
    audio_path = Path("sample1.mp3")
    try:
        synthesize_speech(answer, audio_path, "ko")
    except Exception:
        return None
    return audio_path.read_bytes()


def page_main() -> None:
    inject_styles()
    init_state()

    hero_left, hero_right = st.columns([1.45, 0.85], gap="medium")
    with hero_left:
        st.markdown(
            """
            <div class="hero-card">
              <div class="hero-kicker">LUNCH_RECOMMEND_AGENT</div>
              <div class="hero-title">점심 메뉴 추천기</div>
              <div class="hero-copy">
                먼저 물어보고 빠르게 고르세요.<br/>카카오맵 실시간 검색으로 딱 맞는 점심을 찾아드립니다.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with hero_right:
        st.markdown(
            f"""
            <div class="hero-card" style="display:flex; align-items:center; justify-content:center; padding:0.65rem;">
              <img src="data:image/svg+xml;base64,{hero_svg()}" style="width:100%; max-width:320px; display:block; margin:0 auto; border-radius:18px;" />
            </div>
            """,
            unsafe_allow_html=True,
        )

    csv_path = Path(DEFAULT_MENU_CSV)
    selected_weekday = sidebar_controls(csv_path)
    open_context = build_menu_context_for_day(csv_path, selected_weekday)

    # 지도 + 추천 맛집 카드 (채팅 위에 고정)
    if st.session_state.get("kakao_map_html"):
        st.markdown('<div class="section-title" style="margin-top:1.5rem; margin-bottom:0.6rem;">📍 지도에서 보기</div>', unsafe_allow_html=True)
        st.components.v1.html(st.session_state["kakao_map_html"], height=395, scrolling=False)

        places = st.session_state["kakao_places"]
        if places:
            st.markdown('<div class="section-title" style="margin-top:1rem">🍴 추천 맛집</div>', unsafe_allow_html=True)
            cols_per_row = 4
            for row_start in range(0, len(places), cols_per_row):
                row_places = places[row_start:row_start + cols_per_row]
                place_cols = st.columns(len(row_places))
                for col, p in zip(place_cols, row_places):
                    with col:
                        st.markdown(
                            f"""
                            <div class="restaurant-card">
                              <div>
                                <div class="restaurant-name">&#128205; {p['name']}</div>
                                <div class="restaurant-meta">
                                  {p['address']}<br/>
                                  {'&#128222; ' + p['phone'] if p.get('phone') else '&nbsp;'}
                                </div>
                              </div>
                              <div>{'<a href="' + p['url'] + '" target="_blank" style="font-size:0.82rem;color:#b45309;">카카오맵에서 보기 ↗</a>' if p.get('url') else ''}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
        st.divider()

    render_chat_section()
    user_text = st.chat_input("점심 메뉴를 물어보세요")

    # 빠른 질문 버튼 클릭 시 해당 텍스트를 채팅으로 처리
    if st.session_state.get("quick_question"):
        user_text = st.session_state.pop("quick_question")

    if user_text:
        st.session_state.messages.append({"role": "user", "content": user_text})
        with st.chat_message("user"):
            st.markdown(user_text)

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            with st.chat_message("assistant"):
                st.error("OPENAI_API_KEY가 없습니다. `.env` 파일을 확인해 주세요.")
        else:
            client = OpenAI(api_key=api_key)
            with st.chat_message("assistant"):
                with st.spinner("카카오맵에서 맛집을 찾는 중..."):
                    try:
                        # 1. LLM이 검색 키워드 판단
                        keyword = extract_search_keyword(client, user_text)
                        # 2. 사용자 요청 개수 파싱
                        size = extract_place_count(user_text, default=3)
                        # 3. 카카오 맵 검색
                        places = search_places(keyword, size=size)
                        st.session_state["kakao_places"] = places
                        st.session_state["kakao_map_html"] = build_map_html(places)
                        # 3. 검색 결과 기반 LLM 응답
                        if places:
                            answer = generate_response_with_places(client, user_text, places)
                        else:
                            answer = generate_response(
                                client=client,
                                user_text=user_text,
                                open_only_context=open_context,
                            )
                    except APIConnectionError:
                        st.error("OpenAI 연결에 실패했습니다. 네트워크나 방화벽을 확인해 주세요.")
                    else:
                        st.markdown(answer)
                        st.session_state.messages.append(
                            {"role": "assistant", "content": answer}
                        )
                        if st.session_state["tts_enabled"]:
                            audio_bytes = create_tts_audio(answer)
                            st.session_state["latest_audio_bytes"] = audio_bytes
                        else:
                            st.session_state["latest_audio_bytes"] = None
                        st.rerun()


def main() -> None:
    load_dotenv(dotenv_path=Path(__file__).resolve().with_name(".env"))
    st.set_page_config(
        page_title="점심 메뉴 추천기",
        page_icon="L",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    pg = st.navigation(
        [
            st.Page(page_main, title="점심 추천", icon="🍱"),
            st.Page(
                Path(__file__).resolve().parent / "pages" / "db_page.py",
                title="데이터베이스",
                icon="🗃️",
            ),
        ]
    )
    pg.run()


if __name__ == "__main__":
    main()
