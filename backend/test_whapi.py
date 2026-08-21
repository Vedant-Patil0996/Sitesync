import os
import requests
from dotenv import load_dotenv

load_dotenv()

token = os.environ.get("WHAPI_CLOUD_API_TOKEN")
base_url = os.environ.get("WHAPI_CLOUD_BASE_URL", "https://gate.whapi.cloud").rstrip('/')
test_number = os.environ.get("WHATSAPP_TEST_NUMBER")

print(f"Token: {token[:5]}...{token[-5:]}" if token else "No token")
print(f"Base URL: {base_url}")
print(f"Test Number: {test_number}")

endpoint = f"{base_url}/messages/text"

payload = {
    "to": test_number,
    "body": "This is a test message from SiteSync backend."
}

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

try:
    print(f"Sending request to {endpoint} with payload: {payload}")
    response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Request failed: {e}")
