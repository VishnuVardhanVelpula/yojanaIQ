"""
app.py — Conversational chatbot UI for AP Scheme Advisor
Run: streamlit run app.py
"""

import streamlit as st
import json
import os
from rag import run_rag
from rule_filter import rule_filter

# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="YojanaIQ",
    page_icon="✨",
    layout="centered",
)

# ─── Load schemes ─────────────────────────────────────────────────────────────
base_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(base_dir, "data", "schemes.json"), encoding="utf-8") as f:
    ALL_SCHEMES = json.load(f)
SCHEME_LOOKUP = {s["id"]: s for s in ALL_SCHEMES}

# ─── Official website links per scheme id ─────────────────────────────────────
SCHEME_URLS = {
    "amma_vodi":            "https://ammavodi.ap.gov.in",
    "vidya_deevena":        "https://apsche.ap.gov.in",
    "vasathi_deevena":      "https://apsche.ap.gov.in",
    "vidya_kanuka":         "https://jaganannavidyakanuka.ap.gov.in",
    "rythu_bharosa":        "https://apagrisnet.gov.in",
    "pm_kisan":             "https://pmkisan.gov.in",
    "free_crop_insurance":  "https://apagrisnet.gov.in",
    "ysr_cheyutha":         "https://ysrcheyutha.ap.gov.in",
    "sunna_vaddi":          "https://ysrsunnavaddi.ap.gov.in",
    "aarogyasri":           "https://aarogyasri.ap.gov.in",
    "jagananna_suraksha":   "https://jaganannasuraksha.ap.gov.in",
    "ysr_housing":          "https://navaratnalu.ap.gov.in",
    "ysr_pension":          "https://ysrpensionkanuka.ap.gov.in",
    "jagananna_thodu":      "https://jaganannatodustores.ap.gov.in",
    "sc_corporation":       "https://apscfc.ap.gov.in",
    "st_corporation":       "https://apstfc.ap.gov.in",
    "bc_corporation":       "https://apbcfc.ap.gov.in",
    "minority_scholarship": "https://minorities.ap.gov.in",
    "pmay_urban":           "https://pmaymis.gov.in",
    "ntr_bharosa":          "https://ysrpensionkanuka.ap.gov.in",
    "nethanna_nestham":     "https://ysrnethananestham.ap.gov.in",
    "vahana_mitra":         "https://ysrvahanamitra.ap.gov.in",
    "jagananna_chedodu":    "https://jaganannatodustores.ap.gov.in",
    "kapu_nestham":         "https://ysrkapunestham.ap.gov.in",
    "matsyakara_bharosa":   "https://apfisheries.gov.in",
    "kalyanamasthu":        "https://ysrkalyanamasthu.ap.gov.in",
    "aadabidda_nidhi":      "https://navaratnalu.ap.gov.in",
    "talliki_vandanam":     "https://tallikikivandanam.ap.gov.in",
    "deepam":               "https://navaratnalu.ap.gov.in",
    "annadatha_sukhibhava": "https://apagrisnet.gov.in",
    "nirudyoga_bruthi":     "https://navaratnalu.ap.gov.in",
    "apsrtc_free_bus":      "https://apsrtc.ap.gov.in",
}

