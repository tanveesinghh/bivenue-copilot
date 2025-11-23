def classify_domain(text: str):
    """
    Very simple rule-based classifier.
    Replace this later with AI logic.
    """
    text = text.lower()

    if "intercompany" in text:
        return "Intercompany"
    if "consolidation" in text:
        return "Consolidation"
    if "p2p" in text or "procure" in text:
        return "P2P"
    if "o2c" in text or "order" in text:
        return "O2C"
    if "r2r" in text or "record" in text or "close" in text:
        return "R2R"

    return "General Finance"
