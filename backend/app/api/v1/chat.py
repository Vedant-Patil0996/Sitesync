"""
backend/app/api/v1/chat.py
--------------------------
REST endpoint for the SiteSync conversational chat assistant.

POST /api/v1/chat/
  - Accepts a plain-English question from the frontend chat bubble
  - Runs it through the chat_agent (LangGraph ReAct agent)
  - Returns a JSON response with the markdown answer
"""

import os
import sys
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import require_role
from app.models.user import User

router = APIRouter()


# ── Request / Response schemas ────────────────────────────────────────────────

class ChatRequest(BaseModel):
    question: str
    site_id: Optional[str] = None
    company_id: Optional[str] = None


class ChatResponse(BaseModel):
    question: str
    answer: str


# ── Helper: ensure project root on sys.path ───────────────────────────────────

def _ensure_ai_on_path():
    project_root = os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.dirname(os.path.abspath(__file__))
                )
            )
        )
    )
    if project_root not in sys.path:
        sys.path.insert(0, project_root)


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post("/", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "pm", "finance", "contractor")),
):
    """
    Natural language operational query endpoint.

    The frontend chat bubble POSTs here with the user's question.
    The endpoint passes it to the chat agent which queries the live
    database and returns a grounded markdown answer.

    Example request:
        POST /api/v1/chat/
        { "question": "What is the budget status for Site 2?", "site_id": "2" }
    """
    if not body.question or not body.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    _ensure_ai_on_path()

    try:
        import asyncio
        from ai.agent.chat_agent import run_chat

        loop = asyncio.get_running_loop()
        answer = await loop.run_in_executor(
            None,
            run_chat,
            body.question.strip(),
            body.site_id,
            body.company_id,
        )
        return ChatResponse(question=body.question, answer=answer)

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Chat agent error: {str(exc)}")
