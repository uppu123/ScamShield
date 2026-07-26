import os

import requests
import streamlit as st

from components import render_result

BACKEND = os.environ.get("BACKEND_URL", "http://localhost:5000")

st.set_page_config(page_title="ScamShield", layout="wide")
st.title("ScamShield")
st.caption("Fake Job Posting & Recruitment Fraud Detector")


tab_text, tab_image, tab_reports, tab_chat = st.tabs(
    ["Analyze text", "Analyze screenshot", "Recent reports", "Ask ScamShield"]
)

with tab_text:
    text = st.text_area("Paste the job posting text", height=300)
    if st.button("Analyze", type="primary"):
        if text.strip():
            try:
                response = requests.post(
                    f"{BACKEND}/analyze_text", json={"text": text}, timeout=60
                )
                render_result(response.json())
            except requests.ConnectionError:
                st.error(f"Cannot reach backend at {BACKEND}. Is it running?")

with tab_image:
    file = st.file_uploader("Upload a screenshot (WhatsApp / LinkedIn post)", type=["png", "jpg", "jpeg", "webp"])
    if st.button("Analyze image", type="primary"):
        if file is not None:
            try:
                response = requests.post(
                    f"{BACKEND}/analyze_image",
                    files={"image": (file.name, file.getvalue())},
                    timeout=60,
                )
                render_result(response.json())
            except requests.ConnectionError:
                st.error(f"Cannot reach backend at {BACKEND}. Is it running?")

with tab_reports:
    if st.button("Refresh feed"):
        try:
            response = requests.get(f"{BACKEND}/reports", params={"limit": 10}, timeout=30)
            reports = response.json().get("reports", [])
            for report in reports:
                with st.expander(f"{report.get('source', 'unknown')} · {report.get('created_at', '')}"):
                    st.write(report.get("text", ""))
                    if report.get("notes"):
                        st.info(report.get("notes"))
        except requests.ConnectionError:
            st.error(f"Cannot reach backend at {BACKEND}. Is it running?")

with tab_chat:
    st.caption("Ask questions like: 'Is asking for a security deposit normal?'")
    message = st.text_input("Your question")
    if st.button("Send", type="primary"):
        if message.strip():
            try:
                response = requests.post(
                    f"{BACKEND}/chat", json={"message": message}, timeout=30
                )
                st.info(response.json().get("reply"))
            except requests.ConnectionError:
                st.error(f"Cannot reach backend at {BACKEND}. Is it running?")
