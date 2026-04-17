import React, { useState, useEffect, useRef } from 'react';

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const I18N = {
  English: {
    app_title: "YojanaIQ",
    app_subtitle: "Discover Andhra Pradesh Government Welfare Schemes Automatically",
    select_pref: "Select your preference",
    confirm_btn: "Confirm ▸",
    ask_placeholder: "Ask YojanaIQ anything...",
    reset: "🔄 Start Over",
    search_msg: "Analyse protocol initiated... Scanning logic matrices for AP government scheme matches...",
    no_match: "😔 No schemes instantly matched your profile.\n\nPlease visit your nearest Ward Secretariat or MeeSeva centre for custom guidance.",
    match_found: "Great news! You are eligible for {count} scheme(s).\n\nHere are the details:",
    tap_hint: "💡 Tap any scheme card above for a complete guide, or type a custom question in the chat box below to ask me directly.",
    err_server: "⚠️ System offline or unreachable. Please start the Python API server.",
    err_fetch: "Error fetching details.",
    go_to_portal: "Go to Portal ↗"
  },
  Telugu: {
    app_title: "యోజనాIQ (YojanaIQ)",
    app_subtitle: "ఆంధ్రప్రదేశ్ ప్రభుత్వ సంక్షేమ పథకాలను ఆటోమేటిక్‌గా తెలుసుకోండి",
    select_pref: "మీ ఎంపికను ఎంచుకోండి",
    confirm_btn: "నిర్ధారించండి ▸",
    ask_placeholder: "యోజనాIQ ను ఏదైనా అడగండి...",
    reset: "🔄 మళ్ళీ మొదలుపెట్టండి",
    search_msg: "విశ్లేషణ ప్రారంభించబడింది... మీ ప్రొఫైల్‌కు సరిపోయే AP ప్రభుత్వ పథకాల కోసం వెతుకుతోంది...",
    no_match: "😔 ప్రస్తుతం మీ ప్రొఫైల్‌కు సరిపోయే పథకాలు ఏమీ దొరకలేదు.\n\nదయచేసి మీ సమీపంలోని గ్రామ/వార్డు సచివాలయాన్ని సందర్శించండి.",
    match_found: "శుభవార్త! మీరు {count} పథకాలకు అర్హులు.\n\nవివరాలు ఇక్కడ ఉన్నాయి:",
    tap_hint: "💡 పూర్తి మార్గదర్శకం కోసం పైన ఉన్న ఏదైనా స్కీమ్ కార్డును నొక్కండి లేదా మీ స్వంత ప్రశ్నను చాట్ బాక్స్‌లో టైప్ చేయండి.",
    err_server: "⚠️ సర్వర్ ఆఫ్‌లైన్‌లో ఉంది. దయచేసి పైథాన్ API ని ప్రారంభించండి.",
    err_fetch: "వివరాలను పొందడంలో లోపం.",
    go_to_portal: "పోర్టల్‌కి వెళ్లండి ↗"
  },
  Hindi: {
    app_title: "योजनाIQ",
    app_subtitle: "आंध्र प्रदेश सरकार की कल्याणकारी योजनाओं को स्वचालित रूप से खोजें",
    select_pref: "अपनी पसंद चुनें",
    confirm_btn: "पुष्टि करें ▸",
    ask_placeholder: "योजनाIQ से कुछ भी पूछें...",
    reset: "🔄 पुनः आरंभ करें",
    search_msg: "विश्लेषण प्रारंभ... आपकी प्रोफाइल के लिए एपी सरकारी योजनाओं को खोजा जा रहा है...",
    no_match: "😔 आपके प्रोफाइल से मेल खाने वाली कोई योजना नहीं मिली।\n\nकृपया अपने नजदीकी वार्ड सचिवालय से संपर्क करें।",
    match_found: "बड़ी खुशखबरी! आप {count} योजना(ओं) के लिए पात्र हैं।\n\nयहाँ विवरण हैं:",
    tap_hint: "💡 पूरी गाइड के लिए ऊपर दिए गए किसी भी कार्ड पर टैप करें, या सीधे मुझसे कोई भी सवाल पूछें।",
    err_server: "⚠️ सर्वर ऑफ़लाइन है। कृपया पायथन एपीआई शुरू करें।",
    err_fetch: "विवरण प्राप्त करने में त्रुटि।",
    go_to_portal: "पोर्टल पर जाएं ↗"
  }
};

