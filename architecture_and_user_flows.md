# SiteSync — Architecture, User Journeys & Decision Trees

---

## 1. FULL SYSTEM ARCHITECTURE (ASCII)

```
╔══════════════════════════════════════════════════════════════════════════════════╗
║                        SITESYNC — SYSTEM ARCHITECTURE                          ║
╚══════════════════════════════════════════════════════════════════════════════════╝

 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                     FRONTEND  (Next.js 13 · App Router)                     │
 │                                                                             │
 │  PUBLIC ROUTES                  PROTECTED APP ROUTES                        │
 │  ──────────────                 ──────────────────────────────────────────  │
 │  /                              /dashboard                                  │
 │  /login                         /sites        /sites/[siteId]               │
 │  /get-started                   /projects     /projects/[projectId]         │
 │                                 /inventory                                  │
 │                                 /equipment                                  │
 │                                 /procurement/requests                       │
 │                                 /procurement/quotes        ← finance only   │
 │                                 /finance                   ← finance only   │
 │                                 /finance/purchase-orders   ← finance only   │
 │                                 /finance/payments          ← finance only   │
 │                                 /alerts                                     │
 │                                 /my-site                   ← contractor     │
 │                                 /admin/users               ← admin only     │
 │                                 /admin/audit-log           ← admin only     │
 │                                 /admin/sites/new           ← admin only     │
 │                                                                             │
 │  ┌─────────────────────────────────────────────────────────────────────┐   │
 │  │  RoleProvider  →  reads JWT role  →  filters sidebar nav items      │   │
 │  │  roles: admin | pm | contractor | finance                           │   │
 │  └─────────────────────────────────────────────────────────────────────┘   │
 │                                                                             │
 │  ┌──────────────────────┐      ┌──────────────────────────────────────┐    │
 │  │  WebSocket Context   │      │  AI Chat Bubble (floating)           │    │
 │  │  ─────────────────── │      │  ──────────────────────────────────  │    │
 │  │  live notifications  │      │  canned responses → real LangGraph   │    │
 │  │  bell counter update │      │  agent in V2                         │    │
 │  └──────────┬───────────┘      └──────────────────────────────────────┘    │
 └─────────────┼───────────────────────────────────────────────────────────────┘
               │
               │   REST  (JWT Bearer)   +   WebSocket  (/ws/notifications)
               │
 ┌─────────────▼───────────────────────────────────────────────────────────────┐
 │                         BACKEND  (FastAPI · Python)                         │
 │                                                                             │
 │  AUTH                RBAC middleware                                        │
 │  ─────               ──────────────────────────────────────────────────     │
 │  POST /auth/register       get_current_user()  →  require_role()           │
 │  POST /auth/login          JWT decode → user.role → endpoint guard         │
 │  POST /auth/refresh                                                         │
 │                                                                             │
 │  REST ENDPOINTS                                                             │
 │  ──────────────────────────────────────────────────────────────────────     │
 │  GET/POST   /api/v1/sites                                                   │
 │  GET/PUT    /api/v1/sites/{id}                                              │
 │  GET/POST   /api/v1/projects                                                │
 │  GET/POST   /api/v1/inventory                                               │
 │  GET/POST   /api/v1/inventory/transactions                                  │
 │  GET/POST   /api/v1/equipment                                               │
 │  GET/POST   /api/v1/procurement/requests                                    │
 │  PATCH      /api/v1/procurement/requests/{id}/approve  ← pm/admin          │
 │  GET/POST   /api/v1/procurement/quotes                                      │
 │  GET/POST   /api/v1/finance/purchase-orders                                 │
 │  PATCH      /api/v1/finance/purchase-orders/{id}/approve ← finance/admin   │
 │  GET/POST   /api/v1/finance/payments                                        │
 │  PATCH      /api/v1/finance/payments/{id}/release       ← finance/admin    │
 │  GET/PATCH  /api/v1/alerts                                                  │
 │  GET/PATCH  /api/v1/notifications                                           │
 │  GET        /api/v1/admin/users                         ← admin only       │
 │  GET        /api/v1/admin/audit-log                     ← admin only       │
 │                                                                             │
 │  WEBSOCKET                                                                  │
 │  ───────────────────────────────────────────────────────────────────────    │
 │  WS /ws/notifications  →  ConnectionManager  →  push to user's socket      │
 └──────────┬───────────────────────────────┬────────────────────────────────┘
            │                               │
            │ SQLAlchemy ORM                │ triggers
            │                               │
 ┌──────────▼─────────────┐    ┌────────────▼────────────────────────────────┐
 │     PostgreSQL          │    │   Background Worker  (APScheduler)          │
 │  ──────────────────     │    │   ────────────────────────────────────────  │
 │  users                  │    │   Every 5 minutes:                          │
 │  sites                  │    │                                             │
 │  site_assignments        │    │   ┌─ Check inventory.current_stock         │
 │  projects               │◄───┤   │    ≤ reorder_level  →  STOCK ALERT     │
 │  tasks                  │    │   │                                         │
 │  milestones             │    │   ├─ Check equipment.status = 'idle'        │
 │  inventory              │    │   │    idle > 48h        →  EQUIP ALERT     │
 │  inventory_transactions │    │   │                                         │
 │  equipment              │    │   ├─ Check budget burn rate                 │
 │  contractors            │    │   │    spend/budget > 0.8 →  BUDGET ALERT  │
 │  vendors                │    │   │                                         │
 │  material_requests      │    │   └─ Check task.status = 'delayed'          │
 │  vendor_quotes          │    │        + blocked deps    →  TASK ALERT      │
 │  purchase_orders        │    │                                             │
 │  payments               │◄───┤   On risk detected:                         │
 │  alerts                 │    │   trigger AI Agent  →  create Alert row     │
 │  notifications          │    │                     →  push WebSocket       │
 │  audit_log              │    └────────────────────────────┬────────────────┘
 │  chat_messages          │                                 │
 │  documents (vector)     │    ┌────────────────────────────▼────────────────┐
 │  (pgvector extension)   │    │   AI Agent  (LangGraph · Python)            │
 └─────────────────────────┘    │   ─────────────────────────────────────     │
            ▲                   │   Orchestrator                              │
            │                   │      │                                      │
            │ RAG retrieval      │      ├── Inventory Specialist               │
            │                   │      ├── Finance Specialist                 │
            │                   │      ├── Equipment Specialist               │
            │                   │      └── Project Specialist                 │
            │                   │                                             │
            └───────────────────│   Tools: db_tools.py → read PostgreSQL      │
                                │   RAG:   pgvector → semantic search docs   │
                                │   Output: Alert + Recommendation           │
                                └─────────────────────────────────────────────┘
```

