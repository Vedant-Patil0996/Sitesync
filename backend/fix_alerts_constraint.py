import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")

def main():
    if not DB_URL:
        print("No DB_URL found")
        return

    print("Connecting to DB...")
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    cursor = conn.cursor()

    print("Fixing alerts_status_check constraint...")
    try:
        cursor.execute("ALTER TABLE alerts DROP CONSTRAINT IF EXISTS alerts_status_check;")
        cursor.execute("ALTER TABLE alerts ADD CONSTRAINT alerts_status_check CHECK (status IN ('open', 'approved', 'resolved', 'dismissed', 'snoozed'));")
        print("Constraint updated successfully.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
