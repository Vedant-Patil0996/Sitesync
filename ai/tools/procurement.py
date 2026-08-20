import json
from typing import Dict, Any, List

def evaluate_vendor_reliability(vendor_id: str) -> Dict[str, Any]:
    """Evaluate a vendor's historical performance, delivery times, and quality issues."""
    # Mocked for hackathon demo
    return {
        "vendor_id": vendor_id,
        "on_time_delivery_rate": 82.5,
        "quality_reject_rate": 2.1,
        "average_lead_time_days": 4,
        "historical_issues": [
            "Delayed delivery on 2025-11-04 (Weather)",
            "Partial delivery on 2026-03-12 (Stockout)"
        ]
    }

def get_market_price_benchmark(material_id: str) -> Dict[str, Any]:
    """Get the current regional market benchmark price for a material."""
    return {
        "material_id": material_id,
        "regional_avg_price": 450.00,
        "price_trend_30d": "+5%",
        "supply_chain_status": "Strained - High Demand"
    }
