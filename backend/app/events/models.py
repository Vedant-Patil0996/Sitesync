from datetime import datetime
from typing import Optional, Any, Dict
import uuid


def make_event(
    run_id: str,
    type: str,
    agent: str,
    content: str,
    tool_name: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
) -> dict:
    """Build a standardized agent event dict."""
    return {
        "id": f"evt_{uuid.uuid4().hex[:8]}",
        "run_id": run_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "type": type,          # e.g. RUN_STARTED, AGENT_STARTED, TOOL_STARTED, MESSAGE, RUN_COMPLETED
        "agent": agent,        # e.g. SYSTEM, SUPERVISOR, EQUIPMENT_AGENT, DB_SYSTEM, REPORTER
        "content": content,
        "tool_name": tool_name,
        "data": data or {},
    }
