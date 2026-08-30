import operator
import json
import time
import os
import sys
import uuid
from datetime import datetime, timedelta
from typing import Annotated, Sequence, TypedDict, Literal, Optional, Callable

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from ai.agent.config import WORKER_CONFIG


# ── Event emission ─────────────────────────────────────────────────────────────

# Global run_id and emitter — set once per execution by handle_alert()
_run_id: str = ""
_emit: Optional[Callable[[dict], None]] = None


def _make_event(type: str, agent: str, content: str, tool_name: Optional[str] = None, data: Optional[dict] = None) -> dict:
    return {
        "id": f"evt_{uuid.uuid4().hex[:8]}",
        "run_id": _run_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "type": type,
        "agent": agent,
        "content": content,
        "tool_name": tool_name,
        "data": data or {},
    }


def _emit_event(type: str, agent: str, content: str, tool_name: Optional[str] = None, data: Optional[dict] = None):
    """Print a JSON event line to stdout so the FastAPI process can read and broadcast it."""
    evt = _make_event(type, agent, content, tool_name, data)
    # Print JSON event so FastAPI subprocess reader picks it up
    print(json.dumps(evt, ensure_ascii=False), flush=True)


# ── Graph state ────────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_node: str
    visited_nodes: Annotated[Sequence[str], operator.add]


# Use Groq's flagship model
llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)


# ── Node helpers ───────────────────────────────────────────────────────────────

_AGENT_LABEL = {
    "anomaly_detector": "ANOMALY_DETECTOR",
    "supervisor": "SUPERVISOR",
    "stock_agent": "STOCK_AGENT",
    "budget_agent": "BUDGET_AGENT",
    "equipment_agent": "EQUIPMENT_AGENT",
    "project_agent": "PROJECT_AGENT",
    "procurement_agent": "PROCUREMENT_AGENT",
    "reporter": "REPORTER",
}


# ── Graph nodes ────────────────────────────────────────────────────────────────

def anomaly_detector_node(state: AgentState) -> dict:
    _emit_event("AGENT_STARTED", "ANOMALY_DETECTOR", "Analyzing incoming alert...")
    raw_log = state["messages"][0].content
    prompt = SystemMessage(content=(
        "You are the Anomaly Detection Engine for a construction site.\n"
        "Analyze the following raw operational log (JSON). Determine if it represents a problem (e.g. low stock, excessive consumption, budget drift, equipment failure).\n"
        "Translate the raw JSON into a clear, urgent natural language alert for the Supervisor. Do NOT solve the problem, just report the anomaly clearly."
    ))
    response = llm.invoke([prompt, HumanMessage(content=raw_log)])
    _emit_event("AGENT_COMPLETED", "ANOMALY_DETECTOR", response.content)
    return {"messages": [HumanMessage(content=response.content)]}


def _clean_messages_for_non_tool_nodes(messages: list) -> list:
    """
    Sanitize messages by converting raw ToolMessages and tool-calling AIMessages into plain text.
    This prevents Groq API 400 errors ('Tool choice is none, but model called a tool')
    when invoking non-tool LLM calls (like supervisor and reporter) with context history.
    """
    clean = []
    for msg in messages:
        msg_type = getattr(msg, "type", None)
        if msg_type == "tool":
            tool_name = getattr(msg, "name", "tool")
            content_str = msg.content if isinstance(msg.content, str) else json.dumps(msg.content)
            clean.append(HumanMessage(content=f"[Tool result — {tool_name}]: {content_str[:500]}"))
        elif msg_type == "ai":
            tc = getattr(msg, "tool_calls", None)
            if msg.content:
                from langchain_core.messages import AIMessage
                clean.append(AIMessage(content=msg.content))
            elif tc:
                calls_str = ", ".join(tc[i]["name"] for i in range(len(tc)))
                clean.append(HumanMessage(content=f"[Agent called tools: {calls_str}]"))
        else:
            clean.append(msg)
    return clean


