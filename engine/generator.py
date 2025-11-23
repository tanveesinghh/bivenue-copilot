def generate_recommendations(domain: str, text: str):
    """
    Produce transformation recommendations based on the identified domain.
    This is a placeholder. Later we will replace it with AI-powered logic.
    """

    if domain == "Intercompany":
        return """
        🔍 **Intercompany Root Cause Diagnosis**
        - Mismatched transaction timing
        - Lack of automated matching rules
        - Missing entity-level reconciliation governance

        🚀 **Recommended Actions**
        1. Implement automated IC reconciliation in SAP / Oracle.
        2. Create standardized IC templates & entity-level deadlines.
        3. Introduce rule-based matching (amount, currency, tolerance).
        """

    if domain == "Consolidation":
        return """
        🔍 **Consolidation Root Cause Diagnosis**
        - Late submissions from entities
        - Manual consolidation adjustments
        - Lack of validations before group close

        🚀 **Recommended Actions**
        1. Introduce pre-close validation checks.
        2. Automate consolidation journals in BlackLine / OneStream.
        3. Enforce entity-level submission SLAs.
        """

    if domain == "P2P":
        return """
        🔍 **P2P Diagnosis**
        - Invoice exceptions causing delays
        - Vendor master inconsistencies
        - Manual PO approvals

        🚀 **Recommended Actions**
        1. Implement 3-way match automation.
        2. Establish vendor master governance.
        3. Digitize PO approval workflow.
        """

    if domain == "O2C":
        return """
        🔍 **O2C Diagnosis**
        - Delayed billing
        - Manual cash application
        - Credit management inefficiencies

        🚀 **Recommended Actions**
        1. Automate billing triggers.
        2. Deploy cash application tools (HighRadius).
        3. Implement credit scoring & DSO dashboards.
        """

    if domain == "R2R":
        return """
        🔍 **R2R Diagnosis**
        - Manual journal entries
        - Delayed reconciliations
        - Lack of standardized close checklist

        🚀 **Recommended Actions**
        1. Automate recurring journals in ERP.
        2. Implement BlackLine reconciliations.
        3. Deploy a global month-end close calendar.
        """

    return """
    🚀 **General Transformation Recommendations**
    1. Assess AS-IS → TO-BE processes.
    2. Define automation roadmap.
    3. Standardize controls & governance.
    4. Align Process + Tech + Data + People.
    """
