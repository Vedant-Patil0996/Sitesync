from statistics import mean


def compare_with_peers(
    contractor_usage,
    peer_usage,
):
    """
    Compare one contractor against other contractors.

    contractor_usage: resource usage of the target contractor
    peer_usage: list of resource usage values from comparable contractors
    """

    if not peer_usage:
        return {
            "status": "insufficient_data",
            "risk_score": 0.0,
            "reasons": ["No peer contractor data available."]
        }

    peer_average = mean(peer_usage)

    deviation_percent = (
        (contractor_usage - peer_average) / peer_average * 100
        if peer_average > 0 else 0
    )

    reasons = []
    risk = 0.0

    if deviation_percent > 50:
        risk = 0.75
        reasons.append(
            f"Contractor usage is {deviation_percent:.1f}% "
            f"above the peer average."
        )

    elif deviation_percent > 30:
        risk = 0.50
        reasons.append(
            f"Contractor usage is {deviation_percent:.1f}% "
            f"above the peer average."
        )

    elif deviation_percent > 15:
        risk = 0.25
        reasons.append(
            f"Contractor usage is {deviation_percent:.1f}% "
            f"above the peer average."
        )

    return {
        "contractor_usage": contractor_usage,
        "peer_average": round(peer_average, 2),
        "deviation_percent": round(deviation_percent, 2),
        "risk_score": risk,
        "reasons": reasons
    }