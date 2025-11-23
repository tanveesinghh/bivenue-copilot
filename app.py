import streamlit as st

st.set_page_config(page_title="Bienvenue Copilot", layout="wide")

st.title("🧠 Bienvenue Copilot")
st.write("Your AI Advisor for Finance Transformation.")

# Text input
challenge = st.text_area(
    "Describe your finance transformation challenge",
    placeholder="e.g., 'Intercompany mismatches causing consolidation delays'"
)

# Simple placeholder logic (remove when real engine is ready)
def diagnose(challenge_text):
    if "intercompany" in challenge_text.lower():
        return "Likely root cause: Poor IC eliminations, mismatched entities, or missing mappings."
    elif "p2p" in challenge_text.lower():
        return "Likely root cause: Vendor master issues, invoice exceptions, GR/IR mismatches."
    elif "o2c" in challenge_text.lower():
        return "Likely root cause: Credit management gaps, billing delays, unapplied cash."
    elif "r2r" in challenge_text.lower():
        return "Likely root cause: Journal errors, late adjustments, manual reconciliations."
    else:
        return "Challenge detected. The Copilot will diagnose once the engine is connected."

# Diagnose button
if st.button("Diagnose"):
    if challenge.strip():
        st.subheader("Diagnosis")
        st.write(diagnose(challenge))
    else:
        st.warning("Please enter a challenge first.")
