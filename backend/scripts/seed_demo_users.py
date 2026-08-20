import os
import sys
import asyncio
from dotenv import load_dotenv

# Add backend directory to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.supabase import get_supabase
from app.db.session import SessionLocal
from app.models.company import Company
from app.models.user import User

async def seed():
    # Load env vars
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
    load_dotenv(env_path)
    
    sb = get_supabase()
    db = SessionLocal()
    
    print("Seeding demo data...")
    
    try:
        # 1. Create a demo company
        company = db.query(Company).filter(Company.name == "Demo Construction Co.").first()
        if not company:
            company = Company(name="Demo Construction Co.")
            db.add(company)
            db.commit()
            db.refresh(company)
            print(f"Created company: {company.name}")
        else:
            print(f"Company '{company.name}' already exists.")

        # 2. Define demo users
        demo_users = [
            {"email": "admin@sitesync.local", "password": "adminpassword", "name": "Alice Admin", "role": "admin"},
            {"email": "pm@sitesync.local", "password": "pmpassword", "name": "Pete PM", "role": "pm"},
            {"email": "contractor@sitesync.local", "password": "contractorpassword", "name": "Craig Contractor", "role": "contractor"},
            {"email": "finance@sitesync.local", "password": "financepassword", "name": "Fiona Finance", "role": "finance"},
        ]

        for u in demo_users:
            # Check if user already exists in DB
            db_user = db.query(User).filter(User.email == u["email"]).first()
            if db_user:
                print(f"User {u['email']} already exists in database.")
                continue

            # Create in Supabase Auth
            print(f"Creating {u['email']} in Supabase Auth...")
            try:
                # Use admin api to create user and auto-confirm email
                auth_res = sb.auth.admin.create_user({
                    "email": u["email"],
                    "password": u["password"],
                    "email_confirm": True
                })
                
                # Insert into our DB
                new_user = User(
                    company_id=company.id,
                    name=u["name"],
                    email=u["email"],
                    password_hash="supa-auth", # We rely on Supabase for auth, so hash is just a placeholder
                    role=u["role"],
                    is_active=True
                )
                db.add(new_user)
                db.commit()
                print(f"Successfully seeded {u['email']} (role: {u['role']})")
                
            except Exception as e:
                print(f"Failed to create {u['email']}: {e}")
                db.rollback()

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(seed())
