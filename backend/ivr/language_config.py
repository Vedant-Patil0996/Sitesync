from twilio.twiml.voice_response import Gather, Say

def speak(text, language):
    lang_map = {"en": "en-US", "hi": "hi-IN", "mr": "hi-IN"} # Twilio doesn't natively support mr, fallback to hi
    say = Say(message=text, language=lang_map.get(language, "en-US"))
    return say

def gather(language, action, hints="", timeout=10):
    """
    timeout      = seconds Twilio waits for caller to START speaking (default 10)
    speechTimeout= seconds of silence AFTER speech ends before Twilio submits (3s = full sentences)
    """
    lang_map = {"en": "en-US", "hi": "hi-IN", "mr": "hi-IN"}
    return Gather(
        input="speech dtmf",
        action=action,
        language=lang_map.get(language, "en-US"),
        hints=hints,
        timeout=timeout,          # wait 10s for caller to start
        speechTimeout="3",        # wait 3s of silence after speech (not "auto" which cuts too early)
    )
