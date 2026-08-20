import operator
import json
import time
import os
from datetime import datetime, timedelta
from typing import Annotated, Sequence, TypedDict, Literal

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from ai.agent.config import WORKER_CONFIG

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_node: str
    visited_nodes: Annotated[Sequence[str], operator.add]

# Use Groq's flagship model specified by user
llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)

def anomaly_detector_node(state: AgentState) -> dict:
    raw_log = state["messages"][0].content
    prompt = SystemMessage(content=(
        "You are the Anomaly Detection Engine for a construction site.\n"
        "Analyze the following raw operational log (JSON). Determine if it represents a problem (e.g. low stock, excessive consumption, budget drift, equipment failure).\n"
        "Translate the raw JSON into a clear, urgent natural language alert for the Supervisor. Do NOT solve the problem, just report the anomaly clearly."
    ))
    response = llm.invoke([prompt, HumanMessage(content=raw_log)])
    print(f"[Anomaly Detector] {response.content}", flush=True)
    return {"messages": [HumanMessage(content=response.content)]}

def supervisor_node(state: AgentState) -> dict:
    visited = list(state.get("visited_nodes", []))
    visited_str = ", ".join(set(visited)) if visited else "None"

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
    # Sleep to prevent Groq free-tier rate limits
    time.sleep(1.5)
    response = llm.invoke([supervisor_prompt] + state["messages"])
    
    try:
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
            
        data = json.loads(content)
        next_node = data.get("next_node", "FINISH")
        print(f"\n[Supervisor Reasoning] {data.get('reasoning', 'No reasoning provided.')}", flush=True)
    except Exception as e:
        print(f"[Supervisor Error] Failed to parse JSON: {response.content}", flush=True)
        next_node = "FINISH"
    
    # Fallback routing - prevent re-visiting an agent
    valid_agents = ["stock_agent", "budget_agent", "equipment_agent", "project_agent", "procurement_agent"]
    if next_node in visited and next_node in valid_agents:
        print(f"[Supervisor Safeguard] Node '{next_node}' was already visited. Terminating loop -> FINISH.", flush=True)
        next_node = "FINISH"
    elif next_node not in valid_agents:
        next_node = "FINISH"
        
    print(f"[Supervisor] Routing to: {next_node}", flush=True)
    
    new_visited = [next_node] if next_node != "FINISH" else []
    return {"next_node": next_node, "visited_nodes": new_visited}

def stock_agent_node(state: AgentState) -> dict:
    prompt = SystemMessage(content=WORKER_CONFIG["stock"]["system_prompt"])
    stock_llm = llm.bind_tools(WORKER_CONFIG["stock"]["tools"])
    time.sleep(1.5)
    response = stock_llm.invoke([prompt] + state["messages"])
    return {"messages": [response]}

def budget_agent_node(state: AgentState) -> dict:
    prompt = SystemMessage(content=WORKER_CONFIG["budget"]["system_prompt"])
    budget_llm = llm.bind_tools(WORKER_CONFIG["budget"]["tools"])
    time.sleep(1.5)
    response = budget_llm.invoke([prompt] + state["messages"])
    return {"messages": [response]}

def equipment_agent_node(state: AgentState) -> dict:
    prompt = SystemMessage(content=WORKER_CONFIG["equipment"]["system_prompt"])
    equipment_llm = llm.bind_tools(WORKER_CONFIG["equipment"]["tools"])
    time.sleep(1.5)
    response = equipment_llm.invoke([prompt] + state["messages"])
    return {"messages": [response]}

def project_agent_node(state: AgentState) -> dict:
    prompt = SystemMessage(content=WORKER_CONFIG["project"]["system_prompt"])
    project_llm = llm.bind_tools(WORKER_CONFIG["project"]["tools"])
    time.sleep(1.5)
    response = project_llm.invoke([prompt] + state["messages"])
    return {"messages": [response]}

def procurement_agent_node(state: AgentState) -> dict:
    prompt = SystemMessage(content=WORKER_CONFIG["procurement"]["system_prompt"])
    procurement_llm = llm.bind_tools(WORKER_CONFIG["procurement"]["tools"])
    time.sleep(1.5)
    response = procurement_llm.invoke([prompt] + state["messages"])
    return {"messages": [response]}

