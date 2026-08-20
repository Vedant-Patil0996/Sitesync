from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import auth, sites, projects, inventory, equipment, procurement, finance, alerts, notifications, admin, dashboard
from ivr import webhook

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
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(sites.router, prefix="/api/v1/sites", tags=["Sites"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["Projects"])
app.include_router(inventory.router, prefix="/api/v1/inventory", tags=["Inventory"])
app.include_router(equipment.router, prefix="/api/v1/equipment", tags=["Equipment"])
app.include_router(procurement.router, prefix="/api/v1/procurement", tags=["Procurement"])
app.include_router(finance.router, prefix="/api/v1/finance", tags=["Finance"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["Alerts"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notifications"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(webhook.router, prefix="/ivr", tags=["IVR"])

@app.get("/health")
def health_check():
    return {"status": "ok"}

