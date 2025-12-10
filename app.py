import os
import textwrap
from typing import List, Dict, Any

import streamlit as st
from dotenv import load_dotenv

from openai import OpenAI
from tavily import TavilyClient

# -----------------------------
# 🔐 Load environment variables
# -----------------------------
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

if not OPENAI_API_KEY:
    st.warning("⚠️ OPENAI_API_KEY is not set. Add it to your environment or .env file.")
if not TAVILY_API_KEY:
    st.info("ℹ️ TAVILY_API_KEY not found. Web search will be disabled and answers will be LLM-only.")

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
tavily_client = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None


# -----------------------------
# 🎨 Global Page Config + Theme
# -----------------------------
st.set_page_config(
    page_title="Bivenue – Finance AI Copilot",
    page_icon=" ",
    layout="wide",
)

MIDNIGHT_BLUE_CSS = """
<style>
/* Force full dark background */
.stApp {
    background-color: #050814 !important;
}

/* Main content */
section.main > div {
    background: #050814 !important;
}

/* Remove any light overlay at top */
.block-container {
    padding-top: 1.5rem;
    background-color: #050814 !important;
}

/* Header bar */
header[data-testid="stHeader"] {
    background: #050814 !important;
    border-bottom: 1px solid rgba(120, 159, 255, 0.25);
}

/* Global text */
h1, h2, h3, h4, h5, h6, label, p, span, li {
    color: #f5f7ff !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #030512 !important;
}

/* Inputs */
.stTextInput, .stTextArea, .stSelectbox, .stNumberInput {
    background-color: #080c1a !important;
}
.stTextInput input, .stTextArea textarea {
    background-color: #080c1a !important;
    color: #f5f7ff !important;
}

/* Answer card */
.biv-card {
    border-radius: 16px;
    padding: 1.2rem 1.4rem;
    background: #080c1a;
    border: 1px solid rgba(120, 159, 255, 0.35);
    box-shadow: 0 18px 40px rgba(0, 0, 0, 0.7);
}

/* Chips & subtle text */
.biv-chip {
    display: inline-block;
    padding: 0.25rem 0.7rem;
    border-radius: 999px;
    background: rgba(75, 138, 255, 0.25);
    color: #e0e6ff;
    font-size: 0.72rem;
    margin-right: 0.25rem;
    margin-bottom: 0.25rem;
}
.biv-tag {
    font-size: 0.78rem;
    color: #b8c2ff;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
.biv-subtle {
    color: #9ca6e8 !important;
    font-size: 0.8rem;
}

/* Sources */
.biv-source {
    font-size: 0.85rem;
    margin-bottom: 0.5rem;
}
.biv-source a {
    color: #8fb2ff !important;
    text-decoration: none;
}
.biv-source a:hover {
    text-decoration: underline;
}
</style>
"""


st.markdown(MIDNIGHT_BLUE_CSS, unsafe_allow_html=True)


# -----------------------------
# 🧠 Helper: Call OpenAI Chat
# -----------------------------
def ask_gpt(
    messages: List[Dict[str, str]],
    model: str = "gpt-4.1-mini",
    temperature: float = 0.35,
    max_tokens: int = 1000,
) -> str:
    if not client:
        return "⚠️ OpenAI client not initialized. Please set OPENAI_API_KEY."

    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return completion.choices[0].message.content