def reporter_node(state: AgentState) -> dict:
    prompt = SystemMessage(content=(
        "You are the Master Reporter. Review the entire multi-agent investigation history.\n"
        "Compile a final, comprehensive report of findings and recommendations. Focus on grounding and safety.\n"
        "\nREPORT FORMAT RULES:\n"
        "- Cite DB-sourced facts as [source_table: record_id] (e.g. [equipment: 1], [tasks: 5]).\n"
        "- Cite provisional/estimated values as [provisional] (e.g. the proposed transfer reference number, estimated arrival date).\n"
        "- If a reallocation was proposed, write 'PROPOSED ACTION — awaiting human approval:' before describing it.\n"
        "  Do NOT write 'submitted', 'completed', 'executed', or any past-tense that implies the action already happened.\n"
        "- If an agent returned empty lists, errors, or no data, state exactly: 'No data available for [topic]'. Do NOT guess, estimate, or fabricate details.\n"
        "Keep the report concise, professional, and formatted in clean Markdown."
    ))
    time.sleep(1.5)
    response = llm.invoke([prompt] + state["messages"])
    return {"messages": [response]}

# Maximum tool invocations per agent TURN (resets for each new agent visited)
MAX_TOOL_CALLS = {"stock": 3, "budget": 3, "equipment": 3, "project": 3, "procurement": 3}

def _count_consecutive_agent_tool_rounds(state: AgentState) -> int:
    """
    Count COMPLETED tool-execution rounds at the TAIL of the message chain.
    Counts 'tool' response messages (not AI decisions) so that MAX_TOOL_CALLS=3
    means exactly 3 tool calls actually ran, not 2.
    Stops as soon as it hits an AI message without tool_calls (plain summary text),
    which is how the boundary between two different agents is detected.
    """
    count = 0
    for msg in reversed(state["messages"]):
        msg_type = getattr(msg, "type", None)
        if msg_type == "tool":
            # A completed tool response — count it
            count += 1
        elif msg_type == "ai" and hasattr(msg, "tool_calls") and msg.tool_calls:
            # AI message that issued tool calls — part of this agent's turn, skip
            continue
        else:
            # AI plain text reply or human message — this is the boundary, stop counting
            break
    return count

def should_continue_stock(state: AgentState) -> Literal["stock_tools", "supervisor"]:
    last_message = state["messages"][-1]
    agent_rounds = _count_consecutive_agent_tool_rounds(state)
    if last_message.tool_calls and agent_rounds < MAX_TOOL_CALLS["stock"]:
        print(f"[Stock Agent] Called {len(last_message.tool_calls)} tool(s). (agent round {agent_rounds+1}/{MAX_TOOL_CALLS['stock']})", flush=True)
        return "stock_tools"
    if last_message.tool_calls and agent_rounds >= MAX_TOOL_CALLS["stock"]:
        print(f"[Stock Agent] Reached {MAX_TOOL_CALLS['stock']}-round limit — handing off to supervisor.", flush=True)
    else:
        print(f"[Stock Agent] Finished investigation.", flush=True)
    return "supervisor"

def should_continue_budget(state: AgentState) -> Literal["budget_tools", "supervisor"]:
    last_message = state["messages"][-1]
    agent_rounds = _count_consecutive_agent_tool_rounds(state)
    if last_message.tool_calls and agent_rounds < MAX_TOOL_CALLS["budget"]:
        print(f"[Budget Agent] Called {len(last_message.tool_calls)} tool(s). (agent round {agent_rounds+1}/{MAX_TOOL_CALLS['budget']})", flush=True)
        return "budget_tools"
    if last_message.tool_calls and agent_rounds >= MAX_TOOL_CALLS["budget"]:
        print(f"[Budget Agent] Reached {MAX_TOOL_CALLS['budget']}-round limit — handing off to supervisor.", flush=True)
    else:
        print(f"[Budget Agent] Finished investigation.", flush=True)
    return "supervisor"