# ─── Conversation flow ────────────────────────────────────────────────────────
FLOW = [
    {
        "key":      "gender",
        "question": "✨ Namaskaram! I'm **YojanaIQ**.\n\nI will intuitively match you with AP government welfare programs using AI.\n\nFirst, what is your **gender**?",
        "options":  ["👩 Female", "👨 Male", "🧑 Other"],
        "map":      {"👩 Female": "female", "👨 Male": "male", "🧑 Other": "other"},
    },
    {
        "key":      "age",
        "question": "Got it! What is your **age group**?",
        "options":  ["Under 18", "18–25", "26–40", "41–60", "60+"],
        "map":      {"Under 18": 15, "18–25": 22, "26–40": 33, "41–60": 50, "60+": 65},
    },
    {
        "key":      "caste",
        "question": "What is your **caste category**?",
        "options":  ["🟦 SC", "🟩 ST", "🟨 BC", "⬜ OC", "🕌 Minority"],
        "map":      {"🟦 SC": "SC", "🟩 ST": "ST", "🟨 BC": "BC", "⬜ OC": "OC", "🕌 Minority": "Minority"},
    },
    {
        "key":      "religion",
        "question": "What is your **religion**?",
        "options":  ["🕉️ Hindu", "☪️ Muslim", "✝️ Christian", "Other"],
        "map":      {"🕉️ Hindu": "hindu", "☪️ Muslim": "muslim", "✝️ Christian": "christian", "Other": "other"},
    },
    {
        "key":      "occupation",
        "question": "What is your **occupation**?",
        "options":  ["🎓 Student", "🌾 Farmer", "🧵 Weaver", "🐟 Fisher",
                     "🚗 Auto Driver", "👷 Daily Wage Worker", "🏪 Self Employed", "🔍 Unemployed"],
        "map":      {
            "🎓 Student": "student", "🌾 Farmer": "farmer", "🧵 Weaver": "weaver",
            "🐟 Fisher": "fisher", "🚗 Auto Driver": "auto driver",
            "👷 Daily Wage Worker": "daily wage worker",
            "🏪 Self Employed": "self employed", "🔍 Unemployed": "unemployed",
        },
    },
    {
        "key":      "income",
        "question": "What is your approximate **annual family income**?",
        "options":  ["Below ₹1L", "₹1L – ₹2L", "₹2L – ₹5L", "₹5L – ₹10L", "Above ₹10L"],
        "map":      {
            "Below ₹1L": 80000, "₹1L – ₹2L": 150000,
            "₹2L – ₹5L": 350000, "₹5L – ₹10L": 750000, "Above ₹10L": 1200000,
        },
    },
    {
        "key":      "flags",
        "question": "Last question! Do any of these apply to you?\n*(Select all that apply, then tap **Done**)*",
        "options":  ["Widow", "Disabled / Differently Abled", "SHG Member",
                     "BPL Card Holder", "Pregnant / New Mother", "Senior Citizen (60+)"],
        "multi":    True,
        "map":      {
            "Widow": "widow",
            "Disabled / Differently Abled": "disabled",
            "SHG Member": "shg_member",
            "BPL Card Holder": "bpl",
            "Pregnant / New Mother": "pregnant",
            "Senior Citizen (60+)": "senior_citizen",
        },
    },
]

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800&family=Outfit:wght@300;400;600;700&display=swap');

html, body, [class*="css"], .stApp { font-family: 'Outfit', sans-serif; }

