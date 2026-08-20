SESSIONS = {}

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
