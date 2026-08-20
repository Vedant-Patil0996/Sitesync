def verify_qr(
    expected_quantity,
    actual_quantity,
    po_match=True,
    material_match=True,
    site_match=True,
    vendor_match=True,
    qr_already_used=False
):
    """
    Verify whether a QR-scanned delivery/resource record
    is consistent with the expected procurement record.

    Returns a risk score between 0 and 1.
    """

    risk_score = 0.0
    reasons = []

    # ---------------------------------------------------------
    # 1. PO IDENTITY CHECK
    # ---------------------------------------------------------
    if not po_match:
        risk_score += 0.30
        reasons.append("QR record does not match the expected purchase order.")

    # ---------------------------------------------------------
    # 2. MATERIAL IDENTITY CHECK
    # ---------------------------------------------------------
    if not material_match:
        risk_score += 0.25
        reasons.append("Scanned material does not match the expected material.")

    # ---------------------------------------------------------
    # 3. SITE IDENTITY CHECK
    # ---------------------------------------------------------
    if not site_match:
        risk_score += 0.20
        reasons.append("Scanned site does not match the expected delivery site.")

    # ---------------------------------------------------------
    # 4. VENDOR IDENTITY CHECK
    # ---------------------------------------------------------
    if not vendor_match:
        risk_score += 0.15
        reasons.append("Scanned vendor does not match the expected vendor.")

    # ---------------------------------------------------------
    # 5. DUPLICATE QR CHECK
    # ---------------------------------------------------------
    if qr_already_used:
        risk_score += 0.35
        reasons.append("QR code has already been used.")

    # ---------------------------------------------------------
    # 6. QUANTITY CHECK
    # ---------------------------------------------------------
    if expected_quantity <= 0:
        quantity_difference_percent = 0
    else:
        quantity_difference = abs(expected_quantity - actual_quantity)
        quantity_difference_percent = (
            quantity_difference / expected_quantity
        ) * 100

        if quantity_difference_percent > 25:
            risk_score += 0.30
            reasons.append(
                f"Actual quantity differs from expected quantity by "
                f"{quantity_difference_percent:.1f}%."
            )

        elif quantity_difference_percent > 10:
            risk_score += 0.15
            reasons.append(
                f"Actual quantity differs from expected quantity by "
                f"{quantity_difference_percent:.1f}%."
            )

        elif quantity_difference_percent > 0:
            risk_score += 0.05
            reasons.append(
                f"Actual quantity is {quantity_difference_percent:.1f}% "
                f"different from expected quantity."
            )

    # Keep score within [0, 1]
    risk_score = min(risk_score, 1.0)

    return {
        "expected_quantity": expected_quantity,
        "actual_quantity": actual_quantity,
        "quantity_difference": abs(expected_quantity - actual_quantity),
        "quantity_difference_percent": round(
            quantity_difference_percent, 2
        ),

        "po_match": po_match,
        "material_match": material_match,
        "site_match": site_match,
        "vendor_match": vendor_match,
        "qr_already_used": qr_already_used,

        "risk_score": round(risk_score, 2),
        "risk_percent": round(risk_score * 100, 1),
        "reasons": reasons
    }