/* Animated Futuristic Background */
.stApp {
    background: radial-gradient(circle at top left, #0b132b, #1c2541, #001524);
    background-size: 200% 200%;
    animation: gradientBG 15s ease infinite;
    min-height: 100vh;
}
@keyframes gradientBG {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

.block-container { padding-top: 2rem !important; max-width: 800px !important; }

/* Header with neon liquid glow */
.chat-header { 
    text-align: center; 
    padding: 1.5rem 0 1.5rem; 
    margin-bottom: 2rem;
    border-bottom: 1px solid rgba(0, 255, 255, 0.1);
    background: rgba(11, 19, 43, 0.4);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border-radius: 20px;
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
}
.chat-header h1 { 
    font-family: 'Orbitron', sans-serif;
    font-size: 3rem; 
    font-weight: 800; 
    margin: 0; 
    background: linear-gradient(90deg, #00f2fe 0%, #4facfe 50%, #00f2fe 100%);
    background-size: 200% auto;
    color: #fff;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: shine 3s linear infinite;
    text-shadow: 0px 4px 15px rgba(0, 242, 254, 0.1);
}
@keyframes shine {
    to { background-position: 200% center; }
}
.chat-header p { font-size: 0.95rem; color: #a1b2d1; margin: 8px 0 0; letter-spacing: 2px; text-transform: uppercase; font-weight: 600;}

/* Bot Bubble Glassmorphism */
.bot-bubble {
    background: rgba(28, 37, 65, 0.4);
    backdrop-filter: blur(15px);
    -webkit-backdrop-filter: blur(15px);
    border: 1px solid rgba(0, 242, 254, 0.2);
    border-radius: 4px 20px 20px 20px;
    padding: 16px 22px;
    margin: 10px 0 5px;
    color: #edf2f4;
    font-size: 1rem;
    line-height: 1.6;
    max-width: 85%;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    position: relative;
}

/* User Bubble Premium */
.user-bubble {
    background: linear-gradient(135deg, #00c6ff, #0072ff);
    border-radius: 20px 4px 20px 20px;
    padding: 12px 20px;
    margin: 5px 0 5px auto;
    color: #fff;
    font-size: 1rem;
    font-weight: 600;
    max-width: 70%;
    text-align: right;
    box-shadow: 0 4px 15px rgba(0, 114, 255, 0.4);
    width: fit-content;
    display: block;
}

/* Scheme Card Premium Holographic */
.scheme-card {
    background: rgba(11, 19, 43, 0.6);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-left: 4px solid #00f2fe;
    border-radius: 16px;
    padding: 18px 20px;
    margin: 10px 0;
    color: #e2e8f0;
    transition: all 0.3s ease;
}
.scheme-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 25px rgba(0, 242, 254, 0.15);
    border-color: rgba(0, 242, 254, 0.3);
}
.scheme-card h4 { color: #edf2f4; margin:0 0 8px; font-size:1.1rem; font-weight:700; font-family: 'Orbitron', sans-serif; letter-spacing: 0.5px;}
.scheme-card .benefit {
    background: rgba(0, 242, 254, 0.1);
    border-left: 3px solid #00f2fe;
    padding: 8px 12px;
    border-radius: 0 8px 8px 0;
    font-size:0.9rem;
    color:#4facfe;
    margin: 8px 0;
    font-weight: 600;
}
.scheme-card .cat-tag {
    display:inline-block;
    background: linear-gradient(90deg, #1c2541, #0b132b);
    border: 1px solid #4facfe;
    color:#00f2fe;
    border-radius:999px;
    padding:4px 12px;
    font-size:0.75rem;
    font-weight:600;
    margin-bottom:8px;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.scheme-card .apply { font-size:0.85rem; color:#8d99ae; margin-top:6px; }
.scheme-card a { color:#00c6ff; font-size:0.85rem; text-decoration:none; display: inline-block; margin-top: 8px; font-weight: 600;}
.scheme-card a:hover { text-decoration:underline; color: #fff;}

/* Quick reply buttons (Futuristic) */
.stButton > button {
    background: rgba(28, 37, 65, 0.5) !important;
    backdrop-filter: blur(4px) !important;
    -webkit-backdrop-filter: blur(4px) !important;
    border: 1px solid rgba(0, 242, 254, 0.3) !important;
    color: #4facfe !important;
    border-radius: 999px !important;
    padding: 10px 20px !important;
    font-size: 0.95rem !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 600 !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #00f2fe, #4facfe) !important;
    border-color: #00f2fe !important;
    color: #fff !important;
    transform: translateY(-2px) scale(1.02) !important;
    box-shadow: 0 8px 20px rgba(0, 242, 254, 0.3) !important;
}
.stButton > button:focus:not(:active) { box-shadow: 0 0 0 3px rgba(0, 242, 254, 0.4) !important; }

/* Selected Button State */
.sel-btn > button, .sel-btn > button:hover {
    background: linear-gradient(135deg, #00c6ff, #0072ff) !important;
    border-color: #0072ff !important;
    color: #fff !important;
    box-shadow: 0 4px 15px rgba(0, 114, 255, 0.4) !important;
}

.section-hint {
    font-size:0.85rem; color:#8d99ae;
    margin: 15px 0 8px; padding-left:2px;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: 600;
}

/* Input Area */
.stChatInput textarea {
    background: rgba(11, 19, 43, 0.7) !important;
    backdrop-filter: blur(10px) !important;
    -webkit-backdrop-filter: blur(10px) !important;
    border: 1px solid rgba(79, 172, 254, 0.4) !important;
    color: #fff !important;
    border-radius: 16px !important;
    font-size: 1rem !important;
    padding: 12px 16px !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2) !important;
}
.stChatInput textarea:focus {
    border-color: #00f2fe !important;
    box-shadow: 0 0 15px rgba(0, 242, 254, 0.2) !important;
}
hr { border-color: rgba(79, 172, 254, 0.15) !important; margin: 2rem 0 !important; }

/* Hide Streamlit elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="chat-header">
  <h1>YojanaIQ</h1>
  <p>✨ AI-Powered Welfare Scheme Matching</p>
</div>
""", unsafe_allow_html=True)

# ─── Session state ────────────────────────────────────────────────────────────
defaults = {
    "messages":       [],
    "step":           0,
    "profile":        {},
    "multi_sel":      set(),
    "done":           False,
    "matched_schemes": [],   # list of full scheme dicts
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

def bot(content, mtype="text", cards=None):
    st.session_state.messages.append(
        {"role": "bot", "content": content, "type": mtype, "cards": cards or []}
    )

def usr(content):
    st.session_state.messages.append({"role": "user", "content": content})

# ─── RAG runner (called after last flow step) ─────────────────────────────────
def _run_rag_and_finish():
    p = st.session_state.profile
    p.setdefault("flags", [])
    p.setdefault("religion", "hindu")

    bot("⏳ Checking all 32 AP government schemes for your profile...")

    matched, _ = rule_filter(p)
    st.session_state.matched_schemes = matched

    if not matched:
        bot(
            "😔 No schemes currently match your profile.\n\n"
            "Please visit your nearest **Ward Secretariat** or **MeeSeva centre** "
            "for personalised guidance from a government officer."
        )
        st.session_state.done = True
        return

    result = run_rag(
        p,
        user_query="What schemes am I eligible for? Give a clear summary of each with benefits."
    )

    n = len(matched)
    bot(f"🎉 Great news! You are eligible for **{n} scheme{'s' if n > 1 else ''}**!\n\nHere's a quick overview of each:")

    cards = [
        {"id": s["id"], "name": s["name"],
         "category": s["category"], "benefits": s["benefits"], "apply_at": s["apply_at"]}
        for s in matched
    ]
    bot("", mtype="schemes", cards=cards)

    bot(
        result["answer"] +
        "\n\n---\n👇 **Tap any scheme above for full details** (eligibility reason, documents needed, step-by-step application), "
        "or type your own question!"
    )
    st.session_state.done = True

# First message
if not st.session_state.messages:
    bot(FLOW[0]["question"])

# ─── Render history ───────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    if msg["role"] == "bot":
        if msg["type"] == "schemes":
            st.markdown(f'<div class="bot-bubble">{msg["content"]}</div>', unsafe_allow_html=True)
            for s in msg["cards"]:
                url = SCHEME_URLS.get(s["id"], "https://ap.gov.in")
                st.markdown(f"""
<div class="scheme-card">
  <div class="cat-tag">{s['category']}</div>
  <h4>✅ {s['name']}</h4>
  <div class="benefit">💰 {s['benefits']}</div>
  <div class="apply">📍 {s['apply_at']}</div>
  <div style="margin-top:8px">
    <a href="{url}" target="_blank">🔗 Official Website →</a>
  </div>
</div>""", unsafe_allow_html=True)
        else:
            html = msg["content"].replace("\n", "<br>")
            st.markdown(f'<div class="bot-bubble">{html}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="user-bubble">{msg["content"]}</div>', unsafe_allow_html=True)

# ─── Active input area ────────────────────────────────────────────────────────
if not st.session_state.done and st.session_state.step < len(FLOW):
    step = FLOW[st.session_state.step]
    is_multi = step.get("multi", False)

    st.markdown('<div class="section-hint">👇 Tap an option to continue</div>', unsafe_allow_html=True)

    if is_multi:
        # Multi-select toggles
        cols = st.columns(3)
        for i, opt in enumerate(step["options"]):
            sel = opt in st.session_state.multi_sel
            label = ("✅ " if sel else "") + opt
            if cols[i % 3].button(label, key=f"ms_{i}"):
                if sel:
                    st.session_state.multi_sel.discard(opt)
                else:
                    st.session_state.multi_sel.add(opt)
                st.rerun()

        st.markdown("")
        c1, c2 = st.columns(2)
        if c1.button("✅ Done — These apply", key="ms_done"):
            sel_list = list(st.session_state.multi_sel)
            flags = [step["map"][f] for f in sel_list if step["map"].get(f)]
            usr(", ".join(sel_list) if sel_list else "None selected")
            st.session_state.profile["flags"] = flags
            st.session_state.multi_sel = set()
            st.session_state.step += 1
            _run_rag_and_finish()
            st.rerun()

        if c2.button("⏭️ None apply to me", key="ms_none"):
            usr("None of these apply")
            st.session_state.profile["flags"] = []
            st.session_state.multi_sel = set()
            st.session_state.step += 1
            _run_rag_and_finish()
            st.rerun()

    else:
        cols = st.columns(min(len(step["options"]), 4))
        for i, opt in enumerate(step["options"]):
            if cols[i % len(cols)].button(opt, key=f"opt_{st.session_state.step}_{i}"):
                usr(opt)
                st.session_state.profile[step["key"]] = step["map"][opt]
                st.session_state.step += 1
                if st.session_state.step < len(FLOW):
                    bot(FLOW[st.session_state.step]["question"])
                st.rerun()

elif st.session_state.done:
    # ── Scheme detail buttons ──────────────────────────────────────────────────
    if st.session_state.matched_schemes:
        st.markdown('<div class="section-hint">📋 Tap a scheme for full details, or type your question below</div>', unsafe_allow_html=True)
        cols = st.columns(2)
        for i, s in enumerate(st.session_state.matched_schemes[:8]):
            if cols[i % 2].button(f"📋 {s['name']}", key=f"det_{i}"):
                usr(f"Tell me more about {s['name']}")
                with st.spinner("Getting details..."):
                    query = (
                        f"Explain {s['name']} in detail. "
                        f"Why is this specific person eligible? "
                        f"What exact benefit amount or service will they receive? "
                        f"Step-by-step application process? "
                        f"What documents are needed? Any tips or deadlines?"
                    )
                    result = run_rag(st.session_state.profile, user_query=query)
                bot(result["answer"])
                st.rerun()

    # ── Free text ──────────────────────────────────────────────────────────────
    user_input = st.chat_input("Ask anything about your schemes...")
    if user_input:
        usr(user_input)
        with st.spinner("Thinking..."):
            result = run_rag(st.session_state.profile, user_query=user_input)
        bot(result["answer"])
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Start Over", key="restart"):
        for k in list(defaults.keys()):
            del st.session_state[k]
        st.rerun()