def should_continue_equipment(state: AgentState) -> Literal["equipment_tools", "supervisor"]:
    last_message = state["messages"][-1]
    agent_rounds = _count_consecutive_agent_tool_rounds(state)
    if last_message.tool_calls and agent_rounds < MAX_TOOL_CALLS["equipment"]:
        print(f"[Equipment Agent] Called {len(last_message.tool_calls)} tool(s). (agent round {agent_rounds+1}/{MAX_TOOL_CALLS['equipment']})", flush=True)
        return "equipment_tools"
    if last_message.tool_calls and agent_rounds >= MAX_TOOL_CALLS["equipment"]:
        print(f"[Equipment Agent] Reached {MAX_TOOL_CALLS['equipment']}-round limit — handing off to supervisor.", flush=True)
    else:
        print(f"[Equipment Agent] Finished investigation.", flush=True)
    return "supervisor"

def should_continue_project(state: AgentState) -> Literal["project_tools", "supervisor"]:
    last_message = state["messages"][-1]
    agent_rounds = _count_consecutive_agent_tool_rounds(state)
    if last_message.tool_calls and agent_rounds < MAX_TOOL_CALLS["project"]:
        print(f"[Project Agent] Called {len(last_message.tool_calls)} tool(s). (agent round {agent_rounds+1}/{MAX_TOOL_CALLS['project']})", flush=True)
        return "project_tools"
    if last_message.tool_calls and agent_rounds >= MAX_TOOL_CALLS["project"]:
        print(f"[Project Agent] Reached {MAX_TOOL_CALLS['project']}-round limit — handing off to supervisor.", flush=True)
    else:
        print(f"[Project Agent] Finished investigation.", flush=True)
    return "supervisor"

def should_continue_procurement(state: AgentState) -> Literal["procurement_tools", "supervisor"]:
    last_message = state["messages"][-1]
    agent_rounds = _count_consecutive_agent_tool_rounds(state)
    if last_message.tool_calls and agent_rounds < MAX_TOOL_CALLS["procurement"]:
        print(f"[Procurement Agent] Called {len(last_message.tool_calls)} tool(s). (agent round {agent_rounds+1}/{MAX_TOOL_CALLS['procurement']})", flush=True)
        return "procurement_tools"
    if last_message.tool_calls and agent_rounds >= MAX_TOOL_CALLS["procurement"]:
        print(f"[Procurement Agent] Reached {MAX_TOOL_CALLS['procurement']}-round limit — handing off to supervisor.", flush=True)
    else:
        print(f"[Procurement Agent] Finished investigation.", flush=True)
    return "supervisor"

def router(state: AgentState) -> str:
    next_node = state["next_node"]
    if next_node == "FINISH":
        return "reporter"
    return next_node

# Wrap tools in ToolNode
stock_tools_node = ToolNode(WORKER_CONFIG["stock"]["tools"])
budget_tools_node = ToolNode(WORKER_CONFIG["budget"]["tools"])
equipment_tools_node = ToolNode(WORKER_CONFIG["equipment"]["tools"])
project_tools_node = ToolNode(WORKER_CONFIG["project"]["tools"])
procurement_tools_node = ToolNode(WORKER_CONFIG["procurement"]["tools"])

# Build Graph
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

workflow.add_conditional_edges(
    "stock_agent",
    should_continue_stock,
    {"stock_tools": "stock_tools", "supervisor": "supervisor"}
)
workflow.add_edge("stock_tools", "stock_agent")

workflow.add_conditional_edges(
    "budget_agent",
    should_continue_budget,
    {"budget_tools": "budget_tools", "supervisor": "supervisor"}
)
workflow.add_edge("budget_tools", "budget_agent")

workflow.add_conditional_edges(
    "equipment_agent",
    should_continue_equipment,
    {"equipment_tools": "equipment_tools", "supervisor": "supervisor"}
)
workflow.add_edge("equipment_tools", "equipment_agent")

workflow.add_conditional_edges(
    "project_agent",
    should_continue_project,
    {"project_tools": "project_tools", "supervisor": "supervisor"}
)
workflow.add_edge("project_tools", "project_agent")

workflow.add_conditional_edges(
    "procurement_agent",
    should_continue_procurement,
    {"procurement_tools": "procurement_tools", "supervisor": "supervisor"}
)
workflow.add_edge("procurement_tools", "procurement_agent")

app = workflow.compile()

