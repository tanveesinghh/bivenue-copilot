import os
import textwrap
from typing import List, Dict, Any

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from tavily import TavilyClient

# -----------------------------
# 🔐 Environment
# -----------------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
tavily_client = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None

# -----------------------------
# 🎨 Page Config
# -----------------------------
st.set_page_config(
    page_title="Bivenue – Finance AI Copilot",
    page_icon="📊",
    layout="wide",
)

# -----------------------------
# 🎨 Global Styling (Perplexity-inspired)
# -----------------------------
PAGE_CSS = """
<style>
body {
    background-color: #f5f7fb;
}

/* Center main content */
.block-container {
    max-width: 980px;
    margin: 0 auto;
    padding-top: 3rem !important;
}

/* Sidebar – minimal and light */
[data-testid="stSidebar"] {
    background-color: #f1f5f9 !important;
    border-right: 1px solid #e2e8f0;
}
[data-testid="stSidebar"] * {
    font-size: 0.9rem !important;
    color: #0f172a !important;
}

/* Headings */
h1, h2, h3, h4 {
    color: #0f172a !important;
}

/* Centered title + subtitle */
.biv-header-title {
    text-align: center;
    font-size: 2.2rem;
    font-weight: 600;
    margin-bottom: 0.25rem;
}
.biv-header-subtitle {
    text-align: center;
    color: #6b7280;
    font-size: 0.95rem;
    margin-bottom: 1.5rem;
}
.biv-divider {
    border: 0;
    height: 1px;
    background-color: #e5e7eb;
    margin: 0 0 1.8rem 0;
}

/* Big rounded search bar */
.biv-search-wrapper {
    display: flex;
    justify-content: center;
    margin-bottom: 1.2rem;
}
.biv-search-inner {
    width: 100%;
    max-width: 720px;
    padding: 0.3rem 0.9rem;
    border-radius: 999px;
    border: 1px solid #cbd5f5;
    background-color: #ffffff;
    box-shadow: 0 8px 20px rgba(15, 23, 42, 0.06);
}
.biv-search-inner input {
    border: none !important;
    box-shadow: none !important;
}
.biv-search-inner div[data-baseweb="input"] {
    background-color: transparent !important;
}


/* Primary buttons */
.stButton > button {
    border-radius: 999px;
    background-color: #0f766e !important;
    color: #ffffff !important;
    border: none !important;
    padding: 0.35rem 1.3rem !important;
    font-weight: 500;
}
.stButton > button:hover {
    background-color: #115e59 !important;
}

/* Answer card */
.biv-card {
    border-radius: 16px;
    padding: 1.4rem 1.5rem;
    background: #ffffff;
    border: 1px solid rgba(15, 23, 42, 0.06);
    box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
    margin-top: 1rem;
}
.biv-tag {
    font-size: 0.75rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #64748b;
    margin-bottom: 0.4rem;
}

/* Sources */
.biv-source {
    font-size: 0.85rem;
    color: #374151;
    margin-bottom: 0.35rem;
}
.biv-source a {
    color: #0f766e;
    text-decoration: none;
}
.biv-source a:hover {
    text-decoration: underline;
}
</style>
"""

st.markdown(PAGE_CSS, unsafe_allow_html=True)

# -----------------------------
# 🧠 OpenAI helper
# -----------------------------
def ask_gpt(
    messages: List[Dict[str, str]],
    model: str = "gpt-4.1-mini",
    temperature: float = 0.35,
    max_tokens: int = 1000,
) -> str:
    if not client:
        return "⚠️ OpenAI API key not found in Streamlit Secrets."
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


