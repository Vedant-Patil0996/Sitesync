from fastapi import APIRouter, Request, Form, Response
from twilio.twiml.voice_response import VoiceResponse
from app.db.session import SessionLocal
from app.models.procurement import MaterialRequest
from app.models.site import SiteAssignment
from app.models.user import User

from ivr.session_store import get_session, update_session, append_conversation
from ivr.caller_lookup import get_caller_info, get_caller_for_intent, get_site_id_by_name, get_material_id_by_name
from ivr.language_config import speak, gather
from ivr.intent_classifier import classify_intent
from ivr.request_extractor import extract_request
from ivr.response_compressor import compress_response
from ivr.tool_adapters import query_stock, query_equipment, query_budget
from ivr.demo_logger import log_demo_turn, get_all_logs
from ivr.faq_knowledge import FAQ_SYSTEM_PROMPT
import google.generativeai as genai
import os

router = APIRouter()

def get_twiml_response():
    return VoiceResponse()

@router.get("/logs")
async def get_logs():
    """Retrieve all simulated/actual IVR logs for frontend display."""
    return get_all_logs()

@router.post("/simulate")
async def simulate_ivr(request: Request):
    """Simulate an IVR turn in JSON format directly from the frontend."""
    data = await request.json()
    speech = data.get("speech", "")
    from_number = data.get("phone", "+15093511940")
    call_sid = data.get("call_sid", "SIM_CALL_123")
    
    # 1. Caller lookup with fallbacks
    caller_info = get_caller_info(from_number)
    if not caller_info:
        caller_info = {
            "user_id": "1",
            "role": "contractor",
            "site_ids": ["1"],
            "name": "Simulated User"
        }
        
    session = get_session(call_sid)
    if "user_id" not in session:
        session.update({
            "user_id": caller_info["user_id"],
            "role": caller_info["role"],
            "site_ids": caller_info["site_ids"],
            "name": caller_info["name"],
            "selected_language": session.get("selected_language", "en")
        })
        
    language = session.get("selected_language", "en")
    pending = session.get("pending_material_request")
    reply = ""
    action = ""
    intent = ""
    extracted = None
    
    if pending:
        # Check confirmation
        is_yes = "yes" in speech.lower() or "हां" in speech.lower() or "हो" in speech.lower() or "हाँ" in speech.lower()
        is_no = "no" in speech.lower() or "नहीं" in speech.lower() or "नाही" in speech.lower()
        
        if is_no:
            session["pending_material_request"] = None
            reply = "Cancelled request. What else can I help you with?"
            action = "Cancelled pending request"
            intent = "confirm_request"
        elif is_yes:
            db = SessionLocal()
            try:
                req = MaterialRequest(
                    site_id=pending["site_id"],
                    material_id=pending["material_id"],
                    quantity=pending["quantity"],
                    requested_by=session["user_id"],
                    justification="Submitted via voice simulator",
                    pm_status="pending",
                    finance_status="not_applicable"
                )
                db.add(req)
                db.commit()
                reply = "Request submitted. Your project manager has been notified."
                action = "Placed material request in database"
            except Exception as e:
                db.rollback()
                reply = f"Error saving request: {e}"
                action = f"DB Error: {e}"
            finally:
                db.close()
                session["pending_material_request"] = None
            intent = "confirm_request"
        else:
            reply = "Please say yes or no to confirm."
            action = "Prompted yes/no confirmation"
            intent = "confirm_request"
    else:
        # Process intent
        intent = classify_intent(speech, session["role"], session["site_ids"])
        
        intent_user = get_caller_for_intent(intent, from_number)
        if intent_user:
            session.update({
                "user_id": intent_user["user_id"],
                "role": intent_user["role"],
                "site_ids": intent_user["site_ids"],
                "name": intent_user["name"]
            })
            
        if intent == "unclear":
            reply = "I didn't quite catch that. Could you repeat it?"
            action = "Prompted clarify"
        elif intent == "create_request":
            extracted = extract_request(speech, session["role"], session["site_ids"])
            mat_name = extracted.get("material")
            qty = extracted.get("quantity")
            unit = extracted.get("unit", "units")
            site_name = extracted.get("site")
            
            if not (mat_name and qty and site_name):
                reply = "I didn't get all the details. Please specify material, quantity, and site."
                action = "Awaiting full request details"
            else:
                site_id = get_site_id_by_name(site_name, session["site_ids"])
                mat_id = get_material_id_by_name(mat_name)
                
                if not site_id:
                    reply = f"You are not assigned to site {site_name}."
                    action = "Rejected: site unauthorized"
                elif not mat_id:
                    reply = f"I couldn't find material {mat_name} in catalog."
                    action = "Rejected: material not found"
                else:
                    session["pending_material_request"] = {
                        "site_id": site_id,
                        "material_id": mat_id,
                        "quantity": qty,
                        "desc": f"{qty} {unit} of {mat_name} for {site_name}"
                    }
                    reply = f"Confirming. {qty} {unit} of {mat_name} for {site_name}. Is that correct?"
                    action = "Created pending request, awaiting confirmation"
        else:
            # Queries
            tool_output = ""
            if intent == "stock_query":
                extracted = extract_request(speech, session["role"], session["site_ids"])
                site_id = get_site_id_by_name(extracted.get("site"), session["site_ids"]) if extracted.get("site") else (session["site_ids"][0] if session["site_ids"] else None)
                mat_id = get_material_id_by_name(extracted.get("material")) if extracted.get("material") else None
                if not site_id or not mat_id:
                    reply = "Please specify both material and site clearly."
                else:
                    tool_output = query_stock(str(mat_id), str(site_id))
            elif intent == "equipment_query":
                extracted = extract_request(speech, session["role"], session["site_ids"])
                eq_name = extracted.get("material") or speech
                tool_output = query_equipment(str(eq_name))
            elif intent == "budget_query":
                if session["role"] != "pm":
                    reply = "Only PMs can query budget."
                else:
                    site_id = session["site_ids"][0] if session["site_ids"] else None
                    tool_output = query_budget(str(site_id))
            elif intent == "general_faq":
                reply = "SiteSync is a construction site management system. Please refer to your user manual."
                action = "Answered FAQ"
                
            if tool_output:
                reply = compress_response(tool_output, language)
                action = f"Processed {intent} query"
                
    if not reply:
        reply = "Sorry, I couldn't process your request."
        
    log_demo_turn(call_sid, session["name"], session["role"], session["site_ids"], language, speech, intent, extracted, action, reply)
    
    return {
        "call_sid": call_sid,
        "intent": intent,
        "extracted": extracted,
        "reply": reply,
        "action": action,
        "name": session["name"],
        "role": session["role"],
        "pending_request": session.get("pending_material_request")
    }

