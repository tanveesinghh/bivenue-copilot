from typing import Optional

import streamlit as st

from engine.classifier import classify_domain
from engine.generator import generate_recommendations
from engine.llm import generate_ai_analysis, LLMNotConfigured
from engine.pdf_export import create_consulting_brief_pdf


st.set_page_config(page_title="Bivenue Copilot", layout="wide")

# -------- Content Filter / Input Guardrail -------- #

FORBIDDEN_KEYWORDS = [
    "porn", "porno", "nude", "nudity", "sex", "sexual", "xxx",
    "escort", "fetish", "adult video", "onlyfans",
    "terrorist", "terrorism", "bomb", "explosive",
    "drugs", "cocaine", "heroin", "meth",
    "kill", "murder", "shoot", "rape",
    "hack", "hacking", "ddos", "malware",
]

NON_FINANCE_TOPICS = [
    "dating", "relationship", "romantic", "tinder", "hinge",
    "gaming", "video game", "minecraft", "pubg", "valorant",
    "movie", "film", "anime", "manga",
]


def validate_challenge_input(text: str) -> str | None:
    """
    Returns an error message string if the input is not allowed,
    otherwise returns None (meaning it's safe to process).
    """
    if not text:
        return "Please describe your finance transformation challenge first."

    lowered = text.lower()

    # Block obviously disallowed / NSFW / illegal content
    for word in FORBIDDEN_KEYWORDS:
        if word in lowered:
            return (
                "This copilot is restricted to **finance / business transformation** "
                "use cases only. Content with sexual, violent, criminal or harmful "
                "intent is not allowed."
            )

    # Gently push away non-finance topics
    for word in NON_FINANCE_TOPICS:
        if word in lowered:
            return (
                "It looks like your question is not about **finance transformation**. "
                "Please describe a challenge related to R2R, P2P, O2C, FP&A, "
                "intercompany, consolidation, close, or process/tech/people change."
            )

    # Optional: very long input guard
    if len(text) > 4000:
        return (
            "Your description is a bit too long. Please summarise the challenge "
            "in under 4,000 characters."
        )

    return None


def render_header() -> None:
    st.title("🧠 Bivenue Copilot")
    st.caption("Your AI Advisor for Finance Transformation.")


def render_input() -> str:
    st.subheader("Describe your finance transformation challenge")
    challenge = st.text_area(
        label="Describe your finance transformation challenge",
        placeholder=(
            "e.g., 'Intercompany mismatches causing consolidation delays across entities "
            "using SAP and BlackLine; lots of manual Excel reconciliations; unclear "
            "ownership between GBS and local controllers.'"
        ),
        height=160,
        label_visibility="collapsed",
    )
    return challenge


def render_result(domain: str, recommendations: str, challenge: str) -> None:
    st.success("Rule-based diagnostic complete.")

    st.subheader("1) Detected finance domain")
    st.write(f"**Domain:** {domain}")

    with st.expander("See original problem statement"):
        st.write(challenge)

    st.subheader("2) Recommended focus areas & actions")
    st.markdown(recommendations)

    st.info(
        "This is a rule-based v1 engine. Future versions will use your playbooks, "
        "historical data, and LLMs to refine the diagnosis and roadmap."
    )


def render_ai_section(
    challenge: str,
    domain: str,
    recommendations: str,
) -> None:
    st.divider()
    st.subheader("3) AI deep-dive analysis (experimental)")

    ai_brief: Optional[str] = None
    ai_error: Optional[str] = None

    try:
        with st.spinner("Asking the AI copilot for a deeper analysis..."):
            ai_brief = generate_ai_analysis(
                problem=challenge,
                domain=domain,
                rule_based_summary=recommendations,
            )
    except LLMNotConfigured as e:
        ai_error = str(e)
    except Exception as e:
        ai_error = f"AI error: {e}"

    if ai_brief:
        # Show the AI analysis on screen
        st.markdown(ai_brief)

        # --- Build branded PDF and expose download button ---
       pdf_bytes = create_consulting_brief_pdf(
    domain=domain,
    challenge=challenge,
    rule_based_summary=recommendations,
    ai_brief=ai_brief,
    company_name="Butterfield-style Client",
    industry="Finance",
    revenue=None,
    employees=None,
)

        st.download_button(
            label="📥 Download 1-page consulting brief (PDF)",
            data=pdf_bytes,
            file_name="bivenue_finance_brief.pdf",
            mime="application/pdf",
        )

    elif ai_error:
        st.warning(ai_error)


def main() -> None:
    render_header()
    challenge = render_input()

    if st.button("Diagnose", type="primary"):
        # 1) Run our content filter first
        error_message = validate_challenge_input(challenge.strip())
        if error_message:
            st.warning(error_message)
            return

        # 2) If safe, continue with rule-based engine
        with st.spinner("Running rule-based diagnostic..."):
            domain = classify_domain(challenge)
            recommendations = generate_recommendations(domain, challenge)

        render_result(domain, recommendations, challenge)
        render_ai_section(challenge, domain, recommendations)


if __name__ == "__main__":
    main()
