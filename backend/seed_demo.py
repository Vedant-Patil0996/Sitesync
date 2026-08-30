"""
SiteSync Hackathon Demo Seed Script
=====================================
Idempotent — safe to re-run. Uses name-based lookup to avoid duplicates.
Covers all 5 demo scenarios:
  1. Material Shortage (Riverside Mall cement crisis)
  2. Equipment Bottleneck (Apex Hospital excavator idle vs Tech Park need)
  3. Project Delay (dependency chain with one genuinely delayed task)
  4. Budget Drift (Tech Park over-budget with traceable expenses)
  5. Vendor Decision (3-quote comparison where cheapest != best)
"""

import sys
import os
from datetime import date, timedelta, datetime, timezone
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from app.db.session import SessionLocal
from app.models.company import Company
from app.models.user import User
from app.models.site import Site, SiteAssignment
from app.models.project import Project, Task, Milestone
from app.models.inventory import Material, Inventory, InventoryTransaction
from app.models.equipment import Equipment, EquipmentLog, LaborLog
from app.models.procurement import MaterialRequest, VendorQuote, PurchaseOrder, Delivery
from app.models.vendor import Vendor
from app.models.finance import Expense, Payment
from app.models.alert import Alert, Notification
from app.models.audit import AuditLog
import bcrypt

def get_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

TODAY = date.today()
NOW   = datetime.now(timezone.utc)


def d(offset):
    return TODAY + timedelta(days=offset)


def dt(offset):
    return NOW + timedelta(days=offset)


def get_or_create(db, model, filter_kwargs, create_kwargs=None):
    obj = db.query(model).filter_by(**filter_kwargs).first()
    if obj:
        return obj, False
    kwargs = dict(filter_kwargs)
    if create_kwargs:
        kwargs.update(create_kwargs)
    obj = model(**kwargs)
    db.add(obj)
    db.flush()
    return obj, True


