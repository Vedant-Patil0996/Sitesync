import google.generativeai as genai
import os
import json
import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="google")

def _format_stock_response(tool_output: str, language: str) -> str:
    """Format a stock JSON response into a readable IVR reply — no API calls."""
    try:
        data = json.loads(tool_output)
        if "error" in data:
            msgs = {
                "en": "Sorry, I couldn't find that stock information.",
                "hi": "क्षमा करें, मुझे वह स्टॉक जानकारी नहीं मिली।",
                "mr": "माफ करा, मला ती स्टॉक माहिती मिळाली नाही.",
            }
            return msgs.get(language, msgs["en"])

        mat  = data.get("material_name", "the material")
        qty  = data.get("current_stock", 0)
        unit = data.get("unit", "units")

        # Round to clean number if it's a whole number
        if qty == int(qty):
            qty = int(qty)

        msgs = {
            "en": f"There are currently {qty} {unit} of {mat} available.",
            "hi": f"अभी {mat} का {qty} {unit} उपलब्ध है।",
            "mr": f"सध्या {mat} चे {qty} {unit} उपलब्ध आहे.",
        }
        return msgs.get(language, msgs["en"])
    except Exception:
        return tool_output  # Return raw if JSON parse fails


def compress_response(tool_output: str, language: str) -> str:
    """
    Convert a JSON tool response into a concise, conversational IVR reply.
    Tries Gemini first; falls back to a hand-crafted formatter.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return _format_stock_response(tool_output, language)

    for model_name in ["gemini-3.5-flash-lite", "gemini-3.6-flash"]:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name)
            lang_names = {"en": "English", "hi": "Hindi", "mr": "Marathi"}
            lang_name = lang_names.get(language, "English")
            prompt = (
                f"Convert this JSON data into a concise, conversational 1-2 sentence response "
                f"in {lang_name} suitable for a phone call. Be natural and clear.\n\n"
                f"Data: {tool_output}"
            )
            resp = model.generate_content(prompt)
            return resp.text.strip()
        except Exception as e:
            err = str(e)
            print(f"[ERROR] Compression failed ({model_name}): {err}")
            if "429" in err or "quota" in err.lower():
                break
            continue

    # Fallback to hand-crafted formatter
    return _format_stock_response(tool_output, language)