---

## 2. USER JOURNEY — ALL ROLES

### 2A. ADMIN (Priya Sharma)

```
  Browser opens SiteSync
        │
        ▼
  /  (Landing page)
        │
        ▼
  /login  ──► enters credentials ──► JWT issued (role: admin)
        │
        ▼
  /dashboard
  ┌─────────────────────────────────────────────────────────────────────┐
  │  Stat cards visible to ADMIN:                                       │
  │  ● Active Sites    ● Open Alerts    ● Pending Approvals             │
  │  ● Pending POs     ● Low Stock      ● Total Users                   │
  │                                                                     │
  │  Sections visible:                                                  │
  │  ● Recent Alerts           ● Budget Overview                        │
  │  ● Pending Material Reqs   ● Pending PO Approvals                   │
  │  ● Equipment Status                                                 │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ├──► /sites ──► sees ALL sites ──► "+ Add Site" button visible
        │       └──► /sites/[siteId] ──► full site detail (all tabs)
        │
        ├──► /projects ──► sees ALL projects across all sites
        │       └──► /projects/[projectId] ──► tasks + milestones
        │
        ├──► /inventory ──► read all, reorder flags
        │
        ├──► /equipment ──► full status board
        │
        ├──► /procurement/requests
        │       └──► APPROVE or REJECT material requests (step 1 of 2)
        │
        ├──► /procurement/quotes
        │       └──► see all vendor quotes, select winner → create PO
        │
        ├──► /finance
        │       ├──► /finance/purchase-orders ──► APPROVE or REJECT POs
        │       └──► /finance/payments ──► RELEASE payments
        │
        ├──► /alerts ──► RESOLVE / SNOOZE / DISMISS any alert
        │
        ├──► /admin/users
        │       └──► invite users, change roles, deactivate accounts
        │
        └──► /admin/audit-log ──► see every action taken by every user
```

---

### 2B. PROJECT MANAGER — PM (Arjun Mehta, default user)

