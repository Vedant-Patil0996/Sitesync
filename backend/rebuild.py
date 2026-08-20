import os

files = {
    'intent_classifier.py': '''import google.generativeai as genai
import os

def classify_intent(speech, role, site_ids):
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key: return 'unclear'
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')
    prompt = f"""Classify the following user speech into one of these intents:
- create_request: User wants to order or request materials (e.g. cement, bricks)
- stock_query: User asks how much of a material is available
- equipment_query: User asks about equipment status
- budget_query: User asks about budget (only allowed if role is 'pm')
- general_faq: User asks general questions about SiteSync
- unclear: Cannot determine

Speech: {speech}
Role: {role}

Respond with only the intent name."""
    try:
        resp = model.generate_content(prompt)
        return resp.text.strip().lower()
    except Exception as e:
        print(f"[ERROR] Intent classification failed: {e}")
        return 'unclear'
''',

    'request_extractor.py': '''import google.generativeai as genai
import os
import json

def extract_request(speech, role, site_ids):
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key: return {}
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')
    prompt = f"""Extract details from the following speech into a JSON object with keys:
"material" (string, e.g. "cement", "bricks", "crane"),
"quantity" (number),
"unit" (string, e.g. "bags", "tons"),
"site" (string, inferred from speech, e.g. "downtown", "uptown").

Speech: {speech}

Return ONLY valid JSON."""
    try:
        resp = model.generate_content(prompt)
        text = resp.text.strip()
        if text.startswith("```json"): text = text[7:]
        if text.endswith("```"): text = text[:-3]
        return json.loads(text)
    except Exception as e:
        print(f"[ERROR] Extraction failed: {e}")
        return {}
''',

    'response_compressor.py': '''import google.generativeai as genai
import os

def compress_response(tool_output, language):
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key: return "Processed."
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')
    prompt = f"""Convert this JSON data into a concise, conversational 1-2 sentence response.
Translate the response into this language code: {language}.

Data: {tool_output}"""
    try:
        resp = model.generate_content(prompt)
        return resp.text.strip()
    except Exception as e:
        print(f"[ERROR] Compression failed: {e}")
        return "Sorry, there was an error processing the result."
''',

    'caller_lookup.py': '''from app.db.session import SessionLocal
from app.models.user import User
from app.models.site import Site, SiteAssignment
from app.models.inventory import Material

def get_caller_info(phone_number):
    # Mocking for the demo
    return {"user_id": "u123", "role": "admin", "site_ids": ["s1", "s2"], "name": "Alice Admin"}

def get_site_id_by_name(site_name, site_ids):
    # Mocking
    return "s1"

def get_material_id_by_name(mat_name):
    # Mocking
    return "m1"
''',

    'session_store.py': '''SESSIONS = {}

def get_session(call_sid):
    if call_sid not in SESSIONS:
        SESSIONS[call_sid] = {"history": []}
    return SESSIONS[call_sid]

def update_session(call_sid, data):
    session = get_session(call_sid)
    session.update(data)

def append_conversation(call_sid, role, msg):
    session = get_session(call_sid)
    session["history"].append({"role": role, "msg": msg})
''',

    'language_config.py': '''from twilio.twiml.voice_response import Gather, Say

def speak(text, language):
    lang_map = {"en": "en-US", "hi": "hi-IN", "mr": "hi-IN"} # Twilio doesn't natively support mr, fallback to hi
    say = Say(message=text, language=lang_map.get(language, "en-US"))
    return say

def gather(language, action, hints=""):
    lang_map = {"en": "en-US", "hi": "hi-IN", "mr": "hi-IN"}
    return Gather(input="speech dtmf", action=action, language=lang_map.get(language, "en-US"), hints=hints, speechTimeout="auto")
''',

    'demo_logger.py': '''def log_demo_turn(call_sid, name, role, site_ids, language, speech_result="", intent="", extracted=None, action="", reply=""):
    print("-" * 60)
    print(f"[CALL {call_sid[-6:]}] Caller: {name} ({role}, Sites: {site_ids}) | Language: {language}")
    if speech_result: print(f"[CALL {call_sid[-6:]}] Heard:     '{speech_result}'")
    if intent: print(f"[CALL {call_sid[-6:]}] Intent:    {intent}")
    if extracted: print(f"[CALL {call_sid[-6:]}] Extracted: {extracted}")
    if action: print(f"[CALL {call_sid[-6:]}] Action:    {action}")
    if reply: print(f"[CALL {call_sid[-6:]}] Replied:   '{reply}'")
''',

    'faq_knowledge.py': '''FAQ_SYSTEM_PROMPT = """You are SiteSync's automated assistant. 
Answer concisely. Do not make up information."""
''',
}

base_dir = r"c:\\MyFiles\\Desktop\\Development\\Sitesync\\backend\\ivr"
for fname, content in files.items():
    with open(os.path.join(base_dir, fname), 'w', encoding='utf-8') as f:
        f.write(content)
