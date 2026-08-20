import google.generativeai as genai
import os
import re
import json
import threading
import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="google")

# ---------------------------------------------------------------------------
# Keyword/regex extractor — runs FIRST, instant, no API calls
# ---------------------------------------------------------------------------
_QUANTITY_RE = re.compile(
    r"\b(\d+(?:\.\d+)?)\s*(kg|kgs|ton|tons|tonne|bag|bags|unit|units|piece|pieces|"
    r"pipe|pipes|sheet|sheets|metre|meters|litre|litres|liter|liters|"
    r"square feet|sq ft|nos|number|pallet|pallets)?\b",
    re.IGNORECASE
)

_STOPWORDS = {
    "how", "many", "much", "is", "are", "the", "a", "an", "do",
    "i", "we", "have", "there", "at", "for", "of", "in", "any",
    "and", "or", "to", "that", "this", "request", "order", "add",
    "need", "want", "please", "can", "you", "get", "me", "my",
    # unit words (extracted separately, don't mix into material name)
    "bags", "bag", "tons", "ton", "kg", "kgs", "units", "unit",
    "pieces", "piece", "pallets", "pallet", "meters", "metre",
    "litres", "liter", "liters", "litre", "nos", "number",
    # common adjectives/fillers that aren't material names
    "available", "current", "existing", "total", "remaining",
    "many", "much", "all", "some", "what", "which",
}


def _keyword_extract(speech: str) -> dict:
    """
    Instant regex/keyword-based extraction — no API calls.
    Returns dict with keys: material, quantity, unit, site.
    """
    text = speech.lower()

    # Extract quantity (first number in the speech)
    qty = None
    unit = None
    m = _QUANTITY_RE.search(text)
    if m:
        qty_str = m.group(1)
        qty = int(float(qty_str)) if float(qty_str) == int(float(qty_str)) else float(qty_str)
        unit = m.group(2) or "units"

    # Extract site — everything after "at", "for site", "at the", "in"
    site = None
    for prep in [" at the ", " at ", " for site ", " in the ", " in ", " for "]:
        idx = text.rfind(prep)
        if idx != -1:
            candidate = speech[idx + len(prep):].strip()
            # Remove trailing punctuation / common endings
            candidate = re.split(r'[.?!,]', candidate)[0].strip()
            if 2 < len(candidate) < 60:
                site = candidate
                break

    # Extract material — find content words before any site preposition
    material = None
    # Stop collecting words at site prepositions
    _SITE_PREPS = {"at", "for", "in"}
    words = re.findall(r"[A-Za-z]+", speech)
    material_words = []
    for w in words:
        wl = w.lower()
        if wl in _SITE_PREPS:
            break  # Stop at "at", "for", "in" — everything after is the site
        if wl not in _STOPWORDS and len(w) > 2:
            material_words.append(w.lower())
            if len(material_words) == 2:
                break  # Max 2-word material name
    if material_words:
        material = " ".join(material_words)


    return {"material": material, "quantity": qty, "unit": unit, "site": site}


def _gemini_extract(speech: str, api_key: str) -> dict | None:
    """Calls Gemini with a 3-second hard timeout. Returns dict or None."""
    result_holder = [None]

    def _call():
        for model_name in ["gemini-3.5-flash-lite", "gemini-3.6-flash"]:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(model_name)
                prompt = (
                    "Extract details from the following speech into a JSON object with these keys:\n"
                    '  "material": string (e.g. "cement", "PVC pipes", "bricks") or null\n'
                    '  "quantity": number or null\n'
                    '  "unit": string (e.g. "bags", "tons", "pieces") or null\n'
                    '  "site": string (site name, e.g. "Downtown Plaza", "Riverside Complex") or null\n\n'
                    f"Speech: {speech}\n\n"
                    "Return ONLY valid JSON with those four keys. No markdown, no extra text."
                )
                resp = model.generate_content(prompt)
                text = resp.text.strip()
                text = re.sub(r"^```(?:json)?\s*", "", text)
                text = re.sub(r"\s*```$", "", text)
                data = json.loads(text.strip())
                for k in ("material", "quantity", "unit", "site"):
                    data.setdefault(k, None)
                result_holder[0] = data
                return
            except Exception as e:
                err = str(e)
                print(f"[ERROR] Gemini extract failed ({model_name}): {err}")
                if "429" in err or "quota" in err.lower():
                    return

    t = threading.Thread(target=_call, daemon=True)
    t.start()
    t.join(timeout=3.0)  # Hard 3-second timeout
    return result_holder[0]


def extract_request(speech: str, role: str, site_ids: list) -> dict:
    """
    1. Keyword/regex extraction first (INSTANT)
    2. If quantity or material not found, try Gemini with 3s hard timeout
    3. Always returns the best available result
    """
    if not speech or not speech.strip():
        return {}

    # Step 1: Instant keyword extraction
    keyword_result = _keyword_extract(speech)

    # If we already have material AND (quantity OR site) → good enough, skip Gemini
    if keyword_result.get("material") and (
        keyword_result.get("quantity") or keyword_result.get("site")
    ):
        print(f"[INFO] Extraction by keyword: {keyword_result}")
        return keyword_result

    # Step 2: Keyword result was incomplete — try Gemini with timeout
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        gemini_result = _gemini_extract(speech, api_key)
        if gemini_result:
            # Merge: prefer Gemini values, fall back to keyword values
            for k in ("material", "quantity", "unit", "site"):
                if not gemini_result.get(k) and keyword_result.get(k):
                    gemini_result[k] = keyword_result[k]
            print(f"[INFO] Extraction by Gemini: {gemini_result}")
            return gemini_result

    print(f"[INFO] Extraction by keyword fallback: {keyword_result}")
    return keyword_result