```
  /login ──► JWT (role: pm)
        │
        ▼
  /dashboard
  ┌─────────────────────────────────────────────────────────────────────┐
  │  Stat cards visible to PM:                                          │
  │  ● Active Sites    ● Open Alerts    ● Pending Approvals             │
  │  ● Low Stock Items                                                  │
  │                                                                     │
  │  Sections visible:                                                  │
  │  ● Recent Alerts           ● Budget Overview                        │
  │  ● Pending Material Reqs   ● Equipment Status                       │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ├──► /sites ──► read all sites (NO "+ Add Site" button)
        │       └──► /sites/[siteId] ──► read-only detail
        │
        ├──► /projects ──► read + update task progress
        │       └──► /projects/[projectId] ──► mark tasks in_progress/complete
        │
        ├──► /inventory ──► check stock levels, flag issues
        │
        ├──► /equipment ──► check status and allocation
        │
        ├──► /procurement/requests
        │       └──► APPROVE or REJECT contractor requests
        │              (step 1 of 2-step flow — PM approval)
        │              After PM approves → goes to Finance
        │
        ├──► /alerts ──► RESOLVE / SNOOZE / DISMISS
        │
        └──► ❌ NO ACCESS: finance pages, vendor quotes, PO approval,
                           payment release, user management, audit log
```

---

### 2C. CONTRACTOR (Suresh Patel / Deepak Singh)

```
  /login ──► JWT (role: contractor)
        │
        ▼
  /dashboard
  ┌─────────────────────────────────────────────────────────────────────┐
  │  Stat cards visible to CONTRACTOR:                                  │
  │  ● Active Sites    ● Open Alerts    ● My Requests (own only)        │
  │                                                                     │
  │  Sections visible:                                                  │
  │  ● Recent Alerts (read-only, no action buttons)                     │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ├──► /sites ──► read-only list
        │       └──► /sites/[siteId] ──► read-only
        │
        ├──► /projects ──► read-only task list
        │       └──► /projects/[projectId] ──► read-only
        │
        ├──► /procurement/requests
        │       └──► SUBMIT new material request
        │              enters: material name, quantity, unit, site
        │              → status starts as pm_status: 'pending'
        │              → sees status of OWN requests only
        │
        ├──► /my-site (exclusive to contractor)
        │       ├──► Active tasks at their assigned site
        │       ├──► Site alerts (read only)
        │       ├──► Inventory status
        │       └──► Equipment on site
        │
        └──► ❌ NO ACCESS: inventory mgmt, equipment mgmt, vendor quotes,
                           finance, purchase orders, payments,
                           alerts actions (resolve/dismiss), user mgmt, audit log
```

---

### 2D. FINANCE (Rajesh Kumar)

```
  /login ──► JWT (role: finance)
        │
        ▼
  /dashboard
  ┌─────────────────────────────────────────────────────────────────────┐
  │  Stat cards visible to FINANCE:                                     │
  │  ● Active Sites    ● Open Alerts    ● Pending POs (with total ₹)   │
  │                                                                     │
  │  Sections visible:                                                  │
  │  ● Recent Alerts           ● Budget Overview                        │
  │  ● Pending PO Approvals                                             │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ├──► /sites ──► read-only
        │       └──► /sites/[siteId] ──► read-only
        │
        ├──► /projects ──► read-only (budget tracking)
        │
        ├──► /procurement/quotes
        │       └──► SELECT winning vendor quote → Purchase Order created
        │
        ├──► /finance
        │       └──► budget vs actual per site table
        │
        ├──► /finance/purchase-orders
        │       └──► APPROVE or REJECT POs
        │              (step 2 of 2-step flow — Finance approval)
        │              After Finance approves → delivery tracked
        │              After delivery → payment scheduled
        │
        ├──► /finance/payments
        │       └──► RELEASE payment to vendor
        │              → payment.status changes to 'released'
        │              → audit log entry created
        │
        ├──► /alerts ──► read + resolve budget-type alerts
        │
        └──► ❌ NO ACCESS: inventory mgmt, equipment mgmt,
                           material requests approval, user mgmt, audit log
```

---

## 3. TWO-STEP PROCUREMENT APPROVAL FLOW