def handle_alert(raw_json_log: str):
    """
    Entrypoint for the system. We pass a raw JSON webhook payload.
    """
    inputs = {"messages": [HumanMessage(content=raw_json_log)], "next_node": "", "visited_nodes": []}
    
    # Run the graph
    print("============================================================")
    print("MULTI-AGENT INVESTIGATION STARTED (LangGraph via Groq API)")
    print("============================================================")
    
    final_state = app.invoke(inputs, {"recursion_limit": 50})
    
    print("============================================================")
    print("MULTI-AGENT INVESTIGATION COMPLETE")
    print("============================================================")
    
    # Write a detailed trace to agent_trace.md
    with open("agent_trace.md", "w", encoding="utf-8") as f:
        f.write("# LangGraph Execution Trace\n\n")
        for msg in final_state["messages"]:
            if msg.type == "human":
                f.write(f"### 🧑 Human\n**Alert:** {msg.content}\n\n")
            elif msg.type == "ai":
                if msg.content:
                    f.write(f"### 🤖 AI (Supervisor / Agent)\n{msg.content}\n\n")
                if msg.tool_calls:
                    f.write(f"### 🛠️ AI Tool Request\n")
                    for tc in msg.tool_calls:
                        f.write(f"- **Calling:** `{tc['name']}`\n")
                        f.write(f"- **Args:** `{json.dumps(tc['args'])}`\n")
                    f.write("\n")
            elif msg.type == "tool":
                f.write(f"### ⚙️ Tool Response ({msg.name})\n```json\n{msg.content}\n```\n\n")
            else:
                f.write(f"### 📝 {msg.type.capitalize()}\n{msg.content}\n\n")
                
    # Write JSON trace for frontend terminal
    trace_events = []
    base_time = datetime.now()
    
    for i, msg in enumerate(final_state["messages"]):
        # Increment time slightly for each log to simulate progression
        timestamp = (base_time + (i * timedelta(seconds=1.5) if hasattr(time, 'timedelta') else timedelta(seconds=i*1.5))).isoformat() + "Z"
        
        if msg.type == "human":
            trace_events.append({
                "id": f"human_{i}",
                "timestamp": timestamp,
                "agent": "SYSTEM",
                "type": "boot",
                "content": f"Ingested alert: {msg.content}"
            })
        elif msg.type == "ai":
            # Heuristic to figure out which agent this is (since LangGraph flattens it)
            agent_name = "AI_AGENT"
            if msg.content and "Master Supervisor" in msg.content or "Routing to" in msg.content or "reasoning" in msg.content:
                agent_name = "SUPERVISOR"
            elif msg.content and "Master Reporter" in msg.content or "PROPOSED ACTION" in msg.content:
                agent_name = "REPORTER"
            elif msg.tool_calls:
                # Based on tool name, guess the agent
                tc_name = msg.tool_calls[0]["name"]
                if "budget" in tc_name or "expense" in tc_name: agent_name = "BUDGET_AGENT"
                elif "equipment" in tc_name or "replacement" in tc_name: agent_name = "EQUIPMENT_AGENT"
                elif "stock" in tc_name or "inventory" in tc_name: agent_name = "STOCK_AGENT"
                elif "task" in tc_name or "project" in tc_name: agent_name = "PROJECT_AGENT"
                elif "quote" in tc_name or "historical" in tc_name: agent_name = "PROCUREMENT_AGENT"
                
            if msg.content:
                trace_events.append({
                    "id": f"ai_reasoning_{i}",
                    "timestamp": timestamp,
                    "agent": agent_name,
                    "type": "reasoning",
                    "content": msg.content
                })
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for idx, tc in enumerate(msg.tool_calls):
                    trace_events.append({
                        "id": f"ai_tool_{i}_{idx}",
                        "timestamp": timestamp,
                        "agent": agent_name,
                        "type": "tool_execution",
                        "tool_name": tc['name'],
                        "content": json.dumps(tc['args'])
                    })
        elif msg.type == "tool":
            trace_events.append({
                "id": f"tool_res_{i}",
                "timestamp": timestamp,
                "agent": "DB_SYSTEM",
                "type": "tool_result",
                "tool_name": msg.name,
                "content": msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
            })
            
    public_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend", "public")
    os.makedirs(public_dir, exist_ok=True)
    json_path = os.path.join(public_dir, "agent_trace.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(trace_events, f, indent=2)
    
    # Return the final message
    return final_state["messages"][-1].content