def supervisor_node(state: AgentState) -> dict:
    visited = list(state.get("visited_nodes", []))
    visited_str = ", ".join(set(visited)) if visited else "None"
    _emit_event("AGENT_STARTED", "SUPERVISOR", f"Deciding next agent. Already visited: [{visited_str}]")

    supervisor_prompt = SystemMessage(content=(
        "You are the Master Supervisor. Review the entire conversation history.\n"
        f"Agents already visited so far: [{visited_str}].\n"
        "RULES:\n"
        "1. Do NOT re-route to any agent that has ALREADY completed its investigation in the list above!\n"
        "2. If all relevant agents for this issue have completed, output 'FINISH'.\n"
        "3. You must output a strictly valid JSON object with exactly two keys: 'reasoning' and 'next_node'.\n"
        "Valid next nodes are: 'stock_agent', 'budget_agent', 'equipment_agent', 'project_agent', 'procurement_agent', or 'FINISH'.\n"
        "Example output:\n"
        "{\n"
        "  \"reasoning\": \"The equipment agent completed its report. The project agent also completed schedule analysis. No other agents needed.\",\n"
        "  \"next_node\": \"FINISH\"\n"
        "}\n"
        "Output ONLY the JSON object, nothing else."
    ))
    time.sleep(1.5)
    
    clean_messages = _clean_messages_for_non_tool_nodes(state["messages"])
    
    try:
        response = llm.invoke([supervisor_prompt] + clean_messages)
    except Exception as e:
        _emit_event("MESSAGE", "SYSTEM", f"Supervisor LLM error: {str(e)[:100]}... defaulting to FINISH")
        _emit_event("AGENT_COMPLETED", "SUPERVISOR", "Defaulting to FINISH due to API error", data={"next_node": "FINISH"})
        return {"next_node": "FINISH", "visited_nodes": []}

    try:
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
        data = json.loads(content)
        next_node = data.get("next_node", "FINISH")
        reasoning = data.get("reasoning", "No reasoning provided.")
        _emit_event("AGENT_COMPLETED", "SUPERVISOR", reasoning, data={"next_node": next_node})
    except Exception:
        _emit_event("AGENT_COMPLETED", "SUPERVISOR", f"Parse error — defaulting to FINISH", data={"next_node": "FINISH"})
        next_node = "FINISH"

    valid_agents = ["stock_agent", "budget_agent", "equipment_agent", "project_agent", "procurement_agent"]
    if next_node in visited and next_node in valid_agents:
        next_node = "FINISH"
    elif next_node not in valid_agents:
        next_node = "FINISH"

    _emit_event("MESSAGE", "SUPERVISOR", f"Routing to: {next_node}")

    new_visited = [next_node] if next_node != "FINISH" else []
    return {"next_node": next_node, "visited_nodes": new_visited}


def _worker_node(key: str, agent_label: str, state: AgentState) -> dict:
    _emit_event("AGENT_STARTED", agent_label, f"Starting investigation...")
    prompt = SystemMessage(content=WORKER_CONFIG[key]["system_prompt"])
    worker_llm = llm.bind_tools(WORKER_CONFIG[key]["tools"])
    time.sleep(1.5)
    response = worker_llm.invoke([prompt] + state["messages"])

    if response.tool_calls:
        for tc in response.tool_calls:
            _emit_event("TOOL_STARTED", agent_label, f"Calling tool: {tc['name']}", tool_name=tc["name"], data={"args": tc.get("args", {})})
    else:
        _emit_event("AGENT_COMPLETED", agent_label, response.content or "Investigation done.")

    return {"messages": [response]}


def stock_agent_node(state: AgentState) -> dict:
    return _worker_node("stock", "STOCK_AGENT", state)

def budget_agent_node(state: AgentState) -> dict:
    return _worker_node("budget", "BUDGET_AGENT", state)

def equipment_agent_node(state: AgentState) -> dict:
    return _worker_node("equipment", "EQUIPMENT_AGENT", state)

def project_agent_node(state: AgentState) -> dict:
    return _worker_node("project", "PROJECT_AGENT", state)

def procurement_agent_node(state: AgentState) -> dict:
    return _worker_node("procurement", "PROCUREMENT_AGENT", state)


def _tool_node_with_emit(key: str, agent_label: str):
    """Wraps ToolNode to emit TOOL_COMPLETED after tools execute."""
    base_node = ToolNode(WORKER_CONFIG[key]["tools"])

    def wrapped(state: AgentState) -> dict:
        result = base_node.invoke(state)
        # Emit result for each tool message
        for msg in result.get("messages", []):
            if hasattr(msg, "name"):
                content = msg.content if isinstance(msg.content, str) else json.dumps(msg.content)
                _emit_event("TOOL_COMPLETED", "DB_SYSTEM", content[:300], tool_name=msg.name)
        return result

    return wrapped


