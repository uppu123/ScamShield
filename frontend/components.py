import html
import json

import streamlit as st

from cloud_client import health, recent_reports, report_scam
from report import build_pdf_report

PRIMARY = "#4f46e5"
SCAM = "#dc2626"
CAUTION = "#d97706"
SAFE = "#16a34a"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
  --bg:#f8fafc; --card:#ffffff; --border:#e2e8f0;
  --ink:#0f172a; --ink-2:#1e293b; --muted:#64748b;
  --flag-bg:#fffbfb; --flag-border:#fecaca; --flag-ev:#ffffff;
  color-scheme:light;
}

.stApp { background:var(--bg); font-family:'Inter',-apple-system,'Segoe UI',sans-serif; color-scheme:light; }
.block-container { padding-top:2rem; max-width:1100px; }
[data-testid="stAppViewContainer"] { background:var(--bg); color:var(--ink-2); }

[data-testid="stSidebar"] { background:#0f172a; }
[data-testid="stSidebar"] * { color:#e2e8f0; }
[data-testid="stSidebar"] hr { border-color:#1e293b; }
[data-testid="stWidgetLabel"] p { color:#0f172a; }

.ss-hero { background:linear-gradient(135deg,#4f46e5,#7c3aed 55%,#db2777); border-radius:20px; padding:28px 34px; color:#fff; margin-bottom:22px; box-shadow:0 10px 30px -12px rgba(79,70,229,.5); }
.ss-hero h1 { color:#fff !important; font-size:2.1rem; font-weight:800; margin:0 0 6px; }
.ss-hero p { color:#e0e7ff !important; font-size:1.02rem; margin:0; }

.sb-brand { font-size:1.25rem; font-weight:800; color:#fff; letter-spacing:.02em; }
.sb-status { margin-top:10px; font-size:.9rem; color:#cbd5e1; }
.sb-status .dot { display:inline-block; width:9px; height:9px; border-radius:50%; margin-right:7px; vertical-align:middle; }
.dot.ok { background:#22c55e; box-shadow:0 0 8px #22c55e; }
.dot.bad { background:#ef4444; box-shadow:0 0 8px #ef4444; }

.ss-card { background:var(--card); border:1px solid var(--border); border-radius:16px; padding:18px 20px; box-shadow:0 1px 3px rgba(15,23,42,.06); margin-bottom:14px; }
.ss-card h3 { margin:0 0 12px; font-size:1.05rem; font-weight:700; color:var(--ink); }

.ss-pill { display:inline-block; padding:4px 12px; border-radius:999px; font-size:.76rem; font-weight:700; letter-spacing:.03em; }
.ss-pill.red { background:#fee2e2; color:#b91c1c; }
.ss-pill.amber { background:#fef3c7; color:#b45309; }
.ss-pill.green { background:#dcfce7; color:#15803d; }
.ss-pill.slate { background:#f1f5f9; color:#475569; }
.ss-pill.indigo { background:#eef2ff; color:#4338ca; }

.gauge { --c:#16a34a; --p:0; border-radius:50%; background:conic-gradient(var(--c) calc(var(--p)*1%), var(--border) 0); display:grid; place-items:center; position:relative; margin:0 auto; }
.gauge::before { content:""; position:absolute; inset:15px; border-radius:50%; background:var(--card); box-shadow:inset 0 1px 4px rgba(15,23,42,.08); }
.gauge .gval { position:relative; z-index:1; font-size:2.1rem; font-weight:800; color:var(--c); line-height:1; text-align:center; }
.gauge .glab { position:relative; z-index:1; font-size:.66rem; color:var(--muted); letter-spacing:.1em; text-transform:uppercase; text-align:center; margin-top:4px; }

.stat { background:var(--card); border:1px solid var(--border); border-radius:14px; padding:14px 12px; text-align:center; }
.stat .k { font-size:.7rem; color:var(--muted); text-transform:uppercase; letter-spacing:.06em; font-weight:700; }
.stat .v { font-size:1.45rem; font-weight:800; color:var(--ink); margin-top:2px; }

.flag { border:1px solid var(--flag-border); border-left:5px solid #dc2626; background:var(--flag-bg); border-radius:12px; padding:12px 14px; margin-bottom:10px; }
.flag h4 { margin:0; font-size:.95rem; font-weight:700; color:#991b1b; }
.flag .ev { margin-top:8px; }
.flag .ev span { display:inline-block; background:var(--flag-ev); border:1px solid var(--flag-border); border-radius:6px; padding:2px 8px; margin:2px 6px 2px 0; font-family:Consolas,'Courier New',monospace; font-size:.75rem; color:#9f1239; }

.msg { border-radius:16px; padding:10px 14px; margin-bottom:8px; max-width:85%; line-height:1.55; font-size:.92rem; }
.msg.user { background:#4f46e5; color:#fff; margin-left:auto; border-bottom-right-radius:4px; }
.msg.bot { background:var(--card); border:1px solid var(--border); border-bottom-left-radius:4px; color:var(--ink-2); }
.msg-src { font-size:.66rem; color:#94a3b8; margin-top:5px; text-align:right; }
.msg.user .msg-src { color:#c7d2fe; }
.typing { display:inline-flex; gap:5px; align-items:center; padding:6px 2px; }
.typing span { width:8px; height:8px; border-radius:50%; background:#94a3b8; animation:ss-bounce 1.3s infinite ease-in-out; }
.typing span:nth-child(2) { animation-delay:.18s; }
.typing span:nth-child(3) { animation-delay:.36s; }

.stTabs [data-baseweb="tab-list"] { gap:8px; border-bottom:1px solid var(--border); }
.stTabs [data-baseweb="tab"] { border-radius:10px 10px 0 0; font-weight:600; color:var(--muted); padding:8px 16px; }
.stTabs [data-baseweb="tab"]:hover { color:#4f46e5; }
.stTabs [aria-selected="true"] { color:#4f46e5; border-bottom:2px solid #4f46e5; }

.stButton > button { border-radius:10px; font-weight:600; border:1px solid var(--border); }
.stButton > button[kind="primary"] { background:#4f46e5; border:1px solid #4f46e5; color:#fff; }
.stButton > button[kind="primary"]:hover { background:#4338ca; }
.stTextInput input, .stTextArea textarea, [data-baseweb="select"] > div, [data-testid="stDateInput"] input { border-radius:10px; }
[data-testid="stTextArea"] textarea, [data-testid="stTextInput"] input,
[data-testid="stDateInput"] input, [data-baseweb="select"] > div {
  background:#ffffff !important; color:#0f172a !important; border-color:#cbd5e1 !important;
  caret-color:#0f172a;
}
[data-testid="stTextArea"] textarea::placeholder, [data-testid="stTextInput"] input::placeholder,
[data-testid="stDateInput"] input::placeholder,
[data-testid="stTextArea"] textarea::-webkit-input-placeholder,
[data-testid="stTextInput"] input::-webkit-input-placeholder,
[data-testid="stDateInput"] input::-webkit-input-placeholder {
  color:#64748b !important; opacity:1 !important;
}
[data-testid="stTextInput"] input:-webkit-autofill, [data-testid="stTextArea"] textarea:-webkit-autofill {
  -webkit-text-fill-color:#0f172a; -webkit-box-shadow:0 0 0 1000px #ffffff inset; caret-color:#0f172a;
}
[data-testid="stTextArea"] textarea:focus, [data-testid="stTextInput"] input:focus { border-color:#4f46e5; box-shadow:0 0 0 2px rgba(79,70,229,.15); }
[data-testid="stFileUploaderDropzone"] { border-radius:14px; border:2px dashed #c7d2fe; background:#eef2ff !important; color:#1e293b; }

.streamlit-expanderHeader { font-weight:600; color:var(--ink-2); }
[data-testid="stExpander"] { border-radius:12px; }

mark { background:#ffe4e6; color:#be123c; padding:0 3px; border-radius:4px; font-weight:600; }
footer { visibility:hidden; }

.ss-loader { display:flex; flex-direction:column; align-items:center; justify-content:center; padding:52px 0 44px; }
.ss-loader .ring { position:relative; width:104px; height:104px; }
.ss-loader .ring svg { width:100%; height:100%; animation:ss-spin 1.3s linear infinite; }
.ss-loader .shield { position:absolute; inset:0; display:grid; place-items:center; font-size:2.5rem; animation:ss-pulse 1.1s ease-in-out infinite; }
.ss-loader .bar { width:264px; height:8px; border-radius:999px; background:var(--border); overflow:hidden; margin-top:24px; position:relative; }
.ss-loader .bar span { position:absolute; inset:0; background:linear-gradient(90deg,#4f46e5,#7c3aed,#db2777); border-radius:999px; animation:ss-fill 1.5s ease-in-out infinite; }
.ss-loader p { margin:14px 0 0; color:var(--muted); font-weight:600; letter-spacing:.04em; font-size:.95rem; }
.ss-loader .dots::after { content:""; animation:ss-dots 1.4s steps(4,end) infinite; }

.ss-dl { display:inline-block; width:100%; text-align:center; padding:10px 12px; border-radius:10px; font-weight:600; font-size:.92rem; text-decoration:none !important; cursor:pointer; transition:transform .15s ease, box-shadow .2s ease; box-sizing:border-box; }
.ss-dl.json { background:var(--card); border:1px solid var(--border); color:var(--ink); }
.ss-dl.json:hover { border-color:#4f46e5; color:#4f46e5; }
.ss-dl.pdf { background:#4f46e5; border:1px solid #4f46e5; color:#fff; box-shadow:0 6px 16px -6px rgba(79,70,229,.55); }
.ss-dl.pdf:hover { box-shadow:0 12px 24px -8px rgba(79,70,229,.7); }
.ss-dl:active { transform:scale(.97); }
.ss-dl.done { animation:ss-pop .5s ease; }

.ss-ready { display:flex; align-items:center; gap:10px; color:#16a34a; font-weight:700; font-size:.95rem; margin-bottom:4px; animation:ss-pop .5s ease; }
.ss-ready .spark { display:inline-block; animation:ss-pulse 1.4s ease-in-out infinite; }

@keyframes ss-spin { to { transform:rotate(360deg); } }
@keyframes ss-pulse { 0%,100% { transform:scale(1); } 50% { transform:scale(1.1); } }
@keyframes ss-bounce { 0%,60%,100% { transform:translateY(0); opacity:.45; } 30% { transform:translateY(-5px); opacity:1; } }
@keyframes ss-fill { 0% { transform:translateX(-110%); } 100% { transform:translateX(110%); } }
@keyframes ss-pop { 0% { transform:scale(.96); } 45% { transform:scale(1.03); } 100% { transform:scale(1); } }
@keyframes ss-dots { 0% { content:""; } 25% { content:"."; } 50% { content:".."; } 75% { content:"..."; } }
</style>
"""

DARK_CSS = """
<style>
.stApp {
  --bg:#0b1220; --card:#111a2e; --border:#1e293b;
  --ink:#f1f5f9; --ink-2:#cbd5e1; --muted:#94a3b8;
  --flag-bg:#2a1215; --flag-border:#7f1d1d; --flag-ev:#3b1a1e;
}
.stApp { background:var(--bg); color:var(--ink-2); color-scheme:dark; }
[data-testid="stSidebar"] { background:#0b1220; }
[data-testid="stSidebar"] * { color:#e2e8f0; }

[data-testid="stWidgetLabel"] p { color:#cbd5e1; }
.stRadio [role="radiogroup"] label p { color:#cbd5e1; }
.stSelectbox [data-baseweb="select"] > div { background:#0f172a !important; color:#e2e8f0 !important; }
[data-testid="stFileUploaderDropzone"] p { color:#cbd5e1; }

[data-testid="stTextArea"] textarea, [data-testid="stTextInput"] input,
[data-testid="stDateInput"] input, [data-baseweb="select"] > div {
  background:#0f172a !important; color:#e2e8f0 !important; border-color:#1e293b !important;
  caret-color:#e2e8f0;
}
[data-testid="stTextArea"] textarea::placeholder, [data-testid="stTextInput"] input::placeholder,
[data-testid="stDateInput"] input::placeholder,
[data-testid="stTextArea"] textarea::-webkit-input-placeholder,
[data-testid="stTextInput"] input::-webkit-input-placeholder,
[data-testid="stDateInput"] input::-webkit-input-placeholder {
  color:#94a3b8 !important; opacity:1 !important;
}
[data-testid="stTextArea"] textarea:focus, [data-testid="stTextInput"] input:focus { border-color:#4f46e5; }
[data-testid="stTextInput"] input:-webkit-autofill, [data-testid="stTextArea"] textarea:-webkit-autofill {
  -webkit-text-fill-color:#e2e8f0; -webkit-box-shadow:0 0 0 1000px #0f172a inset; caret-color:#e2e8f0;
}

.stButton > button:not([kind="primary"]) { background:#0f172a; border-color:#1e293b; color:#e2e8f0; }
.stButton > button:not([kind="primary"]):hover { border-color:#4f46e5; color:#818cf8; }
.stDownloadButton > button { background:#0f172a; border-color:#1e293b; color:#e2e8f0; }
.stDownloadButton > button:hover { border-color:#4f46e5; color:#818cf8; }

[data-testid="stFileUploaderDropzone"] { background:#0f172a !important; border-color:#334155; }
[data-testid="stFileUploaderDropzone"]:hover { border-color:#4f46e5; }
[data-testid="stExpander"] { background:#0f172a; border-color:#1e293b; }
.streamlit-expanderHeader { color:#e2e8f0; }

[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li { color:var(--ink-2); }
[data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3, [data-testid="stMarkdownContainer"] h4 { color:var(--ink); }

.stTabs [data-baseweb="tab-list"] { border-bottom-color:#1e293b; }
[data-baseweb="tab-highlight"] { background-color:#4f46e5; }
.flag p { color:#fda4af !important; }
.flag h4 { color:#f87171; }
.flag .ev span { color:#fda4af !important; }
.ss-hero { box-shadow:0 10px 30px -12px rgba(0,0,0,.6); }

[data-testid="stCaptionContainer"] p { color:#94a3b8; }
[data-testid="stMarkdownContainer"] hr { border-color:#1e293b; }

[data-testid="stAlert"], [data-testid="stSuccessAlert"], [data-testid="stErrorAlert"],
[data-testid="stWarningAlert"], [data-testid="stInfoAlert"] {
  background:#111a2e; border-color:#1e293b;
}
[data-testid="stAlert"] p, [data-testid="stSuccessAlert"] p, [data-testid="stErrorAlert"] p,
[data-testid="stWarningAlert"] p, [data-testid="stInfoAlert"] p { color:#e2e8f0 !important; }
[data-testid="stAlert"] [data-testid="stMarkdownContainer"] strong, [data-testid="stSuccessAlert"] [data-testid="stMarkdownContainer"] strong,
[data-testid="stErrorAlert"] [data-testid="stMarkdownContainer"] strong, [data-testid="stWarningAlert"] [data-testid="stMarkdownContainer"] strong,
[data-testid="stInfoAlert"] [data-testid="stMarkdownContainer"] strong { color:#f8fafc !important; }

[data-testid="stJson"] { background:#0f172a; border-color:#1e293b; }
[data-testid="stJson"] pre, [data-testid="stJson"] code { color:#cbd5e1 !important; background:transparent !important; }

[data-baseweb="popover"], [data-baseweb="menu"], [data-baseweb="popover"] [role="listbox"] { background:#111a2e !important; }
[data-baseweb="menu-item"], [data-baseweb="popover"] [role="option"], [data-baseweb="popover"] li { color:#e2e8f0 !important; }
[data-baseweb="menu-item"]:hover, [data-baseweb="popover"] [role="option"]:hover, [data-baseweb="popover"] li:hover { background:#1e293b !important; }
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def inject_dark_css():
    st.markdown(DARK_CSS, unsafe_allow_html=True)


def render_typing():
    return (
        '<div class="msg bot">'
        '<span class="typing"><span></span><span></span><span></span></span>'
        "</div>"
    )


def render_loader(text="Scanning for scam signals"):
    return (
        '<div class="ss-loader">'
        '<div class="ring">'
        '<svg viewBox="0 0 100 100">'
        '<circle cx="50" cy="50" r="46" fill="none" stroke="#e2e8f0" stroke-width="6"/>'
        '<circle cx="50" cy="50" r="46" fill="none" stroke="#4f46e5" stroke-width="6" '
        'stroke-linecap="round" stroke-dasharray="72 217"/>'
        "</svg>"
        '<div class="shield">&#128737;</div>'
        "</div>"
        '<div class="bar"><span></span></div>'
        f"<p>{html.escape(text)}<span class='dots'></span></p>"
        "</div>"
    )


def download_link(label, data, file_name, mime, cls="json"):
    import base64

    b64 = base64.b64encode(data).decode("ascii")
    href = f"data:{mime};base64,{b64}"
    return (
        f'<a class="ss-dl {cls}" href="{href}" download="{file_name}" '
        'onclick="this.classList.add(\'done\');setTimeout(()=>this.classList.remove(\'done\'),500)">'
        f'{html.escape(label)}</a>'
    )


def score_meta(score):
    if score >= 0.7:
        return SCAM, "High risk", "red"
    if score >= 0.4:
        return CAUTION, "Medium risk", "amber"
    return SAFE, "Low risk", "green"


def severity_meta(severity):
    if severity >= 0.9:
        return "red", "CRITICAL"
    if severity >= 0.7:
        return "amber", "HIGH"
    return "slate", "MEDIUM"


def _gauge_html(score, color, size):
    pct = max(0.0, min(1.0, score)) * 100
    return (
        f'<div class="gauge" style="--c:{color};--p:{pct:.0f};width:{size}px;height:{size}px">'
        '<div>'
        f'<div class="gval">{score * 100:.0f}%</div>'
        '<div class="glab">scam likelihood</div>'
        "</div>"
        "</div>"
    )


def backend_status(_backend=None):
    try:
        return health()
    except Exception:
        return False


@st.cache_data(ttl=30, show_spinner=False)
def fetch_reports(_limit=15):
    try:
        return recent_reports(_limit).get("reports", [])
    except Exception:
        return []


def render_result(result, source_text="", gauge_size=170, uid=None, show_raw=True):
    if result.get("error"):
        st.error(result.get("message", result.get("error")))
        return

    uid = uid or result.get("hash") or "x"

    score = float(result["score"])
    color, verdict, cls = score_meta(score)
    label = result.get("label", "")

    meta_pills = []
    if result.get("type"):
        meta_pills.append(f'<span class="ss-pill indigo">{html.escape(result["type"])}</span>')
    if result.get("created_at"):
        meta_pills.append(
            f'<span class="ss-pill slate">{html.escape(result["created_at"][:16].replace("T", " "))}</span>'
        )
    if result.get("hash"):
        meta_pills.append(f'<span class="ss-pill slate">id {html.escape(result["hash"])}</span>')

    st.markdown(
        '<div class="ss-card">'
        f'{_gauge_html(score, color, gauge_size)}'
        '<div style="text-align:center;margin-top:12px">'
        f'<span class="ss-pill {cls}">{verdict}</span>'
        f'<span style="margin-left:8px;font-weight:800;color:#0f172a">{html.escape(str(label))}</span>'
        "</div>"
        '<div style="text-align:center;margin-top:10px">' + " ".join(meta_pills) + "</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    c1.markdown(
        f'<div class="stat"><div class="k">Rule score</div>'
        f'<div class="v">{result.get("rule_score", 0) * 100:.0f}%</div></div>',
        unsafe_allow_html=True,
    )
    model = result.get("model_confidence")
    c2.markdown(
        f'<div class="stat"><div class="k">Model confidence</div>'
        f'<div class="v">{model * 100:.0f}%</div></div>' if model is not None
        else '<div class="stat"><div class="k">Model confidence</div><div class="v">n/a</div></div>',
        unsafe_allow_html=True,
    )
    dup = result.get("duplicate_template_score")
    c3.markdown(
        f'<div class="stat"><div class="k">Known template match</div>'
        f'<div class="v">{dup * 100:.0f}%</div></div>' if dup is not None
        else '<div class="stat"><div class="k">Known template match</div><div class="v">n/a</div></div>',
        unsafe_allow_html=True,
    )

    summary = result.get("explanation", {}).get("bullet_points", [])
    if summary:
        bullets = "".join(f"<li>{html.escape(b)}</li>" for b in summary)
        st.markdown(
            f'<div class="ss-card"><h3>Summary</h3><ul style="margin:0;padding-left:20px;color:#334155">{bullets}</ul></div>',
            unsafe_allow_html=True,
        )

    red_flags = result.get("red_flags") or []
    if red_flags:
        items = []
        for flag in red_flags:
            sev_cls, sev_label = severity_meta(float(flag.get("severity", 0.5)))
            evidence = "".join(
                f"<span>{html.escape(str(e))}</span>" for e in (flag.get("evidence") or [])
            )
            items.append(
                '<div class="flag">'
                '<div style="display:flex;justify-content:space-between;align-items:center;gap:10px">'
                f'<h4>{html.escape(str(flag.get("name", "")))}</h4>'
                f'<span class="ss-pill {sev_cls}">{sev_label}</span>'
                "</div>"
                f'<p style="margin:6px 0 0;color:#7f1d1d;font-size:.9rem">{html.escape(str(flag.get("explanation", "")))}</p>'
                f'<div class="ev">{evidence}</div>'
                "</div>"
            )
        st.markdown(
            f'<div class="ss-card"><h3>Detected red flags ({len(red_flags)})</h3>{"".join(items)}</div>',
            unsafe_allow_html=True,
        )
    elif not summary:
        st.success("No known scam red-flag patterns matched this posting.")

    highlighted = result.get("highlighted_text")
    if highlighted:
        st.markdown(
            '<div class="ss-card"><h3>Highlighted text</h3>'
            f'<div style="line-height:1.7;color:#334155">{highlighted}</div></div>',
            unsafe_allow_html=True,
        )

    ocr_text = result.get("ocr_text")
    if ocr_text:
        st.markdown(
            '<div class="ss-card"><h3>Text read from image (OCR)</h3>'
            f'<div style="line-height:1.6;color:#475569;font-size:.9rem">{html.escape(str(ocr_text))}</div></div>',
            unsafe_allow_html=True,
        )

    payload_text = source_text or ocr_text or ""
    st.markdown(
        '<div class="ss-ready"><span class="spark">&#10024;</span> Analysis ready - download your report below.</div>',
        unsafe_allow_html=True,
    )
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("Report to community", type="primary", use_container_width=True, key=f"report_{uid}"):
            if not payload_text.strip():
                st.warning("Nothing to report.")
            else:
                try:
                    data = report_scam(
                        payload_text,
                        notes="Reported from ScamShield app",
                        source="community-report",
                    )
                    if data.get("status") == "saved":
                        st.toast("Reported. Thank you for keeping the community safe.")
                    else:
                        st.warning(data.get("message", "Could not save the report."))
                except Exception:
                    st.error("Could not save the report.")
    with c2:
        st.markdown(
            download_link(
                "Download JSON",
                json.dumps(result, indent=2, ensure_ascii=False).encode("utf-8"),
                f"scamshield_{result.get('hash', 'analysis')}.json",
                "application/json",
                "json",
            ),
            unsafe_allow_html=True,
        )
    with c3:
        pdf_bytes = None
        pdf_error = None
        try:
            pdf_bytes = build_pdf_report(result, payload_text)
        except Exception as exc:
            pdf_error = exc
        if pdf_bytes:
            st.markdown(
                download_link(
                    "Download PDF report",
                    pdf_bytes,
                    f"scamshield_report_{result.get('hash', 'analysis')}.pdf",
                    "application/pdf",
                    "pdf",
                ),
                unsafe_allow_html=True,
            )
        else:
            st.caption(f"PDF report unavailable: {pdf_error or 'unknown error'}. JSON works.")
    with c4:
        if st.button("New analysis", use_container_width=True, key=f"new_{uid}"):
            st.session_state.last_result = None
            st.rerun()

    if show_raw:
        with st.expander("Raw analysis (JSON)"):
            st.code(json.dumps(result, indent=2, ensure_ascii=False), language="json")


def render_chat(messages):
    if not messages:
        st.caption(
            "Ask ScamShield anything about job-posting scams. Answers come from a Gemini-powered "
            "assistant (with a local knowledge base as fallback)."
        )
    for message in messages:
        cls = "user" if message["role"] == "user" else "bot"
        source = message.get("source")
        source_tag = ""
        if source == "llm":
            source_tag = '<div class="msg-src">answered by Gemini</div>'
        elif source == "faq":
            source_tag = '<div class="msg-src">local knowledge base</div>'
        elif source == "offline":
            source_tag = '<div class="msg-src">backend offline</div>'
        st.markdown(
            f'<div class="msg {cls}"><div>{html.escape(str(message["text"]))}</div>{source_tag}</div>',
            unsafe_allow_html=True,
        )


def render_reports(reports):
    if not reports:
        st.info("No reports yet. Reports you save from an analysis appear here.")
        return
    st.caption(f"{len(reports)} recent reports")
    for rep in reports:
        source = html.escape(str(rep.get("source", "unknown")))
        created = html.escape(str(rep.get("created_at", ""))[:16].replace("T", " "))
        src_cls = "indigo" if rep.get("source") == "community-report" else "slate"
        pill = f'<span class="ss-pill {src_cls}">{source}</span>'
        pill += f' <span class="ss-pill slate">{created}</span>'
        if rep.get("contact"):
            pill += f' <span class="ss-pill amber">contact: {html.escape(str(rep["contact"]))}</span>'
        body = html.escape(str(rep.get("text", "")))
        notes = rep.get("notes")
        notes_html = (
            f'<p style="color:#64748b;font-size:.85rem;margin:8px 0 0">{html.escape(str(notes))}</p>'
            if notes
            else ""
        )
        st.markdown(
            f'<div class="ss-card">{pill}<p style="margin:10px 0 0;color:#1e293b;line-height:1.55">{body}</p>{notes_html}</div>',
            unsafe_allow_html=True,
        )


def render_history(history):
    if not history:
        st.info("No analyses yet in this session. Run one from the Analyze tabs.")
        return
    st.caption(f"{len(history)} analysis(ies) this session")
    for entry in reversed(history):
        res = entry.get("result", {})
        score = float(res.get("score", 0))
        _, verdict, cls = score_meta(score)
        label = res.get("label", "")
        kind = html.escape(str(entry.get("type", "")))
        created = html.escape(str(entry.get("time", ""))[:16].replace("T", " "))
        head = (
            f'<span class="ss-pill {cls}">{verdict} - {score * 100:.0f}%</span> '
            f'<span style="color:#94a3b8;font-size:.8rem">{kind} - {created}</span>'
        )
        with st.expander(f"{label} - {score * 100:.0f}% likely scam"):
            st.markdown(head, unsafe_allow_html=True)
            render_result(res, entry.get("source_text", ""), gauge_size=140, uid=f"hist_{entry.get('time')}", show_raw=False)
