# ==========================================================
# ELAI (Elevator Logic AI)
# Streamlit Cloud 안정화 FINAL
# ==========================================================

import streamlit as st
st.set_page_config(page_title="ELAI", page_icon="🚧", layout="wide")

import os
import pandas as pd

# ==========================================================
# 🎨 스타일
# ==========================================================
st.markdown("""
<style>
html, body, [class*="css"] {
    background-color:#0f1117;
    color:#e6e6e6;
}
</style>
""", unsafe_allow_html=True)

# ==========================================================
# 🔐 로그인
# ==========================================================
APP_PASSWORD = st.secrets.get("ELAI_PASSWORD", "1234")

if "auth" not in st.session_state:
    st.title("ELAI")
    pwd = st.text_input("비밀번호", type="password")
    if st.button("ENTER"):
        if pwd == APP_PASSWORD:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("접근 불가")
    st.stop()

# ==========================================================
# 📢 공지사항 로딩
# ==========================================================
@st.cache_data(ttl=300)
def load_notices():
    notices = []

    SHEET_ID = "1PMY6Y4lNVbKbnFOYr0CAb956CX3xARaZV_2uy-JlYJM"
    SHEETS = {
        "1호기": "1324822294",
        "2호기": "581675674",
        "3호기": "1718384251"
    }

    for sheet, gid in SHEETS.items():
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
        try:
            df = pd.read_csv(url)
        except:
            continue

        if df.shape[1] < 6:
            continue

        site_col = df.columns[0]
        remain_col = df.columns[5]

        df[remain_col] = pd.to_numeric(df[remain_col], errors="coerce")

        for _, r in df.iterrows():
            if pd.isna(r[remain_col]):
                continue

            d = int(r[remain_col])

            if d < 0:
                status, lv = "만료", 0
            elif d <= 30:
                status, lv = "임박", 1
            else:
                status, lv = "정상", 2

            notices.append({
                "현장": str(r[site_col]),
                "상태": status,
                "일수": d,
                "lv": lv,
                "호기": sheet
            })

    return sorted(notices, key=lambda x: (x["lv"], x["일수"]))

# ==========================================================
# 📢 공지사항 UI
# ==========================================================
st.markdown("## 📢 공지사항")

with st.spinner("공지사항 불러오는 중..."):
    notices = load_notices()

def draw_notice(n):
    msg = f"{n['상태']} | {n['현장']} ({n['일수']}일) [{n['호기']}]"
    if n["상태"] == "만료":
        st.info("⚪ " + msg)
    elif n["상태"] == "임박":
        st.error("🔴 " + msg)
    else:
        st.success("🟢 " + msg)

urgent = [n for n in notices if n["상태"] == "임박"][:3]

st.markdown("### 🚨 임박 TOP 3")
if urgent:
    for n in urgent:
        draw_notice(n)
else:
    st.success("임박 없음")

with st.expander("전체 보기"):
    for n in notices:
        draw_notice(n)

# ==========================================================
# 🤖 AI 고장 진단
# ==========================================================
st.divider()
st.title("ELAI 고장 진단")

question = st.text_input("고장 증상 입력")

if st.button("AI 진단"):
    if not question:
        st.warning("질문 입력 필요")
        st.stop()

    # 🔑 OpenAI 초기화
    try:
        from openai import OpenAI

        api_key = st.secrets.get("OPENAI_API_KEY", None)
        if not api_key:
            st.error("❌ OPENAI_API_KEY 없음 (Streamlit Secrets 확인)")
            st.stop()

        client = OpenAI(api_key=api_key)

    except Exception as e:
        st.error("❌ OpenAI 초기화 실패")
        st.code(str(e))
        st.stop()

    with st.spinner("AI 분석 중..."):
        res = client.responses.create(
            model="gpt-4.1-mini",
            input=f"엘리베이터 고장 질문: {question}"
        )

    st.success(res.output_text)
