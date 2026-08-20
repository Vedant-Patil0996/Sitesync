def log_demo_turn(call_sid, name, role, site_ids, language, speech_result="", intent="", extracted=None, action="", reply=""):
    print("-" * 60)
    print(f"[CALL {call_sid[-6:]}] Caller: {name} ({role}, Sites: {site_ids}) | Language: {language}")
    if speech_result: print(f"[CALL {call_sid[-6:]}] Heard:     '{speech_result}'")
    if intent: print(f"[CALL {call_sid[-6:]}] Intent:    {intent}")
    if extracted: print(f"[CALL {call_sid[-6:]}] Extracted: {extracted}")
    if action: print(f"[CALL {call_sid[-6:]}] Action:    {action}")
    if reply: print(f"[CALL {call_sid[-6:]}] Replied:   '{reply}'")
