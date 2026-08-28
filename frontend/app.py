from datetime import datetime, timezone

import streamlit as st

import cloud_client
from components import (
    backend_status,
    copy_to_clipboard,
    fetch_reports,
    inject_css,
    inject_dark_css,
    render_chat,
    render_history,
    render_how_it_works,
    render_loader,
    render_reports,
    render_result,
    render_typing,
    show_analysis_error,
)

SCAM_SAMPLE = (
    "URGENT: Work from home data entry job! Earn Rs. 50,000/month guaranteed income. "
    "No experience required. Pay a refundable security deposit of Rs. 2,000 to book your seat. "
    "Limited seats, apply within 24 hours. WhatsApp +91 98765 43210 or email hr.recruitment@gmail.com"
)
LEGIT_SAMPLE = (
    "Software Engineer II at Acme Systems Pvt Ltd. "
    "3+ years of experience in Python and backend development required. "
    "Salary as per company standards, negotiable based on experience. "
    "Apply via careers@acme.co.in or call HR at +91 22 4000 0000."
)

NAV_LABELS = {
    "text": "\u270d\ufe0f Analyze text",
    "image": "\U0001f5bc\ufe0f Analyze screenshot",
    "reports": "\U0001f4ca Recent reports",
    "history": "\u23f3 Session history",
    "chat": "\U0001f4ac Ask ScamShield",
}

st.set_page_config(page_title="ScamShield", page_icon="SS", layout="wide")
inject_css()

for key, default in (
    ("last_result", None),
    ("last_source", ""),
    ("history", []),
    ("chat", []),
    ("theme", "Light"),
    ("nav", "text"),
):
    if key not in st.session_state:
        st.session_state[key] = default

if st.session_state.theme == "Dark":
    inject_dark_css()

online = backend_status()

