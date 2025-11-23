import streamlit as st

from engine.classifier import classify_domain
from engine.generator import generate_recommendations


st.set_page_config(page_title="Bivenue Copilot", layout="wide")


def render_header():
    st.title("🧠 Bivenue Copilot")
    st.caption("Your AI Advisor for Finance Transformation.")


def render_input() -> str:
    st.subheader("Describe your finance transformation challenge")
    challenge = st.text_area(
        label="Describe your finance transformation challenge",
        placeholder="e.g., 'Intercompany mismatches causing consolidation delays across entities using SAP and BlackLine'",
        height=160,
        label_visibility="collapsed",
    )
    return challenge


def render_result(domain: str, recommendations: str, challenge: str):
    st.success("Diagnostic complete.")

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


def main():
    render_header()
    challenge = render_input()

    if st.button("Diagnose", type="primary"):
        if not challenge.strip():
            st.warning("Please describe your challenge first.")
            return

        with st.spinner("Analyzing your challenge..."):
            domain = classify_domain(challenge)
            recommendations = generate_recommendations(domain, challenge)

        render_result(domain, recommendations, challenge)


if __name__ == "__main__":
    main()
