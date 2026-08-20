from fastapi import APIRouter, BackgroundTasks
import subprocess
import os

router = APIRouter()

def run_agent_script():
    # Execute the test_agent.py script from the ai/scripts directory
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    script_path = os.path.join(project_root, 'ai', 'scripts', 'test_agent.py')
    
    # Run in the project root directory
    env = os.environ.copy()
    print(f"Triggering AI agent from {script_path}...", flush=True)
    
    try:
        subprocess.run(["python", script_path], env=env, cwd=project_root)
        print("AI agent execution completed.", flush=True)
    except Exception as e:
        print(f"Failed to trigger AI agent: {e}", flush=True)

@router.post("/trigger")
async def trigger_ai(background_tasks: BackgroundTasks):
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    # Empty out the agent_trace.json file to reset the frontend state immediately
    public_dir = os.path.join(project_root, "frontend", "public")
    json_path = os.path.join(public_dir, "agent_trace.json")
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            f.write("[]")
    except Exception as e:
        print(f"Could not clear trace file: {e}")
        
    background_tasks.add_task(run_agent_script)
    return {"status": "started", "message": "AI investigation triggered in background"}
