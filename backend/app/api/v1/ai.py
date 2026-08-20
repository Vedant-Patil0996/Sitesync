import asyncio
import sys
import os
import uuid
import json
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.events.manager import event_manager
from app.events.models import make_event

router = APIRouter()

# ── helpers ──────────────────────────────────────────────────────────────────

def _project_root() -> str:
    # backend/app/api/v1/ai.py  →  go up 5 levels  →  project root
    return os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.dirname(os.path.abspath(__file__))
                )
            )
        )
    )


def _run_agent(run_id: str, loop: asyncio.AbstractEventLoop):
    """
    Runs test_agent.py in a background thread, publishing events to the
    EventManager as they arrive over stdout (one JSON event per line).
    The script writes JSON-lines to stdout; we parse and re-publish.
    """
    import subprocess

    project_root = _project_root()
    script_path = os.path.join(project_root, "ai", "scripts", "test_agent.py")

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["AI_RUN_ID"] = run_id           # passed to the script

    # Publish RUN_STARTED
    event_manager.publish_sync(
        run_id,
        make_event(run_id, "RUN_STARTED", "SYSTEM", "Multi-agent investigation started"),
        loop,
    )

    try:
        proc = subprocess.Popen(
            [sys.executable, script_path],
            env=env,
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        for line in proc.stdout:
            line = line.rstrip("\n")
            if not line:
                continue

            # Try to parse as JSON event from orchestrator
            if line.startswith("{") and '"type"' in line:
                try:
                    evt = json.loads(line)
                    evt["run_id"] = run_id
                    event_manager.publish_sync(run_id, evt, loop)
                    continue
                except json.JSONDecodeError:
                    pass

            # Fallback: publish as a plain MESSAGE event
            event_manager.publish_sync(
                run_id,
                make_event(run_id, "MESSAGE", "SYSTEM", line),
                loop,
            )

        proc.wait()

    except Exception as exc:
        event_manager.publish_sync(
            run_id,
            make_event(run_id, "RUN_FAILED", "SYSTEM", str(exc)),
            loop,
        )

    finally:
        event_manager.publish_sync(
            run_id,
            make_event(run_id, "RUN_COMPLETED", "SYSTEM", "Investigation complete"),
            loop,
        )


# ── endpoints ─────────────────────────────────────────────────────────────────

@router.post("/trigger")
async def trigger_ai():
    """
    Creates a new run_id and launches the agent in a background thread.
    Returns the run_id so the frontend can open the WS stream.
    """
    run_id = f"run_{uuid.uuid4().hex[:12]}"
    loop = asyncio.get_event_loop()

    # Run in a thread so FastAPI is not blocked
    asyncio.get_event_loop().run_in_executor(None, _run_agent, run_id, loop)

    return {"status": "started", "run_id": run_id}


@router.websocket("/stream/{run_id}")
async def stream_run(websocket: WebSocket, run_id: str):
    """
    WebSocket endpoint. Subscribe to all events for a given run_id.
    Events are pushed as JSON as soon as they are published.
    """
    await websocket.accept()

    # Subscribe to this run
    q = event_manager.subscribe(run_id)

    try:
        while True:
            try:
                # Wait up to 30 s for an event; send a keepalive ping if nothing arrives
                event = await asyncio.wait_for(q.get(), timeout=30.0)
                await websocket.send_json(event)

                # If the run finished, send and close cleanly
                if event.get("type") in ("RUN_COMPLETED", "RUN_FAILED"):
                    await websocket.close(code=1000)
                    break

            except asyncio.TimeoutError:
                # Send a ping to keep the connection alive
                await websocket.send_json({"type": "PING"})

    except WebSocketDisconnect:
        pass
    finally:
        event_manager.unsubscribe(run_id, q)
