"""
chat_agent.py
-------------
A lightweight ReAct-style conversational agent for natural-language
operational queries against the SiteSync database.

Unlike the alert orchestrator (orchestrator.py) which is triggered by
automated anomaly detection, this agent is triggered on-demand by a user
question from the chat bubble or an MCP client.

Flow:
  user question -> agent (reasons + calls tools) -> loops until done -> final answer
"""

import operator
from typing import Annotated, Sequence, TypedDict, Optional

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from ai.agent.config import (
    list_sites,
    list_materials,
    get_transaction_history,
    compare_across_sites,
    get_consumption_rate_history,
    get_pending_requests_and_pos,
    get_budget_actuals,
    get_expense_breakdown_by_category,
    get_po_history,
    get_vendor_price_trend,
    compare_vendor_quotes,
    get_equipment_status,
    find_replacement_equipment,
    reallocate_equipment,
    get_task_dependencies,
    calculate_delay_impact,
    evaluate_vendor_reliability,
    get_market_price_benchmark,
    search_historical_records,
)

# ── All tools available to the chat agent ────────────────────────────────────

ALL_TOOLS = [
    list_sites,
    list_materials,
    get_transaction_history,
    compare_across_sites,
    get_consumption_rate_history,
    get_pending_requests_and_pos,
    get_budget_actuals,
    get_expense_breakdown_by_category,
    get_po_history,
    get_vendor_price_trend,
    compare_vendor_quotes,
    get_equipment_status,
    find_replacement_equipment,
    reallocate_equipment,
    get_task_dependencies,
    calculate_delay_impact,
    evaluate_vendor_reliability,
    get_market_price_benchmark,
    search_historical_records,
]

# ── LLM ──────────────────────────────────────────────────────────────────────

_llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0)
_llm_with_tools = _llm.bind_tools(ALL_TOOLS)

MAX_TOOL_ROUNDS = 5

# ── System prompt ─────────────────────────────────────────────────────────────

CHAT_SYSTEM_PROMPT = SystemMessage(content=(
    "You are SiteSync Assistant, a helpful AI for construction site operations.\n"
    "You have access to live database tools for stock, budget, equipment, project tasks, and procurement.\n\n"
    "ID LOOKUP RULES — CRITICAL:\n"
    "- site_id, material_id, vendor_id, task_id MUST be PURE NUMERIC STRINGS (e.g. '42', '7').\n"
    "- NEVER guess IDs like 'site_1', 'Site A', or '1' without looking them up first.\n"
    "- When user mentions a site by name (e.g. 'Site 1', 'Northwood'), call list_sites() FIRST\n"
    "  to get the real numeric ID, THEN call the site-specific tool with that ID.\n"
    "- When user mentions a material by name (e.g. 'cement', 'steel'), call list_materials() FIRST.\n"
    "- For general questions with no specific site/material, use search_historical_records.\n\n"
    "ANSWER RULES:\n"
    "1. Use tools to get real data — never fabricate numbers.\n"
    "2. Keep answers concise and in plain English. Use bullet points for lists.\n"
    "3. Cite data inline: e.g. [sites: 42] or [equipment: EXC-01].\n"
    "4. If tools return empty or error: say 'No data available for [topic]'.\n"
    "5. Stop after 5 tool calls and answer with what you have.\n"
    "6. For greetings or general questions needing no DB data, answer directly.\n"
))


# ── Graph state ───────────────────────────────────────────────────────────────

class ChatState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]


# ── Graph nodes ───────────────────────────────────────────────────────────────

def agent_node(state: ChatState) -> dict:
    """Main reasoning node - decides what to say or which tools to call."""
    response = _llm_with_tools.invoke([CHAT_SYSTEM_PROMPT] + list(state["messages"]))
    return {"messages": [response]}


def should_continue(state: ChatState) -> str:
    """Route back to tools, or end if done."""
    last = state["messages"][-1]
    tool_rounds = sum(1 for m in state["messages"] if getattr(m, "type", None) == "tool")
    if getattr(last, "tool_calls", None) and tool_rounds < MAX_TOOL_ROUNDS:
        return "tools"
    return END


# ── Build graph ───────────────────────────────────────────────────────────────

_tools_node = ToolNode(ALL_TOOLS)

_graph = StateGraph(ChatState)
_graph.add_node("agent", agent_node)
_graph.add_node("tools", _tools_node)
_graph.add_edge(START, "agent")
_graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
_graph.add_edge("tools", "agent")

chat_app = _graph.compile()


# ── Public entrypoint ─────────────────────────────────────────────────────────

def run_chat(
    question: str,
    site_id: Optional[str] = None,
    company_id: Optional[str] = None,
) -> str:
    """
    Run a natural-language question through the chat agent.

    Args:
        question:   Plain-English question from the user or MCP client.
        site_id:    Optional numeric site context (e.g. "2").
        company_id: Optional numeric company context.

    Returns:
        A markdown-formatted answer grounded in real database data.
    """
    # Inject optional context into the user message
    context_parts = []
    if site_id:
        context_parts.append(f"site_id={site_id}")
    if company_id:
        context_parts.append(f"company_id={company_id}")

    user_content = question
    if context_parts:
        user_content = f"[Context: {', '.join(context_parts)}]\n\n{question}"

    initial_state: ChatState = {"messages": [HumanMessage(content=user_content)]}
    final_state = chat_app.invoke(initial_state, {"recursion_limit": 20})

    # Return the last AI message that has text content
    for msg in reversed(final_state["messages"]):
        if getattr(msg, "type", None) == "ai" and msg.content:
            return msg.content

    return "I could not find relevant data for your question. Please try rephrasing."
