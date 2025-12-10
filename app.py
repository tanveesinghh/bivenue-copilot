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

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
tavily_client = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None


# -----------------------------
# 🎨 Page Config (Light theme)
# -----------------------------
st.set_page_config(
    page_title="Bivenue – Finance AI Copilot",
    page_icon="📊",
    layout="wide",
)

# Simple card styling
SIMPLE_CSS = """
<style>
.biv-card {
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    background: #ffffff;
    border: 1px solid rgba(0,0,0,0.06);
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.06);
}
.biv-tag {
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #64748b;
}
.biv-source {
    font-size: 0.85rem;
    color: #374151;
    margin-bottom: 0.3rem;
}
.biv-source a {
    color: #2563eb;
    text-decoration: none;
}
.biv-source a:hover {
    text-decoration: underline;
}
</style>
"""

st.markdown(SIMPLE_CSS, unsafe_allow_html=True)


# -----------------------------
# 🧠 Helper: Call OpenAI
# -----------------------------
def ask_gpt(messages, model="gpt-4.1-mini", temperature=0.35, max_tokens=1000):
    if not client:
        return "⚠️ OpenAI API key not found in Streamlit Secrets."
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
    )
    return response.choices[0].message.content


# -----------------------------
# 🌐 Web Search (Research Mode)
# -----------------------------
def tavily_search(query: str, max_results: int = 5):
    if not tavily_client:
        return []
    response = tavily_client.search(
        query=query,
        max_results=max_results,
        search_depth="advanced"
    )
    return response.get("results", [])


def build_citation_context(results):
    lines = []
    for i, r in enumerate(results):
        idx = i + 1
        title = r.get("title", f"Source {idx}")
        url = r.get("url", "")
        content = r.get("content", "")
        snippet = textwrap.shorten(content, width=400, placeholder="…")
        lines.append(f"[{idx}] {title}\nURL: {url}\nSummary: {snippet}")
    return "\n\n".join(lines)


def answer_with_citations(query: str):
    results = tavily_search(query, max_results=6)
    context = build_citation_context(results) if results else "No web data found."

    system_msg = {
        "role": "system",
        "content": "You are Bivenue, a factual, research-oriented AI. Always use citations like [1], [2]."
    }

    user_msg = {
        "role": "user",
        "content": (
            f"Question: {query}\n\n"
            f"Use these sources:\n{context}\n\n"
            f"If no sources are found, answer from general knowledge without citations."
        ),
    }

    answer = ask_gpt([system_msg, user_msg], model="gpt-4.1-mini", max_tokens=1400)
    return {"answer": answer, "sources": results}


# -----------------------------
# 💼 Finance Transformation AI
# -----------------------------
def finance_transform_answer(task_type: str, context: str):
    system = {
        "role": "system",
        "content": (
            "You are a Finance Transformation Director. Provide structured, "
            "practical recommendations for R2R, P2P, O2C, Automation, Audit, Close, etc."
        ),
    }

    user = {
        "role": "user",
        "content": f"Task type: {task_type}\n\nContext:\n{context}",
    }

    return ask_gpt([system, user], model="gpt-4.1", max_tokens=1800)


