import asyncio
import os
import uuid

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

# Register every SQLAlchemy model before any request can flush ORM state.
from app.db import base  # noqa: F401
from app.api.v1 import (
    auth, sites, projects, inventory, equipment,
    procurement, finance, alerts, notifications, admin, dashboard, ai, chat
)
from ivr import webhook
from app.events.manager import event_manager
from app.events.models import make_event

app = FastAPI(
    title="SiteSync API",
    version="1.0.0",
    description="Construction Resource Management API",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router,          prefix="/api/v1/auth",          tags=["Auth"])
app.include_router(sites.router,         prefix="/api/v1/sites",         tags=["Sites"])
app.include_router(projects.router,      prefix="/api/v1/projects",      tags=["Projects"])
app.include_router(inventory.router,     prefix="/api/v1/inventory",     tags=["Inventory"])
app.include_router(equipment.router,     prefix="/api/v1/equipment",     tags=["Equipment"])
app.include_router(procurement.router,   prefix="/api/v1/procurement",   tags=["Procurement"])
app.include_router(finance.router,       prefix="/api/v1/finance",       tags=["Finance"])
app.include_router(alerts.router,        prefix="/api/v1/alerts",        tags=["Alerts"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notifications"])
app.include_router(admin.router,         prefix="/api/v1/admin",         tags=["Admin"])
app.include_router(dashboard.router,     prefix="/api/v1/dashboard",     tags=["Dashboard"])
app.include_router(ai.router,            prefix="/api/v1/ai",            tags=["AI"])
app.include_router(chat.router,          prefix="/api/v1/chat",          tags=["Chat"])
app.include_router(webhook.router,       prefix="/ivr",                  tags=["IVR"])


@app.get("/health")
def health_check():
    return {"status": "ok"}


# ── Cron Job: Auto-simulation every 15 minutes ────────────────────────────────

# Rotating scenario sequence for the cron job
_CRON_SCENARIOS = [
    "equipment_critical_failure",
    "stock_critically_low",
    "budget_overrun",
    "task_delay_cascade",
    "vendor_price_spike",
    "safety_violation",
    "multi_site_cascade",
    "schedule_risk_scan",
]
_cron_scenario_index = 0


async def _auto_simulate():
    """
    Picks the next scenario in rotation and triggers the AI agent.
    Runs every 15 minutes automatically.
    """
    global _cron_scenario_index

    scenario_id = _CRON_SCENARIOS[_cron_scenario_index % len(_CRON_SCENARIOS)]
    _cron_scenario_index += 1

    run_id = f"cron_{uuid.uuid4().hex[:10]}"
    loop = asyncio.get_event_loop()

    print(f"[CRON] Auto-simulation triggered: scenario={scenario_id}, run_id={run_id}", flush=True)

    # Reuse the same background runner from ai.py
    from app.api.v1.ai import _run_agent
    loop.run_in_executor(None, _run_agent, run_id, loop, scenario_id, "", "")


async def _run_schedule_monitor():
    """
    Executes schedule checks asynchronously in an executor.
    """
    print("[CRON] Running proactive schedule scan...", flush=True)
    from app.services.schedule_monitor import run_schedule_check
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, run_schedule_check)


scheduler = AsyncIOScheduler()


@app.on_event("startup")
async def startup_event():
    # 1. Register AI Auto-Simulation
    scheduler.add_job(
        _auto_simulate,
        trigger=IntervalTrigger(minutes=15),
        id="auto_simulation",
        name="AI Auto-Simulation (15 min)",
        replace_existing=True,
        next_run_time=None,   # Don't run immediately on startup — wait first interval
    )
    # 2. Register Proactive Schedule Monitor Scan (runs every 30 minutes)
    scheduler.add_job(
        _run_schedule_monitor,
        trigger=IntervalTrigger(minutes=30),
        id="schedule_monitor",
        name="Proactive Project Schedule Scan (30 min)",
        replace_existing=True,
        next_run_time=None,
    )
    scheduler.start()
    print("[CRON] Auto-simulation and Schedule Monitor schedulers started.", flush=True)


@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
