from app.db.session import SessionLocal
from app.models.user import User
from app.models.site import Site, SiteAssignment
from app.models.inventory import Material, Inventory


def _user_to_dict(user, db):
    """Convert a User ORM object to the caller info dict."""
    assignments = db.query(SiteAssignment).filter(SiteAssignment.user_id == user.id).all()
    site_ids = [str(a.site_id) for a in assignments]

    # If no site assignments, give access to all sites (demo convenience)
    if not site_ids:
        all_sites = db.query(Site).limit(10).all()
        site_ids = [str(s.id) for s in all_sites]

    display_name = getattr(user, "full_name", None) or getattr(user, "name", None) or "Unknown"
    return {
        "user_id": str(user.id),
        "role": user.role,
        "site_ids": site_ids,
        "name": display_name
    }


def get_caller_info(phone_number):
    """
    Returns caller info dict based on phone number.
    If multiple users share the same number (demo scenario), returns the FIRST user
    found for initial session setup. Intent-specific lookup happens in get_caller_for_intent().
    Falls back to first admin, then first user in DB.
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.phone == phone_number).first()
        if not user:
            user = db.query(User).filter(User.role == "admin").first()
        if not user:
            user = db.query(User).first()
        if not user:
            return None
        return _user_to_dict(user, db)
    except Exception as e:
        print(f"[ERROR] get_caller_info failed: {e}")
        return None
    finally:
        db.close()


def get_caller_for_intent(intent: str, phone_number: str):
    """
    Picks the most appropriate user for a given intent.

    Rules (per user's design):
    - create_request  → contractor (they submit material requests)
    - stock_query     → first user found (anyone can check stock)
    - equipment_query → first user found
    - budget_query    → pm (only PMs should see budget)
    - general_faq     → first user found (admin / anyone)
    - unclear         → first user found

    When multiple users share the same phone (demo), this ensures the
    right role is used for DB inserts (e.g., requested_by must be a contractor).
    """
    role_map = {
        "create_request":  "contractor",
        "budget_query":    "pm",
        "equipment_query": None,   # anyone
        "stock_query":     None,   # anyone
        "general_faq":     None,   # anyone
        "unclear":         None,   # anyone
    }
    preferred_role = role_map.get(intent)

    db = SessionLocal()
    try:
        user = None
        if preferred_role:
            # Try to find a user with the preferred role sharing the same phone
            user = db.query(User).filter(
                User.phone == phone_number,
                User.role == preferred_role
            ).first()
            # If phone doesn't match any user with that role, find any user with that role
            if not user:
                user = db.query(User).filter(User.role == preferred_role).first()

        # Fallback: any user with the phone, then first user overall
        if not user:
            user = db.query(User).filter(User.phone == phone_number).first()
        if not user:
            user = db.query(User).filter(User.role == "admin").first()
        if not user:
            user = db.query(User).first()
        if not user:
            return None

        return _user_to_dict(user, db)
    except Exception as e:
        print(f"[ERROR] get_caller_for_intent failed: {e}")
        return None
    finally:
        db.close()


def get_site_id_by_name(site_name, site_ids):
    """Find site by name (fuzzy). Prioritizes sites that have inventory entries."""
    if not site_name:
        return site_ids[0] if site_ids else None
    db = SessionLocal()
    try:
        # First try: Find a site matching the name that actually has inventory entries
        site = db.query(Site).join(Inventory, Inventory.site_id == Site.id).filter(
            Site.name.ilike(f"%{site_name}%")
        ).first()
        
        # Second try: Fallback to any site matching the name
        if not site:
            site = db.query(Site).filter(Site.name.ilike(f"%{site_name}%")).first()
            
        if site:
            return str(site.id)
        return site_ids[0] if site_ids else None
    except Exception as e:
        print(f"[ERROR] get_site_id_by_name failed: {e}")
        return site_ids[0] if site_ids else None
    finally:
        db.close()


def get_material_id_by_name(mat_name):
    """Find material by name (fuzzy match). Prioritizes materials that have inventory entries."""
    if not mat_name:
        return None
    db = SessionLocal()
    try:
        # First try: Find a material matching the name that actually has inventory entries
        mat = db.query(Material).join(Inventory, Inventory.material_id == Material.id).filter(
            Material.name.ilike(f"%{mat_name}%")
        ).first()
        
        # Second try: Fallback to any material matching the name
        if not mat:
            mat = db.query(Material).filter(Material.name.ilike(f"%{mat_name}%")).first()
            
        if mat:
            return str(mat.id)
        return None
    except Exception as e:
        print(f"[ERROR] get_material_id_by_name failed: {e}")
        return None
    finally:
        db.close()