# -----------------------------
# 🧾 SOP Builder
# -----------------------------
def build_sop(name: str, context: str, steps: str):
    system = {
        "role": "system",
        "content": "You are a Finance Process Expert. Generate execution-ready SOPs."
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
- Roles
- Detailed procedure
- Controls
- KPIs
- Automation opportunities
"""
    }

    return ask_gpt([system, user], model="gpt-4.1", max_tokens=2000)


# -----------------------------
# 🤖 Automation + Time Study
# -----------------------------
def automation_analysis(desc: str, metrics: dict):
    system = {
        "role": "system",
        "content": "You are a Lean Six Sigma + Automation Director."
    }

    user = {
        "role": "user",
        "content": f"""
Analyze this process for automation:

Description:
{desc}

Metrics:
{metrics}

Provide:
- Wastes
- Automation opportunities
- Estimated impact
- Quick wins
- Roadmap
"""
    }

    return ask_gpt([system, user], model="gpt-4.1", max_tokens=1600)


# -----------------------------
# 🧠 SAP Copilot
# -----------------------------
def sap_copilot_answer(question: str, module: str):
    system = {
        "role": "system",
        "content": "You are an SAP S/4HANA FI/CO Architect. Explain root causes, T-codes, flows."
    }

    user = {
        "role": "user",
        "content": f"Module: {module}\n\nQuestion: {question}"
    }

    return ask_gpt([system, user], model="gpt-4.1", max_tokens=1600)


# -----------------------------
# 📊 Deck Generator
# -----------------------------
def build_exec_deck(deck_type: str, context: str):
    system = {
        "role": "system",
        "content": "You are a McKinsey consultant. Create slide-by-slide deck outlines."
    }

    user = {
        "role": "user",
        "content": f"Create a 12-slide deck: {deck_type}\n\nContext:\n{context}"
    }

    return ask_gpt([system, user], model="gpt-4.1-mini", max_tokens=1800)


# -----------------------------
# UI Helper
# -----------------------------
def render_answer(content, title="Answer"):
    st.markdown(
        f"""
        <div class="biv-card">
            <div class="biv-tag">{title}</div>
            <div style="margin-top:0.5rem;">{content}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_sources(sources):
    if not sources:
        return
    st.markdown("#### Sources")
    for i, src in enumerate(sources):
        st.markdown(
            f"""
            <div class="biv-source">
            <strong>[{i+1}] {src.get("title","")}</strong><br>
            <a href="{src.get("url","")}" target="_blank">{src.get("url","")}</a>
            </div>
            """,
            unsafe_allow_html=True
        )


# -----------------------------
# MAIN APP
# -----------------------------
def main():
    st.sidebar.title("📊 Bivenue – Finance AI Copilot")
    st.sidebar.write("Hybrid Research + Finance Transformation + SAP Copilot")

    mode = st.sidebar.radio(
        "Choose mode",
        [
            "🔍 Research",
            "💼 Finance Transformation",
            "🧾 SOP Builder",
            "🤖 Automation Analysis",
            "🧠 SAP Copilot",
            "📈 Deck Generator",
        ],
    )

    st.markdown("## Bivenue – Finance AI Copilot")
    st.caption("Ask anything. Then dive deeper into Finance, Automation, and SAP.")

    if mode == "🔍 Research":
        research_ui()
    elif mode == "💼 Finance Transformation":
        finance_ui()
    elif mode == "🧾 SOP Builder":
        sop_ui()
    elif mode == "🤖 Automation Analysis":
        automation_ui()
    elif mode == "🧠 SAP Copilot":
        sap_ui()
    elif mode == "📈 Deck Generator":
        deck_ui()


# -----------------------------
# UI Pages
# -----------------------------
def research_ui():
    st.subheader("Research Mode")
    query = st.text_input("Ask any question:")

    if st.button("Search"):
        with st.spinner("Researching…"):
            res = answer_with_citations(query)
        render_answer(res["answer"], "Research Answer")
        render_sources(res["sources"])


def finance_ui():
    st.subheader("Finance Transformation")
    task = st.selectbox("Select focus:", ["R2R", "P2P", "O2C", "Close", "Audit", "Automation Roadmap"])
    context = st.text_area("Describe your situation:", height=200)

    if st.button("Generate Plan"):
        with st.spinner("Building plan…"):
            ans = finance_transform_answer(task, context)
        render_answer(ans, "Transformation Plan")


def sop_ui():
    st.subheader("SOP Builder")
    name = st.text_input("Process name:")
    context = st.text_area("Business context:", height=150)
    steps = st.text_area("List steps:", height=200)

    if st.button("Generate SOP"):
        with st.spinner("Creating SOP…"):
            ans = build_sop(name, context, steps)
        render_answer(ans, "Standard Operating Procedure")


def automation_ui():
    st.subheader("Automation Analysis")
    desc = st.text_area("Describe the process:", height=200)

    fte = st.number_input("FTE", min_value=0.0, step=0.5)
    vol = st.number_input("Volume per month", min_value=0)
    aht = st.number_input("AHT (minutes per transaction)", min_value=0.0)

    metrics = {"FTE": fte, "Volume": vol, "AHT": aht}

    if st.button("Analyze"):
        with st.spinner("Analyzing…"):
            ans = automation_analysis(desc, metrics)
        render_answer(ans, "Automation Insights")


def sap_ui():
    st.subheader("SAP Copilot")
    module = st.selectbox("Module:", ["R2R", "P2P", "O2C", "FI/CO", "AA", "Tax"])
    question = st.text_area("Ask your SAP question:", height=150)

    if st.button("Ask Copilot"):
        with st.spinner("Thinking…"):
            ans = sap_copilot_answer(question, module)
        render_answer(ans, "SAP Answer")


def deck_ui():
    st.subheader("Deck Generator")
    deck_type = st.selectbox("Deck type:", [
        "Finance Transformation",
        "R2R Optimization",
        "P2P Automation",
        "O2C Acceleration",
        "Close Optimization"
    ])
    ctx = st.text_area("Context:", height=150)

    if st.button("Generate Deck"):
        with st.spinner("Building deck…"):
            ans = build_exec_deck(deck_type, ctx)
        render_answer(ans, "Executive Deck")


# Run App
if __name__ == "__main__":
    main()
