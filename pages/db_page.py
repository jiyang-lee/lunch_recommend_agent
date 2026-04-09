"""데이터베이스 페이지 — 전체 가게 목록을 테이블로 표시합니다."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from menu_db import DEFAULT_MENU_CSV, load_menu_rows

_CSV_PATH = Path(__file__).resolve().parent.parent / DEFAULT_MENU_CSV

st.title("🗃️ 데이터베이스")
st.caption("restaurants.csv 전체 데이터")

rows = load_menu_rows(_CSV_PATH)

if not rows:
    st.warning(f"CSV 파일을 찾지 못했습니다: {_CSV_PATH}")
else:
    df = pd.DataFrame(
        [
            {
                "ID": row.id,
                "가게이름": row.name,
                "휴무일": row.closed_day or "없음",
                "주소": row.address,
            }
            for row in rows
        ]
    )
    st.metric("총 가게 수", len(rows))
    st.dataframe(df, use_container_width=True, hide_index=True)
