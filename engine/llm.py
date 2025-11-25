# engine/llm.py

import os
from typing import Optional
from openai import OpenAI

# ------------------------------------------
# Exception used when key is missing or invalid
# ------------------------------------------
class LLMNotConfigured(Exception):
    """Raised when the OpenAI API key is missing or invalid."""
    pass


# ------------------------------------------
# System Prompt – Consulting Grade
# ------------------------------------------
SYSTEM_PROMPT = """
You are Bivenue Copilot — an elite Finance Transformation Advisor with expertise in:
- SAP S/4HANA, Oracle, NetSuite
- BlackLine, Anaplan, Power BI
- Global Intercompany, R2R, P2P, O2C, FP&A
- Close acceleration, automation, and finance operating models

Your mission:
Produce a consulting-grade, CFO-facing transformation brief.

MANDATORY RULES:
- NO generic advice. NO repeating yourself. NO filler.
- Diagnose like a senior consultant from McKinsey / BCG / Bain / Accenture.
- Reference systems and processes explicitly (SAP, BlackLine, Anaplan, etc.) when relevant.
- Use sharp, short bullets. Executive-level tone.
- Assume the reader is a CFO, Finance Director or GBS Leader.
- Follow the EXACT structure below:

# Consulting Brief: {short title}

## 1. Context & Problem Summary
Short CFO-level summary (3–6 lines).

## 2. Root Causes
3–7 sharp, non-generic root causes across process, data, systems, org, or governance.

## 3. Quick Wins (0–3 months)
Concrete, high-impact actions that give momentum.

## 4. Roadmap (3–6 months)
Medium-term structural fixes (process, data, systems, operating model).

## 5. Roadmap (6–12 months)
Scale, automation, analytics, target-operating-model redesign.

## 6. Risks & Mitigation
Key risks with practical mitigation pairs.

## 7. KPIs & Value Story
Measurable KPIs with targets + business value narrative.

Write like a real consultant.
No fluff. No repeating lines. No long paragraphs.
"""


# ------------------------------------------
# Build the OpenAI client safely
# ------------------------------------------
def _build_client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or len(api_key) < 20:
        raise LLMNotConfigured(
            "AI is not configured yet. Please set OPENAI_API_KEY in your Streamlit secrets."
        )

    try:
        client = OpenAI(api_key=api_key)
    except Exception:
        raise LLMNotConfigured(
            "Your OpenAI key is invalid or restricted. Try a different permission mode."
        )
    return client


# ------------------------------------------
# Generate Consulting-Grade AI Analysis
# ------------------------------------------
def generate_ai_analysis(
    problem: str,
    domain: str,
    rule_based_summary: str,
) -> Optional[str]:
    """
    Produces a full consulting brief using the upgraded Bivenue Copilot logic.
    """

    client = _build_client()

    user_prompt = (
        f"Finance domain: {domain}\n"
        f"Business problem:\n{problem}\n\n"
        f"Rule-based diagnostic summary:\n{rule_based_summary}\n\n"
        "Generate the full consulting brief now."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.25,
            max_tokens=1600,
        )

        return response.choices[0].message["content"]

    except Exception as e:
        # Catch any token limits, network errors, or permissions errors
        return f"AI analysis failed: {str(e)}"