# -----------------------------
# 🌐 Web search (research)
# -----------------------------
def tavily_search(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    if not tavily_client:
        return []
    response = tavily_client.search(
        query=query,
        max_results=max_results,
        search_depth="advanced",
    )
    return response.get("results", [])


def build_citation_context(results: List[Dict[str, Any]]) -> str:
    lines = []
    for i, r in enumerate(results):
        idx = i + 1
        title = r.get("title", f"Source {idx}")
        url = r.get("url", "")
        content = r.get("content", "")
        snippet = textwrap.shorten(content, width=400, placeholder="…")
        lines.append(f"[{idx}] {title}\nURL: {url}\nSummary: {snippet}")
    return "\n\n".join(lines)


def answer_with_citations(query: str) -> Dict[str, Any]:
    results = tavily_search(query, max_results=6)
    context = build_citation_context(results) if results else "No web data found."

    system_msg = {
        "role": "system",
        "content": (
            "You are Bivenue, a factual, research-oriented AI assistant. "
            "Use citations like [1], [2] that refer to the provided sources."
        ),
    }
    user_msg = {
        "role": "user",
        "content": (
            f"Question: {query}\n\n"
            f"Use these sources where helpful:\n{context}\n\n"
            f"If no sources are relevant, answer from general knowledge and skip citations."
        ),
    }

    answer = ask_gpt([system_msg, user_msg], model="gpt-4.1-mini", max_tokens=1400)
    return {"answer": answer, "sources": results}


# -----------------------------
# 💼 Finance Transformation
# -----------------------------
def finance_transform_answer(task_type: str, context: str) -> str:
    system = {
        "role": "system",
        "content": (
            "You are a Finance Transformation Director. Provide structured, "
            "practical recommendations for R2R, P2P, O2C, Close, Audit, and "
            "automation roadmaps."
        ),
    }
    user = {
        "role": "user",
        "content": f"Focus area: {task_type}\n\nBusiness context:\n{context}",
    }
    return ask_gpt([system, user], model="gpt-4.1", max_tokens=1800)


# -----------------------------
# 🧾 SOP Builder
# -----------------------------
def build_sop(name: str, context: str, steps: str) -> str:
    system = {
        "role": "system",
        "content": "You are a Finance Process Excellence Lead. Create execution-ready SOPs.",
    }
    user = {
        "role": "user",
        "content": f"""
Create an SOP.

Process name: {name}

Business context:
{context}

Steps:
{steps}

Include:
- Purpose
- Scope
- Roles & responsibilities
- Detailed procedure
- Controls
- KPIs
- Automation opportunities
""",
    }
    return ask_gpt([system, user], model="gpt-4.1", max_tokens=2000)


# -----------------------------
# 🤖 Automation & Time Study
# -----------------------------
def automation_analysis(desc: str, metrics: Dict[str, Any]) -> str:
    system = {
        "role": "system",
        "content": "You are a Lean Six Sigma Black Belt and Automation Director.",
    }
    user = {
        "role": "user",
        "content": f"""
Analyze this finance / shared-services process for automation:

Description:
{desc}

Metrics:
{metrics}

Provide:
- Key wastes
- Automation opportunities
- Estimated impact (FTE, cycle time)
- Quick wins
- Roadmap
""",
    }
    return ask_gpt([system, user], model="gpt-4.1", max_tokens=1600)


# -----------------------------
# 💰 Cost–Benefit Analysis
# -----------------------------
def cost_benefit_report(
    project_name: str,
    description: str,
    horizon_years: int,
    currency: str,
    one_time_cost: float,
    annual_cost: float,
    annual_benefit: float,
    discount_rate: float,
    notes: str,
) -> str:
    system = {
        "role": "system",
        "content": (
            "You are a senior Finance Manager and Transformation Lead. "
            "You prepare clear, executive-friendly Cost–Benefit Analysis (CBA) reports. "
            "Use the numbers provided to calculate simple metrics, but clearly say "
            "they are directional estimates, not audited financials."
        ),
    }

    user_content = f"""
Project name: {project_name}
Description: {description}

Time horizon (years): {horizon_years}
Currency: {currency}

Estimated one-time investment: {one_time_cost} {currency}
Estimated recurring annual cost: {annual_cost} {currency}
Estimated recurring annual benefit: {annual_benefit} {currency}
Discount rate (for NPV intuition): {discount_rate} %

Additional notes / assumptions from user:
{notes}

Using this information, prepare a Cost–Benefit Analysis report with the following structure:

1. Executive summary (2–3 bullet points for CFO)
2. Key assumptions (time horizon, currency, discount rate, what is included/excluded)
3. Cost breakdown
4. Benefit breakdown
5. Directional financial view:
   - Simple annual net benefit
   - Rough payback period (years)
   - Simple ROI %
   - High-level NPV / value narrative (no need for detailed table, just qualitative based on inputs)
6. Strategic / qualitative benefits (if any)
7. Risks & sensitivities
8. Recommendation (Go / No-Go / Pilot first), stated clearly.

If numbers are missing or zero, still give a qualitative analysis and call out that figures were not provided.
"""

    user = {"role": "user", "content": user_content}

    return ask_gpt([system, user], model="gpt-4.1", max_tokens=2000)


# -----------------------------
# 🧠 SAP Copilot
# -----------------------------
def sap_copilot_answer(question: str, module: str) -> str:
    system = {
        "role": "system",
        "content": (
            "You are an SAP S/4HANA FI/CO Architect. Explain root causes, T-codes, "
            "and process flows in clear, practical language."
        ),
    }
    user = {
        "role": "user",
        "content": f"Module: {module}\n\nQuestion:\n{question}",
    }
    return ask_gpt([system, user], model="gpt-4.1", max_tokens=1600)


# -----------------------------
# 📊 Deck Generator
# -----------------------------
def build_exec_deck(deck_type: str, context: str) -> str:
    system = {
        "role": "system",
        "content": "You are a McKinsey-style consultant. Create slide-by-slide deck outlines.",
    }
    user = {
        "role": "user",
        "content": f"Create a 12-slide deck: {deck_type}\n\nContext:\n{context}",
    }
    return ask_gpt([system, user], model="gpt-4.1-mini", max_tokens=1800)


# -----------------------------
# UI helpers
# -----------------------------
def render_answer(content: str, title: str):
    st.markdown(
        f"""
        <div class="biv-card">
            <div class="biv-tag">{title}</div>
            <div style="margin-top:0.5rem;">{content}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sources(sources: List[Dict[str, Any]]):
    if not sources:
        return
    st.markdown("#### Sources")
    for i, src in enumerate(sources):
        st.markdown(
            f"""
            <div class="biv-source">
                <strong>[{i+1}] {src.get("title","")}</strong><br/>
                <a href="{src.get("url","")}" target="_blank">{src.get("url","")}</a>
            </div>
            """,
            unsafe_allow_html=True,
        )


# -----------------------------
# MAIN APP
# -----------------------------
def main():
    # Sidebar – professional text labels only
    st.sidebar.title("Bivenue – Finance AI")
    st.sidebar.write("Research • Transformation • Automation • SAP")

    mode = st.sidebar.radio(
        "Mode",
        [
            "Research",
            "Finance Transformation",
            "SOP Builder",
            "Automation Analysis",
            "Cost–Benefit Analysis",
            "SAP Copilot",
            "Deck Generator",
        ],
    )

    # Centered header
    st.markdown(
        "<div class='biv-header-title'>Bivenue – Finance AI Copilot</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='biv-header-subtitle'>AI research and copilots for R2R, P2P, O2C, Close, Automation, and SAP.</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<hr class='biv-divider' />", unsafe_allow_html=True)

    # Route to sections
    if mode == "Research":
        research_ui()
    elif mode == "Finance Transformation":
        finance_ui()
    elif mode == "SOP Builder":
        sop_ui()
    elif mode == "Automation Analysis":
        automation_ui()
    elif mode == "Cost–Benefit Analysis":
        cba_ui()
    elif mode == "SAP Copilot":
        sap_ui()
    elif mode == "Deck Generator":
        deck_ui()


# -----------------------------
# UI Pages
# -----------------------------
def research_ui():
    st.subheader("Research Mode")

    # --- Perplexity-style centered search bar (single input) ---
    st.markdown(
        "<div class='biv-search-wrapper'><div class='biv-search-inner'>",
        unsafe_allow_html=True,
    )

    query = st.text_input(
        label="",
        placeholder="Ask anything. Type your finance, automation, or SAP question.",
        label_visibility="collapsed",       # 👈 hides the label so no extra grey bar
        key="research_query",
    )

    st.markdown("</div></div>", unsafe_allow_html=True)

    # --- Centered Search button only ---
    col = st.columns([3, 1, 3])[1]
    run = col.button("Search")

    if not run:
        return

    if not query.strip():
        st.warning("Please enter a question.")
        return

    with st.spinner("Researching…"):
        res = answer_with_citations(query)

    # --- Full-width, nicely centered answer card ---
    st.markdown("<div style='max-width: 720px; margin: 1.5rem auto;'>", unsafe_allow_html=True)
    render_answer(res["answer"], "Research Answer")
    render_sources(res["sources"])
    st.markdown("</div>", unsafe_allow_html=True)
def finance_ui():
    st.subheader("Finance Transformation")

    task = st.selectbox(
        "Focus area",
        ["R2R", "P2P", "O2C", "Close", "Audit", "Automation roadmap"],
    )
    context = st.text_area(
        "Describe your current state, pain points, and objectives:",
        height=200,
    )

    if st.button("Generate transformation plan"):
        if not context.strip():
            st.warning("Please describe your situation.")
            return
        with st.spinner("Designing transformation plan…"):
            ans = finance_transform_answer(task, context)
        render_answer(ans, "Transformation Plan")


def sop_ui():
    st.subheader("SOP Builder")

    name = st.text_input("Process name")
    context = st.text_area("Business context (systems, region, compliance, etc.)", height=140)
    steps = st.text_area("Steps (one per line)", height=200)

    if st.button("Generate SOP"):
        if not name.strip() or not steps.strip():
            st.warning("Please add at least a process name and some steps.")
            return
        with st.spinner("Creating SOP…"):
            ans = build_sop(name, context, steps)
        render_answer(ans, "Standard Operating Procedure")


def automation_ui():
    st.subheader("Automation Analysis")

    desc = st.text_area("Describe the process (scope, systems, volume, issues):", height=200)

    col1, col2, col3 = st.columns(3)
    with col1:
        fte = st.number_input("FTE", min_value=0.0, step=0.5)
    with col2:
        vol = st.number_input("Volume per month", min_value=0, step=100)
    with col3:
        aht = st.number_input("AHT (minutes/transaction)", min_value=0.0, step=0.5)

    metrics = {"FTE": fte, "Volume/month": vol, "AHT (min/txn)": aht}

    if st.button("Analyze automation potential"):
        if not desc.strip():
            st.warning("Please describe the process.")
            return
        with st.spinner("Analyzing…"):
            ans = automation_analysis(desc, metrics)
        render_answer(ans, "Automation & Lean Insights")


def cba_ui():
    st.subheader("Cost–Benefit Analysis")

    project_name = st.text_input("Project name")
    description = st.text_area("Brief description of the initiative:", height=120)

    col1, col2 = st.columns(2)
    with col1:
        horizon_years = st.number_input("Time horizon (years)", min_value=1, max_value=10, value=3, step=1)
        currency = st.text_input("Currency (e.g. USD, EUR, INR)", value="USD")
    with col2:
        discount_rate = st.number_input("Discount rate (%) – rough WACC", min_value=0.0, max_value=40.0, value=10.0, step=0.5)

    st.markdown("#### Financial estimates (optional but recommended)")
    col3, col4, col5 = st.columns(3)
    with col3:
        one_time_cost = st.number_input("One-time investment", min_value=0.0, step=1000.0)
    with col4:
        annual_cost = st.number_input("Recurring annual cost", min_value=0.0, step=1000.0)
    with col5:
        annual_benefit = st.number_input("Recurring annual benefit", min_value=0.0, step=1000.0)

    notes = st.text_area(
        "Additional notes (benefit drivers, assumptions, constraints):",
        height=120,
        placeholder="Example: Benefits driven by FTE reduction, late fee avoidance, faster cash collection, fewer audit issues…",
    )

    if st.button("Generate CBA report"):
        if not project_name.strip():
            st.warning("Please provide at least a project name.")
            return
        with st.spinner("Building cost–benefit analysis…"):
            report = cost_benefit_report(
                project_name=project_name,
                description=description,
                horizon_years=int(horizon_years),
                currency=currency,
                one_time_cost=float(one_time_cost),
                annual_cost=float(annual_cost),
                annual_benefit=float(annual_benefit),
                discount_rate=float(discount_rate),
                notes=notes,
            )
        render_answer(report, "Cost–Benefit Analysis")


def sap_ui():
    st.subheader("SAP Copilot")

    module = st.selectbox(
        "Module",
        ["R2R", "P2P", "O2C", "FI/CO", "Asset Accounting", "Tax"],
    )
    question = st.text_area("Ask your SAP finance question:", height=160)

    if st.button("Ask SAP Copilot"):
        if not question.strip():
            st.warning("Please enter a question.")
            return
        with st.spinner("Thinking like an SAP Architect…"):
            ans = sap_copilot_answer(question, module)
        render_answer(ans, "SAP Answer")


def deck_ui():
    st.subheader("Deck Generator")

    deck_type = st.selectbox(
        "Deck type",
        [
            "Finance Transformation Storyline",
            "R2R Optimization",
            "P2P Automation Business Case",
            "O2C Cash Acceleration",
            "Close Acceleration & Quality",
        ],
    )
    ctx = st.text_area("Business context / key points for the deck:", height=160)

    if st.button("Generate deck outline"):
        if not ctx.strip():
            st.warning("Please provide context so the deck is specific.")
            return
        with st.spinner("Designing executive deck…"):
            ans = build_exec_deck(deck_type, ctx)
        render_answer(ans, "Executive Deck Outline")


# -----------------------------
# Run app
# -----------------------------
if __name__ == "__main__":
    main()