const getFlow = (lang) => {
  const isTe = lang === "Telugu";
  const isHi = lang === "Hindi";

  return [
    {
      key: "gender",
      question: isTe ? "నమస్కారం! నేను యోజనాIQ ని.\n\nAI సహాయంతో మీకు సరిపోయే ఆంధ్రప్రదేశ్ ప్రభుత్వ పథకాలను నేను చూపిస్తాను.\n\nముందుగా, మీ లింగం ఏమిటి?" 
              : isHi ? "नमस्कार! मैं योजनाIQ हूँ।\n\nमैं एआई का उपयोग करके आपको एपी सरकार की कल्याणकारी योजनाओं से मिलाऊंगा।\n\nसबसे पहले, आपका लिंग क्या है?"
              : "Namaskaram! I'm YojanaIQ.\n\nI will intuitively match you with AP government welfare programs using AI.\n\nFirst, what is your gender?",
      options: isTe ? ["👩 స్త్రీ", "👨 పురుషుడు", "🧑 ఇతరులు"] : isHi ? ["👩 महिला", "👨 पुरुष", "🧑 अन्य"] : ["👩 Female", "👨 Male", "🧑 Other"],
      map: {
        "👩 Female": "female", "👨 Male": "male", "🧑 Other": "other",
        "👩 స్త్రీ": "female", "👨 పురుషుడు": "male", "🧑 ఇతరులు": "other",
        "👩 महिला": "female", "👨 पुरुष": "male", "🧑 अन्य": "other"
      },
    },
    {
      key: "age",
      question: isTe ? "అర్థమైంది! మీ వయస్సు ఎంత?" : isHi ? "समझ गया! आपकी आयु सीमा क्या है?" : "Got it! What is your age group?",
      options: isTe ? ["18 లోపు", "18–25", "26–40", "41–60", "60+"] : isHi ? ["18 से कम", "18–25", "26–40", "41–60", "60+"] : ["Under 18", "18–25", "26–40", "41–60", "60+"],
      map: {
        "Under 18": 15, "18–25": 22, "26–40": 33, "41–60": 50, "60+": 65,
        "18 లోపు": 15, "18 से कम": 15
      },
      // simple mapper function for generic numbers
      mapFunc: (o) => (o.includes("18") && o.includes("Under")) || o.includes("లోపు") || o.includes("से कम") ? 15 : o.includes("25") ? 22 : o.includes("40") ? 33 : o.includes("60") && !o.includes("+") ? 50 : 65
    },
    {
      key: "caste",
      question: isTe ? "మీ కులం వర్గం ఏమిటి?" : isHi ? "आपकी जाति श्रेणी क्या है?" : "What is your caste category?",
      options: isTe ? ["🟦 SC", "🟩 ST", "🟨 BC", "⬜ OC", "🕌 మైనారిటీ"] : isHi ? ["🟦 SC", "🟩 ST", "🟨 BC", "⬜ OC", "🕌 अल्पसंख्यक"] : ["🟦 SC", "🟩 ST", "🟨 BC", "⬜ OC", "🕌 Minority"],
      mapFunc: (o) => o.includes("SC") ? "SC" : o.includes("ST") ? "ST" : o.includes("BC") ? "BC" : o.includes("OC") ? "OC" : "Minority"
    },
    {
      key: "religion",
      question: isTe ? "మీ మతం ఏమిటి?" : isHi ? "आपका धर्म क्या है?" : "What is your religion?",
      options: isTe ? ["🕉️ హిందూ", "☪️ ముస్లిం", "✝️ క్రిస్టియన్", "ఇతర"] : isHi ? ["🕉️ हिंदू", "☪️ मुस्लिम", "✝️ ईसाई", "अन्य"] : ["🕉️ Hindu", "☪️ Muslim", "✝️ Christian", "Other"],
      mapFunc: (o) => o.includes("Hindu") || o.includes("హిందూ") || o.includes("हिंदू") ? "hindu" : o.includes("Muslim") || o.includes("ముస్లిం") || o.includes("मुस्लिम") ? "muslim" : o.includes("Christian") || o.includes("క్రిస్టియన్") || o.includes("ईसाई") ? "christian" : "other"
    },
    {
      key: "occupation",
      question: isTe ? "మీ వృత్తి ఏమిటి?" : isHi ? "आपका पेशा क्या है?" : "What is your occupation?",
      options: isTe ? ["🎓 విద్యార్థి", "🌾 రైతు", "🧵 నేత కార్మికుడు", "🐟 మత్స్యకారుడు", "🚗 ఆటో డ్రైవర్", "👷 దినసరి కూలీ", "🏪 స్వయం ఉపాధి", "🔍 నిరుద్యోగి"]
               : isHi ? ["🎓 छात्र", "🌾 किसान", "🧵 बुनकर", "🐟 मछुआरा", "🚗 ऑटो ड्राइवर", "👷 दैनिक मजदूर", "🏪 स्व-नियोजित", "🔍 बेरोजगार"]
               : ["🎓 Student", "🌾 Farmer", "🧵 Weaver", "🐟 Fisher", "🚗 Auto Driver", "👷 Daily Wage Worker", "🏪 Self Employed", "🔍 Unemployed"],
      mapFunc: (o) => o.includes("Student") || o.includes("విద్యార్థి") || o.includes("छात्र") ? "student" :
                       o.includes("Farmer") || o.includes("రైతు") || o.includes("किसान") ? "farmer" :
                       o.includes("Weaver") || o.includes("నేత") || o.includes("बुनकर") ? "weaver" :
                       o.includes("Fisher") || o.includes("మత్స్యకారుడు") || o.includes("मछुआरा") ? "fisher" :
                       o.includes("Auto") || o.includes("ఆటో") || o.includes("ऑटो") ? "auto driver" :
                       o.includes("Daily") || o.includes("కూలీ") || o.includes("मजदूर") ? "daily wage worker" :
                       o.includes("Self") || o.includes("స్వయం") || o.includes("स्व-नियोजित") ? "self employed" : "unemployed"
    },
    {
      key: "income",
      question: isTe ? "మీ కుటుంబ సుమారు వార్షిక ఆదాయం ఎంత?" : isHi ? "आपकी अनुमानित वार्षिक पारिवारिक आय क्या है?" : "What is your approximate annual family income?",
      options: isTe ? ["₹1L లోపు", "₹1L – ₹2L", "₹2L – ₹5L", "₹5L – ₹10L", "₹10L పైన"]
               : isHi ? ["₹1L से कम", "₹1L – ₹2L", "₹2L – ₹5L", "₹5L – ₹10L", "₹10L से ऊपर"]
               : ["Below ₹1L", "₹1L – ₹2L", "₹2L – ₹5L", "₹5L – ₹10L", "Above ₹10L"],
      mapFunc: (o) => o.includes("Below") || o.includes("లోపు") || o.includes("से कम") ? 80000 : o.includes("1L –") ? 150000 : o.includes("2L") ? 350000 : o.includes("5L") ? 750000 : 1200000
    },
    {
      key: "residence_type",
      question: isTe ? "మీ నివాస ప్రాంతం ఏమిటి?" : isHi ? "आपका निवास क्षेत्र कौन सा है?" : "What is your residence area?",
      options: isTe ? ["గ్రామీణ (పల్లె)", "పట్టణ (నగరం)"] : isHi ? ["ग्रामीण (गाँव)", "शहरी (शहर)"] : ["Rural (Village)", "Urban (Town/City)"],
      mapFunc: (o) => o.includes("Rural") || o.includes("గ్రామీణ") || o.includes("ग्रामीण") ? "rural" : "urban"
    },
    {
      key: "marital_status",
      question: isTe ? "మీ వైవాహిక స్థితి ఏమిటి?" : isHi ? "आपकी वैवाहिक स्थिति क्या है?" : "What is your marital status?",
      options: isTe ? ["వివాహిత (Married)", "అవివాహిత (Single)", "వితంతువు (Widowed)", "విడాకులు (Separated)"] : isHi ? ["विवाहित (Married)", "अविवाहित (Single)", "विधवा (Widowed)", "तलाकशुदा (Separated)"] : ["Married", "Single", "Widowed", "Separated"],
      mapFunc: (o) => o.includes("Married") || o.includes("వివాహిత") || o.includes("विवाहित") ? "married"
                      : o.includes("Single") || o.includes("అవివాహిత") || o.includes("अविवाहित") ? "single"
                      : o.includes("Widow") || o.includes("వితంతువు") || o.includes("विधवा") ? "widowed" : "separated"
    },
    {
      key: "houseless",
      question: isTe ? "మీకు ప్రస్తుతం సొంత ఇల్లు లేదా? (నిరాశ్రయులు)" : isHi ? "क्या आपके पास अभी अपना घर नहीं है (बेघर)?" : "Do you currently not own a house (houseless)?",
      options: isTe ? ["అవును, ఇల్లు లేదు", "కాదు, ఇల్లు ఉంది"] : isHi ? ["हाँ, घर नहीं है", "नहीं, घर है"] : ["Yes, I am houseless", "No, I have a house"],
      mapFunc: (o) => Boolean(o.includes("Yes") || o.includes("అవును") || o.includes("हाँ"))
    },
    {
      key: "flags",
      question: isTe ? "చివరి ప్రశ్న! వీటిలో ఏదైనా మీకు వర్తిస్తుందా?\n(వర్తించే వాటన్నింటికీ టిక్ చేసి, 'నిర్ధారించండి' నొక్కండి)" 
               : isHi ? "आखिरी सवाल! क्या इनमें से कोई आप पर लागू होता है?\n(सभी लागू विकल्पों को चुनें, फिर 'पुष्टि करें' दबाएं)" 
               : "Last question! Do any of these apply to you?\n(Select all that apply, then tap Confirm)",
      options: isTe ? ["వితంతువు", "దివ్యాంగులు", "డ్వాక్రా (SHG) మహిళ", "BPL రేషన్ కార్డు", "గర్భిణీ / బాలింత", "Senior Citizen (60+)"]
               : isHi ? ["विधवा", "विकलांग", "SHG सदस्य", "BPL कार्ड धारक", "गर्भवती / नई माँ", "वरिष्ठ नागरिक (60+)"]
               : ["Widow", "Disabled / Differently Abled", "SHG Member", "BPL Card Holder", "Pregnant / New Mother", "Senior Citizen (60+)"],
      multi: true,
      mapFunc: (o) => o.includes("Widow") || o.includes("వితంతువు") || o.includes("विधवा") ? "widow" :
                       o.includes("Disabled") || o.includes("దివ్యాంగులు") || o.includes("विकलांग") ? "disabled" :
                       o.includes("SHG") || o.includes("డ్వాక్రా") ? "shg_member" :
                       o.includes("BPL") ? "bpl" :
                       o.includes("Pregnant") || o.includes("గర్భిణీ") || o.includes("गर्भवती") ? "pregnant" : "senior_citizen"
    },
  ];
};

