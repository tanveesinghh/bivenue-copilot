from typing import Optional

import streamlit as st

from engine.classifier import classify_domain
from engine.generator import generate_recommendations
from engine.llm import generate_ai_analysis, LLMNotConfigured


st.set_page_config(page_title="Bivenue Copilot", layout="wide")


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
      except LLMNotConfigured as e:
        ai_error = str(e)
    except Exception as e:
        # Show the real error message so we can debug
        ai_error = f"AI error: {e}"


    if ai_brief:
        st.markdown(ai_brief)
    elif ai_error:
        st.warning(ai_error)


def main() -> None:
    render_header()
    challenge = render_input()

    if st.button("Diagnose", type="primary"):
        if not challenge.strip():
            st.warning("Please describe your challenge first.")
            return

        with st.spinner("Running rule-based diagnostic..."):
            domain = classify_domain(challenge)
            recommendations = generate_recommendations(domain, challenge)

        render_result(domain, recommendations, challenge)
        render_ai_section(challenge, domain, recommendations)


if __name__ == "__main__":
    main()
