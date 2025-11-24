import os
from typing import Optional

from openai import OpenAI


class LLMNotConfigured(Exception):
    """Raised when OPENAI_API_KEY is missing."""
    pass


def _get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise LLMNotConfigured(
            "OPENAI_API_KEY not set. Configure it in Streamlit Cloud → Settings → Secrets."
        )
    return OpenAI(api_key=api_key)


def generate_ai_analysis(
    problem: str,
    domain: str,
    rule_based_summary: str,
) -> str:
    """
    Call OpenAI to generate a consultant-style deep-dive analysis.

    Returns a markdown string.
    """
    client = _get_client()

    system_prompt = (
        "You are a senior Finance Transformation director. "
        "You specialise in R2R, Intercompany, Consolidation, P2P, O2C and FP&A. "
        "Your job is to take an existing rule-based diagnosis and turn it into a "
        "clear, executive-ready analysis with bullet points and short paragraphs."
    )

    user_prompt = f"""
Problem statement from the client:

\"\"\"{problem}\"\"\"


Detected finance domain: {domain}

Rule-based recommendations from the engine:

\"\"\"{rule_based_summary}\"\"\"


Please provide:

1. A 2–3 line executive summary.
2. 3–5 key root causes, grouped by Process / Technology / Organisation / Data / Policy.
3. A short, prioritised action plan (Quick wins → 3–6 months → 6–12 months).

Keep it concise, practical, and non-technical. Use markdown formatting.
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",  # cheap + smart
        temperature=0.3,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    return response.choices[0].message.content.strip()
