import threading

# Global call logs store for simple UI viewing
CALL_LOGS = []
_logs_lock = threading.Lock()

def get_all_logs():
    with _logs_lock:
        return list(CALL_LOGS)

def log_demo_turn(call_sid, name, role, site_ids, language, speech_result="", intent="", extracted=None, action="", reply=""):
    print("-" * 60)
    print(f"[CALL {call_sid[-6:]}] Caller: {name} ({role}, Sites: {site_ids}) | Language: {language}")
    if speech_result: print(f"[CALL {call_sid[-6:]}] Heard:     '{speech_result}'")
    if intent: print(f"[CALL {call_sid[-6:]}] Intent:    {intent}")
    if extracted: print(f"[CALL {call_sid[-6:]}] Extracted: {extracted}")
    if action: print(f"[CALL {call_sid[-6:]}] Action:    {action}")
    if reply: print(f"[CALL {call_sid[-6:]}] Replied:   '{reply}'")

    log_entry = {
        "call_sid": call_sid,
        "name": name,
        "role": role,
        "site_ids": site_ids,
        "language": language,
        "speech_result": speech_result,
        "intent": intent,
        "extracted": extracted,
        "action": action,
        "reply": reply,
        "timestamp": threading.local()  # Python thread local isn't needed, standard iso format is better
    }
    
    # Use datetime for timestamp
    from datetime import datetime
    log_entry["timestamp"] = datetime.utcnow().isoformat() + "Z"

    with _logs_lock:
        CALL_LOGS.insert(0, log_entry)
        # Limit to last 100 entries to prevent memory growth
        if len(CALL_LOGS) > 100:
            CALL_LOGS.pop()
