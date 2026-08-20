import operator
import json
import time
from typing import Annotated, Sequence, TypedDict, Literal

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from ai.agent.config import WORKER_CONFIG

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_node: str

# Use the robust OSS model on Groq
llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)

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
    supervisor_prompt = SystemMessage(content=(
        "You are the Master Supervisor. Review the entire conversation history.\n"
        "You must output a strictly valid JSON object with exactly two keys: 'reasoning' and 'next_node'.\n"
        "In 'reasoning', explain step-by-step why you are making your routing decision.\n"
        "In 'next_node', output the name of the next agent to route to, or 'FINISH' if the investigation is 100% resolved (including ALL secondary impacts like budget drift or schedule delays).\n"
        "Valid next nodes are: 'stock_agent', 'budget_agent', 'equipment_agent', 'project_agent', 'procurement_agent', or 'FINISH'.\n"
        "Example output:\n"
        "{\n"
        "  \"reasoning\": \"The equipment agent noted a 5-day downtime. This will cause downstream schedule delays, so I must route to the project agent to calculate the impact.\",\n"
        "  \"next_node\": \"project_agent\"\n"
        "}\n"
        "Output ONLY the JSON object, nothing else."
    ))
    # Sleep to prevent Groq free-tier rate limits
    time.sleep(1.5)
    response = llm.invoke([supervisor_prompt] + state["messages"])
    
    try:
        content = response.content.strip()
        # Clean up markdown code blocks if the LLM adds them
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
    
    # Fallback routing
    valid_agents = ["stock_agent", "budget_agent", "equipment_agent", "project_agent", "procurement_agent", "FINISH"]
    if next_node not in valid_agents:
        next_node = "FINISH"
        
    print(f"[Supervisor] Routing to: {next_node}", flush=True)
    return {"next_node": next_node}

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

def should_continue_stock(state: AgentState) -> Literal["stock_tools", "supervisor"]:
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        print(f"[Stock Agent] Called {len(last_message.tool_calls)} tools.", flush=True)
        return "stock_tools"
    print(f"[Stock Agent] Finished investigation.", flush=True)
    return "supervisor"

def should_continue_budget(state: AgentState) -> Literal["budget_tools", "supervisor"]:
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        print(f"[Budget Agent] Called {len(last_message.tool_calls)} tools.", flush=True)
        return "budget_tools"
    print(f"[Budget Agent] Finished investigation.", flush=True)
    return "supervisor"

def should_continue_equipment(state: AgentState) -> Literal["equipment_tools", "supervisor"]:
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        print(f"[Equipment Agent] Called {len(last_message.tool_calls)} tools.", flush=True)
        return "equipment_tools"
    print(f"[Equipment Agent] Finished investigation.", flush=True)
    return "supervisor"

def should_continue_project(state: AgentState) -> Literal["project_tools", "supervisor"]:
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        print(f"[Project Agent] Called {len(last_message.tool_calls)} tools.", flush=True)
        return "project_tools"
    print(f"[Project Agent] Finished investigation.", flush=True)
    return "supervisor"

def should_continue_procurement(state: AgentState) -> Literal["procurement_tools", "supervisor"]:
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        print(f"[Procurement Agent] Called {len(last_message.tool_calls)} tools.", flush=True)
        return "procurement_tools"
    print(f"[Procurement Agent] Finished investigation.", flush=True)
    return "supervisor"

def router(state: AgentState) -> str:
    next_node = state["next_node"]
    if next_node == "FINISH":
        return END
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
        END: END
    }
)

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
    inputs = {"messages": [HumanMessage(content=raw_json_log)], "next_node": ""}
    
    # Run the graph
    print("============================================================")
    print("MULTI-AGENT INVESTIGATION STARTED (LangGraph via Groq API)")
    print("============================================================")
    
    final_state = app.invoke(inputs, {"recursion_limit": 25})
    
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
    
    # Return the final message
    return final_state["messages"][-1].content