const SCHEME_URLS = {
  amma_vodi: "https://ammavodi.ap.gov.in",
  vidya_deevena: "https://apsche.ap.gov.in",
  vasathi_deevena: "https://apsche.ap.gov.in",
  rythu_bharosa: "https://apagrisnet.gov.in",
  pm_kisan: "https://pmkisan.gov.in",
  ysr_cheyutha: "https://ysrcheyutha.ap.gov.in",
  aarogyasri: "https://aarogyasri.ap.gov.in",
  jagananna_suraksha: "https://jaganannasuraksha.ap.gov.in",
  ysr_housing: "https://navaratnalu.ap.gov.in",
  ysr_pension: "https://ysrpensionkanuka.ap.gov.in",
  jagananna_thodu: "https://jaganannatodustores.ap.gov.in",
  kalyanamasthu: "https://ysrkalyanamasthu.ap.gov.in",
  aadabidda_nidhi: "https://navaratnalu.ap.gov.in",
  talliki_vandanam: "https://tallikikivandanam.ap.gov.in",
  deepam_2_0_free_gas: "https://navaratnalu.ap.gov.in",
  annadatha_sukhibhava_2024: "https://apagrisnet.gov.in",
  nirudyoga_bruthi_2024: "https://navaratnalu.ap.gov.in",
  apsrtc_free_bus_women: "https://apsrtc.ap.gov.in",
};

