import json
from ai.core.config import groq_client
from ai.agent.config import WORKER_CONFIG, TOOL_FUNCTIONS

def execute_tool_call(tool_call):
    name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)
    
    if name not in TOOL_FUNCTIONS:
        raise ValueError(f"Unknown tool: {name}")
        
    fn = TOOL_FUNCTIONS[name]
    return fn(**args)

def run_worker_agent(worker_name: str, alert_context: dict, max_iterations: int = 8):
    if worker_name not in WORKER_CONFIG:
        raise ValueError(f"Unknown worker: {worker_name}")
        
    config = WORKER_CONFIG[worker_name]
    system_prompt = config['system_prompt']
    tools = config['tools']
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(alert_context)}
    ]
    
    for i in range(max_iterations):
        response = groq_client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=1024
        )
        
        response_message = response.choices[0].message
        
        if response_message.tool_calls:
            print(f"Iteration {i+1}: Agent called {len(response_message.tool_calls)} tools.", flush=True)
            # Append assistant message with tool calls (need to convert to dict for standard python openai/groq structures or just append the object depending on the SDK version)
            messages.append(response_message)
            
            # Execute all tool calls
            for tool_call in response_message.tool_calls:
                print(f"  -> Calling {tool_call.function.name} with {tool_call.function.arguments}", flush=True)
                try:
                    result = execute_tool_call(tool_call)
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": tool_call.function.name,
                        "content": json.dumps(result)
                    })
                except Exception as e:
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": tool_call.function.name,
                        "content": f"Error: {str(e)}"
                    })
        else:
            # Agent replied with text
            print(f"Iteration {i+1}: Agent provided final text response.", flush=True)
            return response_message.content
            
    return "Investigation exceeded max iterations."

def handle_alert(alert: dict):
    alert_type = alert.get('type')
    worker_map = {
        'stock_low': ['stock'],
        'budget_drift': ['budget']
    }
    
    workers = worker_map.get(alert_type, [])
    
    results = {}
    for w in workers:
        results[w] = run_worker_agent(w, alert)
        
    return {
        "alert": alert,
        "results": results
    }
