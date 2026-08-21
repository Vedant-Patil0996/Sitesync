import os
import sys
from dotenv import load_dotenv
load_dotenv()

sys.stdout.reconfigure(encoding='utf-8')

from app.db import base
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.notification_service import create_alert_and_notify

def main():
    db = SessionLocal()
    try:
        # We need a valid site_id. Let's just pick site_id=1
        report = """# Stock Critically Low
The site is out of cement and operations will halt.
"""
        print("Triggering mock AI alert for site 1...")
        alert = create_alert_and_notify(
            db=db,
            site_id=1,
            report=report,
            scenario_id="stock_critically_low",
            run_id="mock_run_123"
        )
        print(f"Success! Alert created: {alert.id}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