def reporter_node(state: AgentState) -> dict:
    _emit_event("AGENT_STARTED", "REPORTER", "Compiling final investigation report...")
    prompt = SystemMessage(content=(
        "You are the Master Reporter. Review the entire multi-agent investigation history.\n"
        "Compile a final, comprehensive report of findings and recommendations. Focus on grounding and safety.\n"
        "\nREPORT FORMAT RULES:\n"
        "- Cite DB-sourced facts as [source_table: record_id] (e.g. [equipment: 1], [tasks: 5]).\n"
        "- Cite provisional/estimated values as [provisional] (e.g. the proposed transfer reference number, estimated arrival date).\n"
        "- If multiple options or agent trade-offs exist (e.g. speed vs. cost, transfer vs. purchase), construct a clear 'Trade-Off Matrix' table comparing Options, Schedule Impact, Cost/Budget Impact, Risk, and Recommendation.\n"
        "- If a reallocation was proposed, write 'PROPOSED ACTION — awaiting human approval:' before describing it.\n"
        "  Do NOT write 'submitted', 'completed', 'executed', or any past-tense that implies the action already happened.\n"
        "- If an agent returned empty lists, errors, or no data, state exactly: 'No data available for [topic]'. Do NOT guess, estimate, or fabricate details.\n"
        "Keep the report concise, professional, and formatted in clean Markdown."
    ))

    # Filter messages: strip tool-result messages and AI messages that only have
    # tool_calls (no text content). This prevents Groq 400 errors when the reporter
    # LLM has no tools bound but sees tool-call history in context.
    clean_messages = _clean_messages_for_non_tool_nodes(state["messages"])

    time.sleep(1.5)
    
    try:
        response = llm.invoke([prompt] + clean_messages)
        content = response.content
    except Exception as e:
        # Fallback if Groq API throws 400 Parsing Failed or other errors
        _emit_event("MESSAGE", "SYSTEM", f"Reporter LLM encountered an API error: {str(e)[:100]}... Falling back to raw summary.")
        content = "## Automated Fallback Report\n\nThe AI reporter encountered an API formatting error (400) while compiling the final summary.\n\n**Raw Agent Actions:**\n"
        for m in clean_messages:
            if isinstance(m, HumanMessage) and m.content.startswith("["):
                content += f"- {m.content}\n"
        from langchain_core.messages import AIMessage
        response = AIMessage(content=content)

    _emit_event("AGENT_COMPLETED", "REPORTER", content)
    # Emit a dedicated FINAL_REPORT event so the frontend can display it separately
    _emit_event("FINAL_REPORT", "REPORTER", content)
    return {"messages": [response]}


# ── Routing edges ──────────────────────────────────────────────────────────────

MAX_TOOL_CALLS = {"stock": 3, "budget": 3, "equipment": 3, "project": 3, "procurement": 3}


def _count_consecutive_agent_tool_rounds(state: AgentState) -> int:
    count = 0
    for msg in reversed(state["messages"]):
        msg_type = getattr(msg, "type", None)
        if msg_type == "tool":
            count += 1
        elif msg_type == "ai" and hasattr(msg, "tool_calls") and msg.tool_calls:
            continue
        else:
            break
    return count


def _should_continue(key: str, agent_label: str, state: AgentState):
    last_message = state["messages"][-1]
    agent_rounds = _count_consecutive_agent_tool_rounds(state)
    if last_message.tool_calls and agent_rounds < MAX_TOOL_CALLS[key]:
        _emit_event("MESSAGE", agent_label, f"Calling tool (round {agent_rounds+1}/{MAX_TOOL_CALLS[key]})")
        return f"{key}_tools"
    if last_message.tool_calls and agent_rounds >= MAX_TOOL_CALLS[key]:
        _emit_event("AGENT_COMPLETED", agent_label, f"Reached {MAX_TOOL_CALLS[key]}-round limit — handing off.")
    else:
        _emit_event("AGENT_COMPLETED", agent_label, "Investigation complete.")
    return "supervisor"


def should_continue_stock(state): return _should_continue("stock", "STOCK_AGENT", state)
def should_continue_budget(state): return _should_continue("budget", "BUDGET_AGENT", state)
def should_continue_equipment(state): return _should_continue("equipment", "EQUIPMENT_AGENT", state)
def should_continue_project(state): return _should_continue("project", "PROJECT_AGENT", state)
def should_continue_procurement(state): return _should_continue("procurement", "PROCUREMENT_AGENT", state)


def router(state: AgentState) -> str:
    next_node = state["next_node"]
    if next_node == "FINISH":
        return "reporter"
    return next_node


# ── Build graph ────────────────────────────────────────────────────────────────

stock_tools_node = _tool_node_with_emit("stock", "STOCK_AGENT")
budget_tools_node = _tool_node_with_emit("budget", "BUDGET_AGENT")
equipment_tools_node = _tool_node_with_emit("equipment", "EQUIPMENT_AGENT")
project_tools_node = _tool_node_with_emit("project", "PROJECT_AGENT")
procurement_tools_node = _tool_node_with_emit("procurement", "PROCUREMENT_AGENT")

