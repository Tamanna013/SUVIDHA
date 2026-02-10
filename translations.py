# translations.py
import json
import os

class TranslationSystem:
    def __init__(self):
        self.translations = {
            "en": {
                # Login & Authentication
                "welcome": "Welcome to SUVIDHA",
                "login": "Login",
                "logout": "Logout",
                "register": "Register",
                "aadhaar_number": "Aadhaar Number",
                "mobile_number": "Mobile Number",
                "full_name": "Full Name",
                "email": "Email",
                "otp": "OTP",
                "send_otp": "Send OTP",
                "verify_otp": "Verify OTP",
                "guest_access": "Guest Access",
                "admin_login": "Admin Login",
                
                # Navigation
                "dashboard": "Dashboard",
                "new_request": "New Request",
                "track_status": "Track Status",
                "pay_bills": "Pay Bills",
                "documents": "Documents",
                "notifications": "Notifications",
                "settings": "Settings",
                "emergency": "Emergency",
                "voice_assistant": "Voice Assistant",
                
                # Departments
                "electricity_department": "Electricity Department",
                "water_department": "Water Department",
                "gas_department": "Gas Department",
                "waste_management": "Waste Management",
                
                # Services
                "power_outage": "Power Outage",
                "new_connection": "New Connection",
                "bill_issue": "Bill Issue",
                "meter_complaint": "Meter Complaint",
                "no_water": "No Water Supply",
                "water_quality": "Water Quality Issue",
                "gas_leak": "Gas Leak",
                "garbage_not_collected": "Garbage Not Collected",
                "sanitation": "Sanitation Complaint",
                
                # Common
                "submit": "Submit",
                "cancel": "Cancel",
                "save": "Save",
                "delete": "Delete",
                "view": "View",
                "edit": "Edit",
                "update": "Update",
                "search": "Search",
                "filter": "Filter",
                "download": "Download",
                "upload": "Upload",
                "confirm": "Confirm",
                "back": "Back",
                "next": "Next",
                "previous": "Previous",
                
                # Status
                "pending": "Pending",
                "in_progress": "In Progress",
                "completed": "Completed",
                "rejected": "Rejected",
                
                # Priority
                "low": "Low",
                "medium": "Medium",
                "high": "High",
                "emergency_priority": "Emergency",
                
                # Messages
                "success": "Success",
                "error": "Error",
                "warning": "Warning",
                "info": "Information",
                "required_field": "This field is required",
                "invalid_input": "Invalid input",
                "processing": "Processing...",
                "loading": "Loading...",
                
                # Dashboard
                "total_requests": "Total Requests",
                "pending_requests": "Pending Requests",
                "completed_requests": "Completed Requests",
                "active_today": "Active Today",
                "quick_actions": "Quick Actions",
                "recent_activity": "Recent Activity",
                "quick_stats": "Quick Stats",
                
                # Service Request
                "select_department": "Select Department",
                "service_type": "Service Type",
                "description": "Description",
                "address": "Address",
                "landmark": "Landmark",
                "pincode": "Pincode",
                "zone": "Zone",
                "priority_level": "Priority Level",
                "attach_documents": "Attach Documents",
                "contact_method": "Contact Method",
                "terms_agree": "I agree to terms and conditions",
                "request_submitted": "Request Submitted Successfully",
                "request_id": "Request ID",
                "expected_resolution": "Expected Resolution",
                "track_url": "Track URL",
                
                # Payments
                "bill_payment": "Bill Payment",
                "amount": "Amount",
                "due_date": "Due Date",
                "payment_method": "Payment Method",
                "transaction_id": "Transaction ID",
                "payment_successful": "Payment Successful",
                "payment_failed": "Payment Failed",
                "receipt": "Receipt",
                "payment_history": "Payment History",
                
                # Documents
                "document_type": "Document Type",
                "document_name": "Document Name",
                "upload_date": "Upload Date",
                "verified": "Verified",
                "not_verified": "Not Verified",
                "upload_successful": "Upload Successful",
                
                # Notifications
                "unread_notifications": "Unread Notifications",
                "mark_all_read": "Mark All as Read",
                "no_notifications": "No Notifications",
                
                # Settings
                "profile_information": "Profile Information",
                "preferences": "Preferences",
                "language": "Language",
                "notifications_enabled": "Notifications Enabled",
                "email_alerts": "Email Alerts",
                "sms_alerts": "SMS Alerts",
                "account_security": "Account Security",
                "change_password": "Change Password",
                "danger_zone": "Danger Zone",
                "export_data": "Export My Data",
                "delete_account": "Delete Account",
                
                # Emergency
                "emergency_services": "Emergency Services",
                "police": "Police",
                "fire": "Fire",
                "ambulance": "Ambulance",
                "women_helpline": "Women Helpline",
                "child_helpline": "Child Helpline",
                "report_emergency": "Report Emergency",
                "emergency_type": "Emergency Type",
                "location": "Location",
                "severity": "Severity",
                "reporter_info": "Reporter Information",
                
                # Voice Assistant
                "voice_assistant_title": "Voice Assistant",
                "speak_language": "Speak in language",
                "start_listening": "Start Listening",
                "speak_help": "Speak Help",
                "hear_response": "Hear Response",
                "listening": "Listening... Speak now",
                "speech_detected": "No speech detected",
                "speech_not_understood": "Could not understand audio",
                "speech_service_unavailable": "Speech service unavailable",
                "try_saying": "Try saying:",
                
                # Webcam
                "capture_photo": "Capture Photo for Verification",
                "upload_photo": "Upload Photo",
                "take_photo": "Take Photo",
                "use_photo": "Use this photo",
                "photo_captured": "Photo Captured",
                "photo_verification": "Photo Verification",
                
                # Admin
                "admin_dashboard": "Admin Dashboard",
                "user_management": "User Management",
                "all_requests": "All Requests",
                "system_settings": "System Settings",
                "analytics": "Analytics",
                "generate_reports": "Generate Reports",
                "total_users": "Total Users",
                "revenue": "Revenue",
                "system_health": "System Health",
            },
            
            "hi": {
                # Login & Authentication
                "welcome": "सुविधा में आपका स्वागत है",
                "login": "लॉगिन",
                "logout": "लॉगआउट",
                "register": "पंजीकरण",
                "aadhaar_number": "आधार नंबर",
                "mobile_number": "मोबाइल नंबर",
                "full_name": "पूरा नाम",
                "email": "ईमेल",
                "otp": "ओटीपी",
                "send_otp": "ओटीपी भेजें",
                "verify_otp": "ओटीपी सत्यापित करें",
                "guest_access": "अतिथि पहुंच",
                "admin_login": "एडमिन लॉगिन",
                
                # Navigation
                "dashboard": "डैशबोर्ड",
                "new_request": "नया अनुरोध",
                "track_status": "स्थिति ट्रैक करें",
                "pay_bills": "बिल भुगतान",
                "documents": "दस्तावेज़",
                "notifications": "सूचनाएं",
                "settings": "सेटिंग्स",
                "emergency": "आपातकाल",
                "voice_assistant": "वॉयस असिस्टेंट",
                
                # Departments
                "electricity_department": "बिजली विभाग",
                "water_department": "जल विभाग",
                "gas_department": "गैस विभाग",
                "waste_management": "कचरा प्रबंधन",
                
                # Services
                "power_outage": "बिजली गुल",
                "new_connection": "नया कनेक्शन",
                "bill_issue": "बिल समस्या",
                "meter_complaint": "मीटर शिकायत",
                "no_water": "पानी आपूर्ति नहीं",
                "water_quality": "पानी गुणवत्ता समस्या",
                "gas_leak": "गैस रिसाव",
                "garbage_not_collected": "कचरा संग्रह नहीं",
                "sanitation": "सफाई शिकायत",
                
                # Common
                "submit": "जमा करें",
                "cancel": "रद्द करें",
                "save": "सहेजें",
                "delete": "हटाएं",
                "view": "देखें",
                "edit": "संपादित करें",
                "update": "अपडेट करें",
                "search": "खोजें",
                "filter": "फ़िल्टर",
                "download": "डाउनलोड",
                "upload": "अपलोड",
                "confirm": "पुष्टि करें",
                "back": "वापस",
                "next": "आगे",
                "previous": "पिछला",
                
                # Status
                "pending": "लंबित",
                "in_progress": "प्रगति में",
                "completed": "पूर्ण",
                "rejected": "अस्वीकृत",
                
                # Priority
                "low": "कम",
                "medium": "मध्यम",
                "high": "उच्च",
                "emergency_priority": "आपातकाल",
                
                # Messages
                "success": "सफल",
                "error": "त्रुटि",
                "warning": "चेतावनी",
                "info": "जानकारी",
                "required_field": "यह फ़ील्ड आवश्यक है",
                "invalid_input": "अमान्य इनपुट",
                "processing": "प्रसंस्करण...",
                "loading": "लोड हो रहा है...",
                
                # Dashboard
                "total_requests": "कुल अनुरोध",
                "pending_requests": "लंबित अनुरोध",
                "completed_requests": "पूर्ण अनुरोध",
                "active_today": "आज सक्रिय",
                "quick_actions": "त्वरित कार्य",
                "recent_activity": "हाल की गतिविधि",
                "quick_stats": "त्वरित आँकड़े",
                
                # Service Request
                "select_department": "विभाग चुनें",
                "service_type": "सेवा प्रकार",
                "description": "विवरण",
                "address": "पता",
                "landmark": "लैंडमार्क",
                "pincode": "पिन कोड",
                "zone": "ज़ोन",
                "priority_level": "प्राथमिकता स्तर",
                "attach_documents": "दस्तावेज़ संलग्न करें",
                "contact_method": "संपर्क विधि",
                "terms_agree": "मैं नियम और शर्तों से सहमत हूं",
                "request_submitted": "अनुरोध सफलतापूर्वक जमा किया गया",
                "request_id": "अनुरोध आईडी",
                "expected_resolution": "अपेक्षित समाधान",
                "track_url": "ट्रैक यूआरएल",
                
                # Payments
                "bill_payment": "बिल भुगतान",
                "amount": "राशि",
                "due_date": "नियत तारीख",
                "payment_method": "भुगतान विधि",
                "transaction_id": "लेनदेन आईडी",
                "payment_successful": "भुगतान सफल",
                "payment_failed": "भुगतान विफल",
                "receipt": "रसीद",
                "payment_history": "भुगतान इतिहास",
                
                # Documents
                "document_type": "दस्तावेज़ प्रकार",
                "document_name": "दस्तावेज़ नाम",
                "upload_date": "अपलोड तिथि",
                "verified": "सत्यापित",
                "not_verified": "असत्यापित",
                "upload_successful": "अपलोड सफल",
                
                # Notifications
                "unread_notifications": "अपठित सूचनाएं",
                "mark_all_read": "सभी पठित करें",
                "no_notifications": "कोई सूचना नहीं",
                
                # Settings
                "profile_information": "प्रोफ़ाइल जानकारी",
                "preferences": "वरीयताएं",
                "language": "भाषा",
                "notifications_enabled": "सूचनाएं सक्षम",
                "email_alerts": "ईमेल अलर्ट",
                "sms_alerts": "एसएमएस अलर्ट",
                "account_security": "खाता सुरक्षा",
                "change_password": "पासवर्ड बदलें",
                "danger_zone": "खतरा क्षेत्र",
                "export_data": "मेरा डेटा निर्यात करें",
                "delete_account": "खाता हटाएं",
                
                # Emergency
                "emergency_services": "आपातकालीन सेवाएं",
                "police": "पुलिस",
                "fire": "आग",
                "ambulance": "एम्बुलेंस",
                "women_helpline": "महिला हेल्पलाइन",
                "child_helpline": "बाल हेल्पलाइन",
                "report_emergency": "आपातकाल की रिपोर्ट करें",
                "emergency_type": "आपातकाल प्रकार",
                "location": "स्थान",
                "severity": "गंभीरता",
                "reporter_info": "रिपोर्टर जानकारी",
                
                # Voice Assistant
                "voice_assistant_title": "वॉयस असिस्टेंट",
                "speak_language": "भाषा में बोलें",
                "start_listening": "सुनना शुरू करें",
                "speak_help": "सहायता बोलें",
                "hear_response": "प्रतिक्रिया सुनें",
                "listening": "सुन रहा हूं... अब बोलें",
                "speech_detected": "कोई भाषण नहीं मिला",
                "speech_not_understood": "ऑडियो समझ नहीं आया",
                "speech_service_unavailable": "भाषण सेवा अनुपलब्ध",
                "try_saying": "कहने का प्रयास करें:",
                
                # Webcam
                "capture_photo": "सत्यापन के लिए फोटो कैप्चर करें",
                "upload_photo": "फोटो अपलोड करें",
                "take_photo": "फोटो लें",
                "use_photo": "इस फोटो का उपयोग करें",
                "photo_captured": "फोटो कैप्चर किया गया",
                "photo_verification": "फोटो सत्यापन",
                
                # Admin
                "admin_dashboard": "एडमिन डैशबोर्ड",
                "user_management": "उपयोगकर्ता प्रबंधन",
                "all_requests": "सभी अनुरोध",
                "system_settings": "सिस्टम सेटिंग्स",
                "analytics": "विश्लेषण",
                "generate_reports": "रिपोर्ट जेनरेट करें",
                "total_users": "कुल उपयोगकर्ता",
                "revenue": "राजस्व",
                "system_health": "सिस्टम स्वास्थ्य",
            },
            
            "mr": {
                "welcome": "सुविधा मध्ये आपले स्वागत आहे",
                "login": "लॉगिन",
                "logout": "लॉगआउट",
                "aadhaar_number": "आधार क्रमांक",
                "mobile_number": "मोबाईल नंबर",
                "full_name": "पूर्ण नाव",
                "submit": "सबमिट करा",
                # Add more Marathi translations...
            },
            
            "ta": {
                "welcome": "சுயிதாவுக்கு வரவேற்கிறோம்",
                "login": "உள்நுழை",
                "logout": "வெளியேறு",
                "aadhaar_number": "ஆதார் எண்",
                "mobile_number": "மொபைல் எண்",
                "full_name": "முழுப் பெயர்",
                "submit": "சமர்ப்பி",
                # Add more Tamil translations...
            },
            
            "te": {
                "welcome": "సుపిడాకు స్వాగతం",
                "login": "లాగిన్",
                "logout": "లాగ్అవుట్",
                "aadhaar_number": "ఆధార్ నంబర్",
                "mobile_number": "మొబైల్ నంబర్",
                "full_name": "పూర్తి పేరు",
                "submit": "సమర్పించండి",
                # Add more Telugu translations...
            },
            
            "kn": {
                "welcome": "ಸುವಿದಾಗೆ ಸ್ವಾಗತ",
                "login": "ಲಾಗಿನ್",
                "logout": "ಲಾಗ್ಔಟ್",
                "aadhaar_number": "ಆಧಾರ್ ಸಂಖ್ಯೆ",
                "mobile_number": "ಮೊಬೈಲ್ ನಂಬರ್",
                "full_name": "ಪೂರ್ಣ ಹೆಸರು",
                "submit": "ಸಲ್ಲಿಸು",
                # Add more Kannada translations...
            },
            
            "ml": {
                "welcome": "സുവിദയിലേക്ക് സ്വാഗതം",
                "login": "ലോഗിൻ",
                "logout": "ലോഗൗട്ട്",
                "aadhaar_number": "ആധാർ നമ്പർ",
                "mobile_number": "മൊബൈൽ നമ്പർ",
                "full_name": "പൂർണ്ണ നാമം",
                "submit": "സമർപ്പിക്കുക",
                # Add more Malayalam translations...
            },
            
            "bn": {
                "welcome": "সুবিধায় স্বাগতম",
                "login": "লগইন",
                "logout": "লগআউট",
                "aadhaar_number": "আধার নম্বর",
                "mobile_number": "মোবাইল নম্বর",
                "full_name": "সম্পূর্ণ নাম",
                "submit": "জমা দিন",
                # Add more Bengali translations...
            }
        }
        
        self.language_names = {
            "en": "English",
            "hi": "हिंदी",
            "mr": "मराठी",
            "ta": "தமிழ்",
            "te": "తెలుగు",
            "kn": "ಕನ್ನಡ",
            "ml": "മലയാളം",
            "bn": "বাংলা"
        }
    
    def get_text(self, key, lang="en"):
        """Get translated text for a key"""
        # Default to English if translation not found
        return self.translations.get(lang, self.translations["en"]).get(key, key)
    
    def get_language_name(self, code):
        """Get language name from code"""
        return self.language_names.get(code, "English")
    
    def get_all_languages(self):
        """Get all supported languages"""
        return self.language_names
    
    def save_translation(self, lang, key, text):
        """Save new translation (for admin use)"""
        if lang not in self.translations:
            self.translations[lang] = {}
        self.translations[lang][key] = text
        
        # Save to file
        self.save_to_file()
    
    def save_to_file(self):
        """Save translations to JSON file"""
        with open('translations.json', 'w', encoding='utf-8') as f:
            json.dump(self.translations, f, ensure_ascii=False, indent=2)
    
    def load_from_file(self):
        """Load translations from JSON file"""
        if os.path.exists('translations.json'):
            with open('translations.json', 'r', encoding='utf-8') as f:
                self.translations = json.load(f)

# Create singleton instance
translator = TranslationSystem()

# Helper function for easy access
def t(key, lang=None):
    """Get translation for key"""
    if lang is None:
        lang = st.session_state.get('language', 'en')
    return translator.get_text(key, lang)