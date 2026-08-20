from statistics import mean, stdev


def analyze_consumption(
    historical_usage,
    current_request,
    task_progress_percent,
):
    """
    Analyze whether a contractor's current resource request
    is unusual compared with their historical usage.

    historical_usage: list of previous quantities used/requested
    current_request: current requested quantity
    task_progress_percent: current task completion percentage
    """

    if not historical_usage:
        return {
            "status": "insufficient_data",
            "risk_score": 0.0,
            "reasons": ["No historical usage data available."]
        }

    historical_avg = mean(historical_usage)

    # Percentage difference from historical average
    increase_percent = (
        (current_request - historical_avg) / historical_avg * 100
        if historical_avg > 0 else 0
    )

    # Estimate expected usage based on historical average
    # relative to task progress.
    expected_usage = historical_avg * (task_progress_percent / 100)

    progress_deviation_percent = (
        (current_request - expected_usage) / expected_usage * 100
        if expected_usage > 0 else 0
    )

    reasons = []
    risk = 0.0

    # Signal 1: request much higher than historical usage
    if increase_percent > 50:
        risk += 0.35
        reasons.append(
            f"Current request is {increase_percent:.1f}% above historical average."
        )
    elif increase_percent > 25:
        risk += 0.20
        reasons.append(
            f"Current request is {increase_percent:.1f}% above historical average."
        )

    # Signal 2: request high relative to task progress
    if progress_deviation_percent > 75:
        risk += 0.35
        reasons.append(
            f"Requested quantity is {progress_deviation_percent:.1f}% "
            f"above expected usage for current task progress."
        )
    elif progress_deviation_percent > 40:
        risk += 0.20
        reasons.append(
            f"Requested quantity is {progress_deviation_percent:.1f}% "
            f"above expected usage for current task progress."
        )

    return {
        "historical_average": round(historical_avg, 2),
        "current_request": current_request,
        "task_progress_percent": task_progress_percent,
        "increase_percent": round(increase_percent, 2),
        "expected_usage": round(expected_usage, 2),
        "progress_deviation_percent": round(progress_deviation_percent, 2),
        "risk_score": round(min(risk, 1.0), 2),
        "reasons": reasons
    }