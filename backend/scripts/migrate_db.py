import sys
import os
from sqlalchemy import text

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import engine

def migrate():
    print("Running migration for material_requests table...")
    queries = [
        "ALTER TABLE material_requests ADD COLUMN IF NOT EXISTS priority text NOT NULL DEFAULT 'normal';",
        "ALTER TABLE material_requests ADD COLUMN IF NOT EXISTS required_date date;",
        "ALTER TABLE material_requests ADD COLUMN IF NOT EXISTS estimated_unit_cost numeric;",
        "ALTER TABLE material_requests ADD COLUMN IF NOT EXISTS total_estimated_cost numeric;",
        "ALTER TABLE material_requests ADD COLUMN IF NOT EXISTS attachment_url text;",
        "ALTER TABLE material_requests ADD COLUMN IF NOT EXISTS pm_notes text;",
        "ALTER TABLE material_requests ADD COLUMN IF NOT EXISTS finance_notes text;"
    ]
    with engine.begin() as conn:
        for q in queries:
            print(f"Executing: {q}")
            conn.execute(text(q))
    print("Migration completed successfully!")

if __name__ == "__main__":
    migrate()
