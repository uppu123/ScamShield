import requests
import streamlit as st


def render_result(result):
    if result.get("error"):
        st.error(result.get("message", result.get("error")))
        return
    score = float(result["score"])
    st.subheader(result["label"])
    st.progress(score, text=f"Scam likelihood: {score * 100:.0f}%")
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Rule score", f"{result['rule_score'] * 100:.0f}%")
    col_b.metric(
        "Model confidence",
        f"{result['model_confidence'] * 100:.0f}%"
        if result.get("model_confidence") is not None
        else "n/a",
    )
    col_c.metric(
        "Duplicate template",
        f"{result['duplicate_template_score'] * 100:.0f}%"
        if result.get("duplicate_template_score") is not None
        else "n/a",
    )
    with st.expander("Why this looks like this", expanded=True):
        for bullet in result["explanation"]["bullet_points"]:
            st.markdown(bullet)
    if result.get("red_flags"):
        st.subheader("Detected red flags")
        for flag in result["red_flags"]:
            st.warning(f"**{flag['name']}** — {flag['explanation']}")
            st.code(" | ".join(flag["evidence"]))
    with st.expander("Highlighted text"):
        st.markdown(result["highlighted_text"], unsafe_allow_html=True)