const TypewriterText = ({ text = "", skip, speed = 15 }) => {
  const [displayed, setDisplayed] = useState(skip ? text : "");

  useEffect(() => {
    if (skip || !text) return;
    let i = 0;
    const timer = setInterval(() => {
      setDisplayed(text.slice(0, i + 1));
      i++;
      if (i >= text.length) clearInterval(timer);
    }, speed);
    return () => clearInterval(timer);
  }, [text, skip, speed]);

  return <>{displayed}</>;
};

const ElegantBotIcon = () => (
  <svg className="w-4 h-4 text-elegant-gold" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 2l1.6 6.4L20 10l-6.4 1.6L12 18l-1.6-6.4L4 10l6.4-1.6z"/>
  </svg>
);

export default function App() {
  const [messages, setMessages] = useState([]);
  const [step, setStep] = useState(0);
  const [profile, setProfile] = useState({});
  const [multiSel, setMultiSel] = useState(new Set());
  const [done, setDone] = useState(false);
  const [chatInput, setChatInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [language, setLanguage] = useState("English");
  
  const scrollRef = useRef(null);
  const internalMessagesRef = useRef([]);
  const initialized = useRef(false);

  // Dynamic flow based on language
  const currentFlow = getFlow(language);
  const t = I18N[language];

  useEffect(() => {
    if (!initialized.current) {
      initialized.current = true;
      const initialQuestion = getFlow("English")[0].question;
      internalMessagesRef.current = [{ id: 1, role: "bot", content: initialQuestion, schemes: [], isNew: true }];
      setMessages([...internalMessagesRef.current]);
    }
  }, []);

  // When language changes and user is at step 0 with no history beyond the first message, translate seamlessly
  useEffect(() => {
    if (step === 0 && internalMessagesRef.current.length === 1) {
      internalMessagesRef.current[0].content = currentFlow[0].question;
      setMessages([...internalMessagesRef.current]);
    }
  }, [language, currentFlow, step]);

  const scrollToBottom = () => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const markAllOld = () => {
    internalMessagesRef.current.forEach(m => m.isNew = false);
  };

  const appendBotMessage = (text, schemes = []) => {
    markAllOld();
    internalMessagesRef.current.push({ id: Date.now(), role: "bot", content: text, schemes, isNew: true });
    setMessages([...internalMessagesRef.current]);
  };

  const appendUserMessage = (text) => {
    markAllOld();
    internalMessagesRef.current.push({ id: Date.now(), role: "user", content: text, isNew: false });
    setMessages([...internalMessagesRef.current]);
  };

  const handleReset = () => {
    markAllOld();
    const newSessionMsg = { id: Date.now(), role: "bot", content: currentFlow[0].question, schemes: [], isNew: true };
    internalMessagesRef.current = [newSessionMsg];
    setMessages([newSessionMsg]);
    setStep(0);
    setProfile({});
    setMultiSel(new Set());
    setDone(false);
    setChatInput("");
  };

  const handleOptionSelect = (opt) => {
    const currentStepConfig = currentFlow[step];
    
    if (currentStepConfig.multi) {
      const newSel = new Set(multiSel);
      if (newSel.has(opt)) newSel.delete(opt);
      else newSel.add(opt);
      setMultiSel(newSel);
    } else {
      appendUserMessage(opt);
      // use mapFunc or map for value retrieval
      const val = currentStepConfig.mapFunc ? currentStepConfig.mapFunc(opt) : currentStepConfig.map[opt];
      const newProfile = { ...profile, [currentStepConfig.key]: val };
      setProfile(newProfile);
      
      const nextStep = step + 1;
      setStep(nextStep);
      
      if (nextStep < currentFlow.length) {
        setTimeout(() => appendBotMessage(currentFlow[nextStep].question), 300);
      } else {
        finishFlow(newProfile);
      }
    }
  };

  const finishFlow = async (finalProfile) => {
    setDone(true);
    appendBotMessage(t.search_msg);
    setLoading(true);

    try {
      const opts = Array.from(multiSel);
      const confFlags = currentFlow[6];
      const flagVals = opts.map(o => confFlags.mapFunc(o)).filter(Boolean);
      
      const p = { ...finalProfile, flags: flagVals, religion: finalProfile.religion || "hindu", language };
      
      const matchResponse = await fetch(`${API_URL}/api/match`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(p)
      });
      const matchData = await matchResponse.json();
      const matched = matchData.matched;

      if (matched.length === 0) {
        appendBotMessage(t.no_match);
        setLoading(false);
        return;
      }

      appendBotMessage(t.match_found.replace("{count}", matched.length), matched);
      appendBotMessage(t.tap_hint);
      setProfile(p);
    } catch (err) {
      appendBotMessage(t.err_server);
    }
    setLoading(false);
  };

  const handleMultiDone = () => {
    const opts = Array.from(multiSel);
    appendUserMessage(opts.length > 0 ? opts.join(", ") : "None");
    const confFlags = currentFlow[step];
    const flagVals = opts.map(o => confFlags.mapFunc ? confFlags.mapFunc(o) : confFlags.map[o]).filter(Boolean);
    const p = { ...profile, flags: flagVals };
    setProfile(p);
    setStep(step + 1);
    finishFlow(p);
  };

  const handleSchemeDetail = async (s) => {
    appendUserMessage(`Tell me about ${s.name}`);
    setLoading(true);
    try {
      const query = `Explain ${s.name} in detail. Why is this person eligible? What exact benefit amount? Step-by-step application and documents?`;
      const res = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ profile, query, language })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Server error");
      if (!data.answer) throw new Error("Empty response generated");
      appendBotMessage(data.answer);
    } catch (e) {
      appendBotMessage(t.err_fetch + " " + e.message);
    }
    setLoading(false);
  };

  const handleChatParams = async (e) => {
    e.preventDefault();
    if (!chatInput.trim()) return;
    
    appendUserMessage(chatInput);
    const query = chatInput;
    setChatInput("");
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ profile, query, language })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Server error");
      if (!data.answer) throw new Error("Empty response generated");
      appendBotMessage(data.answer);
    } catch (err) {
      appendBotMessage(t.err_fetch + " " + err.message);
    }
    setLoading(false);
  };

  return (
    <div className="fixed inset-0 w-full h-full flex flex-col md:flex-row font-sans bg-black text-white overflow-hidden">
      
      {/* Left Banner */}
      <div className="hidden md:flex md:w-[40%] h-full relative items-center justify-center border-r-[4px] border-elegant-gold shadow-2xl z-20 bg-elegant-maroon overflow-hidden">
         <div className="absolute inset-0 bg-[url('/ap_map_v2.png')] bg-cover bg-center mix-blend-overlay opacity-60"></div>
         <div className="absolute inset-0 bg-gradient-to-t from-elegant-maroon via-transparent to-elegant-maroon/80"></div>
         <div className="absolute top-0 right-0 w-full h-full bg-gradient-to-l from-black/80 to-transparent"></div>
         
         <div className="relative z-10 p-10 text-center text-white flex flex-col items-center">
            <h1 className="font-heading text-5xl xl:text-6xl font-bold tracking-wide drop-shadow-2xl text-elegant-gold mb-5">
               {t.app_title}
            </h1>
            <p className="font-sans text-sm xl:text-base font-medium tracking-wider drop-shadow-md text-white/90 leading-relaxed max-w-sm border-t border-elegant-gold/40 pt-5">
               {t.app_subtitle}
            </p>
         </div>
      </div>

      {/* Right Chatbot */}
      <div className="w-full md:w-[60%] flex flex-col h-full py-4 px-4 md:px-8 bg-black">
        
        {/* Mobile Header */}
        <div className="md:hidden text-center mb-6 py-6 px-4 rounded-2xl z-10 w-full border-b border-neutral-800 bg-black/60 backdrop-blur-md">
          <h1 className="font-heading text-3xl font-bold text-elegant-gold tracking-wide">
            {t.app_title}
          </h1>
          <p className="text-white/80 font-semibold tracking-widest uppercase text-xs mt-3">
            AP Welfare Intelligence
          </p>
        </div>

        <div className="max-w-4xl mx-auto w-full flex flex-col h-full mt-2 md:mt-6">
          {/* Header Controls (Language / Reset) */}
          <div className="flex justify-between items-center mb-4 px-2 z-20 shrink-0">
            <button onClick={handleReset} className="text-[0.65rem] text-neutral-400 hover:text-elegant-gold uppercase tracking-widest font-bold transition-colors outline-none">
              {t.reset}
            </button>
            <select 
              value={language} 
              onChange={e => {
                setLanguage(e.target.value);
                appendBotMessage(`Language changed to **${e.target.value}**!`);
              }}
              className="bg-neutral-900 border border-neutral-700 text-neutral-300 text-xs px-3 py-1.5 rounded-full cursor-pointer hover:border-elegant-gold transition-colors focus:outline-none focus:ring-1 focus:ring-elegant-gold"
            >
              <option value="English">🇬🇧 English</option>
              <option value="Telugu">తెలుగు (Telugu)</option>
              <option value="Hindi">हिंदी (Hindi)</option>
            </select>
          </div>

          {/* Chat Window */}
          <div className="flex-1 overflow-y-auto mb-4 pr-3 custom-scrollbar z-10 scroll-smooth">
            {messages.map((msg, i) => (
              <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start items-end'} mb-6`}>
                
                {msg.role === 'bot' && (
                  <div className="flex-shrink-0 mr-3 mb-1 h-8 w-8 flex items-center justify-center bg-neutral-900 border border-elegant-gold/40 rounded-full shadow-lg z-20">
                    <ElegantBotIcon />
                  </div>
                )}

                <div className={`
                  ${msg.role === 'user' 
                    ? 'bg-gradient-to-br from-elegant-maroon to-red-900 text-white shadow-lg rounded-bl-2xl rounded-tr-2xl rounded-tl-2xl' 
                    : 'bg-neutral-900/90 backdrop-blur-sm border border-elegant-gold/30 text-white shadow-lg rounded-br-2xl rounded-tl-2xl rounded-tr-2xl'}
                  px-5 py-3.5 max-w-[80%] relative
                `}>
                  <div className="whitespace-pre-wrap leading-relaxed text-sm font-medium tracking-wide">
                    {msg.role === 'bot' 
                      ? <TypewriterText text={msg.content} skip={!msg.isNew} speed={10} /> 
                      : msg.content
                    }
                  </div>
                  
                  {msg.schemes && msg.schemes.length > 0 && (
                    <div className="mt-4 grid gap-4 grid-cols-1 md:grid-cols-2">
                      {msg.schemes.map(s => (
                        <div key={s.id} 
                             onClick={() => handleSchemeDetail(s)}
                             className="bg-neutral-950 hover:bg-neutral-900 border-y border-r border-y-transparent border-r-transparent hover:border-elegant-gold border-l-4 border-l-elegant-maroon transition-all cursor-pointer rounded-xl p-4 shadow-xl">
                          <span className="text-[0.6rem] uppercase tracking-widest text-elegant-gold font-bold bg-elegant-maroon/60 px-2 py-1 rounded">
                            {s.category}
                          </span>
                          <h4 className="font-heading font-bold text-white text-base mt-2 leading-tight">{s.name}</h4>
                          <p className="text-xs text-elegant-gold mt-2 font-semibold bg-elegant-gold/10 p-2 rounded-r border-l-[3px] border-elegant-gold">
                            {s.benefits}
                          </p>
                          <a href={SCHEME_URLS[s.id] || "https://ap.gov.in"} target="_blank" rel="noreferrer" 
                             onClick={(e) => e.stopPropagation()}
                             className="text-[0.65rem] text-red-400 hover:text-red-300 mt-3 inline-block font-bold tracking-widest uppercase">
                            {t.go_to_portal}
                          </a>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start items-end mb-6">
                <div className="flex-shrink-0 mr-3 mb-1 h-8 w-8 flex items-center justify-center bg-neutral-900 border border-elegant-gold/40 rounded-full shadow-lg z-20">
                  <ElegantBotIcon />
                </div>
                <div className="bg-neutral-900 border border-elegant-gold/30 rounded-br-2xl rounded-tl-2xl rounded-tr-2xl px-4 py-3 w-20 flex justify-between shadow-lg">
                   <span className="w-2 h-2 rounded-full bg-elegant-gold opacity-80 animate-bounce"></span>
                   <span className="w-2 h-2 rounded-full bg-elegant-gold opacity-80 animate-bounce delay-75"></span>
                   <span className="w-2 h-2 rounded-full bg-elegant-gold opacity-80 animate-bounce delay-150"></span>
                </div>
              </div>
            )}
            <div ref={scrollRef}></div>
          </div>

          {/* Input Area */}
          <div className="mt-auto bg-neutral-900/60 backdrop-blur-xl border border-neutral-800 p-4 rounded-[1.5rem] z-10 relative overflow-hidden shrink-0 shadow-2xl mb-4">
            
            {!done && step < currentFlow.length && (
              <div>
                <p className="text-[0.65rem] text-neutral-400 uppercase tracking-widest font-bold mb-4 text-center">
                  {t.select_pref}
                </p>
                <div className="flex flex-wrap justify-center gap-2.5">
                  {currentFlow[step].options.map((opt) => {
                    const isSel = multiSel.has(opt);
                    return (
                      <button key={opt}
                        onClick={() => handleOptionSelect(opt)}
                        className={`
                          glow-btn font-semibold text-xs px-4 py-2 rounded-full border transition-all
                          ${isSel 
                            ? 'bg-elegant-maroon border-elegant-maroon text-white shadow-xl shadow-elegant-maroon/30 scale-105' 
                            : 'bg-neutral-950/80 backdrop-blur-sm border-neutral-800 text-neutral-300 hover:border-elegant-gold hover:text-elegant-gold'}
                        `}
                      >
                        {opt}
                      </button>
                    );
                  })}
                </div>
                {currentFlow[step].multi && (
                  <div className="mt-5 flex justify-center gap-4">
                    <button onClick={handleMultiDone} className="glow-btn bg-elegant-gold hover:bg-yellow-500 text-black px-6 py-2.5 rounded-full font-bold shadow-xl shadow-elegant-gold/20 text-[0.7rem] tracking-widest uppercase transition-all">
                      {t.confirm_btn}
                    </button>
                  </div>
                )}
              </div>
            )}

            {done && (
              <form onSubmit={handleChatParams} className="relative flex items-center">
                <input 
                  type="text" 
                  value={chatInput}
                  onChange={e => setChatInput(e.target.value)}
                  placeholder={t.ask_placeholder}
                  className="w-full bg-neutral-950/80 backdrop-blur-md border border-neutral-800 rounded-full py-3.5 pl-5 pr-12 text-white placeholder-neutral-500 focus:outline-none focus:border-elegant-gold focus:ring-1 focus:ring-elegant-gold shadow-inner font-medium text-sm text-left"
                />
                <button disabled={loading || !chatInput} type="submit" 
                  className="absolute right-2 top-1/2 -translate-y-1/2 bg-elegant-gold hover:bg-yellow-400 text-black disabled:opacity-50 p-2.5 rounded-full font-bold transition-all shadow-md hover:shadow-xl hover:-translate-y-0.5">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.707l-3-3a1 1 0 00-1.414 0l-3 3a1 1 0 001.414 1.414L9 9.414V13a1 1 0 102 0V9.414l1.293 1.293a1 1 0 001.414-1.414z" clipRule="evenodd" />
                  </svg>
                </button>
              </form>
            )}

          </div>
        </div>
      </div>
    </div>
  );
}