workflow = StateGraph(AgentState)

workflow.add_node("anomaly_detector", anomaly_detector_node)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("stock_agent", stock_agent_node)
workflow.add_node("budget_agent", budget_agent_node)
workflow.add_node("equipment_agent", equipment_agent_node)
workflow.add_node("project_agent", project_agent_node)
workflow.add_node("procurement_agent", procurement_agent_node)
workflow.add_node("reporter", reporter_node)

workflow.add_node("stock_tools", stock_tools_node)
workflow.add_node("budget_tools", budget_tools_node)
workflow.add_node("equipment_tools", equipment_tools_node)
workflow.add_node("project_tools", project_tools_node)
workflow.add_node("procurement_tools", procurement_tools_node)

workflow.add_edge(START, "anomaly_detector")
workflow.add_edge("anomaly_detector", "supervisor")

workflow.add_conditional_edges(
    "supervisor",
    router,
    {
        "stock_agent": "stock_agent",
        "budget_agent": "budget_agent",
        "equipment_agent": "equipment_agent",
        "project_agent": "project_agent",
        "procurement_agent": "procurement_agent",
        "reporter": "reporter"
    }
)

workflow.add_edge("reporter", END)

workflow.add_conditional_edges("stock_agent", should_continue_stock, {"stock_tools": "stock_tools", "supervisor": "supervisor"})
workflow.add_edge("stock_tools", "stock_agent")

workflow.add_conditional_edges("budget_agent", should_continue_budget, {"budget_tools": "budget_tools", "supervisor": "supervisor"})
workflow.add_edge("budget_tools", "budget_agent")

workflow.add_conditional_edges("equipment_agent", should_continue_equipment, {"equipment_tools": "equipment_tools", "supervisor": "supervisor"})
workflow.add_edge("equipment_tools", "equipment_agent")

workflow.add_conditional_edges("project_agent", should_continue_project, {"project_tools": "project_tools", "supervisor": "supervisor"})
workflow.add_edge("project_tools", "project_agent")

workflow.add_conditional_edges("procurement_agent", should_continue_procurement, {"procurement_tools": "procurement_tools", "supervisor": "supervisor"})
workflow.add_edge("procurement_tools", "procurement_agent")

app = workflow.compile()


# ── Entrypoint ─────────────────────────────────────────────────────────────────

def handle_alert(raw_json_log: str, run_id: str = ""):
    """
    Entrypoint. Pass a raw JSON webhook payload and an optional run_id.
    All events are emitted to stdout as JSON lines for the FastAPI process to relay.
    """
    global _run_id
    _run_id = run_id or os.environ.get("AI_RUN_ID", f"run_{uuid.uuid4().hex[:8]}")

    inputs = {"messages": [HumanMessage(content=raw_json_log)], "next_node": "", "visited_nodes": []}

    _emit_event("MESSAGE", "SYSTEM", "============================================================")
    _emit_event("MESSAGE", "SYSTEM", "MULTI-AGENT INVESTIGATION STARTED (LangGraph via Groq API)")
    _emit_event("MESSAGE", "SYSTEM", "============================================================")

    final_state = app.invoke(inputs, {"recursion_limit": 50})

    _emit_event("MESSAGE", "SYSTEM", "============================================================")
    _emit_event("MESSAGE", "SYSTEM", "MULTI-AGENT INVESTIGATION COMPLETE")
    _emit_event("MESSAGE", "SYSTEM", "============================================================")

    # Write markdown trace for reference
    try:
        with open("agent_trace.md", "w", encoding="utf-8") as f:
            f.write("# LangGraph Execution Trace\n\n")
            for msg in final_state["messages"]:
                if msg.type == "human":
                    f.write(f"### Human\n**Alert:** {msg.content}\n\n")
                elif msg.type == "ai":
                    if msg.content:
                        f.write(f"### AI\n{msg.content}\n\n")
                    if msg.tool_calls:
                        f.write("### Tool Request\n")
                        for tc in msg.tool_calls:
                            f.write(f"- **Calling:** `{tc['name']}`\n")
                            f.write(f"- **Args:** `{json.dumps(tc['args'])}`\n")
                        f.write("\n")
                elif msg.type == "tool":
                    f.write(f"### Tool Response ({msg.name})\n```json\n{msg.content}\n```\n\n")
    except Exception:
        pass

    # Write output report
    final_content = final_state["messages"][-1].content
    try:
        with open("agent_output.md", "w", encoding="utf-8") as f:
            f.write(final_content)
    except Exception:
        pass

    return final_content
