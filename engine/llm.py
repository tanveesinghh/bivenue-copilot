# engine/llm.py

import os
from typing import Optional

from openai import OpenAI


class LLMNotConfigured(Exception):
    """Raised when the OpenAI API key is not configured."""
    pass


def _get_client() -> OpenAI:
    """
    Returns an OpenAI client, or raises LLMNotConfigured if the API key is missing.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # Streamlit Cloud: you probably set this in Secrets.
        raise LLMNotConfigured(
            "AI analysis is not configured yet. Please add OPENAI_API_KEY "
            "to your Streamlit secrets or environment."
        )
    return OpenAI(api_key=api_key)


def generate_ai_analysis(
    problem: str,
    domain: str,
    rule_based_summary: str,
    model: str = "gpt-4.1-mini",
    temperature: float = 0.2,
    max_tokens: int = 1400,
) -> str:
    """
    Call OpenAI to generate a consulting-style deep-dive brief.

    Returns a markdown string ready to render with st.markdown().
    Raises LLMNotConfigured if the API key is missing.
    Propagates other exceptions to be handled in app.py.
    """
    client = _get_client()

    # System message: how the AI should behave
    system_msg = (
        "You are a senior finance transformation consultant (Big-4 / Gartner style). "
        "Write concise but high-quality consulting briefs for CFOs and Finance leaders. "
        "Your tone is practical, structured and non-fluffy. "
        "Always organize output under clearly numbered headings."
    )

    # User message: concrete task
    user_prompt = f"""
You are helping a CFO diagnose and solve a **{domain}** challenge.

### Original problem (verbatim from client)
\"\"\"{problem.strip()}\"\"\"

### Rule-based summary from an internal diagnostic engine
{rule_based_summary.strip()}

### Task
Write a 1-page consulting brief in markdown with the following structure and headings:

# Consulting Brief: Short, impactful title (max 1 line)

1. Context & Problem Restatement  
   - Restate the situation in plain language (2–3 bullet points).  
   - Focus on why this is painful for Finance and the business.

2. Likely Root Causes  
   - 4–6 bullets grouped around Process, Technology, Data, Organization, Governance.  
   - Make them specific and realistic for a global finance organization.

3. Quick Wins (0–3 months)  
   - 4–6 very concrete, execution-ready actions.  
   - Each bullet should start with a strong verb (e.g., "Standardize...", "Deploy...", "Launch...").

4. Roadmap 3–6 months  
   - 3–5 bullets describing medium-term initiatives (process, tech, operating model).

5. Roadmap 6–12 months  
   - 3–5 bullets for more advanced / structural changes.

6. Risks & Dependencies  
   - 4–6 bullets on execution risks, data/tech dependencies, change management.

7. Success Metrics / KPIs  
   - 6–8 metrics a CFO would track (cycle time, close quality, automation %, IC breaks, etc.).

Make it specific to the problem and domain, not generic.  
Avoid repeating the headings inside the bullets (no **Context:** etc inside bullets).  
Do NOT include any extra sections outside 1–7.
"""

    response = client.chat.completions.create(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_prompt},
        ],
    )

    # Correct way: access the message via .choices[0].message.content
    message = response.choices[0].message
    content: Optional[str] = message.content if message is not None else None

    if not content:
        raise RuntimeError("LLM returned an empty response.")

    return content.strip()
