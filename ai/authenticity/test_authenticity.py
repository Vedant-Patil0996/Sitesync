# from consumption import analyze_consumption
# from peer_comparison import compare_with_peers
# from qr_verification import verify_delivery
# from risk_score import calculate_authenticity_risk


# # -----------------------------------
# # 1. Contractor's historical pattern
# # -----------------------------------

# consumption = analyze_consumption(
#     historical_usage=[
#         100,
#         105,
#         110,
#         98,
#         108,
#         102
#     ],
#     current_request=180,
#     task_progress_percent=40
# )


# # -----------------------------------
# # 2. Compare against other contractors
# # -----------------------------------

# peer = compare_with_peers(
#     contractor_usage=180,
#     peer_usage=[
#         105,
#         110,
#         100,
#         115,
#         108
#     ]
# )


# # -----------------------------------
# # 3. Verify delivery
# # -----------------------------------

# qr = verify_delivery(
#     expected_quantity=180,
#     actual_quantity=150,
#     qr_expected_po="PO-1023",
#     scanned_po="PO-1023"
# )


# # -----------------------------------
# # 4. Final authenticity risk
# # -----------------------------------

# result = calculate_authenticity_risk(
#     consumption_result=consumption,
#     peer_result=peer,
#     qr_result=qr
# )


# print("\n========== CONSUMPTION ==========")
# print(consumption)

# print("\n========== PEER COMPARISON ==========")
# print(peer)

# print("\n========== QR VERIFICATION ==========")
# print(qr)

# print("\n========== FINAL AUTHENTICITY ==========")
# print(result)


from qr_verification import verify_qr


print("\n========== QR — GENUINE ==========")

print(
    verify_qr(
        expected_quantity=180,
        actual_quantity=180,
        po_match=True,
        material_match=True,
        site_match=True,
        vendor_match=True,
        qr_already_used=False
    )
)


print("\n========== QR — QUANTITY MISMATCH ==========")

print(
    verify_qr(
        expected_quantity=180,
        actual_quantity=120,
        po_match=True,
        material_match=True,
        site_match=True,
        vendor_match=True,
        qr_already_used=False
    )
)


print("\n========== QR — SUSPICIOUS ==========")

print(
    verify_qr(
        expected_quantity=180,
        actual_quantity=180,
        po_match=True,
        material_match=True,
        site_match=False,
        vendor_match=False,
        qr_already_used=True
    )
)