def seed():
    db = SessionLocal()
    try:
        print("\n Seeding SiteSync Demo Database...\n")

        # 1. COMPANY
        company, _ = get_or_create(db, Company, {"name": "SiteSync Demo Corp"})
        cid = company.id
        print(f"  Company: {company.name}  (id={cid})")

        # 2. USERS
        def make_user(name, email, role, phone=None):
            u, _ = get_or_create(
                db, User, {"email": email},
                {
                    "company_id": cid, "name": name,
                    "password_hash": get_hash("Demo@1234"),
                    "phone": phone, "role": role, "is_active": True,
                }
            )
            return u

        admin = make_user("Arjun Mehta",    "arjun.admin@sitesync.demo",    "admin",      "+91-9000000001")
        pm1   = make_user("Pooja Sharma",   "pooja.pm@sitesync.demo",       "pm",         "+91-9000000002")
        pm2   = make_user("Rahul Verma",    "rahul.pm@sitesync.demo",       "pm",         "+91-9000000003")
        pm3   = make_user("Sneha Iyer",     "sneha.pm@sitesync.demo",       "pm",         "+91-9000000004")
        fin1  = make_user("Kavita Nair",    "kavita.finance@sitesync.demo", "finance",    "+91-9000000005")
        fin2  = make_user("Deepak Joshi",   "deepak.finance@sitesync.demo", "finance",    "+91-9000000006")
        c1    = make_user("Ramesh Kumar",   "ramesh.c@sitesync.demo",       "contractor", "+91-9100000001")
        c2    = make_user("Suresh Patil",   "suresh.c@sitesync.demo",       "contractor", "+91-9100000002")
        c3    = make_user("Priya Desai",    "priya.c@sitesync.demo",        "contractor", "+91-9100000003")
        c4    = make_user("Vikram Singh",   "vikram.c@sitesync.demo",       "contractor", "+91-9100000004")
        c5    = make_user("Anita Rao",      "anita.c@sitesync.demo",        "contractor", "+91-9100000005")
        c6    = make_user("Mohan Das",      "mohan.c@sitesync.demo",        "contractor", "+91-9100000006")
        c7    = make_user("Lakshmi Menon",  "lakshmi.c@sitesync.demo",      "contractor", "+91-9100000007")
        c8    = make_user("Rajesh Gupta",   "rajesh.c@sitesync.demo",       "contractor", "+91-9100000008")
        print(f"  Users: 14")

        # 3. SITES
        def make_site(name, location, lat, lng):
            s, _ = get_or_create(
                db, Site, {"company_id": cid, "name": name},
                {"location": location, "latitude": lat, "longitude": lng,
                 "status": "active", "created_by": admin.id}
            )
            return s

        site_mum  = make_site("Mumbai Heights",    "Andheri East, Mumbai",     19.1136, 72.8697)
        site_riv  = make_site("Riverside Mall",    "Thane, Maharashtra",       19.2183, 72.9781)
        site_apex = make_site("Apex Hospital",     "Powai, Mumbai",            19.1176, 72.9060)
        site_tech = make_site("Tech Park",         "Navi Mumbai, Maharashtra", 19.0330, 73.0297)
        site_cst  = make_site("Coastal Residency", "Vasai, Maharashtra",       19.3939, 72.8397)
        print("  Sites: 5")

        def assign(site, user, role):
            get_or_create(db, SiteAssignment,
                          {"site_id": site.id, "user_id": user.id},
                          {"assigned_role": role})

        for u, r in [(admin,"admin"),(pm1,"pm"),(c1,"contractor"),(c2,"contractor"),(fin1,"finance")]:
            assign(site_mum, u, r)
        for u, r in [(admin,"admin"),(pm2,"pm"),(c3,"contractor"),(c4,"contractor"),(fin1,"finance")]:
            assign(site_riv, u, r)
        for u, r in [(admin,"admin"),(pm1,"pm"),(c5,"contractor"),(fin2,"finance")]:
            assign(site_apex, u, r)
        for u, r in [(admin,"admin"),(pm3,"pm"),(c6,"contractor"),(c7,"contractor"),(fin2,"finance")]:
            assign(site_tech, u, r)
        for u, r in [(admin,"admin"),(pm2,"pm"),(c8,"contractor"),(fin1,"finance")]:
            assign(site_cst, u, r)

        # 4. MATERIALS
        def make_mat(name, unit, reorder):
            m, _ = get_or_create(
                db, Material, {"company_id": cid, "name": name},
                {"unit": unit, "default_reorder_level": reorder}
            )
            return m

        mat_cement = make_mat("Cement",           "bags",   100)
        mat_steel  = make_mat("Steel",            "tonnes",  10)
        mat_sand   = make_mat("Sand",             "cu.m",    20)
        mat_bricks = make_mat("Bricks",           "units",  500)
        mat_conc   = make_mat("Concrete Mix",     "cu.m",    15)
        mat_glass  = make_mat("Glass Panels",     "pcs",     20)
        mat_tiles  = make_mat("Tiles",            "sq.ft",  200)
        mat_pvc    = make_mat("PVC Pipe",         "mtrs",    50)
        mat_cable  = make_mat("Electrical Cable", "mtrs",   100)
        mat_agg    = make_mat("Aggregate",        "cu.m",    20)
        mat_paint  = make_mat("Paint",            "litres",  50)
        mat_gyp    = make_mat("Gypsum Board",     "sheets",  30)
        print("  Materials: 12")

        # 5. VENDORS
        def make_vendor(name, phone, email, category, rating):
            v, _ = get_or_create(
                db, Vendor, {"company_id": cid, "name": name},
                {"contact_phone": phone, "contact_email": email,
                 "category": category, "rating": rating}
            )
            return v

        v_rapid = make_vendor("Rapid Build Supplies",    "+91-2200001111", "rapid@vendor.demo",   "cement",     Decimal("4.2"))
        v_metro = make_vendor("Metro Construction Mart", "+91-2200002222", "metro@vendor.demo",   "cement",     Decimal("3.8"))
        v_swift = make_vendor("SwiftDeliver Materials",  "+91-2200003333", "swift@vendor.demo",   "cement",     Decimal("4.7"))
        v_steel = make_vendor("SteelPro India",          "+91-2200004444", "steelpro@vendor.demo","steel",      Decimal("4.5"))
        v_elec  = make_vendor("ElectroCable Co",         "+91-2200005555", "elec@vendor.demo",    "electrical", Decimal("4.3"))
        v_tile  = make_vendor("TileWorld Decor",         "+91-2200006666", "tile@vendor.demo",    "finishing",  Decimal("4.0"))
        print("  Vendors: 6")

        # 6. PROJECTS
        def make_project(name, site, pm, budget, start_off, end_off, status, progress, desc=""):
            p, _ = get_or_create(
                db, Project, {"company_id": cid, "name": name},
                {
                    "site_id": site.id, "pm_id": pm.id, "description": desc,
                    "budget_allocated": Decimal(str(budget)),
                    "start_date": d(start_off), "end_date": d(end_off),
                    "status": status, "progress_percent": Decimal(str(progress)),
                    "created_by": admin.id,
                }
            )
            return p

        proj_mum      = make_project("Mumbai Heights Residential Tower",  site_mum,  pm1, 8500000,  -90, 180, "in_progress", 42, "32-floor luxury residential tower")
        proj_riv_main = make_project("Riverside Mall Main Construction",  site_riv,  pm2, 12000000, -60, 240, "in_progress", 28, "4-floor shopping mall with food court")
        proj_riv_mep  = make_project("Riverside Mall MEP & Fit-Out",      site_riv,  pm2, 4500000,  -30, 180, "in_progress", 12, "MEP fit-out for Riverside Mall")
        proj_apex     = make_project("Apex Hospital Expansion",           site_apex, pm1, 6500000,  -45, 210, "in_progress", 35, "New 6-floor hospital wing")
        proj_tech     = make_project("Tech Park Data Center",             site_tech, pm3, 5500000,  -30, 150, "in_progress", 20, "Tier-3 data center facility")
        proj_cst      = make_project("Coastal Residency Development",     site_cst,  pm2, 4000000,  -15, 300, "planning",    5,  "Gated housing colony — 200 villas")
        print("  Projects: 6")

        # 7. TASKS
        def make_task(name, project, assigned, start_off, end_off, status, progress,
                      priority="medium", depends_on=None, desc=""):
            t, _ = get_or_create(
                db, Task, {"project_id": project.id, "name": name},
                {
                    "description": desc, "assigned_to": assigned.id,
                    "start_date": d(start_off), "end_date": d(end_off),
                    "status": status, "progress_percent": Decimal(str(progress)),
                    "priority": priority,
                    "depends_on_task_id": depends_on.id if depends_on else None,
                }
            )
            return t

        # Mumbai Heights dependency chain (Scenario 3)
        t_mum_found  = make_task("Foundation Excavation & PCC",       proj_mum, c1, -80, -50, "completed",  100, "critical")
        t_mum_raft   = make_task("Raft Foundation Casting",            proj_mum, c1, -52, -30, "completed",  100, "critical", t_mum_found)
        t_mum_col    = make_task("Ground Floor Column Casting",        proj_mum, c2, -32, -10, "completed",  100, "high",     t_mum_raft)
        t_mum_slab   = make_task("Podium Slab & 1st Floor Deck",       proj_mum, c2, -18,  -3, "delayed",     55, "critical", t_mum_col,
                                 desc="Post-tensioned deck slab; delayed due to formwork shortage")
        t_mum_elec   = make_task("Electrical Conduit Rough-In",        proj_mum, c1,  -2,  25, "not_started",  0, "high",     t_mum_slab)
        t_mum_finish = make_task("Plastering & Internal Finishing",    proj_mum, c2,  20,  75, "not_started",  0, "medium",   t_mum_elec)

        # Riverside Mall (Scenario 1 — cement-dependent slab)
        t_riv_site   = make_task("Site Clearing & Levelling",          proj_riv_main, c3, -55, -40, "completed", 100, "high")
        t_riv_piling = make_task("Pile Foundation Driving",            proj_riv_main, c3, -42, -20, "completed", 100, "critical", t_riv_site)
        t_riv_slab   = make_task("Ground Floor Slab Casting",          proj_riv_main, c4,   0,  14, "in_progress", 20, "critical", t_riv_piling,
                                 desc="CRITICAL: Requires 200 bags cement. Only 15 bags in stock!")
        t_riv_struct = make_task("Structural Frame Level 1",           proj_riv_main, c3,  12,  40, "not_started",  0, "high", t_riv_slab)
        t_riv_hvac   = make_task("HVAC Ducting Rough-In",              proj_riv_mep,  c4,   5,  35, "not_started",  0, "high")
        t_riv_elecm  = make_task("Electrical MDB & Panel Wiring",      proj_riv_mep,  c3,  10,  45, "not_started",  0, "high")

        # Apex Hospital
        t_apex_excav = make_task("New Wing Excavation",                proj_apex, c5, -40, -20, "completed", 100, "critical")
        t_apex_found = make_task("New Wing Foundation & Pile Cap",     proj_apex, c5, -22,  -5, "completed", 100, "critical", t_apex_excav)
        t_apex_rcc   = make_task("RCC Frame Floors 1 to 3",            proj_apex, c5,  -6,  30, "in_progress", 40, "critical", t_apex_found)
        t_apex_mep   = make_task("Hospital MEP Medical Gas Lines",     proj_apex, c5,  25,  70, "not_started",  0, "high",    t_apex_rcc)

        # Tech Park (Scenario 2 — excavator needed)
        t_tech_excav = make_task("Data Hall Excavation",               proj_tech, c6,  -5,  15, "not_started",  0, "critical", None,
                                 desc="Needs excavator. EX-04 at Apex Hospital is idle and can be reallocated.")
        t_tech_found = make_task("Foundation & Slab",                  proj_tech, c7,  14,  35, "not_started",  0, "high",     t_tech_excav)
        t_tech_struct= make_task("Structural Steel & Roofing",         proj_tech, c6,  33,  65, "not_started",  0, "high",     t_tech_found)
        t_tech_mep   = make_task("UPS Room & Cooling Plant Install",   proj_tech, c7,  60, 100, "not_started",  0, "critical", t_tech_struct)
        t_tech_elec  = make_task("HT Power & Data Cabling",            proj_tech, c6,  55,  95, "not_started",  0, "critical", t_tech_struct)

        # Coastal
        t_cst_survey = make_task("Land Survey & Layout Marking",       proj_cst, c8, -10,   5, "in_progress", 60, "medium")
        t_cst_road   = make_task("Internal Road Layout",               proj_cst, c8,  10,  40, "not_started",  0, "low", t_cst_survey)
        print("  Tasks: 23")

        # 8. MILESTONES
        def make_ms(name, project, offset, status):
            m, _ = get_or_create(
                db, Milestone, {"project_id": project.id, "name": name},
                {"due_date": d(offset), "status": status}
            )
            return m

        ms1  = make_ms("Foundation Complete",          proj_mum,      -30, "achieved")
        ms2  = make_ms("Podium Structure Complete",    proj_mum,        7, "upcoming")
        ms3  = make_ms("Superstructure 50%",           proj_mum,       60, "upcoming")
        ms4  = make_ms("Piling Complete",              proj_riv_main, -18, "achieved")
        ms5  = make_ms("Ground Floor Slab Done",       proj_riv_main,  14, "upcoming")
        ms6  = make_ms("MEP Rough-In Complete",        proj_riv_mep,   50, "upcoming")
        ms7  = make_ms("Hospital New Wing Topped-Out", proj_apex,      35, "upcoming")
        ms8  = make_ms("Data Center Shell Complete",   proj_tech,      70, "upcoming")
        ms9  = make_ms("Site Survey Sign-Off",         proj_cst,        7, "upcoming")
        ms10 = make_ms("Apex Foundation Sign-Off",     proj_apex,      -5, "achieved")
        print("  Milestones: 10")

        # 9. EQUIPMENT
        def make_equip(site, name, etype, status, hours, idle_days=None, task=None):
            eq, _ = get_or_create(
                db, Equipment, {"site_id": site.id, "name": name},
                {
                    "type": etype, "status": status, "hours_used": Decimal(str(hours)),
                    "allocated_to_task_id": task.id if task else None,
                    "idle_since": dt(-idle_days) if idle_days else None,
                }
            )
            return eq

        eq_crane_mum  = make_equip(site_mum,  "TC-12 Tower Crane",       "tower_crane",    "active",      340, task=t_mum_slab)
        eq_mixer_mum  = make_equip(site_mum,  "CM-02 Concrete Mixer",    "concrete_mixer", "active",      180, task=t_mum_slab)
        eq_pump_mum   = make_equip(site_mum,  "CP-01 Concrete Pump",     "concrete_pump",  "maintenance", 520)
        eq_crane_riv  = make_equip(site_riv,  "TC-08 Mobile Crane",      "mobile_crane",   "active",      210, task=t_riv_slab)
        eq_mixer_riv  = make_equip(site_riv,  "CM-05 Transit Mixer",     "concrete_mixer", "active",      145, task=t_riv_slab)
        eq_excav_apex = make_equip(site_apex, "EX-04 Excavator",         "excavator",      "idle",        480, idle_days=6)
        eq_crane_apex = make_equip(site_apex, "TC-03 Tower Crane",       "tower_crane",    "active",      390, task=t_apex_rcc)
        eq_gen_tech   = make_equip(site_tech, "GEN-01 Generator 500kVA", "generator",      "active",      60)
        eq_vib_cst    = make_equip(site_cst,  "VB-01 Plate Compactor",   "compactor",      "active",      25)
        eq_jcb_cst    = make_equip(site_cst,  "JCB-3DX Backhoe",        "excavator",      "active",      40)
        print("  Equipment: 10")

        # Equipment Logs
        elog_data = [
            (eq_crane_mum, c1, -5, 8), (eq_crane_mum, c1, -4, 7), (eq_crane_mum, c1, -3, 8), (eq_crane_mum, c1, -2, 6),
            (eq_mixer_mum, c2, -5, 6), (eq_mixer_mum, c2, -3, 7),
            (eq_crane_riv, c3, -4, 8), (eq_crane_riv, c3, -2, 6),
            (eq_mixer_riv, c4, -3, 5), (eq_mixer_riv, c4, -1, 4),
            (eq_excav_apex, c5, -10, 8), (eq_excav_apex, c5, -9, 7), (eq_excav_apex, c5, -8, 6), (eq_excav_apex, c5, -7, 4),
            (eq_crane_apex, c5, -2, 8), (eq_crane_apex, c5, -1, 7),
        ]
        for eq, user, day_off, hours in elog_data:
            if not db.query(EquipmentLog).filter_by(equipment_id=eq.id, logged_by=user.id, log_date=d(day_off)).first():
                db.add(EquipmentLog(equipment_id=eq.id, logged_by=user.id, hours=Decimal(str(hours)), log_date=d(day_off)))

        # Labor Logs
        labor_data = [
            (site_mum,  t_mum_slab,   c1, -3, 18, "Formwork crew on deck slab"),
            (site_mum,  t_mum_slab,   c1, -2, 20, "Reinforcement placement"),
            (site_mum,  t_mum_slab,   c2, -1, 22, "Concrete pour delayed due to formwork gap"),
            (site_riv,  t_riv_slab,   c3, -2, 25, "Pile cap shuttering crew"),
            (site_riv,  t_riv_slab,   c4, -1, 28, "Foundation slab prep"),
            (site_riv,  t_riv_slab,   c4,  0, 30, "Slab casting team waiting on cement"),
            (site_apex, t_apex_rcc,   c5, -3, 15, "Column formwork"),
            (site_apex, t_apex_rcc,   c5, -1, 18, "Beam shuttering"),
            (site_tech, None,          c6, -1, 10, "Site demarcation and setup"),
            (site_cst,  t_cst_survey, c8, -2,  8, "Surveyor team layout peg-out"),
            (site_cst,  t_cst_survey, c8, -1,  8, "Grid layout verification"),
        ]
        for site, task, user, day_off, count, note in labor_data:
            if not db.query(LaborLog).filter_by(site_id=site.id, logged_by=user.id, log_date=d(day_off)).first():
                db.add(LaborLog(
                    site_id=site.id, task_id=task.id if task else None,
                    logged_by=user.id, labor_count=count, log_date=d(day_off), notes=note
                ))
        db.flush()
        print("  Equipment logs & labor logs created")

        # 10. INVENTORY
        inv_raw = [
            (site_riv,  mat_cement,  15,  100),  # HERO — critically low
            (site_riv,  mat_steel,    8,   10),
            (site_riv,  mat_sand,    12,   20),
            (site_riv,  mat_bricks, 2000, 500),
            (site_riv,  mat_conc,    6,   15),
            (site_riv,  mat_pvc,    80,   50),
            (site_riv,  mat_glass,  40,   20),
            (site_riv,  mat_cable, 300,  100),
            (site_mum,  mat_cement, 350,  100),  # surplus for emergency transfer
            (site_mum,  mat_steel,  22,   10),
            (site_mum,  mat_sand,   35,   20),
            (site_mum,  mat_agg,    28,   20),
            (site_mum,  mat_bricks, 8000, 500),
            (site_mum,  mat_paint, 200,   50),
            (site_mum,  mat_tiles, 3000, 200),
            (site_mum,  mat_pvc,   120,   50),
            (site_apex, mat_cement, 120,  100),
            (site_apex, mat_steel,  14,   10),
            (site_apex, mat_conc,   20,   15),
            (site_apex, mat_gyp,   180,   30),
            (site_apex, mat_tiles, 1500, 200),
            (site_apex, mat_cable,  800, 100),
            (site_tech, mat_cable, 1200, 100),
            (site_tech, mat_cement,  80, 100),
            (site_tech, mat_steel,    6,  10),
            (site_tech, mat_gyp,    250,  30),
            (site_cst,  mat_bricks, 5000, 500),
            (site_cst,  mat_sand,   25,   20),
            (site_cst,  mat_cement, 60,  100),
            (site_cst,  mat_pvc,   150,   50),
        ]
        inv_map = {}
        for site, mat, qty, reorder in inv_raw:
            inv, created = get_or_create(
                db, Inventory, {"site_id": site.id, "material_id": mat.id},
                {"quantity": Decimal(str(qty)), "reorder_level": Decimal(str(reorder))}
            )
            if not created:
                inv.quantity = Decimal(str(qty))
                inv.reorder_level = Decimal(str(reorder))
            inv_map[(site.id, mat.id)] = inv
        print(f"  Inventory records: {len(inv_raw)}")

        # Inventory Transactions
        txn_raw = [
            (site_riv, mat_cement, c3, "IN",  200, None,     d(-30), "PO HIST-001 Delivery Initial stock"),
            (site_riv, mat_cement, c3, "OUT",  40, None,     d(-28), "Slab formwork Zone A concrete pour"),
            (site_riv, mat_cement, c3, "OUT",  38, None,     d(-25), "Pile cap concrete work Zone B"),
            (site_riv, mat_cement, c4, "OUT",  42, None,     d(-22), "Column concrete pour 8 columns"),
            (site_riv, mat_cement, c3, "IN",  100, None,     d(-18), "PO HIST-002 Delivery Replenishment"),
            (site_riv, mat_cement, c4, "OUT",  40, None,     d(-15), "Grade beam concrete"),
            (site_riv, mat_cement, c3, "OUT",  35, None,     d(-12), "Lift pit concrete work"),
            (site_riv, mat_cement, c4, "OUT",  40, None,      d(-9), "Foundation raft Zone C"),
            (site_riv, mat_cement, c3, "OUT",  42, None,      d(-6), "Ground slab prep concrete"),
            (site_riv, mat_cement, c4, "OUT",  38, None,      d(-3), "Column starters and kickers"),
            (site_riv, mat_cement, c3, "OUT",  10, None,      d(-1), "Test pour — 15 bags remaining"),
            (site_mum, mat_cement, c1, "IN",  500, None,     d(-45), "PO HIST-003 Delivery Bulk order"),
            (site_mum, mat_cement, c1, "OUT",  60, None,     d(-40), "Foundation raft concrete"),
            (site_mum, mat_cement, c2, "OUT",  45, None,     d(-35), "Column casting lower floors"),
            (site_mum, mat_cement, c1, "OUT",  45, None,     d(-20), "Slab concrete batch 1"),
            (site_mum, mat_steel,  c1, "IN",   30, None,     d(-50), "PO HIST-004 Steel delivery"),
            (site_mum, mat_steel,  c2, "OUT",   8, None,     d(-40), "Raft reinforcement"),
            (site_riv, mat_steel,  c3, "IN",   15, None,     d(-35), "Steel delivery for piling"),
            (site_riv, mat_steel,  c4, "OUT",   7, None,     d(-25), "Pile cap rebar"),
            (site_apex, mat_cement,c5, "IN",  200, None,     d(-40), "Hospital wing cement delivery"),
            (site_apex, mat_cement,c5, "OUT",  50, None,     d(-30), "Foundation concrete pour"),
            (site_apex, mat_cement,c5, "OUT",  30, None,     d(-15), "Column casting floors 1-3"),
            (site_tech, mat_cable, c6, "IN", 1500, None,     d(-20), "Data center cabling delivery"),
            (site_tech, mat_cable, c7, "OUT", 300, None,     d(-10), "Initial conduit run"),
            (site_tech, mat_cement,c6, "IN",  100, None,     d(-25), "Foundation cement delivery"),
            (site_tech, mat_cement,c6, "OUT",  20, None,     d(-10), "Ground beam concrete"),
            (site_mum, mat_cement, c1, "TRANSFER_OUT", 50, site_riv, d(-5), "Emergency transfer to Riverside Mall"),
            (site_riv, mat_cement, c3, "TRANSFER_IN",  50, site_mum, d(-5), "Emergency transfer from Mumbai Heights"),
        ]
        for site, mat, user, ttype, qty, rel_site, txn_date, ref in txn_raw:
            if not db.query(InventoryTransaction).filter_by(
                site_id=site.id, material_id=mat.id, user_id=user.id,
                type=ttype, quantity=Decimal(str(qty)), reference=ref
            ).first():
                db.add(InventoryTransaction(
                    site_id=site.id, material_id=mat.id, user_id=user.id,
                    type=ttype, quantity=Decimal(str(qty)),
                    related_site_id=rel_site.id if rel_site else None,
                    reference=ref,
                    date=datetime(txn_date.year, txn_date.month, txn_date.day, 10, 0, 0, tzinfo=timezone.utc)
                ))
        db.flush()
        print(f"  Inventory transactions: {len(txn_raw)}")

        # 11. MATERIAL REQUESTS
        def make_req(site, project, mat, qty, req_by, pm_st, fin_st, priority,
                     unit_cost, justification, pm_rev=None, fin_rev=None, req_offset=7):
            r, _ = get_or_create(
                db, MaterialRequest,
                {"site_id": site.id, "material_id": mat.id,
                 "requested_by": req_by.id, "justification": justification},
                {
                    "project_id": project.id, "quantity": Decimal(str(qty)),
                    "priority": priority, "required_date": d(req_offset),
                    "estimated_unit_cost": Decimal(str(unit_cost)),
                    "total_estimated_cost": Decimal(str(qty)) * Decimal(str(unit_cost)),
                    "pm_status": pm_st,
                    "pm_reviewed_by": pm_rev.id if pm_rev else None,
                    "pm_reviewed_at": dt(-2) if pm_rev else None,
                    "finance_status": fin_st,
                    "finance_reviewed_by": fin_rev.id if fin_rev else None,
                    "finance_reviewed_at": dt(-1) if fin_rev else None,
                }
            )
            return r

        req_cement    = make_req(site_riv, proj_riv_main, mat_cement, 200, c3,
                                 "approved", "approved", "urgent", 310,
                                 "CRITICAL: Slab next week. Only 15 bags. Need 200 bags minimum.",
                                 pm_rev=pm2, fin_rev=fin1, req_offset=5)
        req_steel_riv = make_req(site_riv, proj_riv_main, mat_steel, 15, c4,
                                 "approved", "pending", "high", 68000,
                                 "Structural steel for Level 1 columns and beams.",
                                 pm_rev=pm2, req_offset=20)
        req_tiles_mum = make_req(site_mum, proj_mum, mat_tiles, 5000, c2,
                                 "approved", "approved", "normal", 75,
                                 "Floor tiles for podium level common areas",
                                 pm_rev=pm1, fin_rev=fin1, req_offset=45)
        req_gyp_apex  = make_req(site_apex, proj_apex, mat_gyp, 300, c5,
                                 "approved", "pending", "high", 420,
                                 "Gypsum board false ceiling for OT and ICU.",
                                 pm_rev=pm1, req_offset=30)
        req_cable_tech= make_req(site_tech, proj_tech, mat_cable, 2000, c7,
                                 "approved", "approved", "high", 85,
                                 "HT data cabling for server room and UPS room.",
                                 pm_rev=pm3, fin_rev=fin2, req_offset=25)
        req_cem_tech  = make_req(site_tech, proj_tech, mat_cement, 80, c6,
                                 "pending", "not_applicable", "normal", 310,
                                 "Foundation concrete for data hall floor slab.",
                                 req_offset=12)
        req_pvc_cst   = make_req(site_cst, proj_cst, mat_pvc, 500, c8,
                                 "pending", "not_applicable", "low", 120,
                                 "Underground drainage pipes for villa plots Phase 1.",
                                 req_offset=45)
        req_paint_mum = make_req(site_mum, proj_mum, mat_paint, 1000, c1,
                                 "approved", "approved", "normal", 180,
                                 "Exterior and interior paint for podium and lower floors.",
                                 pm_rev=pm1, fin_rev=fin1, req_offset=60)
        db.flush()
        print("  Material requests: 8")

        # 12. VENDOR QUOTES
        def make_quote(request, vendor, unit_price, delivery_days, qty, is_selected=False):
            q, _ = get_or_create(
                db, VendorQuote, {"request_id": request.id, "vendor_id": vendor.id},
                {
                    "unit_price": Decimal(str(unit_price)),
                    "delivery_days": delivery_days,
                    "total_price": Decimal(str(unit_price)) * Decimal(str(qty)),
                    "is_selected": is_selected,
                }
            )
            return q

        # SCENARIO 5 — 3 competing cement quotes
        q_cem_a = make_quote(req_cement, v_rapid, 310, 5, 200, False)  # high price, mid speed, mid reliability
        q_cem_b = make_quote(req_cement, v_metro, 295, 7, 200, False)  # cheapest but slowest & lowest reliability
        q_cem_c = make_quote(req_cement, v_swift, 300, 4, 200, True)   # SELECTED: fastest + best reliability + mid price
        q_steel  = make_quote(req_steel_riv, v_steel, 68000, 5, 15, True)
        q_tiles  = make_quote(req_tiles_mum, v_tile, 75, 4, 5000, True)
        q_cable  = make_quote(req_cable_tech, v_elec, 85, 7, 2000, True)
        q_paint  = make_quote(req_paint_mum, v_tile, 180, 3, 1000, True)
        db.flush()
        print("  Vendor quotes: 7")

        # 13. PURCHASE ORDERS
        def make_po(request, quote, vendor, qty, unit_price, status, approved_by=None):
            po, _ = get_or_create(
                db, PurchaseOrder, {"request_id": request.id, "vendor_id": vendor.id},
                {
                    "vendor_quote_id": quote.id,
                    "quantity": Decimal(str(qty)),
                    "unit_price": Decimal(str(unit_price)),
                    "amount": Decimal(str(qty)) * Decimal(str(unit_price)),
                    "status": status,
                    "approved_by": approved_by.id if approved_by else None,
                    "approved_at": dt(-1) if approved_by else None,
                }
            )
            return po

        po_cement = make_po(req_cement,    q_cem_c, v_swift, 200,  300, "approved",        fin1)
        po_tiles  = make_po(req_tiles_mum, q_tiles, v_tile,  5000,  75, "delivered",       fin1)
        po_cable  = make_po(req_cable_tech,q_cable, v_elec,  2000,  85, "approved",        fin2)
        po_paint  = make_po(req_paint_mum, q_paint, v_tile,  1000, 180, "approved",        fin1)
        db.flush()
        print("  Purchase orders: 4")

        # 14. DELIVERIES
        def make_del(po, qty, status, confirmed_by, day_off):
            dv, _ = get_or_create(
                db, Delivery, {"po_id": po.id},
                {"quantity": Decimal(str(qty)), "status": status,
                 "confirmed_by": confirmed_by.id, "delivery_date": dt(day_off)}
            )
            return dv

        del_tiles = make_del(po_tiles, 5000, "delivered", c2, -20)
        db.flush()
        print("  Deliveries: 1 (historical)")

        # 15. EXPENSES — Scenario 4: Tech Park budget drift
        exp_data = [
            (site_mum,  proj_mum,      "material",  820000, "Bulk cement and steel procurement Phases 1-2",           c1,  d(-60)),
            (site_mum,  proj_mum,      "labor",     450000, "Excavation and foundation labour 45 days",               c2,  d(-55)),
            (site_mum,  proj_mum,      "equipment", 180000, "TC-12 crane hire charges Month 1",                      pm1,  d(-45)),
            (site_mum,  proj_mum,      "material",  630000, "Steel reinforcement bars 15 tonnes",                     c1,  d(-35)),
            (site_mum,  proj_mum,      "labor",     380000, "Column and slab labour 30 days",                         c2,  d(-25)),
            (site_mum,  proj_mum,      "misc",       95000, "Site safety equipment and scaffolding",                 pm1,  d(-15)),
            (site_riv,  proj_riv_main, "material",  950000, "Piling materials and grout",                             c3,  d(-50)),
            (site_riv,  proj_riv_main, "labor",     520000, "Foundation and piling labour",                           c4,  d(-40)),
            (site_riv,  proj_riv_main, "equipment", 210000, "Mobile crane and mixer hire",                           pm2,  d(-30)),
            (site_riv,  proj_riv_main, "material",  480000, "Formwork purchase and shuttering",                       c3,  d(-20)),
            (site_riv,  proj_riv_main, "misc",      120000, "Temporary site office and utilities",                   pm2,  d(-10)),
            (site_apex, proj_apex,     "material",  700000, "Cement steel aggregate foundation works",                c5,  d(-38)),
            (site_apex, proj_apex,     "labor",     410000, "Excavation and piling crew 35 days",                    c5,  d(-30)),
            (site_apex, proj_apex,     "equipment", 240000, "EX-04 excavator and TC-03 crane hire",                 pm1,  d(-20)),
            (site_apex, proj_apex,     "material",  360000, "RCC materials columns floors 1-3",                       c5,  d(-10)),
            # SCENARIO 4 — Tech Park budget drift (allocated ₹55,00,000)
            (site_tech, proj_tech,     "material",  850000, "Data center structural steel premium grade",              c6,  d(-25)),
            (site_tech, proj_tech,     "equipment", 620000, "Generator hire and UPS equipment deposit",              pm3,  d(-22)),
            (site_tech, proj_tech,     "material",  980000, "Raised floor system specialized procurement",             c7,  d(-18)),
            (site_tech, proj_tech,     "labor",     550000, "Specialized data center construction crew",               c6,  d(-15)),
            (site_tech, proj_tech,     "misc",      480000, "Security and access control system — unbudgeted scope", pm3,  d(-12)),
            (site_tech, proj_tech,     "equipment", 500000, "Precision cooling CRAC unit emergency procurement",       c7,   d(-8)),
            (site_cst,  proj_cst,      "misc",       85000, "Land survey and soil testing",                           c8,   d(-8)),
            (site_cst,  proj_cst,      "labor",      45000, "Temporary security and site demarcation",                c8,   d(-5)),
        ]
        for site, proj, cat, amount, desc, rec_by, date_val in exp_data:
            if not db.query(Expense).filter_by(
                site_id=site.id, project_id=proj.id, category=cat,
                amount=Decimal(str(amount)), description=desc
            ).first():
                db.add(Expense(
                    site_id=site.id, project_id=proj.id, category=cat,
                    amount=Decimal(str(amount)), description=desc,
                    recorded_by=rec_by.id, date=date_val
                ))
        db.flush()
        print(f"  Expenses: {len(exp_data)}")

        # 16. PAYMENTS
        pay_tiles, _ = get_or_create(
            db, Payment, {"po_id": po_tiles.id},
            {"amount": po_tiles.amount, "status": "released",
             "released_by": fin1.id, "released_at": dt(-15)}
        )
        db.flush()
        print("  Payments: 1 (tiles PO released)")

        # 17. ALERTS
        def make_alert(site, project, atype, severity, title, desc, src_table, src_id, status="open"):
            a, _ = get_or_create(
                db, Alert, {"site_id": site.id, "title": title},
                {
                    "project_id": project.id if project else None,
                    "type": atype, "severity": severity, "description": desc,
                    "source_table": src_table, "source_id": src_id, "status": status,
                }
            )
            return a

        riv_inv_id = inv_map.get((site_riv.id, mat_cement.id), None)
        riv_inv_id = riv_inv_id.id if riv_inv_id else 0

        a_cement   = make_alert(site_riv, proj_riv_main, "stock",    "critical",
            "CRITICAL: Riverside Mall Cement Stock at 15 bags",
            f"Cement stock: 15 bags (reorder: 100). Daily consumption ~40 bags. "
            f"Slab task ID={t_riv_slab.id} starts now. PO ID={po_cement.id} placed with SwiftDeliver — 4 days ETA. "
            f"Mumbai Heights has 350 bags surplus (site_id={site_mum.id}) — emergency transfer possible.",
            "inventory", riv_inv_id)
        a_equip    = make_alert(site_apex, proj_apex, "equipment", "warning",
            "EX-04 Excavator Idle 6 Days at Apex Hospital",
            f"EX-04 idle since {d(-6)}. Tech Park excavation task ID={t_tech_excav.id} is blocked and needs an excavator. "
            f"Reallocation saves approx Rs40000/day idle cost.",
            "equipment", eq_excav_apex.id)
        a_delay    = make_alert(site_mum, proj_mum, "task", "critical",
            "Podium Slab Delayed — 3 Downstream Tasks Blocked",
            f"Task '{t_mum_slab.name}' ID={t_mum_slab.id} is 55pct done but past end_date {t_mum_slab.end_date}. "
            f"Blocking: Electrical Conduit ID={t_mum_elec.id} and Plastering ID={t_mum_finish.id}. "
            f"Milestone 'Podium Structure Complete' due {ms2.due_date} is at risk.",
            "tasks", t_mum_slab.id)
        a_budget   = make_alert(site_tech, proj_tech, "budget", "warning",
            "Tech Park Data Center Budget Overrun Detected",
            f"Budget: Rs5500000. Actual expenses: Rs3980000. Committed PO (cable Rs1700000). "
            f"Total committed: Rs5680000 — over budget by Rs180000. "
            f"Primary drift: Precision cooling unit (Rs500000) + Security system (Rs480000) not in original scope.",
            "projects", proj_tech.id)
        a_steel    = make_alert(site_riv, proj_riv_main, "stock", "warning",
            "Steel Stock Low at Riverside Mall",
            f"Steel: 8T (reorder: 10T). Level 1 frame task requires steel within 20 days. Finance review pending.",
            "inventory", inv_map.get((site_riv.id, mat_steel.id), type('obj', (object,), {'id': 0})()).id)
        a_ms_risk  = make_alert(site_mum, proj_mum, "task", "warning",
            "Milestone at Risk: Podium Structure Complete",
            f"Milestone ID={ms2.id} due {ms2.due_date}. Predecessor slab task delayed. "
            f"Recommend 10-day extension or add 2 formwork crews.",
            "milestones", ms2.id)
        a_tech_exc = make_alert(site_tech, proj_tech, "task", "warning",
            "Tech Park Excavation Not Started — Critical Path Risk",
            f"Excavation task ID={t_tech_excav.id} not started. No excavator assigned. "
            f"EX-04 at Apex Hospital idle for 6 days and available for reallocation.",
            "tasks", t_tech_excav.id)
        a_vendor   = make_alert(site_riv, proj_riv_main, "stock", "info",
            "Vendor Analysis: SwiftDeliver Recommended for Cement PO",
            f"3 quotes for 200 bags cement: "
            f"Rapid Build Rs62000/5d/4.2star (ID={q_cem_a.id}), "
            f"Metro Rs59000/7d/3.8star (ID={q_cem_b.id}), "
            f"SwiftDeliver Rs60000/4d/4.7star (ID={q_cem_c.id}) SELECTED. "
            f"Fastest delivery critical for slab schedule. Highest reliability. Mid-range price.",
            "vendor_quotes", q_cem_c.id)
        db.flush()
        print("  Alerts: 8")

        # 18. NOTIFICATIONS
        notif_raw = [
            (pm2,  a_cement,   "project", proj_riv_main.id, "CRITICAL: Riverside Mall Cement Shortage", "Stock at 15 bags. PO issued. Slab starts today."),
            (fin1, a_cement,   "project", proj_riv_main.id, "Cement PO Approved — Track Delivery",      "SwiftDeliver PO approved. 4-day ETA."),
            (admin,a_cement,   "project", proj_riv_main.id, "ALERT: Riverside material shortage",       "Cement at 15 bags. Milestone at risk."),
            (pm1,  a_equip,    "equipment",eq_excav_apex.id,"EX-04 Excavator Idle 6 Days",             "Consider reallocation to Tech Park."),
            (admin,a_equip,    "equipment",eq_excav_apex.id,"Equipment bottleneck detected",            "EX-04 idle. Tech Park stalled."),
            (pm1,  a_delay,    "task",    t_mum_slab.id,   "Podium Slab Task Delayed",                 "3 downstream tasks now blocked."),
            (admin,a_delay,    "project", proj_mum.id,     "Project delay: Mumbai Heights",            "Podium slab past deadline."),
            (pm3,  a_budget,   "project", proj_tech.id,    "Tech Park Over Budget",                    "Overrun by Rs180000. Review scope."),
            (fin2, a_budget,   "project", proj_tech.id,    "Budget Alert: Tech Park Data Center",      "Actual + committed exceeds budget."),
            (pm2,  a_steel,    "project", proj_riv_main.id,"Steel Running Low — Riverside",            "8T in stock. Finance review needed."),
            (fin1, a_vendor,   "project", proj_riv_main.id,"Vendor Recommendation Ready",              "SwiftDeliver recommended. Please review."),
            (pm3,  a_tech_exc, "task",    t_tech_excav.id, "Excavation Not Started — Tech Park",      "Critical path risk. No equipment assigned."),
            (pm1,  a_ms_risk,  "milestone",ms2.id,         "Milestone at Risk: Podium Structure",      f"Due {ms2.due_date}. Slab delay propagating."),
            (fin1, None, "material_request", req_steel_riv.id, "Finance Review: Steel Request",        "15T steel for Riverside — Rs1020000. PM approved."),
            (fin2, None, "material_request", req_gyp_apex.id,  "Finance Review: Gypsum Board",         "300 sheets for Apex Hospital OT — Rs126000. PM approved."),
        ]
        for user, alert, entity_type, entity_id, title, message in notif_raw:
            if not db.query(Notification).filter_by(user_id=user.id, title=title).first():
                db.add(Notification(
                    user_id=user.id, alert_id=alert.id if alert else None,
                    related_entity_type=entity_type, related_entity_id=entity_id,
                    title=title, message=message, is_read=False,
                ))
        db.flush()
        print(f"  Notifications: {len(notif_raw)}")

        # 19. AUDIT LOGS
        audit_raw = [
            (admin,"project.created",    "project", proj_mum.id,       {"budget": 8500000,  "site": "Mumbai Heights"}),
            (admin,"project.created",    "project", proj_riv_main.id,  {"budget": 12000000, "site": "Riverside Mall"}),
            (admin,"project.created",    "project", proj_tech.id,      {"budget": 5500000,  "site": "Tech Park"}),
            (admin,"project.created",    "project", proj_apex.id,      {"budget": 6500000,  "site": "Apex Hospital"}),
            (c3,  "material_request.created",   "material_request", req_cement.id,    {"material": "Cement", "qty": 200, "priority": "urgent"}),
            (pm2, "material_request.pm_approved","material_request", req_cement.id,   {"note": "Critical for slab schedule"}),
            (fin1,"material_request.finance_approved","material_request",req_cement.id,{"budget_impact": 60000}),
            (c4,  "material_request.created",   "material_request", req_steel_riv.id, {"material": "Steel", "qty": 15}),
            (pm2, "material_request.pm_approved","material_request", req_steel_riv.id,{"note": "Structural requirement"}),
            (c7,  "material_request.created",   "material_request", req_cable_tech.id,{"material": "Electrical Cable", "qty": 2000}),
            (pm3, "material_request.pm_approved","material_request", req_cable_tech.id,{"note": "Data center critical path"}),
            (fin2,"material_request.finance_approved","material_request",req_cable_tech.id,{"budget_impact": 170000}),
            (fin1,"purchase_order.approved",     "purchase_order",   po_cement.id,    {"vendor": "SwiftDeliver", "amount": 60000}),
            (fin1,"purchase_order.approved",     "purchase_order",   po_tiles.id,     {"vendor": "TileWorld", "amount": 375000}),
            (fin2,"purchase_order.approved",     "purchase_order",   po_cable.id,     {"vendor": "ElectroCable", "amount": 170000}),
            (fin1,"payment.released",            "payment",          pay_tiles.id,    {"amount": 375000, "status": "released"}),
            (c1,  "task.updated",  "task", t_mum_slab.id,   {"status": "delayed", "progress": 55, "reason": "formwork shortage"}),
            (c3,  "task.updated",  "task", t_riv_piling.id, {"status": "completed", "progress": 100}),
            (c5,  "task.updated",  "task", t_apex_found.id, {"status": "completed", "progress": 100}),
            (pm1, "equipment.status_changed","equipment", eq_excav_apex.id,{"from": "active", "to": "idle", "reason": "task completed"}),
            (c3,  "inventory.consumed","inventory_transaction", None,{"material": "Cement", "qty": 10, "site": "Riverside Mall"}),
            (c1,  "inventory.received","inventory_transaction", None,{"material": "Cement", "qty": 500,"site": "Mumbai Heights"}),
            (pm3, "expense.created","expense", None,{"category": "equipment", "amount": 500000}),
            (pm3, "expense.created","expense", None,{"category": "misc", "amount": 480000, "note": "unbudgeted security system"}),
            (admin,"site_assignment.created","site_assignment",None,{"site": "Tech Park", "user": pm3.name, "role": "pm"}),
            (admin,"site_assignment.created","site_assignment",None,{"site": "Riverside Mall", "user": c3.name, "role": "contractor"}),
        ]
        for user, action, entity_type, entity_id, meta in audit_raw:
            if not db.query(AuditLog).filter_by(user_id=user.id, action=action, entity_id=entity_id).first():
                db.add(AuditLog(
                    user_id=user.id, action=action, entity_type=entity_type,
                    entity_id=entity_id, event_metadata=meta
                ))
        db.flush()
        print(f"  Audit logs: {len(audit_raw)}")

        # COMMIT
        db.commit()

        # VALIDATION
        print("\n" + "="*65)
        print("DEMO SEED COMPLETE")
        print("="*65)
        print(f"\nRECORD COUNTS:")
        print(f"  Users:                  {db.query(User).filter_by(company_id=cid).count()}")
        print(f"  Sites:                  {db.query(Site).filter_by(company_id=cid).count()}")
        print(f"  Projects:               {db.query(Project).filter_by(company_id=cid).count()}")
        from sqlalchemy import join
        t_count = db.query(Task).join(Project, Task.project_id == Project.id).filter(Project.company_id == cid).count()
        ms_count = db.query(Milestone).join(Project, Milestone.project_id == Project.id).filter(Project.company_id == cid).count()
        print(f"  Tasks:                  {t_count}")
        print(f"  Milestones:             {ms_count}")
        print(f"  Materials:              {db.query(Material).filter_by(company_id=cid).count()}")
        print(f"  Inventory records:      {db.query(Inventory).join(Site, Inventory.site_id == Site.id).filter(Site.company_id == cid).count()}")
        print(f"  Inventory transactions: {db.query(InventoryTransaction).join(Site, InventoryTransaction.site_id == Site.id).filter(Site.company_id == cid).count()}")
        print(f"  Equipment:              {db.query(Equipment).join(Site, Equipment.site_id == Site.id).filter(Site.company_id == cid).count()}")
        print(f"  Material requests:      {db.query(MaterialRequest).join(Site, MaterialRequest.site_id == Site.id).filter(Site.company_id == cid).count()}")
        print(f"  Vendors:                {db.query(Vendor).filter_by(company_id=cid).count()}")
        print(f"  Vendor quotes:          {db.query(VendorQuote).count()}")
        print(f"  Purchase orders:        {db.query(PurchaseOrder).count()}")
        print(f"  Expenses:               {db.query(Expense).join(Site, Expense.site_id == Site.id).filter(Site.company_id == cid).count()}")
        print(f"  Payments:               {db.query(Payment).count()}")
        print(f"  Alerts:                 {db.query(Alert).join(Site, Alert.site_id == Site.id).filter(Site.company_id == cid).count()}")
        print(f"  Notifications:          {db.query(Notification).count()}")
        print(f"  Audit logs:             {db.query(AuditLog).count()}")

        print(f"\nLOGIN CREDENTIALS (all passwords: Demo@1234):")
        print(f"  Admin:      arjun.admin@sitesync.demo   id={admin.id}")
        print(f"  PM:         pooja.pm@sitesync.demo      id={pm1.id}")
        print(f"  PM2:        rahul.pm@sitesync.demo      id={pm2.id}")
        print(f"  PM3:        sneha.pm@sitesync.demo      id={pm3.id}")
        print(f"  Finance:    kavita.finance@sitesync.demo id={fin1.id}")
        print(f"  Contractor: ramesh.c@sitesync.demo      id={c1.id}")

        print(f"\nDEMO SCENARIO KEY IDs:")
        print(f"\n  SCENARIO 1 — Cement Shortage (HERO DEMO):")
        print(f"    Riverside Mall site_id={site_riv.id}  proj_id={proj_riv_main.id}")
        print(f"    Cement stock: 15 bags  (reorder=100, consumption 40/day)")
        print(f"    Slab task needing cement: task_id={t_riv_slab.id}")
        print(f"    Material request: req_id={req_cement.id}  (200 bags, URGENT, fully approved)")
        print(f"    PO issued: po_id={po_cement.id}  Rs60000  status=approved")
        print(f"    Alert: alert_id={a_cement.id}")
        print(f"    Mumbai Heights surplus 350 bags: site_id={site_mum.id}")

        print(f"\n  SCENARIO 2 — Equipment Bottleneck:")
        print(f"    Idle EX-04 Excavator: equip_id={eq_excav_apex.id}  site_id={site_apex.id}  idle 6 days")
        print(f"    Tech Park needs it: task_id={t_tech_excav.id}  proj_id={proj_tech.id}")
        print(f"    Alert: alert_id={a_equip.id}")

        print(f"\n  SCENARIO 3 — Project Delay Chain (Mumbai Heights proj_id={proj_mum.id}):")
        print(f"    Foundation:  task_id={t_mum_found.id}  COMPLETED")
        print(f"    Raft:        task_id={t_mum_raft.id}   COMPLETED")
        print(f"    Columns:     task_id={t_mum_col.id}    COMPLETED")
        print(f"    SLAB:        task_id={t_mum_slab.id}   DELAYED  55pct  end_date={t_mum_slab.end_date}")
        print(f"    Electrical:  task_id={t_mum_elec.id}   NOT_STARTED (blocked)")
        print(f"    Finishing:   task_id={t_mum_finish.id} NOT_STARTED (blocked)")
        print(f"    Alert: alert_id={a_delay.id}")

        print(f"\n  SCENARIO 4 — Budget Drift (Tech Park proj_id={proj_tech.id}):")
        print(f"    Budget allocated: Rs5500000")
        print(f"    Actual expenses:  Rs3980000 (6 expense records)")
        print(f"    Committed PO:     Rs1700000 (cable po_id={po_cable.id})")
        print(f"    Total committed:  Rs5680000  OVERRUN by Rs180000")
        print(f"    Alert: alert_id={a_budget.id}")

        print(f"\n  SCENARIO 5 — Vendor Decision (req_id={req_cement.id}):")
        print(f"    Quote A (Rapid Build):    Rs310/bag  5 days  4.2star  Total Rs62000  quote_id={q_cem_a.id}")
        print(f"    Quote B (Metro Mart):     Rs295/bag  7 days  3.8star  Total Rs59000  quote_id={q_cem_b.id}  CHEAPEST but slowest")
        print(f"    Quote C (SwiftDeliver):   Rs300/bag  4 days  4.7star  Total Rs60000  quote_id={q_cem_c.id}  SELECTED — fastest + best reliability")
        print(f"\n{'='*65}")
        print("DATABASE READY FOR HACKATHON DEMO")
        print("="*65 + "\n")

    except Exception as e:
        db.rollback()
        print(f"\nSEED FAILED — rolled back. Error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()