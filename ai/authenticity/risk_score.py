def calculate_authenticity_risk(
    consumption_result,
    peer_result,
    qr_result=None
):
    """
    Combine independent authenticity signals.

    Current weights:
        Consumption = 40%
        Peer comparison = 30%
        QR verification = 30%
    """

    consumption_score = consumption_result.get("risk_score", 0.0)
    peer_score = peer_result.get("risk_score", 0.0)

    if qr_result:
        qr_score = qr_result.get("risk_score", 0.0)

        final_score = (
            0.40 * consumption_score +
            0.30 * peer_score +
            0.30 * qr_score
        )
    else:
        # If QR data is unavailable, don't pretend it was verified.
        final_score = (
            0.60 * consumption_score +
            0.40 * peer_score
        )

    if final_score >= 0.70:
        level = "HIGH"
    elif final_score >= 0.40:
        level = "MEDIUM"
    else:
        level = "LOW"

    reasons = []

    reasons.extend(consumption_result.get("reasons", []))
    reasons.extend(peer_result.get("reasons", []))

    if qr_result:
        reasons.extend(qr_result.get("reasons", []))

    return {
        "risk_score": round(final_score, 2),
        "risk_percent": round(final_score * 100, 1),
        "risk_level": level,
        "reasons": reasons
    }