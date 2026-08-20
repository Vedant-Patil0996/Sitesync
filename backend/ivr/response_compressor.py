import google.generativeai as genai
import os
import json
import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="google")

def _format_fallback_response(tool_output: str, language: str) -> str:
    """Format a JSON response from any tool into a readable localized IVR reply when AI fails."""
    try:
        data = json.loads(tool_output)
        if "error" in data:
            msgs = {
                "en": f"Sorry, {data['error']}",
                "hi": f"क्षमा करें, {data['error']}",
                "mr": f"माफ करा, {data['error']}",
            }
            return msgs.get(language, msgs["en"])

        # Stock Query Formatting
        if "current_stock" in data:
            mat  = data.get("material_name", "the material")
            qty  = data.get("current_stock", 0)
            unit = data.get("unit", "units")
            if qty == int(qty):
                qty = int(qty)
            msgs = {
                "en": f"There are currently {qty} {unit} of {mat} available.",
                "hi": f"अभी {mat} का {qty} {unit} उपलब्ध है।",
                "mr": f"सध्या {mat} चे {qty} {unit} उपलब्ध आहे.",
            }
            return msgs.get(language, msgs["en"])

        # Equipment Query Formatting
        elif "equipment_name" in data:
            name = data.get("equipment_name")
            status = data.get("status", "unknown")
            site = data.get("site_name", "unassigned site")
            msgs = {
                "en": f"The equipment {name} is currently {status} at {site}.",
                "hi": f"उपकरण {name} अभी {site} पर {status} है।",
                "mr": f"उपकरण {name} सध्या {site} येथे {status} आहे.",
            }
            return msgs.get(language, msgs["en"])

        # Budget Query Formatting
        elif "allocated" in data:
            site = data.get("site_name")
            allocated = data.get("allocated", 0)
            spent = data.get("spent", 0)
            util = data.get("utilization_percent", 0)
            msgs = {
                "en": f"For {site}, the total budget is {allocated} dollars, with {spent} dollars spent. Budget utilization is {util} percent.",
                "hi": f"{site} के लिए, कुल बजट {allocated} डॉलर है, जिसमें से {spent} डॉलर खर्च किया गया है। उपयोग {util} प्रतिशत है।",
                "mr": f"{site} साठी, एकूण बजेट {allocated} डॉलर्स आहे, ज्यापैकी {spent} डॉलर्स खर्च झाले आहेत. उपयोग {util} टक्के आहे.",
            }
            return msgs.get(language, msgs["en"])

        return tool_output
    except Exception:
        return tool_output  # Return raw if JSON parse fails


def compress_response(tool_output: str, language: str) -> str:
    """
    Convert a JSON tool response into a concise, conversational IVR reply.
    Uses the localized hand-crafted formatter directly to keep latency near zero.
    """
    return _format_fallback_response(tool_output, language)