@router.post("/incoming")
async def handle_incoming(request: Request):
    form = await request.form()
    call_sid = form.get("CallSid")
    from_number = form.get("From")
    
    response = get_twiml_response()
    
    caller_info = get_caller_info(from_number)
    if not caller_info:
        response.append(speak("Sorry, this line is only for registered SiteSync users.", "en"))
        response.hangup()
        log_demo_turn(call_sid, from_number, "Unknown", [], "en", action="Rejected unknown caller")
        return Response(content=str(response), media_type="application/xml")
        
    update_session(call_sid, {
        "user_id": caller_info["user_id"],
        "role": caller_info["role"],
        "site_ids": caller_info["site_ids"],
        "name": caller_info["name"]
    })
    
    # Language Selection Prompt
    msg = "For English press 1 or say English. हिंदी के लिए 2 दबाएं या हिंदी बोलें. मराठीसाठी 3 दाबा किंवा मराठी बोला."
    g = gather("hi", "/ivr/language", hints="English, Hindi, Marathi")
    g.append(speak(msg, "hi"))
    response.append(g)
    
    return Response(content=str(response), media_type="application/xml")

@router.post("/language")
async def handle_language(request: Request):
    form = await request.form()
    call_sid = form.get("CallSid")
    speech_result = form.get("SpeechResult", "").lower()
    digits = form.get("Digits", "")
    
    session = get_session(call_sid)
    
    language = "en"
    if "2" in digits or "hindi" in speech_result or "हिंदी" in speech_result:
        language = "hi"
    elif "3" in digits or "marathi" in speech_result or "मराठी" in speech_result:
        language = "mr"
        
    update_session(call_sid, {"selected_language": language})
    
    welcome_msgs = {
        "en": "Welcome to SiteSync. How can I help you?",
        "hi": "साइट सिंक में आपका स्वागत है। मैं आपकी कैसे मदद कर सकता हूँ?",
        "mr": "साइट सिंक मध्ये आपले स्वागत आहे. मी तुम्हाला कशी मदत करू शकतो?"
    }
    
    response = get_twiml_response()
    g = gather(language, "/ivr/process")
    g.append(speak(welcome_msgs[language], language))
    response.append(g)
    
    log_demo_turn(call_sid, session.get("name"), session.get("role"), session.get("site_ids"), language, action="Selected language")
    
    return Response(content=str(response), media_type="application/xml")

