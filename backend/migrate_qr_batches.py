"""
Migration: Create material_batches, delivery_discrepancies tables
and add columns to inventory_transactions.
Run once against your Supabase/PostgreSQL DB.
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")


def main():
    if not DB_URL:
        print("No DATABASE_URL found"); return

    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    cursor = conn.cursor()

    print("Running QR batch migration...")

    sql = """
    -- material_batches: digital passport for physical batches
    CREATE TABLE IF NOT EXISTS material_batches (
        id          bigserial primary key,
        batch_code  text not null unique,
        material_id bigint references materials(id) not null,
        site_id     bigint references sites(id) not null,
        supplier_id bigint references vendors(id),
        original_qty numeric not null,
        current_qty  numeric not null,
        unit        text not null,
        status      text not null default 'RECEIVED',
        received_by bigint references users(id),
        received_at timestamptz,
        notes       text,
        created_at  timestamptz default now()
    );

    -- delivery_discrepancies
    CREATE TABLE IF NOT EXISTS delivery_discrepancies (
        id           bigserial primary key,
        batch_id     bigint references material_batches(id) not null,
        expected_qty numeric not null,
        actual_qty   numeric not null,
        difference   numeric not null,
        reported_by  bigint references users(id) not null,
        site_id      bigint references sites(id) not null,
        created_at   timestamptz default now()
    );

    -- extend inventory_transactions (safe IF NOT EXISTS)
    ALTER TABLE inventory_transactions
        ADD COLUMN IF NOT EXISTS batch_id  bigint references material_batches(id),
        ADD COLUMN IF NOT EXISTS action    text,
        ADD COLUMN IF NOT EXISTS reason    text;
    """

    try:
        cursor.execute(sql)
        print("Migration complete!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
