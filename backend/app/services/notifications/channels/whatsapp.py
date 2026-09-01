import os
import requests
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.alert import Notification, Alert
from app.services.notifications.base import NotificationChannel
import re

def _markdown_to_whatsapp(md_text: str) -> str:
    if not md_text:
        return ""
    # Convert headings (#, ##, ###) to WhatsApp bold
    text = re.sub(r'^(#{1,6})\s+(.*)$', r'*\2*', md_text, flags=re.MULTILINE)
    # Convert bold (**text**) to WhatsApp bold (*text*)
    text = re.sub(r'\*\*(.*?)\*\*', r'*\1*', text)
    # Convert markdown links [text](url) to "text (url)"
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1 (\2)', text)
    return text

class WhatsAppChannel(NotificationChannel):
    def send(self, db: Session, user: User, notification: Notification, alert: Alert):
        if not user.phone:
            print(f"[WhatsApp] User {user.id} has no phone number, skipping.", flush=True)
            return

        print(f"[WhatsApp] Dispatch -> {user.phone} | Alert: {alert.title} | {notification.message[:100]}", flush=True)
        
        token = os.environ.get("WHAPI_CLOUD_API_TOKEN")
        base_url = os.environ.get("WHAPI_CLOUD_BASE_URL", "https://gate.whapi.cloud").rstrip('/')
        
        if not token:
            print("[WhatsApp] WHAPI_CLOUD_API_TOKEN not configured, skipping.", flush=True)
            return
            
        endpoint = f"{base_url}/messages/text"
        
        # If there's a test number in .env, use it. Otherwise, use the DB number.
        test_number = os.environ.get("WHATSAPP_TEST_NUMBER")
        target_number = test_number if test_number else user.phone
        
        # Clean number to digits only and add country code if missing
        import re
        target_number = re.sub(r'[^\d]', '', str(target_number))
        if len(target_number) == 10:
            target_number = f"91{target_number}"

        # Use the full AI report (alert.description) instead of the short notification message
        full_report = alert.description if alert.description else notification.message
        wa_formatted_body = f"*{alert.title}*\n\n{_markdown_to_whatsapp(full_report)}"

        payload = {
            "to": target_number,
            "body": wa_formatted_body
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
            if not response.ok:
                print(f"[WhatsApp] API error {response.status_code}: {response.text}", flush=True)
            else:
                print(f"[WhatsApp] Message sent successfully to {target_number} (recipient user: {user.phone})", flush=True)
        except Exception as e:
            print(f"[WhatsApp] Request failed: {e}", flush=True)