with st.sidebar:
    st.markdown('<div class="sb-brand">ScamShield</div>', unsafe_allow_html=True)
    status_cls = "ok" if online else "bad"
    st.markdown(
        f'<div class="sb-status"><span class="dot {status_cls}"></span>'
        f'{"Engine ready" if online else "Engine unavailable"}</div>',
        unsafe_allow_html=True,
    )
    if not online:
        st.caption("The analysis engine failed to start.")
    st.markdown("---")
    st.markdown('<div class="sb-nav-label">Utilities</div>', unsafe_allow_html=True)
    st.radio(
        "Navigate",
        list(NAV_LABELS.keys()),
        format_func=lambda v: NAV_LABELS[v],
        key="nav",
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.subheader("Appearance")
    st.selectbox("Theme", ["Light", "Dark"], key="theme", label_visibility="collapsed")
    st.markdown("---")
    st.subheader("About")
    st.write(
        "Fake job posting & recruitment fraud detector built for the Indian job market. "
        "Combines a rule engine, an optional ML model, and known-template matching."
    )
    with st.expander("Deploy diagnostics"):
        diag = cloud_client.diagnostics()
        if diag.get("secrets_parse_error"):
            st.error(diag["secrets_parse_error"])
        st.json(diag)
        if st.button("Test MongoDB connection", key="diag_ping"):
            ok, err = cloud_client.ping_db()
            if ok:
                st.success("MongoDB connected.")
            else:
                st.error(f"MongoDB not reachable: {err}")

st.markdown(
    '<div class="ss-hero">'
    '<div class="ss-hero-badge">&#128481; Built for the Indian job market</div>'
    "<h1>ScamShield</h1>"
    "<p>Paste a job posting or upload a screenshot and get an instant, explainable scam-risk verdict.</p>"
    '<div class="ss-hero-chips">'
    "<span>No experience needed</span><span>Earn Rs 50,000/month</span>"
    "<span>Pay a deposit to apply</span><span>Limited seats</span>"
    "</div>"
    "</div>",
    unsafe_allow_html=True,
)


def _analyze(call, label="Running analysis"):
    holder = st.empty()
    holder.markdown(render_loader(label), unsafe_allow_html=True)
    try:
        data = call()
    except Exception as exc:
        data = {"error": "analysis_failed", "message": str(exc)}
    finally:
        holder.empty()
    if data is None or data.get("error"):
        show_analysis_error(
            data.get("error", "analysis_failed") if data else "analysis_failed",
            data.get("message", "") if data else "Analysis failed.",
        )
        return None
    return data


def _commit(result, kind):
    st.session_state.last_result = result
    st.session_state.history.append(
        {
            "type": kind,
            "source_text": st.session_state.last_source,
            "result": result,
            "time": datetime.now(timezone.utc).isoformat(),
        }
    )
    st.rerun()


def _send_chat(message):
    st.session_state.chat.append({"role": "user", "text": message})
    prior = [
        {"role": m["role"], "content": m["text"]}
        for m in st.session_state.chat[:-1]
    ]
    typing = st.empty()
    typing.markdown(render_typing(), unsafe_allow_html=True)
    try:
        data = cloud_client.chat(message, prior)
        reply = data.get("reply", "Sorry, I could not process that.")
        source = data.get("source", "faq")
    except Exception:
        reply = "The assistant could not be reached."
        source = "offline"
    finally:
        typing.empty()
    st.session_state.chat.append({"role": "bot", "text": reply, "source": source})


def page_text():
    render_how_it_works()
    s1, s2, _ = st.columns([1, 1, 2])
    if s1.button("\u2728 Load scam sample", use_container_width=True):
        st.session_state.analyze_text = SCAM_SAMPLE
    if s2.button("\u2705 Load legit sample", use_container_width=True):
        st.session_state.analyze_text = LEGIT_SAMPLE

    st.text_area(
        "Paste the job posting text",
        height=240,
        key="analyze_text",
        placeholder="Paste the job posting text here, or load a sample above. e.g. 'Work from home, earn Rs 50,000/month, pay a refundable deposit to apply...'",
    )

    c1, c2 = st.columns([1, 1])
    run_analysis = c1.button("Analyze posting", type="primary", use_container_width=True)
    clear_all = c2.button("Clear", use_container_width=True)
    if clear_all:
        st.session_state.last_result = None
        st.session_state.analyze_text = ""
        st.rerun()
    if run_analysis:
        text = st.session_state.analyze_text or ""
        if not text.strip():
            st.warning("Paste some job posting text first.")
        else:
            result = _analyze(lambda: cloud_client.analyze_text(text))
            if result is not None:
                st.session_state.last_source = text
                _commit(result, "text")

    if (st.session_state.last_result or {}).get("type") == "text":
        render_result(st.session_state.last_result, st.session_state.last_source, uid="current_text")


def page_image():
    file = st.file_uploader(
        "Upload a screenshot (WhatsApp / LinkedIn post)",
        type=["png", "jpg", "jpeg", "webp"],
        key="uploaded_image",
    )
    c1, c2 = st.columns([1, 1])
    run_image = c1.button("Analyze image", type="primary", use_container_width=True)
    clear_image = c2.button("Clear image", use_container_width=True)
    if clear_image:
        st.session_state.last_result = None
        st.session_state.uploaded_image = None
        st.rerun()
    if run_image:
        if file is None:
            st.warning("Upload a screenshot first.")
        else:
            result = _analyze(
                lambda: cloud_client.analyze_image(file.getvalue()),
                label="Reading text from screenshot",
            )
            if result is not None:
                st.session_state.last_source = result.get("ocr_text", "")
                _commit(result, "image")

    if (st.session_state.last_result or {}).get("type") == "image":
        render_result(st.session_state.last_result, st.session_state.last_source, uid="current_image")


def page_reports():
    if st.button("Refresh feed", use_container_width=True):
        fetch_reports.clear()
    reports = fetch_reports(15)
    render_reports(reports)


def page_history():
    render_history(st.session_state.history)


def page_chat():
    render_chat(st.session_state.chat)
    if st.button("Clear conversation", use_container_width=True):
        st.session_state.chat = []
        st.rerun()
    quick_questions = [
        "Is asking for a security deposit normal?",
        "Should I pay a registration fee?",
        "How do I verify a recruiter?",
        "Too-good salary for freshers?",
    ]
    q_cols = st.columns(len(quick_questions))
    for i, question in enumerate(quick_questions):
        if q_cols[i].button(question, key=f"quick_q_{i}", use_container_width=True):
            _send_chat(question)
            st.rerun()

    with st.form("chat_form"):
        question = st.text_input(
            "Ask a question",
            key="chat_input",
            placeholder="e.g. Is asking for a security deposit normal?",
        )
        submitted = st.form_submit_button("Send", type="primary", use_container_width=True)
    if submitted and question.strip():
        st.session_state.chat_input = ""
        _send_chat(question)
        st.rerun()


page = st.session_state["nav"]
if page == "text":
    page_text()
elif page == "image":
    page_image()
elif page == "reports":
    page_reports()
elif page == "history":
    page_history()
elif page == "chat":
    page_chat()