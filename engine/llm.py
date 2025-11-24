import os
from typing import Optional

from openai import OpenAI


class LLMNotConfigured(Exception):
    """Raised when OPENAI_API_KEY is missing."""
    pass


def _get_client() -> OpenAI:
    """
    Create an OpenAI client using the OPENAI_API_KEY from environment / Streamlit secrets.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise LLMNotConfigured(
            "AI is not configured yet. Please add your OpenAI API key as "
            "OPENAI_API_KEY in Streamlit → Settings → Secrets."
        )
    return OpenAI(api_key=api_key)


def generate_ai_analysis(
    problem: str,
    domain: str,
    rule_based_summary: str,
) -> str:
    """
    Ask the LLM for a structured, consulting-style deep dive.
    Returns markdown text.
    """

    client = _get_client()

    system_msg = (
        "You are a senior Finance Transformation consultant (Big 4 / MBB style). "
        "Your client is a CFO or Global Process Owner. You specialise in R2R, "
        "Intercompany, Consolidation, P2P, O2C and FP&A. Respond in concise, "
        "well-structured markdown. No fluff."
    )

    user_msg = f"""
You are advising a client on a **{domain}** problem.

The user described their challenge as:
\"\"\"{problem}\"\"\"

A simple rule-based engine has already produced this summary:
\"\"\"{rule_based_summary}\"\"\"

Using this as a starting point, produce a **short consulting brief** with the following sections:

1. **Context & Problem Restatement**  
   - Rephrase the situation in 2–4 sentences, in CFO language.

2. **Likely Root Causes**  
   - 3–6 bullet points focusing on process, technology, data and organisation.

3. **Quick Wins (0–3 months)**  
   - 3–5 concrete actions that can be started immediately.  
   - Emphasise low-cost, high-impact changes.

4. **Roadmap 3–6 months**  
   - Key workstreams and milestones (process, tech, org, data).

5. **Roadmap 6–12 months**  
   - Higher maturity items (automation, target operating model, analytics, etc.).

6. **Risks & Dependencies**  
   - 3–5 bullets of things that could block success (e.g. change resistance, data quality, IT capacity).

7. **Success Metrics / KPIs**  
   - 5–8 KPIs a CFO should track (cycle time, IC breaks, close quality, etc.).

Write in **clear bullet points**, no more than ~600–700 words total.
Do not invent specific vendor names unless generic (e.g. “ERP”, “consolidation tool”).
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # use the cheaper, smart model
        temperature=0.3,
        max_tokens=900,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
    )

    return response.choices[0].message.content.strip()