# -----------------------------
# 🌐 Perplexity-style Search
# -----------------------------
def tavily_search(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    if not tavily_client:
        return []

    result = tavily_client.search(
        query=query,
        max_results=max_results,
        search_depth="advanced",
        include_answers=False,
        include_images=False,
        include_raw_content=False,
    )
    return result.get("results", [])


def build_citation_context(results: List[Dict[str, Any]]) -> str:
    context_parts = []
    for i, r in enumerate(results):
        idx = i + 1
        title = r.get("title", f"Source {idx}")
        url = r.get("url", "")
        content = r.get("content", "")
        snippet = textwrap.shorten(content, width=500, placeholder="…")
        context_parts.append(
            f"[{idx}] {title}\nURL: {url}\nSummary: {snippet}\n"
        )
    return "\n\n".join(context_parts)


def answer_with_citations(query: str) -> Dict[str, Any]:
    results = tavily_search(query, max_results=6) if tavily_client else []
    context = build_citation_context(results) if results else "No external search results were available."

    system_msg = {
        "role": "system",
        "content": (
            "You are Bivenue, a research-focused AI that answers concisely, "
            "with clear structure, and uses bracketed citations like [1], [2] "
            "that reference the provided sources. If you are unsure, say so."
        ),
    }

    user_msg = {
        "role": "user",
        "content": (
            f"Question:\n{query}\n\n"
            f"Use the following search results to answer. When you use a fact, "
            f"cite the source index like [1], [2]. If no results are available, "
            f"answer based on your general knowledge and clearly say that "
            f"no web sources were used.\n\n"
            f"Search results:\n{context}"
        ),
    }

    answer = ask_gpt([system_msg, user_msg], model="gpt-4.1-mini", max_tokens=1200)

    return {"answer": answer, "sources": results}


# -----------------------------
# 💼 Finance Transformation AI
# -----------------------------
def finance_transform_answer(task_type: str, prompt: str) -> str:
    system = {
        "role": "system",
        "content": (
            "You are a senior Finance Transformation & Automation Director. "
            "You design R2R, P2P, O2C processes, TOMs, business cases, and "
            "automation opportunities. Your answers must be concise, structured, "
            "and practical, suitable for real-world execution."
        ),
    }

    user = {
        "role": "user",
        "content": (
            f"Task type: {task_type}\n\n"
            f"User context / input:\n{prompt}\n\n"
            "Deliver a structured answer with headers and bullet points. "
            "Whenever relevant, include:\n"
            "- Current state\n"
            "- Pain points\n"
            "- Future state design\n"
            "- KPIs\n"
            "- Automation opportunities\n"
            "- Quick wins vs long-term initiatives\n"
        ),
    }

    return ask_gpt([system, user], model="gpt-4.1", max_tokens=1600)


# -----------------------------
# 🔧 SOP Builder
# -----------------------------
def build_sop(process_name: str, process_context: str, steps_raw: str) -> str:
    system = {
        "role": "system",
        "content": (
            "You are a Finance Process Excellence Lead. You create very clear, "
            "practical SOPs for finance processes (R2R, P2P, O2C, Tax, etc.)."
        ),
    }

    user = {
        "role": "user",
        "content": textwrap.dedent(
            f"""
            Create a detailed Standard Operating Procedure (SOP).

            Process name: {process_name}

            Business context:
            {process_context}

            High-level steps provided by the user:
            {steps_raw}

            SOP output format:

            1. Purpose
            2. Scope
            3. Definitions / Key Terms
            4. Roles & Responsibilities (RACI style)
            5. Detailed Step-by-Step Procedure
               - Step number
               - Description
               - Responsible role
               - Systems / tools
               - Inputs & outputs
            6. Controls & Risk Points
            7. KPIs & SLAs
            8. Automation Opportunities
            9. Appendix (if needed)

            Make it concise but execution-ready.
            """
        ),
    }

    return ask_gpt([system, user], model="gpt-4.1", max_tokens=2000)


# -----------------------------
# ⚙️ Automation & Time Study
# -----------------------------
def automation_analysis(process_desc: str, metrics: Dict[str, Any]) -> str:
    system = {
        "role": "system",
        "content": (
            "You are a Lean Six Sigma Black Belt & Automation Director. "
            "You identify 8 wastes, RPA/AI opportunities, and build quick-win roadmaps."
        ),
    }

    metrics_text = "\n".join(
        [f"- {k}: {v}" for k, v in metrics.items() if v not in (None, "", 0)]
    )

    user = {
        "role": "user",
        "content": textwrap.dedent(
            f"""
            Analyze the following finance/shared-services process for automation potential.

            Process description:
            {process_desc}

            Quantitative metrics (if any):
            {metrics_text}

            Provide:
            1. Summary of current state
            2. Key pain points & 8 wastes (TIMWOODS)
            3. RPA / AI / Workflow automation opportunities
            4. Estimated impact (FTE, cycle time, quality)
            5. Quick wins (0–3 months)
            6. Medium-term initiatives (3–9 months)
            7. Long-term strategic moves (9–24 months)
            8. Risks / dependencies
            """
        ),
    }

    return ask_gpt([system, user], model="gpt-4.1", max_tokens=1600)


# -----------------------------
# 🧾 SAP Copilot
# -----------------------------
def sap_copilot_answer(question: str, module_hint: str) -> str:
    system = {
        "role": "system",
        "content": (
            "You are an expert SAP S/4HANA FI/CO Solution Architect. "
            "You explain SAP finance processes (P2P, O2C, R2R, AA, Tax, etc.) "
            "in simple language. You mention key T-codes, tables, and typical "
            "root causes, but DO NOT invent configuration the user did not ask for. "
            "Be practical and focused on finance operations."
        ),
    }

    user = {
        "role": "user",
        "content": (
            f"Module focus (hint): {module_hint}\n\n"
            f"Question:\n{question}\n\n"
            "Answer structure:\n"
            "1. Short summary\n"
            "2. Likely root causes / explanation\n"
            "3. How to investigate (T-codes / logs)\n"
            "4. Example document flow (if relevant)\n"
            "5. Tips / best practices\n"
        ),
    }

    return ask_gpt([system, user], model="gpt-4.1", max_tokens=1500)


# -----------------------------
# 📊 Deck / Executive Summary
# -----------------------------
def build_exec_deck_outline(deck_type: str, context: str) -> str:
    system = {
        "role": "system",
        "content": (
            "You are a McKinsey-style consultant creating slide outlines for "
            "Finance Transformation decks. You output slide-by-slide content."
        ),
    }

    user = {
        "role": "user",
        "content": textwrap.dedent(
            f"""
            Create a slide-by-slide outline for a {deck_type}.

            Business context:
            {context}

            Output format:

            Slide 1: Title & Subtitle
            - Bullet 1
            - Bullet 2

            Slide 2: ...
            ...
            Limit to 12–15 slides. Make them executive-ready.
            """
        ),
    }

    return ask_gpt([system, user], model="gpt-4.1-mini", max_tokens=1800)


# -----------------------------
# 🧱 UI Components
# -----------------------------
def render_sources(sources: List[Dict[str, Any]]):
    if not sources:
        st.caption("No external sources were used (LLM-only answer).")
        return

    st.markdown("#### Sources")
    for i, src in enumerate(sources):
        idx = i + 1
        title = src.get("title", f"Source {idx}")
        url = src.get("url", "")
        st.markdown(
            f"""
            <div class="biv-source">
            <span class="biv-chip">[{idx}]</span>
            <strong>{title}</strong><br/>
            <a href="{url}" target="_blank">{url}</a>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_answer_box(content: str, title: str = "Answer"):
    st.markdown(
        f"""
        <div class="biv-card">
            <div class="biv-tag">{title}</div>
            <div style="margin-top:0.5rem;">
                {content.replace("\n", "<br/>")}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------
# 🚀 MAIN APP LAYOUT
# -----------------------------
def main():
    # Sidebar
    st.sidebar.markdown("### 📊 Bivenue – Finance AI Copilot")
    st.sidebar.caption("Hybrid Perplexity + Finance Transformation + SAP Copilot")

    mode = st.sidebar.radio(
        "Choose mode",
        [
            " Research ",
            " Finance Transformation AI",
            " SOP Builder",
            " Automation & Time Study",
            " SAP Copilot",
            " Deck Generator ",
        ],
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "<span class='biv-subtle'>Theme: Midnight Blue • Built for Finance & SAP</span>",
        unsafe_allow_html=True,
    )

    # Header
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.markdown("## 📊 Bivenue – Hybrid Finance AI Copilot")
        st.markdown(
            "<span class='biv-subtle'>Ask anything, then go deeper into Finance, Automation, and SAP.</span>",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            "<div style='text-align:right;'><span class='biv-chip'>v2 • Beta</span></div>",
            unsafe_allow_html=True,
        )

    st.markdown("")

    # Mode Handlers
    if mode == " Research ":
        research_mode_ui()
    elif mode == " Finance Transformation AI":
        finance_mode_ui()
    elif mode == " SOP Builder":
        sop_mode_ui()
    elif mode == " Automation & Time Study":
        automation_mode_ui()
    elif mode == " SAP Copilot":
        sap_mode_ui()
    elif mode == " Deck Generator ":
        deck_mode_ui()


# -----------------------------
# 🔍 Research Mode UI
# -----------------------------
def research_mode_ui():
    st.markdown("###  Research Mode ")
    query = st.text_input("Ask a question (general or finance-related):", placeholder="e.g. What is Global Minimum Tax and how does it impact multinationals?")

    col_suggest1, col_suggest2, col_suggest3 = st.columns(3)
    with col_suggest1:
        if st.button("Impact of AI on R2R"):
            query_default = "How is AI changing Record to Report (R2R) processes in large enterprises?"
            st.session_state["research_query"] = query_default
            query = query_default
    with col_suggest2:
        if st.button("Order-to-Cash best practices"):
            query_default = "What are best practices to optimize the Order-to-Cash cycle in a global company?"
            st.session_state["research_query"] = query_default
            query = query_default
    with col_suggest3:
        if st.button("Working capital levers"):
            query_default = "Key working capital levers in P2P, O2C and Inventory management."
            st.session_state["research_query"] = query_default
            query = query_default

    if query:
        with st.spinner("Researching across the web and building your answer..."):
            result = answer_with_citations(query)
            answer = result["answer"]
            sources = result["sources"]

        render_answer_box(answer, title="Research Answer")
        render_sources(sources)


# -----------------------------
# 💼 Finance Mode UI
# -----------------------------
def finance_mode_ui():
    st.markdown("### Finance Transformation AI")

    task_type = st.selectbox(
        "What do you want to design / analyze?",
        [
            "R2R transformation",
            "P2P transformation",
            "O2C transformation",
            "Shared service setup",
            "Automation roadmap",
            "Close optimization",
            "Controllership / audit",
            "Custom transformation topic",
        ],
    )

    prompt = st.text_area(
        "Describe your current situation, challenges, and objectives:",
        height=220,
        placeholder=(
            "Example: We are a global retail company with fragmented R2R processes across 5 regions. "
            "Month-end close takes 10 days, there are many manual journal entries, "
            "and audit adjustments are frequent. I want a target state design with quick wins."
        ),
    )

    if st.button("Generate Transformation Plan"):
        if not prompt.strip():
            st.warning("Please describe your situation so I can generate something concrete.")
            return

        with st.spinner("Designing your finance transformation plan..."):
            answer = finance_transform_answer(task_type, prompt)

        render_answer_box(answer, title="Transformation Recommendation")


# -----------------------------
# 🧾 SOP Builder UI
# -----------------------------
def sop_mode_ui():
    st.markdown("###  SOP Builder")

    process_name = st.text_input("Process name:", placeholder="e.g. Vendor Invoice Processing (P2P)")
    process_context = st.text_area(
        "Business context:",
        height=160,
        placeholder=(
            "Describe the business, region, systems (e.g., SAP S/4HANA, Coupa), "
            "volumes, pain points, and any specific compliance requirements."
        ),
    )
    steps_raw = st.text_area(
        "High-level steps (one per line):",
        height=200,
        placeholder="1. Receive invoice\n2. Perform 3-way match\n3. Post invoice in SAP\n4. Handle exceptions\n5. Run payment proposal\n6. Execute payment run",
    )

    if st.button("Generate SOP"):
        if not process_name.strip() or not steps_raw.strip():
            st.warning("Please provide at least a process name and some steps.")
            return

        with st.spinner("Building an execution-ready SOP..."):
            sop_text = build_sop(process_name, process_context, steps_raw)

        render_answer_box(sop_text, title=f"SOP – {process_name}")


# -----------------------------
# 🤖 Automation & Time Study UI
# -----------------------------
def automation_mode_ui():
    st.markdown("### 🤖 Automation & Time Study")

    process_desc = st.text_area(
        "Describe the process:",
        height=200,
        placeholder=(
            "Example: AP invoice processing for EMEA region. 15 FTE, 12k invoices/month, "
            "manual 3-way match for most invoices, multiple approvals, frequent exceptions..."
        ),
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        fte = st.number_input("Approx. FTE", min_value=0.0, step=0.5)
    with col2:
        volume = st.number_input("Volume/month (transactions)", min_value=0, step=100)
    with col3:
        aht = st.number_input("Avg. handling time (minutes/transaction)", min_value=0.0, step=0.5)

    metrics = {
        "FTE": fte,
        "Volume per month": volume,
        "AHT (minutes/transaction)": aht,
    }

    if st.button("Analyze Automation Potential"):
        if not process_desc.strip():
            st.warning("Please describe the process so I can analyze it.")
            return

        with st.spinner("Analyzing wastes, automation levers, and impact..."):
            analysis_text = automation_analysis(process_desc, metrics)

        render_answer_box(analysis_text, title="Automation & Lean Analysis")


# -----------------------------
# 🧠 SAP Copilot UI
# -----------------------------
def sap_mode_ui():
    st.markdown("###  SAP Copilot – Finance")

    module_hint = st.selectbox(
        "Which area best matches your question?",
        [
            "General Finance / FI",
            "Record to Report (R2R)",
            "Order to Cash (O2C)",
            "Procure to Pay (P2P)",
            "Asset Accounting (AA)",
            "Controlling (CO)",
            "Tax / Withholding",
            "Other / Not sure",
        ],
    )

    question = st.text_area(
        "Ask your SAP finance question:",
        height=200,
        placeholder=(
            "Example: GR/IR is not clearing after MIGO and MIRO in S/4HANA. "
            "What could be the reasons and how do I troubleshoot?"
        ),
    )

    if st.button("Ask SAP Copilot"):
        if not question.strip():
            st.warning("Please type your SAP question.")
            return

        with st.spinner("Thinking like an SAP Solution Architect..."):
            answer = sap_copilot_answer(question, module_hint)

        render_answer_box(answer, title="SAP Copilot Answer")


# -----------------------------
# 📈 Deck Generator UI
# -----------------------------
def deck_mode_ui():
    st.markdown("###  Deck Generator ")

    deck_type = st.selectbox(
        "Deck type:",
        [
            "Finance Transformation Proposal",
            "R2R Optimization Storyline",
            "P2P Automation Business Case",
            "O2C Cash Acceleration Story",
            "Shared Services Setup Proposal",
            "Close Acceleration & Quality Improvement",
        ],
    )

    context = st.text_area(
        "Business context / notes for the deck:",
        height=220,
        placeholder=(
            "Describe the company, current problems, what leadership wants, and "
            "any numbers (savings, FTE, days to close, etc.) you want to highlight."
        ),
    )

    if st.button("Generate Deck Outline"):
        if not context.strip():
            st.warning("Please provide some context so the deck is relevant.")
            return

        with st.spinner("Designing a slide-by-slide storyline..."):
            outline = build_exec_deck_outline(deck_type, context)

        render_answer_box(outline, title=f"Deck Outline – {deck_type}")


# -----------------------------
# 🏁 Run app
# -----------------------------
if __name__ == "__main__":
    main()
