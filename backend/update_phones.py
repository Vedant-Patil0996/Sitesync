import os
import sys

# Ensure backend root is in sys path
root_dir = os.path.abspath(os.path.dirname(__file__))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from app.db.session import SessionLocal
from app.models.user import User

def update_phones():
    db = SessionLocal()
    try:
        # We strip the spaces to match how Twilio usually sends the 'From' number in E.164 format
        target_number = "+919223700700"
        
        # Update all users in one go
        updated_count = db.query(User).update({User.phone: target_number}, synchronize_session=False)
        db.commit()
        print(f"Successfully updated {updated_count} users to use phone number {target_number}!")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    update_phones()
