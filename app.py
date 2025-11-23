import streamlit as st

from engine.classifier import classify_domain
from engine.root_cause import assess_root_causes
from engine.roadmap import build_roadmap


st.set_page_config(page_title="Bivenue Copilot", layout="wide")


def render_header():
    st.title("🧠 Bivenue Copilot")
    st.caption("AI-assisted advisor for Finance Transformation.")


def render_input():
    st.subheader("Describe your finance transformation challenge")
    problem = st.text_area(
        "Give as much context as you can — current pain, impacted teams, systems, geographies.",
        height=200,
        label_visibility="collapsed",
    )
    return problem


def render_classification(primary_domain, scores_by_domain):
    st.subheader("1) Where does this sit in the finance value chain?")
    st.write(f"**Primary domain:** {primary_domain}")

    with st.expander("See domain scoring"):
        for domain, score in scores_by_domain.items():
            bar = "▮" * score if score > 0 else "·"
            st.write(f"- {domain}: {score} {bar}")


def render_root_causes(dim_scores, dim_narratives):
    st.subheader("2) Likely root-cause dimensions")

    cols = st.columns(len(dim_scores))
    for i, (dim, score) in enumerate(dim_scores.items()):
        with cols[i]:
            st.markdown(f"**{dim}**")
            st.write(f"Score: {score}")
            st.caption(dim_narratives.get(dim, ""))


def render_roadmap(roadmap):
    st.subheader("3) High-level transformation roadmap")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### Quick wins (0–8 weeks)")
        for item in roadmap["quick_wins"]:
            st.write(f"- {item}")

    with col2:
        st.markdown("### 3–6 months")
        for item in roadmap["mid_term"]:
            st.write(f"- {item}")

    with col3:
        st.markdown("### 6–12 months")
        for item in roadmap["long_term"]:
            st.write(f"- {item}")

    for note in roadmap.get("note", []):
        st.caption(note)


def main():
    render_header()
    problem = render_input()

    if st.button("Diagnose", type="primary"):
        if not problem.strip():
            st.warning("Please describe your challenge first.")
            return

        with st.spinner("Running rule-based diagnostic..."):
            primary_domain, domain_scores = classify_domain(problem)
            dim_scores, dim_narratives = assess_root_causes(problem)
            roadmap = build_roadmap(primary_domain, dim_scores)

        st.success("Diagnostic complete.")
        st.divider()

        render_classification(primary_domain, domain_scores)
        st.divider()
        render_root_causes(dim_scores, dim_narratives)
        st.divider()
        render_roadmap(roadmap)

        st.info(
            "This is a rule-based v1 engine. "
            "Next iterations will use LLMs, your playbook, and historical data to refine recommendations."
        )


if __name__ == "__main__":
    main()
