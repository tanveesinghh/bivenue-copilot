from typing import Optional
import streamlit as st

from engine.classifier import classify_domain
from engine.generator import generate_recommendations
from engine.llm import generate_ai_analysis, LLMNotConfigured
from engine.pdf_export import create_consulting_brief_pdf


# -------------------------------------------------------
# Streamlit Page Configuration
# -------------------------------------------------------
st.set_page_config(page_title="Bivenue Copilot", layout="wide")


# -------------------------------------------------------
# Content Filter / Safety Guardrails
# -------------------------------------------------------
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
    """Returns an error message if content is not allowed."""
    if not text:
        return "Please describe your finance transformation challenge first."

    lowered = text.lower()

    for word in FORBIDDEN_KEYWORDS:
        if word in lowered:
            return (
                "This copilot supports **finance/business transformation** only. "
                "Sexual, violent, illegal or harmful topics are blocked."
            )

    for word in NON_FINANCE_TOPICS:
        if word in lowered:
            return (
                "It looks like your question is not related to **finance transformation**. "
                "Please describe R2R, P2P, O2C, FP&A, intercompany, consolidation, "
                "close, or process/tech/people challenges."
            )

    if len(text) > 4000:
        return "Please summarise your challenge in under 4,000 characters."

    return None


# -------------------------------------------------------
# UI Rendering
# -------------------------------------------------------
def render_header() -> None:
    st.title("🧠 Bivenue Copilot")
    st.caption("Your AI Advisor for Finance Transformation.")


def render_input() -> str:
    st.subheader("Describe your finance transformation challenge")
    return st.text_area(
        label="Describe your finance transformation challenge",
        placeholder=(
            "e.g., 'Intercompany mismatches causing consolidation delays across "
            "entities using SAP and BlackLine; manual Excel reconciliations; "
            "unclear ownership between GBS and controllers.'"
        ),
        height=160,
        label_visibility="collapsed",
    )


def render_result(domain: str, recommendations: str, challenge: str) -> None:
    st.success("Rule-based diagnostic complete.")

    st.subheader("1) Detected Finance Domain")
    st.write(f"**Domain:** {domain}")

    with st.expander("See original problem statement"):
        st.write(challenge)

    st.subheader("2) Recommended Focus Areas & Actions")
    st.markdown(recommendations)

    st.info(
        "This is a rule-based V1 engine. Future versions will use your playbooks, "
        "historical data, and LLMs to refine the diagnosis."
    )


# -------------------------------------------------------
# AI Deep-Dive Section
# -------------------------------------------------------
def render_ai_section(challenge: str, domain: str, recommendations: str) -> None:
    st.divider()
    st.subheader("3) AI Deep-Dive Analysis (experimental)")

    ai_brief: Optional[str] = None
    ai_error: Optional[str] = None

    try:
        with st.spinner("Asking the AI copilot for a deeper analysis…"):
            ai_brief = generate_ai_analysis(
                problem=challenge,
                domain=domain,
                rule_based_summary=recommendations,
            )
    except LLMNotConfigured as e:
        ai_error = str(e)
    except Exception as e:
        ai_error = f"AI error: {e}"

    # --- Display AI result ---
    if ai_brief:
        st.markdown(ai_brief)

        # --- PDF Generation ---
        pdf_bytes = create_consulting_brief_pdf(
            logo_path="engine/bivenue_logo.png",  # correct path
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
            label="📥 Download 1-page Consulting Brief (PDF)",
            data=pdf_bytes,
            file_name="bivenue_finance_brief.pdf",
            mime="application/pdf",
        )

    elif ai_error:
        st.warning(ai_error)


# -------------------------------------------------------
# Main App
# -------------------------------------------------------
def main() -> None:
    render_header()
    challenge = render_input()

    if st.button("Diagnose", type="primary"):
        # 1. Validate content
        error_message = validate_challenge_input(challenge.strip())
        if error_message:
            st.warning(error_message)
            return

        # 2. Run rule-based engine
        with st.spinner("Running rule-based diagnostic…"):
            domain = classify_domain(challenge)
            recommendations = generate_recommendations(domain, challenge)

        # 3. Show results
        render_result(domain, recommendations, challenge)

        # 4. AI expansion
        render_ai_section(challenge, domain, recommendations)


if __name__ == "__main__":
    main()
