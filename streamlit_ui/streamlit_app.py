"""Streamlit UI for the lunch recommendation agent."""

from __future__ import annotations

import base64
import os
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from openai import APIConnectionError, OpenAI

from db.menu_db import (
    DEFAULT_MENU_CSV,
    KOREAN_WEEKDAYS,
    build_menu_context_for_day,
    current_korean_weekday,
    filter_open_rows,
    load_menu_rows,
)
from llm.llm import generate_response
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
            gap: 0.9rem;
            align-items: center;
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


def food_thumb(label: str) -> str:
    safe_label = (label[:1] or "?").upper()
    svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="120" height="120">
      <defs>
        <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#fff1cc"/>
          <stop offset="100%" stop-color="#ffcb77"/>
        </linearGradient>
      </defs>
      <rect width="120" height="120" rx="24" fill="url(#g)"/>
      <circle cx="60" cy="60" r="31" fill="#fff8ef" stroke="#d97706" stroke-width="4"/>
      <circle cx="60" cy="60" r="18" fill="#fbbf24"/>
      <text x="60" y="68" text-anchor="middle" font-family="Arial, sans-serif" font-size="30" font-weight="700" fill="#7c2d12">{safe_label}</text>
    </svg>
    """
    return f"data:image/svg+xml;base64,{base64.b64encode(svg.encode('utf-8')).decode('ascii')}"


def init_state() -> None:
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("latest_audio_bytes", None)
    st.session_state.setdefault("tts_enabled", True)


def reset_conversation() -> None:
    st.session_state["messages"] = []
    st.session_state["latest_audio_bytes"] = None


def sidebar_controls(csv_path: Path) -> str:
    st.sidebar.title("메뉴 보드")
    st.sidebar.caption("CSV 가게 목록")
    st.session_state["tts_enabled"] = st.sidebar.toggle(
        "TTS 재생",
        value=st.session_state["tts_enabled"],
        help="추천 답변을 음성으로 바로 재생합니다.",
    )

    weekday_options = ["오늘", *KOREAN_WEEKDAYS]
    selected_weekday = st.sidebar.selectbox("요일", weekday_options, index=0)
    search = st.sidebar.text_input("가게 검색", "")

    rows = load_menu_rows(csv_path)
    if not rows:
        st.sidebar.warning(f"CSV 파일을 찾지 못했습니다: {csv_path}")
        return selected_weekday

    effective_weekday = (
        current_korean_weekday() if selected_weekday == "오늘" else selected_weekday
    )
    open_rows = filter_open_rows(rows, effective_weekday)
    filtered_rows = [
        row
        for row in open_rows
        if search.lower() in row.name.lower() or search.lower() in row.address.lower()
    ]

    st.sidebar.metric("전체", len(rows))
    st.sidebar.metric("영업중", len(open_rows))
    st.sidebar.metric("검색결과", len(filtered_rows))
    st.sidebar.divider()

    for row in filtered_rows[:10]:
        st.sidebar.write(f"**{row.name}**")
        st.sidebar.caption(f"{row.address} / 휴무: {row.closed_day or '없음'}")

    return effective_weekday


def render_chat_section() -> None:
    st.markdown('<div class="chat-block">', unsafe_allow_html=True)
    title_col, button_col = st.columns([0.84, 0.16])
    with title_col:
        st.markdown('<div class="section-title">대화</div>', unsafe_allow_html=True)
        st.caption("추천은 CSV에 있는 가게만 사용합니다.")
    with button_col:
        st.write("")
        if st.button("대화 리셋", use_container_width=True):
            reset_conversation()
            st.rerun()

    if st.session_state["latest_audio_bytes"]:
        st.audio(st.session_state["latest_audio_bytes"], format="audio/mp3", autoplay=True)

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    st.markdown("</div>", unsafe_allow_html=True)


def render_dashboard(csv_path: Path, weekday: str) -> str:
    rows = load_menu_rows(csv_path)
    if not rows:
        st.info("`restaurants.csv` 파일을 찾지 못했습니다.")
        return ""

    open_rows = filter_open_rows(rows, weekday)
    st.markdown('<div class="section-title">메뉴 대시보드</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    col1.metric("전체", len(rows))
    col2.metric("영업중", len(open_rows))
    col3.metric("휴무", len(rows) - len(open_rows))

    open_context = build_menu_context_for_day(csv_path, weekday)
    with st.expander("CSV 미리보기", expanded=False):
        preview_df = pd.DataFrame(
            [
                {
                    "id": row.id,
                    "가게": row.name,
                    "휴무일": row.closed_day,
                    "주소": row.address,
                }
                for row in open_rows
            ]
        )
        st.dataframe(preview_df, use_container_width=True, hide_index=True)
        st.code(open_context or "영업 중인 가게가 없습니다.", language="text")

    st.markdown('<div class="section-title">가게 카드</div>', unsafe_allow_html=True)
    cols = st.columns(2)
    for index, row in enumerate(open_rows):
        with cols[index % 2]:
            st.markdown(
                f"""
                <div class="restaurant-card">
                    <img class="restaurant-thumb" src="{food_thumb(row.name)}" />
                    <div>
                      <div class="restaurant-name">{row.name}</div>
                      <div class="restaurant-meta">
                        주소: {row.address}<br/>
                        휴무: {row.closed_day or '없음'}
                      </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

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


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    load_dotenv(dotenv_path=project_root / ".env")
    st.set_page_config(
        page_title="점심 메뉴 추천기",
        page_icon="L",
        layout="wide",
        initial_sidebar_state="expanded",
    )
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
                먼저 물어보고 빠르게 고르세요. CSV에 있는 가게만 기준으로 오늘 점심을 추천합니다.
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

    csv_path = project_root / DEFAULT_MENU_CSV
    selected_weekday = sidebar_controls(csv_path)
    open_context = build_menu_context_for_day(csv_path, selected_weekday)

    render_chat_section()
    user_text = st.chat_input("점심 메뉴를 물어보세요")
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
                with st.spinner("추천을 만드는 중입니다..."):
                    try:
                        answer = generate_response(
                            client=client,
                            user_text=user_text,
                            menu_context="",
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
                            if audio_bytes:
                                st.audio(audio_bytes, format="audio/mp3", autoplay=True)
                        else:
                            st.session_state["latest_audio_bytes"] = None

    st.divider()
    render_dashboard(csv_path, selected_weekday)
    st.markdown("---")
    render_summary_panel()


if __name__ == "__main__":
    main()
