import streamlit as st

st.set_page_config(page_title="Bivenue Copilot", layout="wide")

st.title("🧠 Bivenue Copilot")
st.write("Your AI Advisor for Finance Transformation.")

problem = st.text_area("Describe your finance transformation challenge")

if st.button("Diagnose"):
    if not problem.strip():
        st.warning("Please describe your challenge.")
    else:
        st.success("Diagnosis complete! (This is placeholder output)")
        st.write("""
        The full AI engine will:
        - Classify the challenge (R2R, IC, FP&A, P2P, O2C)
        - Identify root causes across Process, Tech, Org, Data, Policy
        - Generate a consultant-grade PDF brief
        - Provide a transformation roadmap (quick wins → 6–12 months)
        """)
