import asyncio
import sys
import os
import uuid
import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.events.manager import event_manager
from app.events.models import make_event
from app.db.session import SessionLocal

router = APIRouter()

# ── helpers ──────────────────────────────────────────────────────────────────

def _project_root() -> str:
    return os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.dirname(os.path.abspath(__file__))
                )
            )
        )
    )


def _run_agent(run_id: str, loop: asyncio.AbstractEventLoop, scenario_id: str, site_id: str, material_id: str):
    """
    Spawns test_agent.py as a subprocess, reading JSON events from stdout
    and broadcasting them via EventManager in real-time.
    After completion, inserts an Alert + role-based Notifications into the DB.
    """
    import subprocess

    project_root = _project_root()
    script_path = os.path.join(project_root, "ai", "scripts", "test_agent.py")

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["AI_RUN_ID"] = run_id
    env["AI_SCENARIO_ID"] = scenario_id
    env["AI_SITE_ID"] = site_id
    env["AI_MATERIAL_ID"] = material_id

    event_manager.publish_sync(
        run_id,
        make_event(run_id, "RUN_STARTED", "SYSTEM", f"Starting scenario: {scenario_id}"),
        loop,
    )

    final_report = ""

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

            if line.startswith("{") and '"type"' in line:
                try:
                    evt = json.loads(line)
                    evt["run_id"] = run_id
                    # Capture final report text
                    if evt.get("type") == "FINAL_REPORT":
                        final_report = evt.get("content", "")
                    event_manager.publish_sync(run_id, evt, loop)
                    continue
                except json.JSONDecodeError:
                    pass

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
        # ── Insert Alert + Notifications into DB ──────────────────────────
        # Default to site_id="1" if none provided so notifications always fire
        effective_site_id = site_id if site_id else "1"
        if final_report and effective_site_id:
            try:
                from app.services.notification_service import create_alert_and_notify
                db: Session = SessionLocal()
                try:
                    create_alert_and_notify(
                        db=db,
                        site_id=int(effective_site_id),
                        report=final_report,
                        scenario_id=scenario_id,
                        run_id=run_id,
                    )
                finally:
                    db.close()
            except Exception as e:
                print(f"[AI] Notification insert failed: {e}", flush=True)

        event_manager.publish_sync(
            run_id,
            make_event(run_id, "RUN_COMPLETED", "SYSTEM", "Investigation complete"),
            loop,
        )


# ── GET /scenarios ─────────────────────────────────────────────────────────────

@router.get("/scenarios")
async def list_scenarios():
    """Return the list of available simulation scenarios."""
    sys.path.insert(0, _project_root())
    try:
        from ai.agent.scenarios import SCENARIOS
        return {"scenarios": SCENARIOS}
    except ImportError as e:
        return {"scenarios": [], "error": str(e)}


# ── POST /trigger ──────────────────────────────────────────────────────────────

@router.post("/trigger")
async def trigger_ai(body: dict = {}):
    """
    Triggers an AI investigation run.
    Body (all optional):
      - scenario_id: str  (defaults to "equipment_critical_failure")
      - site_id: str
      - material_id: str
    Returns run_id so the frontend can open WS /ai/stream/{run_id}.
    """
    scenario_id = body.get("scenario_id", "equipment_critical_failure")
    site_id = body.get("site_id", "")
    material_id = body.get("material_id", "")

    run_id = f"run_{uuid.uuid4().hex[:12]}"
    loop = asyncio.get_event_loop()

    asyncio.get_event_loop().run_in_executor(
        None, _run_agent, run_id, loop, scenario_id, site_id, material_id
    )

    return {"status": "started", "run_id": run_id, "scenario_id": scenario_id}


# ── WS /stream/{run_id} ────────────────────────────────────────────────────────

@router.websocket("/stream/{run_id}")
async def stream_run(websocket: WebSocket, run_id: str):
    """WebSocket stream for a specific run. Pushes events as they happen."""
    await websocket.accept()
    q = event_manager.subscribe(run_id)

    try:
        while True:
            try:
                event = await asyncio.wait_for(q.get(), timeout=30.0)
                await websocket.send_json(event)

                if event.get("type") in ("RUN_COMPLETED", "RUN_FAILED"):
                    await websocket.close(code=1000)
                    break

            except asyncio.TimeoutError:
                await websocket.send_json({"type": "PING"})

    except WebSocketDisconnect:
        pass
    finally:
        event_manager.unsubscribe(run_id, q)
