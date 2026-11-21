/**
 * CivicResolve Multilingual i18n Dictionary.
 * Covers English, தமிழ் (Tamil), and हिन्दी (Hindi).
 */

export const translations = {
  en: {
    app_title: "CivicResolve",
    tagline: "AI-Powered Municipal Grievance Management",
    nav_report: "Report Issue",
    nav_track: "Track Issue",
    nav_dashboard: "Public Dashboard",
    nav_admin: "Officer Portal",
    skip_link: "Skip to main content",
    demo_banner_title: "Demo Mode Active:",
    demo_banner_text: "Running on in-memory storage. Data may reset on cold starts. AI fallback mode enabled if API key is not configured.",
    demo_admin_hint: "Demo Admin Password:",
    btn_high_contrast: "High Contrast",
    btn_font_size: "A+",
    
    // Report Flow
    report_heading: "Report a Civic Grievance",
    report_sub: "Submit municipal issues with instant AI triage, automated priority scoring, and department routing.",
    sample_title: "Try a Sample Report:",
    sample_pothole: "Pothole near School",
    sample_garbage: "Overflowing Garbage",
    sample_wire: "Exposed Live Wire",
    sample_water: "Water Pipe Burst",
    sample_light: "Broken Streetlights",
    lbl_title: "Issue Title (Optional - AI will generate if blank)",
    lbl_desc: "Description (Required - any language)",
    lbl_desc_placeholder: "Describe the civic issue in detail. You can use English, Tamil, Hindi, or any language...",
    lbl_category: "Category (Optional)",
    lbl_category_ai: "Let AI decide category",
    lbl_location: "Location / Landmark",
    lbl_location_placeholder: "e.g. DB Road, opposite Govt Girls High School",
    btn_get_location: "Use My GPS Location",
    lbl_photo: "Attach Photo (Optional, auto-resized <= 300KB)",
    lbl_name: "Your Name (Optional - no phone/email stored)",
    btn_submit_report: "Submit Civic Report",
    btn_improving: "AI Analyzing Description...",
    btn_improve_desc: "AI Assist & Suggestions",
    assist_title_prefix: "Suggested Title:",
    assist_questions_prefix: "Clarifying Questions to Improve Triage:",
    
    // Confirmation
    confirm_title: "Grievance Lodged Successfully!",
    confirm_ticket: "Ticket ID:",
    confirm_category: "Detected Category:",
    confirm_priority: "Priority Assessment:",
    confirm_dept: "Assigned Department:",
    confirm_sla: "Resolution SLA:",
    confirm_why_priority: "Why this priority score?",
    confirm_duplicates_notice: "Possible Duplicate Reports Nearby:",
    btn_track_this: "Track This Issue",
    btn_report_another: "Report Another Issue",
    
    // Tracking
    track_heading: "Track Grievance Status",
    track_sub: "Enter your Ticket ID to see real-time investigation progress, SLA status, and field officer notes.",
    track_input_label: "Enter Ticket ID (e.g. CR-2026-00001):",
    btn_track: "Lookup Ticket",
    timeline_title: "Resolution Timeline",
    
    // Dashboard
    dash_heading: "Public Transparency & Grievance Dashboard",
    dash_sub: "Real-time municipal grievance resolution performance, category breakdown, and locality map.",
    stat_total: "Total Grievances",
    stat_open: "Open / In Progress",
    stat_resolved: "Resolved",
    stat_avg_sla: "Avg Resolution Time",
    stat_rate: "Resolution Rate",
    filter_status: "Filter Status:",
    filter_category: "Filter Category:",
    filter_priority: "Filter Priority:",
    filter_search: "Search issues...",
    chart_category_title: "Grievances by Category",
    chart_trend_title: "14-Day Grievance Trend",
    chart_map_title: "Locality Incident Scatter Map",
    
    // Admin
    admin_heading: "Municipal Officer Portal",
    admin_login_title: "Officer Authentication",
    admin_login_sub: "Enter municipal admin credentials to access the operational dispatch console.",
    admin_pwd_label: "Administrator Password:",
    btn_login: "Login to Dispatch Console",
    btn_logout: "Logout",
    admin_analytics_title: "Operational Analytics & Workload",
    admin_issues_title: "Incoming & Active Civic Grievances",
    admin_overdue_title: "SLA Breached / Overdue Tickets",
    btn_generate_summary: "Generate AI Operational Summary",
    col_ticket: "Ticket ID",
    col_title: "Issue Title",
    col_category: "Category",
    col_priority: "Priority",
    col_dept: "Department",
    col_status: "Status",
    col_age: "Age / SLA",
    col_actions: "Action",
    btn_manage: "Manage",
  },
  ta: {
    app_title: "சிவிக்ரிசால்வ்",
    tagline: "செயற்கை நுண்ணறிவு அடிப்படையிலான பொதுமக்கள் குறைதீர்ப்பு தளம்",
    nav_report: "புகார் செய்க",
    nav_track: "கண்காணிக்க",
    nav_dashboard: "பொது தகவல் பலகை",
    nav_admin: "அதிகாரிகள் தளம்",
    skip_link: "முக்கிய பகுதிக்கு செல்லவும்",
    demo_banner_title: "டெமோ முறை:",
    demo_banner_text: "நினைவக சேமிப்பகத்தில் இயங்குகிறது. தரவு மீட்டமைக்கப்படலாம்.",
    demo_admin_hint: "டெமோ கடவுச்சொல்:",
    btn_high_contrast: "உயர் மாறுபாடு",
    btn_font_size: "A+",
    
    report_heading: "பொதுமக்கள் குறையை பதிவு செய்க",
    report_sub: "சாலை, குப்பை, தெருவிளக்கு, நீர் கசிவு போன்ற பிரச்சினைகளை உடனடியாக பதிவு செய்யுங்கள்.",
    sample_title: "மாதிரி புகாரை முயற்சிக்கவும்:",
    sample_pothole: "பள்ளி அருகே குழி",
    sample_garbage: "குப்பை தொட்டி நிரம்பியது",
    sample_wire: "மின்கம்பி தொங்குகிறது",
    sample_water: "குடிநீர் குழாய் உடைப்பு",
    sample_light: "தெருவிளக்கு எரியவில்லை",
    lbl_title: "புகார் தலைப்பு (விரும்பினால்)",
    lbl_desc: "விளக்கம் (கட்டாயம் - எந்த மொழியிலும்)",
    lbl_desc_placeholder: "பிரச்சினையை விரிவாக விளக்குங்கள் (தமிழ், ஆங்கிலம், இந்தி)...",
    lbl_category: "வகை (விரும்பினால்)",
    lbl_category_ai: "AI தீர்மானிக்கட்டும்",
    lbl_location: "இடம் / அடையாளம்",
    lbl_location_placeholder: "எ.கா. காந்திபுரம் பேருந்து நிலையம் அருகில்",
    btn_get_location: "என் GPS இருப்பிடத்தைப் பயன்படுத்து",
    lbl_photo: "புகைப்படம் இணைக்க (அதிகபட்சம் 300KB)",
    lbl_name: "உங்கள் பெயர் (விரும்பினால்)",
    btn_submit_report: "புகாரை சமர்ப்பிக்கவும்",
    btn_improving: "AI ஆய்வு செய்கிறது...",
    btn_improve_desc: "AI உதவி & பரிந்துரைகள்",
    
    confirm_title: "புகார் வெற்றிகரமாக பதிவு செய்யப்பட்டது!",
    confirm_ticket: "டோக்கன் எண்:",
    confirm_category: "கண்டறியப்பட்ட பிரிவு:",
    confirm_priority: "முன்னுரிமை மதிப்பீடு:",
    confirm_dept: "ஒதுக்கப்பட்ட துறை:",
    confirm_sla: "தீர்வு நேரம்:",
    confirm_why_priority: "இந்த முன்னுரிமைக்கான காரணம்?",
    btn_track_this: "இந்த புகாரை கண்காணிக்க",
    btn_report_another: "மற்றொரு புகாரை பதிவு செய்ய",
    
    track_heading: "புகார் நிலையை அறிய",
    track_sub: "உங்கள் டோக்கன் எண்ணை உள்ளிட்டு தற்போதைய நிலை மற்றும் அதிகாரிகளின் குறிப்புகளைப் பார்க்கவும்.",
    track_input_label: "டோக்கன் எண்ணை உள்ளிடவும் (எ.கா. CR-2026-00001):",
    btn_track: "தேடுங்கள்",
    timeline_title: "நடவடிக்கை காலவரிசை",
    
    dash_heading: "பொது வெளிப்படைத்தன்மை தகவல் பலகை",
    dash_sub: "நகராட்சி குறைதீர்ப்பு செயல்திறன் மற்றும் பகுதி வாரியான புள்ளிவிவரங்கள்.",
    stat_total: "மொத்த புகார்கள்",
    stat_open: "நடவடிக்கையில் உள்ளவை",
    stat_resolved: "தீர்க்கப்பட்டவை",
    stat_avg_sla: "சராசரி தீர்வு நேரம்",
    stat_rate: "தீர்வு சதவீதம்",
    
    admin_heading: "நகராட்சி அதிகாரிகள் மையம்",
    admin_login_title: "அதிகாரி உள்நுழைவு",
    admin_login_sub: "மேலாண்மை மையத்தை அணுக கடவுச்சொல்லை உள்ளிடவும்.",
    admin_pwd_label: "கடவுச்சொல்:",
    btn_login: "உள்நுழைய",
    btn_logout: "வெளியேறு",
    admin_analytics_title: "பணிப்பாய்வு & பகுப்பாய்வு",
    admin_issues_title: "வரப்பெற்ற புகார்கள்",
    btn_generate_summary: "AI வாராந்திர சுருக்கம் உருவாக்கு",
  },
  hi: {
    app_title: "सिविकरिज़ॉल्व",
    tagline: "एआई-संचालित नागरिक शिकायत प्रबंधन एवं समाधान",
    nav_report: "शिकायत दर्ज करें",
    nav_track: "स्थिति ट्रैक करें",
    nav_dashboard: "सार्वजनिक डैशबोर्ड",
    nav_admin: "अधिकारी पोर्टल",
    skip_link: "मुख्य सामग्री पर जाएं",
    demo_banner_title: "डेमो मोड सक्रिय:",
    demo_banner_text: "इन-मेमोरी स्टोरेज पर चल रहा है। डेटा रीसेट हो सकता है।",
    demo_admin_hint: "डेमो एडमिन पासवर्ड:",
    btn_high_contrast: "उच्च कंट्रास्ट",
    btn_font_size: "A+",
    
    report_heading: "नागरिक समस्या दर्ज करें",
    report_sub: "सड़क के गड्ढे, कचरा, बिजली के तार, पानी का रिसाव आदि तुरंत दर्ज करें।",
    sample_title: "नमूना रिपोर्ट चुनें:",
    sample_pothole: "स्कूल के पास गड्ढा",
    sample_garbage: "कचरे का ढेर",
    sample_wire: "खुला बिजली का तार",
    sample_water: "पानी की पाइपलाइन टूटी",
    sample_light: "स्ट्रीट लाइट खराब",
    lbl_title: "शीर्षक (वैकल्पिक)",
    lbl_desc: "विवरण (आवश्यक - किसी भी भाषा में)",
    lbl_desc_placeholder: "समस्या का विस्तार से विवरण दें...",
    lbl_category: "श्रेणी (वैकल्पिक)",
    lbl_category_ai: "AI तय करेगा",
    lbl_location: "स्थान / लैंडमार्क",
    lbl_location_placeholder: "उदा. मुख्य सड़क, रेलवे स्टेशन के पास",
    btn_get_location: "मेरा GPS स्थान उपयोग करें",
    lbl_photo: "फोटो संलग्न करें (अधिकतम 300KB)",
    lbl_name: "आपका नाम (वैकल्पिक)",
    btn_submit_report: "शिकायत दर्ज करें",
    btn_improving: "AI विश्लेषण कर रहा है...",
    btn_improve_desc: "AI सहायता और सुझाव",
    
    confirm_title: "शिकायत सफलतापूर्वक दर्ज हो गई!",
    confirm_ticket: "टिकट संख्या:",
    confirm_category: "पहचानी गई श्रेणी:",
    confirm_priority: "प्राथमिकता स्तर:",
    confirm_dept: "संबंधित विभाग:",
    confirm_sla: "नियत समाधान समय:",
    confirm_why_priority: "प्राथमिकता का कारण क्या है?",
    btn_track_this: "इस शिकायत को ट्रैक करें",
    btn_report_another: "अन्य शिकायत दर्ज करें",
    
    track_heading: "शिकायत की स्थिति ट्रैक करें",
    track_sub: "जांच की प्रगति और अधिकारियों की टिप्पणी देखने के लिए टिकट आईडी दर्ज करें।",
    track_input_label: "टिकट आईडी दर्ज करें (उदा. CR-2026-00001):",
    btn_track: "खोजें",
    timeline_title: "समाधान समयरेखा",
    
    dash_heading: "सार्वजनिक पारदर्शिता डैशबोर्ड",
    dash_sub: "नगरपालिका के समाधान प्रदर्शन और इलाके की घटनाओं का नक्शा।",
    stat_total: "कुल शिकायतें",
    stat_open: "प्रक्रियाधीन",
    stat_resolved: "समाधान हो चुका",
    stat_avg_sla: "औसत समाधान समय",
    stat_rate: "समाधान दर",
    
    admin_heading: "नगर निगम अधिकारी पोर्टल",
    admin_login_title: "अधिकारी लॉगिन",
    admin_login_sub: "पोर्टल तक पहुंचने के लिए पासवर्ड दर्ज करें।",
    admin_pwd_label: "पासवर्ड:",
    btn_login: "लॉगिन करें",
    btn_logout: "लॉगआउट",
    admin_analytics_title: "कार्यप्रणाली एवं विश्लेषण",
    admin_issues_title: "दर्ज की गई शिकायतें",
    btn_generate_summary: "AI साप्ताहिक रिपोर्ट तैयार करें",
  }
};

let currentLanguage = localStorage.getItem("civic_lang") || "en";

export function getLanguage() {
  return currentLanguage;
}

export function setLanguage(lang) {
  if (translations[lang]) {
    currentLanguage = lang;
    localStorage.setItem("civic_lang", lang);
    document.documentElement.lang = lang;
    updateI18nTexts();
  }
}

export function t(key) {
  const dict = translations[currentLanguage] || translations.en;
  return dict[key] || translations.en[key] || key;
}

export function updateI18nTexts() {
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    if (key) {
      el.textContent = t(key);
    }
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    const key = el.getAttribute("data-i18n-placeholder");
    if (key) {
      el.placeholder = t(key);
    }
  });
}