@router.post("/process")
async def handle_process(request: Request):
    form = await request.form()
    call_sid = form.get("CallSid")
    speech_result = form.get("SpeechResult", "")
    from_number = form.get("From", "")
    
    session = get_session(call_sid)
    language = session.get("selected_language", "en")
    role = session.get("role")
    site_ids = session.get("site_ids")
    
    if not role and from_number:
        caller_info = get_caller_info(from_number)
        if caller_info:
            update_session(call_sid, {
                "user_id": caller_info["user_id"],
                "role": caller_info["role"],
                "site_ids": caller_info["site_ids"],
                "name": caller_info["name"]
            })
            role = caller_info["role"]
            site_ids = caller_info["site_ids"]
            
    role = role or "contractor"
    site_ids = site_ids or []
    
    append_conversation(call_sid, "user", speech_result)
    
    intent = classify_intent(speech_result, role, site_ids)
    
    if from_number:
        intent_user = get_caller_for_intent(intent, from_number)
        if intent_user:
            role = intent_user["role"]
            site_ids = intent_user["site_ids"]
            update_session(call_sid, {
                "user_id": intent_user["user_id"],
                "role": intent_user["role"],
                "site_ids": intent_user["site_ids"],
                "name": intent_user["name"],
            })

    response = get_twiml_response()
    reply = ""
    extracted = None
    action_log = ""

    if intent == "unclear":
        reply = "I didn't quite catch that. Could you repeat it?"
        if language == "hi": reply = "मुझे समझ नहीं आया। क्या आप फिर से कह सकते हैं?"
        if language == "mr": reply = "मला समजले नाही. कृपया पुन्हा सांगाल का?"
        
        g = gather(language, "/ivr/process")
        g.append(speak(reply, language))
        response.append(g)
        log_demo_turn(call_sid, session.get("name"), role, site_ids, language, speech_result, intent, reply=reply)
        return Response(content=str(response), media_type="application/xml")
        
    if intent == "create_request":
        extracted = extract_request(speech_result, role, site_ids)
        mat_name = extracted.get("material")
        qty = extracted.get("quantity")
        unit = extracted.get("unit", "units")
        site_name = extracted.get("site")
            
        if not (mat_name and qty and site_name):
            reply = "I didn't get all the details. Please tell me the material, quantity, and site name."
            if language == "hi": reply = "मुझे पूरी जानकारी नहीं मिली। कृपया सामग्री, मात्रा और साइट का नाम बताएं।"
            if language == "mr": reply = "मला संपूर्ण माहिती मिळाली नाही. कृपया साहित्य, प्रमाण आणि साईटचे नाव सांगा."
            g = gather(language, "/ivr/process")
            g.append(speak(reply, language))
            response.append(g)
        else:
            site_id = get_site_id_by_name(site_name, site_ids)
            mat_id = get_material_id_by_name(mat_name)
            
            if not site_id:
                reply = f"You are not assigned to site {site_name}. Please specify a valid site."
                g = gather(language, "/ivr/process")
                g.append(speak(reply, language))
                response.append(g)
            elif not mat_id:
                reply = f"I couldn't find the material {mat_name} in our catalog. Please try again."
                g = gather(language, "/ivr/process")
                g.append(speak(reply, language))
                response.append(g)
            else:
                update_session(call_sid, {
                    "pending_material_request": {
                        "site_id": site_id,
                        "material_id": mat_id,
                        "quantity": qty,
                        "desc": f"{qty} {unit} of {mat_name} for {site_name}"
                    }
                })
                reply = f"Confirming. {qty} {unit} of {mat_name} for {site_name}. Is that correct?"
                if language == "hi": reply = f"पुष्टि कर रहा हूँ। {site_name} के लिए {qty} {unit} {mat_name}। क्या यह सही है?"
                if language == "mr": reply = f"खात्री करत आहे. {site_name} साठी {qty} {unit} {mat_name}. हे बरोबर आहे का?"
                
                g = gather(language, "/ivr/confirm_request")
                g.append(speak(reply, language))
                response.append(g)
                action_log = "Awaiting confirmation"
                
        log_demo_turn(call_sid, session.get("name"), role, site_ids, language, speech_result, intent, extracted, action_log, reply)
        return Response(content=str(response), media_type="application/xml")

    tool_output = ""
    if intent == "stock_query":
        extracted = extract_request(speech_result, role, site_ids)
        site_id = get_site_id_by_name(extracted.get("site"), site_ids) if extracted.get("site") else (site_ids[0] if site_ids else None)
        mat_id = get_material_id_by_name(extracted.get("material")) if extracted.get("material") else None
        if not site_id or not mat_id:
            reply = "Please specify both material and site clearly."
        else:
            tool_output = query_stock(str(mat_id), str(site_id))
    elif intent == "equipment_query":
        extracted = extract_request(speech_result, role, site_ids)
        eq_name = extracted.get("material") or speech_result
        tool_output = query_equipment(str(eq_name))
    elif intent == "budget_query":
        if role != "pm":
            reply = "Only PMs can query budget."
        else:
            site_id = site_ids[0] if site_ids else None
            tool_output = query_budget(str(site_id))
    elif intent == "general_faq":
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            faq_prompt = f"{FAQ_SYSTEM_PROMPT}\n\nCaller asked: {speech_result}\nReply concisely in {'English' if language == 'en' else 'Hindi' if language == 'hi' else 'Marathi'}. Keep it to 1-2 sentences."
            faq_answered = False
            for _model_name in ["gemini-3.5-flash-lite", "gemini-3.6-flash"]:
                try:
                    genai.configure(api_key=api_key)
                    faq_model = genai.GenerativeModel(_model_name)
                    faq_resp = faq_model.generate_content(faq_prompt)
                    reply = faq_resp.text.strip()
                    faq_answered = True
                    break
                except Exception as _e:
                    _err = str(_e)
                    print(f"[ERROR] FAQ generation failed ({_model_name}): {_err}")
                    if "429" in _err or "quota" in _err.lower():
                        break
            if not faq_answered:
                reply = "SiteSync is a construction site management system. Please visit the app for details."
        else:
            reply = "SiteSync is a construction site management system. Please visit the app for details."

    if tool_output:
        reply = compress_response(tool_output, language)
        action_log = f"Answered query for {intent}"
        
    if not reply:
        reply = "I am sorry, I couldn't process your query."
        
    response.append(speak(reply, language))
    
    prompt_more = "Anything else?"
    if language == "hi": prompt_more = "कुछ और?"
    if language == "mr": prompt_more = "अजून काही?"
    
    g = gather(language, "/ivr/process")
    g.append(speak(prompt_more, language))
    response.append(g)
    
    log_demo_turn(call_sid, session.get("name"), role, site_ids, language, speech_result, intent, extracted, action_log, reply)
    return Response(content=str(response), media_type="application/xml")