```
 Contractor submits request
         │
         ▼
 ┌─────────────────────┐
 │  MaterialRequest    │  pm_status: pending
 │  finance_status:    │  finance_status: not_applicable
 │  not_applicable     │
 └──────────┬──────────┘
            │
            ▼
   PM reviews request   (/procurement/requests)
   ┌────────┴────────┐
   │                 │
  APPROVE          REJECT ──► pm_status: rejected → END
   │
   ▼
 pm_status: approved
 finance_status: pending
   │
   ▼
 Finance sees PM-approved request
 Finance picks vendor quote   (/procurement/quotes)
   │
   ▼
 PurchaseOrder created  (status: pending_finance)
   │
   ▼
 Finance APPROVES PO   (/finance/purchase-orders)
   ┌────────┴────────┐
   │                 │
  APPROVE          REJECT ──► PO status: rejected → END
   │
   ▼
 PO status: approved
 Delivery tracked
   │
   ▼
 Delivery confirmed → Payment created (status: scheduled)
   │
   ▼
 Finance RELEASES payment   (/finance/payments)
   │
   ▼
 payment.status: released
 Audit log: payment.released
 Inventory updated: stock_in
```

---

## 4. AI MONITORING DECISION TREE

```
 ┌─────────────────────────────────────────────────────────────────────────┐
 │                   BACKGROUND WORKER  (runs every 5 min)                │
 └────────────────────────────┬────────────────────────────────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │  Query PostgreSQL   │
                    └────┬───┬───┬───┬───┘
                         │   │   │   │
          ┌──────────────┘   │   │   └──────────────┐
          │                  │   │                   │
          ▼                  ▼   ▼                   ▼
   ┌─────────────┐   ┌──────────────┐   ┌────────────────┐   ┌────────────────┐
   │  INVENTORY  │   │  EQUIPMENT   │   │    BUDGET      │   │     TASKS      │
   │  CHECK      │   │  CHECK       │   │    CHECK       │   │    CHECK       │
   │             │   │              │   │                │   │                │
   │ stock ≤     │   │ status =     │   │ spend/budget   │   │ status =       │
   │ reorder_    │   │ 'idle' AND   │   │ > 0.80         │   │ 'delayed' AND  │
   │ level ?     │   │ idle > 48h ? │   │ threshold?     │   │ deps blocked?  │
   └──────┬──────┘   └──────┬───────┘   └────────┬───────┘   └────────┬───────┘
          │ YES             │ YES                 │ YES                │ YES
          │                 │                     │                    │
          └─────────────────┴──────────┬──────────┴────────────────────┘
                                       │
                                       ▼
                         ┌─────────────────────────────┐
                         │   Trigger AI Agent           │
                         │   (LangGraph Orchestrator)   │
                         └─────────────┬───────────────┘
                                       │
                      ┌────────────────▼────────────────┐
                      │  Route to Specialist Agent       │
                      │  ┌─────────────────────────┐    │
                      │  │ inventory_agent.py       │    │
                      │  │ finance_agent.py         │    │
                      │  │ equipment_agent.py       │    │
                      │  │ project_agent.py         │    │
                      │  └─────────────────────────┘    │
                      └─────────────┬───────────────────┘
                                    │
                      ┌─────────────▼───────────────────┐
                      │  Agent Tools                     │
                      │  ┌─────────────────────────┐    │
                      │  │ db_tools.py              │    │
                      │  │  → read current state    │    │
                      │  │  → read historical data  │    │
                      │  │ pgvector RAG             │    │
                      │  │  → search vendor docs    │    │
                      │  │  → search site policies  │    │
                      │  └─────────────────────────┘    │
                      └─────────────┬───────────────────┘
                                    │
                      ┌─────────────▼───────────────────┐
                      │  Agent generates:                │
                      │  • Finding (what is wrong)       │
                      │  • Evidence (historical data)    │
                      │  • Recommendation (action)       │
                      │  • Source citations (RAG docs)   │
                      └─────────────┬───────────────────┘
                                    │
                      ┌─────────────▼───────────────────┐
                      │  INSERT Alert into PostgreSQL    │
                      │  INSERT Notification record      │
                      └─────────────┬───────────────────┘
                                    │
                      ┌─────────────▼───────────────────┐
                      │  Notification Manager           │
                      │  Is manager connected via WS?   │
                      └──────────┬──────────────────────┘
                                 │
                    ┌────────────┴─────────────┐
              User ONLINE                User OFFLINE
                    │                         │
                    ▼                         ▼
          Push via WebSocket        Alert stored as unread
          Bell counter +1           Shown on next login
                    │                         │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────────────────┐
                    │   Manager sees Alert card in UI      │
                    │                                      │
                    │  ┌──────────────────────────────┐   │
                    │  │ 🚨 Steel Bars Below Reorder  │   │
                    │  │    Whitefield Tower A         │   │
                    │  │                              │   │
                    │  │  Finding: 15 days of stock   │   │
                    │  │  Evidence: Tata Steel had    │   │
                    │  │  3 delivery delays last qtr  │   │
                    │  │  Recommendation: Order now   │   │
                    │  │  from alternate vendor       │   │
                    │  │                              │   │
                    │  │  [Resolve] [Snooze] [Dismiss]│   │
                    │  └──────────────────────────────┘   │
                    └────────────┬────────────────────────┘
                                 │
                    ┌────────────┴──────────────┐
              RESOLVE             SNOOZE            DISMISS
                    │                │                 │
                    ▼                ▼                 ▼
           alert.status=    alert.status=    alert.status=
           'approved'       'snoozed'        'dismissed'
                    │                │                 │
                    └────────────────┴────────────┬────┘
                                                  │
                                    Audit log entry created
```

