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

    print("Applying schema changes to notifications table...")
    try:
        # Add new columns
        cursor.execute("ALTER TABLE notifications ADD COLUMN IF NOT EXISTS status text not null default 'created';")
        cursor.execute("ALTER TABLE notifications ADD COLUMN IF NOT EXISTS read_at timestamptz;")
        cursor.execute("ALTER TABLE notifications ADD COLUMN IF NOT EXISTS delivered_at timestamptz;")
        cursor.execute("ALTER TABLE notifications ADD COLUMN IF NOT EXISTS failed_at timestamptz;")
        
        # Drop old column
        cursor.execute("ALTER TABLE notifications DROP COLUMN IF EXISTS is_read;")
        print("Schema changes applied successfully.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
