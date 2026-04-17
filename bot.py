import os
import json
import logging
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, ContextTypes, filters
)
from rule_filter import rule_filter
from rag import run_rag

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

LANGUAGE, AGE, GENDER, CASTE, RELIGION, OCCUPATION, INCOME, RESIDENCE, MARITAL, HOUSELESS, FLAGS, CHAT = range(12)

BOT_I18N = {
    "English": {
        "age_q": "Great! Let's find your eligible AP government schemes.\n\nPlease enter your *age* (example: 24):",
        "age_err": "❗ Please enter a valid age between 5 and 100:",
        "gender_q": "Got it! Now select your *gender*:",
        "gender_err": "Please choose from the keyboard options:",
        "caste_q": "Select your *caste category*:",
        "rel_q": "Select your *religion*:",
        "occ_q": "What is your *occupation*?",
        "inc_q": "What is your *annual family income* in rupees?\n\nExample: 150000 for ₹1,50,000",
        "inc_err": "❗ Please enter income as a number. Example: 150000",
        "residence_q": "Do you live in a *rural* (village) or *urban* (town/city) area?",
        "marital_q": "What is your *marital status*?",
        "houseless_q": "Do you currently *not own a house* (houseless)?",
        "flags_q": "Do any of these apply to you? *(Select one or say None)*",
        "search": "🔍 Searching for schemes that match your profile...",
        "no_match": "😔 No schemes matched your profile based on the current criteria.\n\nTry /start again with different details.",
        "gender_opts":    [["Male", "Female"], ["Other"]],
        "caste_opts":     [["SC", "ST"], ["BC", "OC"], ["EBC", "Minority"]],
        "rel_opts":       [["Hindu", "Muslim"], ["Christian", "Sikh"], ["Buddhist", "Other"]],
        "occ_opts":       [["Student", "Farmer"], ["Weaver", "Fisherman"], ["Driver", "Worker"], ["Street Vendor", "Small Business"], ["Unemployed", "Salaried"], ["Other"]],
        "residence_opts": [["Rural (Village)", "Urban (Town/City)"]],
        "marital_opts":   [["Married", "Widowed"], ["Single", "Separated"]],
        "houseless_opts": [["Yes, I am houseless", "No, I have a house"]],
        "flag_opts":      [["Widow", "Disabled"], ["SHG Member", "None of these"]]
    },
    "Telugu": {
        "age_q": "చాలా సంతోషం! మీకు సరిపోయే ప్రభుత్వ పథకాలను వెతుకుదాం.\n\nదయచేసి మీ వయస్సు (ఉదాహరణకు: 24) నమోదు చేయండి:",
        "age_err": "❗ దయచేసి 5 మరియు 100 మధ్య సరైన వయస్సును నమోదు చేయండి:",
        "gender_q": "అర్థమైంది! ఇప్పుడు మీ లింగాన్ని ఎంచుకోండి:",
        "gender_err": "దయచేసి కీబోర్డ్ ఎంపికల నుండి ఎంచుకోండి:",
        "caste_q": "మీ కుల వర్గాన్ని ఎంచుకోండి:",
        "rel_q": "మీ మతాన్ని ఎంచుకోండి:",
        "occ_q": "మీ వృత్తి ఏమిటి?",
        "inc_q": "మీ వార్షిక కుటుంబ ఆదాయం ఎంత (రూపాయల్లో)?\n\nఉదాహరణ: లక్షన్నర కోసం 150000",
        "inc_err": "❗ దయచేసి ఆదాయాన్ని నంబర్‌గా నమోదు చేయండి. ఉదాహరణ: 150000",
        "residence_q": "మీరు *గ్రామీణ* (పల్లె) లేదా *పట్టణ* (నగరం) ప్రాంతంలో నివసిస్తున్నారా?",
        "marital_q": "మీ *వైవాహిక స్థితి* ఏమిటి?",
        "houseless_q": "మీకు ప్రస్తుతం సొంత ఇల్లు లేదా? (*నిరాశ్రయులు*)",
        "flags_q": "వీటిలో ఏదైనా మీకు వర్తిస్తుందా? (ఏదైనా ఎంచుకోండి లేదా ఏమీ లేదు అని చెప్పండి):",
        "search": "🔍 మీ ప్రొఫైల్‌కు సరిపోలే పథకాల కోసం వెతుకుతోంది...",
        "no_match": "😔 ప్రస్తుత ప్రమాణాల ఆధారంగా మీ ప్రొఫైల్‌కు సరిపోలే పథకాలు ఏమి లేవు.\n\nవివిద వివరాలతో మరల /start ప్రయత్నించండి.",
        "gender_opts":    [["పురుషుడు", "స్త్రీ"], ["ఇతర"]],
        "caste_opts":     [["SC", "ST"], ["BC", "OC"], ["EBC", "మైనారిటీ"]],
        "rel_opts":       [["హిందూ", "ముస్లిం"], ["క్రిస్టియన్", "సిక్కు"], ["బౌద్ధ", "ఇతర"]],
        "occ_opts":       [["విద్యార్థి", "రైతు"], ["నేత కార్మికుడు", "మత్స్యకారుడు"], ["డ్రైవర్", "కార్మికుడు"], ["వీధి వ్యాపారి", "చిన్న వ్యాపారం"], ["నిరుద్యోగి", "ఉద్యోగి"], ["ఇతర"]],
        "residence_opts": [["గ్రామీణ (పల్లె)", "పట్టణ (నగరం)"]],
        "marital_opts":   [["వివాహిత", "వితంతువు"], ["అవివాహిత", "విడాకులు"]],
        "houseless_opts": [["అవును, నాకు ఇల్లు లేదు", "కాదు, నాకు ఇల్లు ఉంది"]],
        "flag_opts":      [["వితంతువు", "వికలాంగుడు"], ["SHG సభ్యుడు", "ఏవీ కావు"]]
    },
    "Hindi": {
        "age_q": "बहुत बढ़िया! आइए आपके लिए उपयुक्त सरकारी योजनाएं खोजें।\n\nकृपया अपनी आयु दर्ज करें (उदाहरण: 24):",
        "age_err": "❗ कृपया 5 और 100 के बीच एक मान्य आयु दर्ज करें:",
        "gender_q": "समझ गया! अब अपना लिंग चुनें:",
        "gender_err": "कृपया कीबोर्ड विकल्पों में से चुनें:",
        "caste_q": "अपनी जाति श्रेणी चुनें:",
        "rel_q": "अपना धर्म चुनें:",
        "occ_q": "आपका पेशा क्या है?",
        "inc_q": "आपकी वार्षिक पारिवारिक आय रुपये में कितनी है?\n\nउदाहरण: 1,50,000 के लिए 150000",
        "inc_err": "❗ कृपया आय को एक संख्या के रूप में दर्ज करें। उदाहरण: 150000",
        "residence_q": "आप *ग्रामीण* (गाँव) या *शहरी* (शहर) क्षेत्र में रहते हैं?",
        "marital_q": "आपकी *वैवाहिक स्थिति* क्या है?",
        "houseless_q": "क्या आपके पास अभी *अपना घर नहीं है* (बेघर)?",
        "flags_q": "क्या इनमें से कोई आप पर लागू होता है? (एक चुनें या कोई नहीं कहें):",
        "search": "🔍 आपकी प्रोफ़ाइल से मेल खाने वाली योजनाएं खोजी जा रही हैं...",
        "no_match": "😔 वर्तमान मानदंडों के आधार पर आपकी प्रोफ़ाइल से कोई योजना मेल नहीं खाई।\n\nअलग विवरण के साथ फिर से /start प्रयास करें।",
        "gender_opts":    [["पुरुष", "महिला"], ["अन्य"]],
        "caste_opts":     [["SC", "ST"], ["BC", "OC"], ["EBC", "अल्पसंख्यक"]],
        "rel_opts":       [["हिंदू", "मुस्लिम"], ["ईसाई", "सिख"], ["बौद्ध", "अन्य"]],
        "occ_opts":       [["छात्र", "किसान"], ["बुनकर", "मछुआरा"], ["ड्राइवर", "मजदूर"], ["सड़क विक्रेता", "छोटा व्यवसाय"], ["बेरोजगार", "वेतनभोगी"], ["अन्य"]],
        "residence_opts": [["ग्रामीण (गाँव)", "शहरी (शहर)"]],
        "marital_opts":   [["विवाहित", "विधवा"], ["अविवाहित", "अलग"]],
        "houseless_opts": [["हाँ, मेरे पास घर नहीं है", "नहीं, मेरे पास घर है"]],
        "flag_opts":      [["विधवा", "विकलांग"], ["SHG सदस्य", "इनमें से कोई नहीं"]]
    }
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    keyboard = [["English", "Telugu", "Hindi"]]
    await update.message.reply_text(
        "🙏 *Welcome to YojanaIQ!*\n\n"
        "Please select your preferred language:\n"
        "దయచేసి మీకు ఇష్టమైన భాషను ఎంచుకోండి:\n"
        "कृपया अपनी पसंदीदा भाषा चुनें:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return LANGUAGE

async def get_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = update.message.text.strip().capitalize()
    if lang not in ["English", "Telugu", "Hindi"]:
        lang = "English"
    context.user_data["language"] = lang
    t = BOT_I18N[lang]
    await update.message.reply_text(t["age_q"], parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
    return AGE

async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("language", "English")
    t = BOT_I18N[lang]
    text = update.message.text.strip()
    if not text.isdigit() or not (5 <= int(text) <= 100):
        await update.message.reply_text(t["age_err"])
        return AGE
    context.user_data["age"] = int(text)
    await update.message.reply_text(t["gender_q"], parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(t["gender_opts"], one_time_keyboard=True, resize_keyboard=True))
    return GENDER

async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("language", "English")
    t = BOT_I18N[lang]
    text = update.message.text.strip()
    flat_opts = [item for sublist in t["gender_opts"] for item in sublist]
    try:
        idx = flat_opts.index(text)
        eng_flat = [item for sublist in BOT_I18N["English"]["gender_opts"] for item in sublist]
        context.user_data["gender"] = eng_flat[idx].lower()
    except ValueError:
        await update.message.reply_text(t["gender_err"])
        return GENDER
    await update.message.reply_text(t["caste_q"], parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(t["caste_opts"], one_time_keyboard=True, resize_keyboard=True))
    return CASTE

async def get_caste(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("language", "English")
    t = BOT_I18N[lang]
    text = update.message.text.strip()
    flat_opts = [item for sublist in t["caste_opts"] for item in sublist]
    try:
        idx = flat_opts.index(text)
        eng_flat = [item for sublist in BOT_I18N["English"]["caste_opts"] for item in sublist]
        context.user_data["caste"] = eng_flat[idx].upper()
    except ValueError:
        await update.message.reply_text(t["gender_err"])
        return CASTE
    await update.message.reply_text(t["rel_q"], parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(t["rel_opts"], one_time_keyboard=True, resize_keyboard=True))
    return RELIGION

async def get_religion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("language", "English")
    t = BOT_I18N[lang]
    text = update.message.text.strip()
    flat_opts = [item for sublist in t["rel_opts"] for item in sublist]
    try:
        idx = flat_opts.index(text)
        eng_flat = [item for sublist in BOT_I18N["English"]["rel_opts"] for item in sublist]
        context.user_data["religion"] = eng_flat[idx]
    except ValueError:
        await update.message.reply_text(t["gender_err"])
        return RELIGION
    await update.message.reply_text(t["occ_q"], parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(t["occ_opts"], one_time_keyboard=True, resize_keyboard=True))
    return OCCUPATION

async def get_occupation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("language", "English")
    t = BOT_I18N[lang]
    text = update.message.text.strip()
    flat_opts = [item for sublist in t["occ_opts"] for item in sublist]
    try:
        idx = flat_opts.index(text)
        eng_flat = [item for sublist in BOT_I18N["English"]["occ_opts"] for item in sublist]
        context.user_data["occupation"] = eng_flat[idx].lower().replace(" ", "_")
    except ValueError:
        await update.message.reply_text(t["gender_err"])
        return OCCUPATION
    await update.message.reply_text(t["inc_q"], parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
    return INCOME

async def get_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("language", "English")
    t = BOT_I18N[lang]
    text = update.message.text.strip().replace(",", "")
    if not text.isdigit():
        await update.message.reply_text(t["inc_err"])
        return INCOME
    context.user_data["income"] = int(text)
    await update.message.reply_text(t["residence_q"], parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(t["residence_opts"], one_time_keyboard=True, resize_keyboard=True))
    return RESIDENCE

async def get_residence(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("language", "English")
    t = BOT_I18N[lang]
    text = update.message.text.strip()
    flat_opts = [item for sublist in t["residence_opts"] for item in sublist]
    try:
        idx = flat_opts.index(text)
        # English mapping: index 0 = Rural, index 1 = Urban
        context.user_data["residence_type"] = "rural" if idx == 0 else "urban"
    except ValueError:
        await update.message.reply_text(t["gender_err"])
        return RESIDENCE
    await update.message.reply_text(t["marital_q"], parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(t["marital_opts"], one_time_keyboard=True, resize_keyboard=True))
    return MARITAL

async def get_marital(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("language", "English")
    t = BOT_I18N[lang]
    text = update.message.text.strip()
    flat_opts = [item for sublist in t["marital_opts"] for item in sublist]
    try:
        idx = flat_opts.index(text)
        eng_flat = [item for sublist in BOT_I18N["English"]["marital_opts"] for item in sublist]
        context.user_data["marital_status"] = eng_flat[idx].lower()
    except ValueError:
        await update.message.reply_text(t["gender_err"])
        return MARITAL
    await update.message.reply_text(t["houseless_q"], parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(t["houseless_opts"], one_time_keyboard=True, resize_keyboard=True))
    return HOUSELESS

async def get_houseless(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("language", "English")
    t = BOT_I18N[lang]
    text = update.message.text.strip()
    flat_opts = [item for sublist in t["houseless_opts"] for item in sublist]
    try:
        idx = flat_opts.index(text)
        # index 0 = Yes houseless, index 1 = No
        context.user_data["houseless"] = (idx == 0)
    except ValueError:
        await update.message.reply_text(t["gender_err"])
        return HOUSELESS
    await update.message.reply_text(t["flags_q"], parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(t["flag_opts"], one_time_keyboard=True, resize_keyboard=True))
    return FLAGS

async def get_flags(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("language", "English")
    t = BOT_I18N[lang]
    text = update.message.text.strip()
    flat_opts = [item for sublist in t["flag_opts"] for item in sublist]
    try:
        idx = flat_opts.index(text)
        eng_flat = [item for sublist in BOT_I18N["English"]["flag_opts"] for item in sublist]
        eng_val = eng_flat[idx].lower().replace(" ", "_")
        flag_map = {
            "widow": "widow",
            "disabled": "disabled",
            "shg_member": "shg_member",
            "none_of_these": None
        }
        flag = flag_map.get(eng_val)
        context.user_data["flags"] = [flag] if flag else []
    except ValueError:
        await update.message.reply_text(t["gender_err"])
        return FLAGS

    profile = {
        "age":            context.user_data["age"],
        "gender":         context.user_data["gender"],
        "caste":          context.user_data["caste"],
        "religion":       context.user_data["religion"],
        "occupation":     context.user_data["occupation"],
        "income":         context.user_data["income"],
        "residence_type": context.user_data.get("residence_type", "rural"),
        "marital_status": context.user_data.get("marital_status", "married"),
        "houseless":      context.user_data.get("houseless", False),
        "flags":          context.user_data["flags"]
    }
    context.user_data["profile"] = profile

    await update.message.reply_text(t["search"], reply_markup=ReplyKeyboardRemove())
    matched, rejected = rule_filter(profile)

    if not matched:
        await update.message.reply_text(t["no_match"])
        return ConversationHandler.END

    if lang != "English" and len(matched) > 0:
        from groq import Groq
        try:
            client = Groq(api_key=os.environ["GROQ_API_KEY"])
            payload = [{"id": m["id"], "name": m["name"], "category": m["category"], "benefits": m["benefits"]} for m in matched]
            prompt = f"Translate the 'name', 'category', and 'benefits' values in this JSON strictly to {lang}. Keep 'id' exactly as is. Output format MUST be a valid JSON object with a single key 'translated' containing the array of translated objects.\n\nJSON: {json.dumps(payload)}"
            res = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "system", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            trans_items = json.loads(res.choices[0].message.content).get("translated", payload)
            trans_map = {t["id"]: t for t in trans_items if "id" in t}
            for m in matched:
                if m["id"] in trans_map:
                    m["name"]     = trans_map[m["id"]].get("name",     m["name"])
                    m["category"] = trans_map[m["id"]].get("category", m["category"])
                    m["benefits"] = trans_map[m["id"]].get("benefits", m["benefits"])
        except Exception as e:
            logging.error(f"Translation failed: {e}")

    keyboard = []
    if lang == "Telugu":
        summary = f"🎉 *శుభవార్త! మీరు {len(matched)} పథకాలకు అర్హులు.*\n\n"
    elif lang == "Hindi":
        summary = f"🎉 *बड़ी खुशखबरी! आप {len(matched)} योजना(ओं) के लिए पात्र हैं।*\n\n"
    else:
        summary = f"🎉 *Great news! You are eligible for {len(matched)} scheme(s).*\n\n"

    for s in matched:
        summary += f"📌 *{s['name']}*\n{s['benefits']}\n\n"
        keyboard.append([InlineKeyboardButton(s["name"], callback_data=s["id"])])

    context.user_data["matched_schemes"] = matched
    await update.message.reply_text(summary, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    if lang == "Telugu":
        await update.message.reply_text("💡 పూర్తి మార్గదర్శకం కోసం పైన ఉన్న ఏదైనా స్కీమ్ కార్డును నొక్కండి లేదా మీ స్వంత ప్రశ్నను టైప్ చేయండి!\n\n(ఎప్పుడైనా /start టైప్ చేసి మళ్లీ ప్రారంభించవచ్చు)", parse_mode="Markdown")
    elif lang == "Hindi":
        await update.message.reply_text("💡 पूरी गाइड के लिए ऊपर दिए गए किसी भी कार्ड पर टैप करें, या सीधे मुझसे कोई भी सवाल पूछें!\n\n(किसी भी समय /start टाइप करें)", parse_mode="Markdown")
    else:
        await update.message.reply_text("💡 *Tap any scheme button above* for a complete guide, or *type a custom question* directly in the chat below!\n\n(Type /start anytime to restart)", parse_mode="Markdown")

    return CHAT

async def handle_inline_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    scheme_id = query.data
    matched = context.user_data.get("matched_schemes", [])
    scheme_name = next((s["name"] for s in matched if s["id"] == scheme_id), scheme_id)
    lang = context.user_data.get("language", "English")
    if lang == "Telugu":
        msg_wait = f"⏳ *{scheme_name}* వివరాలను పొందుతోంది..."
    elif lang == "Hindi":
        msg_wait = f"⏳ *{scheme_name}* का विवरण प्राप्त किया जा रहा है..."
    else:
        msg_wait = f"⏳ Processing details for *{scheme_name}*..."
    await query.message.reply_text(msg_wait, parse_mode="Markdown")
    profile = context.user_data["profile"]
    try:
        result = run_rag(profile, user_query=f"Tell me everything about {scheme_name}", language=lang)
        await query.message.reply_text(result["answer"])
    except Exception as e:
        await query.message.reply_text(f"Error retrieving details: {str(e)}")
    return CHAT

async def handle_chat_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    profile = context.user_data.get("profile")
    lang = context.user_data.get("language", "English")
    if not profile:
        await update.message.reply_text("Please /start the conversation first.")
        return ConversationHandler.END
    if lang == "Telugu":   msg_wait = "⏳ ఆలోచిస్తోంది..."
    elif lang == "Hindi":  msg_wait = "⏳ सोच रहा हूँ..."
    else:                  msg_wait = "⏳ Thinking..."
    msg = await update.message.reply_text(msg_wait)
    try:
        result = run_rag(profile, user_query=user_text, language=lang)
        await msg.edit_text(result["answer"])
    except Exception as e:
        await msg.edit_text(f"Sorry, I could not process that request right now. Error: {str(e)}")
    return CHAT

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled. Type /start to begin again.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    app = Application.builder().token(TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE:   [MessageHandler(filters.TEXT & ~filters.COMMAND, get_language)],
            AGE:        [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            GENDER:     [MessageHandler(filters.TEXT & ~filters.COMMAND, get_gender)],
            CASTE:      [MessageHandler(filters.TEXT & ~filters.COMMAND, get_caste)],
            RELIGION:   [MessageHandler(filters.TEXT & ~filters.COMMAND, get_religion)],
            OCCUPATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_occupation)],
            INCOME:     [MessageHandler(filters.TEXT & ~filters.COMMAND, get_income)],
            RESIDENCE:  [MessageHandler(filters.TEXT & ~filters.COMMAND, get_residence)],
            MARITAL:    [MessageHandler(filters.TEXT & ~filters.COMMAND, get_marital)],
            HOUSELESS:  [MessageHandler(filters.TEXT & ~filters.COMMAND, get_houseless)],
            FLAGS:      [MessageHandler(filters.TEXT & ~filters.COMMAND, get_flags)],
            CHAT: [
                CallbackQueryHandler(handle_inline_button),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_chat_message)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
    )
    app.add_handler(conv_handler)
    print("YojanaIQ bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()