---

## 5. WHAT CHANGES ARE NEEDED IN THE EXISTING FRONTEND

```
 CURRENT STATE                         TARGET STATE
 ─────────────────────────────────     ──────────────────────────────────────
 Mock data from lib/mock-data.ts   →   API calls via lib/api.ts + useQuery hooks
 Role from local React state       →   Role from decoded JWT token
 Canned AI responses               →   Real LangGraph agent via /api/agent/chat
 No WebSocket                      →   WebSocket context at root layout.tsx
 Bell counter from mock data       →   Bell driven by live WS unread count
 No investigation UI               →   Alert drawer with agent steps + evidence
 No /my-site, /admin/* pages       →   Built and RBAC-gated (done above)
 No backend scaffold               →   FastAPI + APScheduler + LangGraph
```

---

## 6. FOLDER STRUCTURE (Target State)

```
SiteSync/
├── frontend/              (Next.js — already exists, needs API wiring)
│   ├── app/
│   │   ├── (app)/
│   │   │   ├── dashboard/
│   │   │   ├── sites/
│   │   │   ├── projects/
│   │   │   ├── inventory/
│   │   │   ├── equipment/
│   │   │   ├── procurement/
│   │   │   ├── finance/
│   │   │   ├── alerts/
│   │   │   ├── my-site/          ← contractor only
│   │   │   └── admin/
│   │   │       ├── users/        ← admin only
│   │   │       └── audit-log/    ← admin only
│   │   ├── login/
│   │   └── get-started/
│   ├── components/
│   │   ├── layout/       (sidebar, topbar, app-shell)
│   │   ├── providers/    (role-provider → becomes auth+role-provider)
│   │   ├── alerts/       (investigation-drawer ← NEW)
│   │   ├── shared/
│   │   └── ui/           (shadcn components)
│   ├── lib/
│   │   ├── api.ts        ← NEW: axios/fetch client
│   │   ├── websocket.ts  ← NEW: WS context
│   │   ├── mock-data.ts  (kept for demo/fallback)
│   │   └── types.ts
│   └── hooks/
│       └── use-notifications.ts  ← NEW
│
├── backend/               (FastAPI — to be built)
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── security.py    (JWT + password hash)
│   │   ├── api/
│   │   │   ├── dependencies.py  (get_current_user, require_role)
│   │   │   ├── websockets.py    (WS connection manager)
│   │   │   └── v1/
│   │   │       ├── auth.py
│   │   │       ├── sites.py
│   │   │       ├── projects.py
│   │   │       ├── inventory.py
│   │   │       ├── equipment.py
│   │   │       ├── procurement.py
│   │   │       ├── finance.py
│   │   │       ├── alerts.py
│   │   │       ├── notifications.py
│   │   │       └── admin.py
│   │   ├── models/       (SQLAlchemy ORM)
│   │   ├── schemas/      (Pydantic)
│   │   ├── services/     (business logic)
│   │   └── database/
│   │       └── session.py
│   ├── worker/
│   │   └── monitoring.py  (APScheduler jobs)
│   ├── requirements.txt
│   └── Dockerfile
│
├── agents/                (LangGraph — to be built)
│   ├── src/
│   │   ├── state.py
│   │   ├── orchestrator.py
│   │   ├── specialists/
│   │   │   ├── inventory_agent.py
│   │   │   ├── finance_agent.py
│   │   │   ├── equipment_agent.py
│   │   │   └── project_agent.py
│   │   ├── tools/
│   │   │   └── db_tools.py
│   │   └── rag/
│   │       ├── ingestion.py
│   │       └── retrieval.py
│   └── requirements.txt
│
├── docker-compose.yml
├── .env.example
└── README.md
```
