import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

def test_db_connection():
    # Load environment variables from the backend/.env file
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))
    if not os.path.exists(env_path):
        print(f"ERROR: .env file not found at {env_path}")
        return

    load_dotenv(env_path)
    
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL not found in environment variables.")
        return

    print("Attempting to connect to database using URL from .env...")
    
    try:
        # Create SQLAlchemy engine
        engine = create_engine(db_url)
        
        # Try to connect and run a simple query
        with engine.connect() as conn:
            version = conn.execute(text("SELECT version();")).scalar()
            print("\n✅ Successfully connected to PostgreSQL!")
            print(f"Database version: {version}")
            
            # Let's check if our tables exist
            print("\nChecking for SiteSync tables in 'public' schema...")
            tables_result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public';"))
            tables = [row[0] for row in tables_result]
            
            if tables:
                print(f"Found {len(tables)} tables:")
                for table in sorted(tables):
                    print(f"  - {table}")
            else:
                print("No tables found in the public schema. Did you run the schema.sql script?")
                
    except Exception as e:
        print("\n❌ FAILED to connect to the database.")
        print(f"Error details:\n{e}")

if __name__ == "__main__":
    test_db_connection()