@router.post("/confirm_request")
async def handle_confirm(request: Request):
    form = await request.form()
    call_sid = form.get("CallSid")
    speech_result = form.get("SpeechResult", "").lower()
    
    session = get_session(call_sid)
    language = session.get("selected_language", "en")
    pending = session.get("pending_material_request")
    
    response = get_twiml_response()
    
    is_yes = "yes" in speech_result or "हां" in speech_result or "हो" in speech_result or "हाँ" in speech_result
    is_no = "no" in speech_result or "नहीं" in speech_result or "नाही" in speech_result
    
    if is_no:
        update_session(call_sid, {"pending_material_request": None})
        reply = "Okay, cancelled. What else can I help you with?"
        if language == "hi": reply = "ठीक है, रद्द कर दिया। मैं आपकी और क्या मदद कर सकता हूँ?"
        if language == "mr": reply = "ठीक आहे, रद्द केले. मी तुम्हाला अजून कशी मदत करू शकतो?"
        
        g = gather(language, "/ivr/process")
        g.append(speak(reply, language))
        response.append(g)
        log_demo_turn(call_sid, session.get("name"), session.get("role"), session.get("site_ids"), language, speech_result, "confirm_request", action="Cancelled request")
        return Response(content=str(response), media_type="application/xml")
        
    if is_yes and pending:
        db = SessionLocal()
        try:
            req = MaterialRequest(
                site_id=pending["site_id"],
                material_id=pending["material_id"],
                quantity=pending["quantity"],
                requested_by=session["user_id"],
                justification="Submitted via voice call",
                pm_status="pending",
                finance_status="not_applicable"
            )
            db.add(req)
            db.commit()
            
            reply = "Request submitted. Your project manager has been notified."
            if language == "hi": reply = "अनुरोध सबमिट कर दिया गया है। आपके प्रोजेक्ट मैनेजर को सूचित कर दिया गया है।"
            if language == "mr": reply = "विनंती सबमिट केली आहे. तुमच्या प्रोजेक्ट मॅनेजरला सूचित केले आहे."
            
            response.append(speak(reply, language))
            log_demo_turn(call_sid, session.get("name"), session.get("role"), session.get("site_ids"), language, speech_result, "confirm_request", action="Confirmed and inserted request in DB")
            
        except Exception as e:
            db.rollback()
            response.append(speak("There was an error saving your request.", language))
            log_demo_turn(call_sid, session.get("name"), session.get("role"), session.get("site_ids"), language, action=f"Error saving request: {e}")
        finally:
            db.close()
            update_session(call_sid, {"pending_material_request": None})
    else:
        reply = "Please say yes or no."
        if language == "hi": reply = "कृपया हाँ या ना कहें।"
        if language == "mr": reply = "कृपया हो किंवा नाही सांगा."
        g = gather(language, "/ivr/confirm_request")
        g.append(speak(reply, language))
        response.append(g)
        
    return Response(content=str(response), media_type="application/xml")
