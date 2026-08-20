import google.generativeai as genai
import os
import re
import threading
import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="google")

# ---------------------------------------------------------------------------
# Keyword-based classifier — runs FIRST, instant, no API calls
# ---------------------------------------------------------------------------
_STOCK_KEYWORDS = [
    "how many", "how much", "stock", "available", "quantity", "left",
    "kitna", "kitne", "kita", "बचा", "उपलब्ध", "स्टॉक", "किती"
]
_CREATE_KEYWORDS = [
    "request", "order", "add", "need", "want", "send", "deliver", "supply",
    "मंगाओ", "मागवा", "चाहिए", "लाओ", "भेजो", "मागणी", "ऑर्डर"
]
_EQUIPMENT_KEYWORDS = [
    "equipment", "machine", "crane", "excavator", "bulldozer", "mixer",
    "machinery", "tool", "मशीन", "उपकरण"
]
_BUDGET_KEYWORDS = [
    "budget", "cost", "expense", "spend", "money", "खर्च", "बजट"
]
_FAQ_KEYWORDS = [
    "what is", "how does", "explain", "tell me about", "sitesync", "workflow",
    "process", "role", "who", "why", "क्या है", "कैसे", "बताओ", "काय आहे"
]

def _keyword_classify(speech: str, role: str) -> str:
    """Fast keyword-based classifier — zero latency, no API calls."""
    text = speech.lower()
    if any(k in text for k in _STOCK_KEYWORDS):
        return "stock_query"
    if any(k in text for k in _CREATE_KEYWORDS):
        return "create_request"
    if any(k in text for k in _EQUIPMENT_KEYWORDS):
        return "equipment_query"
    if any(k in text for k in _BUDGET_KEYWORDS):
        return "budget_query"
    if any(k in text for k in _FAQ_KEYWORDS):
        return "general_faq"
    return "unclear"


def _gemini_classify(speech: str, role: str, api_key: str) -> str:
    """
    Calls Gemini with a 3-second hard timeout.
    Returns intent string or None if it timed out / failed.
    """
    result_holder = [None]

    def _call():
        for model_name in ["gemini-3.5-flash-lite", "gemini-3.6-flash"]:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(model_name)
                prompt = (
                    "Classify the following user speech into exactly ONE of these intent labels:\n"
                    "- create_request  (user wants to order/request materials)\n"
                    "- stock_query     (user asks how much of a material is available)\n"
                    "- equipment_query (user asks about equipment status)\n"
                    "- budget_query    (user asks about budget)\n"
                    "- general_faq     (user asks a general question about SiteSync)\n"
                    "- unclear         (cannot determine)\n\n"
                    f"Speech: {speech}\nRole: {role}\n\n"
                    "Respond with ONLY the intent label, nothing else."
                )
                resp = model.generate_content(prompt)
                result = resp.text.strip().lower()
                valid = {"create_request", "stock_query", "equipment_query",
                         "budget_query", "general_faq", "unclear"}
                if result in valid:
                    result_holder[0] = result
                return
            except Exception as e:
                err = str(e)
                print(f"[ERROR] Gemini classify failed ({model_name}): {err}")
                if "429" in err or "quota" in err.lower():
                    return  # quota hit, stop trying

    t = threading.Thread(target=_call, daemon=True)
    t.start()
    t.join(timeout=5.0)  # Hard 5-second timeout — Twilio needs response in 5s
    return result_holder[0]


def classify_intent(speech: str, role: str, site_ids: list) -> str:
    """
    1. Try keyword matching first (INSTANT — keeps us well under Twilio's 5s timeout)
    2. Only call Gemini if keywords return 'unclear' (with 3s hard timeout)
    3. Final fallback: keyword result (which is 'unclear')
    """
    if not speech or not speech.strip():
        return "unclear"

    # Step 1: Keywords first — handles 90% of real calls instantly
    keyword_result = _keyword_classify(speech, role)
    if keyword_result != "unclear":
        print(f"[INFO] Intent classified by keyword: {keyword_result}")
        return keyword_result

    # Step 2: Speech was ambiguous — try Gemini with a hard timeout
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        gemini_result = _gemini_classify(speech, role, api_key)
        if gemini_result and gemini_result != "unclear":
            print(f"[INFO] Intent classified by Gemini: {gemini_result}")
            return gemini_result

    # Step 3: Truly unclear
    return "unclear"
