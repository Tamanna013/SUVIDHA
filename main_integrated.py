# main_integrated.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import sqlite3
import qrcode
from PIL import Image
import io
import base64
import uuid
import os
from pathlib import Path
from translations import TranslationSystem, t
from voice_assistant import VoiceAssistant
from webcam_capture import SimpleWebcam

# Initialize translation system
translator = TranslationSystem()

class IntegratedSuvidha:
    def __init__(self):
        self.db = self.init_database()
        self.create_upload_folder()
        self.voice_assistant = VoiceAssistant()
        self.webcam = SimpleWebcam()
        
        # Set default language
        if 'language' not in st.session_state:
            st.session_state.language = 'en'
        
        # Departments with multilingual support
        self.departments = {
            "electricity": {
                "en": "⚡ Electricity Department",
                "hi": "⚡ बिजली विभाग",
                "mr": "⚡ वीज विभाग",
                "ta": "⚡ மின்சார துறை"
            },
            "water": {
                "en": "💧 Water Department",
                "hi": "💧 जल विभाग",
                "mr": "💧 पाणी विभाग",
                "ta": "💧 நீர் துறை"
            },
            "gas": {
                "en": "🔥 Gas Department",
                "hi": "🔥 गैस विभाग",
                "mr": "🔥 गॅस विभाग",
                "ta": "🔥 எரிவாயு துறை"
            },
            "waste": {
                "en": "🗑️ Waste Management",
                "hi": "🗑️ कचरा प्रबंधन",
                "mr": "🗑️ कचरा व्यवस्थापन",
                "ta": "🗑️ குப்பை மேலாண்மை"
            }
        }
        
        # Service types with multilingual support
        self.service_types = {
            "electricity": {
                "en": ["Power Outage", "New Connection", "Bill Issue", "Meter Complaint", "Safety Inspection"],
                "hi": ["बिजली गुल", "नया कनेक्शन", "बिल समस्या", "मीटर शिकायत", "सुरक्षा निरीक्षण"],
                "mr": ["वीज गुल", "नवीन कनेक्शन", "बिल समस्या", "मीटर तक्रार", "सुरक्षा तपासणी"],
                "ta": ["மின்சாரம் இல்லை", "புதிய இணைப்பு", "பில் பிரச்சனை", "மீட்டர் புகார்", "பாதுகாப்பு ஆய்வு"]
            },
            "water": {
                "en": ["No Water Supply", "Water Quality Issue", "New Connection", "Pipeline Leakage", "Bill Payment"],
                "hi": ["पानी आपूर्ति नहीं", "पानी गुणवत्ता समस्या", "नया कनेक्शन", "पाइपलाइन रिसाव", "बिल भुगतान"],
                "mr": ["पाणी पुरवठा नाही", "पाणी गुणवत्ता समस्या", "नवीन कनेक्शन", "पाईपलाइन गळती", "बिल भरपाई"],
                "ta": ["நீர் விநியோகம் இல்லை", "நீர் தரம் பிரச்சனை", "புதிய இணைப்பு", "குழாய் கசிவு", "பில் செலுத்துதல்"]
            },
            "gas": {
                "en": ["Gas Leak Complaint", "New Connection", "Safety Check", "Appliance Service", "Bill Payment"],
                "hi": ["गैस रिसाव शिकायत", "नया कनेक्शन", "सुरक्षा जांच", "उपकरण सेवा", "बिल भुगतान"],
                "mr": ["गॅस गळती तक्रार", "नवीन कनेक्शन", "सुरक्षा तपासणी", "उपकरण सेवा", "बिल भरपाई"],
                "ta": ["எரிவாயு கசிவு புகார்", "புதிய இணைப்பு", "பாதுகாப்பு சோதனை", "உபகரண சேவை", "பில் செலுத்துதல்"]
            },
            "waste": {
                "en": ["Garbage Not Collected", "Sanitation Complaint", "Recycling Information", "Illegal Dumping", "Composting Request"],
                "hi": ["कचरा संग्रह नहीं", "सफाई शिकायत", "पुनर्चक्रण जानकारी", "अवैध डंपिंग", "कम्पोस्टिंग अनुरोध"],
                "mr": ["कचरा संकलन नाही", "स्वच्छता तक्रार", "पुनर्वापर माहिती", "बेकायदेशीर डंपिंग", "कंपोस्टिंग विनंती"],
                "ta": ["குப்பை சேகரிக்கப்படவில்லை", "சுகாதார புகார்", "மறுசுழற்சி தகவல்", "சட்டவிரோத குப்பை கொட்டுதல்", "கரிம உர கோரிக்கை"]
            }
        }
    
    def get_department_name(self, dept_key, lang=None):
        """Get department name in current language"""
        if lang is None:
            lang = st.session_state.language
        return self.departments.get(dept_key, {}).get(lang, dept_key)
    
    def get_service_types(self, dept_key, lang=None):
        """Get service types for department in current language"""
        if lang is None:
            lang = st.session_state.language
        return self.service_types.get(dept_key, {}).get(lang, [])
    
    def init_database(self):
        """Initialize database with multilingual support"""
        conn = sqlite3.connect('suvidha_integrated.db', check_same_thread=False)
        cursor = conn.cursor()
        
        # Add language column to users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE,
                aadhaar TEXT UNIQUE,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT,
                address TEXT,
                pincode TEXT,
                language TEXT DEFAULT 'en',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                user_type TEXT DEFAULT 'citizen'
            )
        ''')
        
        # Add language preference column to service_requests
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS service_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT UNIQUE,
                user_id INTEGER,
                department TEXT NOT NULL,
                service_type TEXT NOT NULL,
                description TEXT NOT NULL,
                address TEXT,
                pincode TEXT,
                language TEXT DEFAULT 'en',
                priority TEXT DEFAULT 'Medium',
                status TEXT DEFAULT 'Pending',
                assigned_to TEXT,
                estimated_completion DATE,
                actual_completion DATE,
                feedback_rating INTEGER,
                feedback_comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # ... rest of database initialization ...
        
        conn.commit()
        return conn
    
    def run(self):
        """Main application runner with multilingual support"""
        # Initialize session state
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'page' not in st.session_state:
            st.session_state.page = 'home'
        if 'user' not in st.session_state:
            st.session_state.user = {}
        
        # Language selector in sidebar (always visible)
        self.show_language_selector()
        
        # Check authentication
        if not st.session_state.authenticated:
            self.show_login()
        else:
            self.show_main_app()
    
    def show_language_selector(self):
        """Show language selector in sidebar"""
        with st.sidebar:
            st.markdown("---")
            current_lang = st.session_state.language
            
            # Language selection
            lang_options = translator.get_all_languages()
            selected_lang = st.selectbox(
                "🌐 " + t('language', current_lang),
                options=list(lang_options.keys()),
                format_func=lambda x: lang_options[x],
                index=list(lang_options.keys()).index(current_lang) if current_lang in lang_options else 0
            )
            
            if selected_lang != current_lang:
                st.session_state.language = selected_lang
                # Update user's language preference in database
                if st.session_state.get('user_id'):
                    cursor = self.db.cursor()
                    cursor.execute('''
                        UPDATE users SET language=? WHERE user_id=?
                    ''', (selected_lang, st.session_state.user_id))
                    self.db.commit()
                st.rerun()
    
    def show_login(self):
        """Show login page with multilingual support"""
        current_lang = st.session_state.language
        
        st.markdown(f'<div class="main-header"><h1>🏙️ {t("welcome", current_lang)}</h1></div>', 
                   unsafe_allow_html=True)
        
        # Login tabs
        tab1, tab2, tab3 = st.tabs([
            t("login", current_lang),
            t("guest_access", current_lang),
            t("admin_login", current_lang)
        ])
        
        with tab1:
            self.citizen_login(current_lang)
        
        with tab2:
            self.guest_login(current_lang)
        
        with tab3:
            self.admin_login(current_lang)
    
    def citizen_login(self, current_lang):
        """Citizen login form with multilingual labels"""
        with st.form("citizen_login_form"):
            st.subheader(t("login", current_lang))
            
            col1, col2 = st.columns(2)
            
            with col1:
                aadhaar = st.text_input(
                    t("aadhaar_number", current_lang),
                    max_chars=12,
                    placeholder="12-digit number"
                )
                phone = st.text_input(
                    t("mobile_number", current_lang),
                    max_chars=10,
                    placeholder="10-digit number"
                )
            
            with col2:
                name = st.text_input(t("full_name", current_lang))
                email = st.text_input(t("email", current_lang) + " (" + t("optional", current_lang) + ")")
            
            # OTP section
            st.subheader(t("otp", current_lang) + " " + t("verification", current_lang))
            col3, col4 = st.columns(2)
            
            with col3:
                if st.form_submit_button(t("send_otp", current_lang)):
                    if self.validate_input(aadhaar, phone, name):
                        otp = self.generate_otp()
                        st.session_state.otp = otp
                        st.success(f"{t('otp', current_lang)} {t('sent', current_lang)} {phone}. {t('demo', current_lang)} {t('otp', current_lang)}: {otp}")
                    else:
                        st.error(t("invalid_input", current_lang))
            
            with col4:
                otp_input = st.text_input(
                    t("enter", current_lang) + " " + t("otp", current_lang),
                    max_chars=6
                )
            
            # Photo capture option
            with st.expander(t("photo_verification", current_lang) + " (" + t("optional", current_lang) + ")"):
                photo = self.webcam.capture_photo_interface(current_lang)
                if photo:
                    st.session_state.user_photo = photo
            
            if st.form_submit_button(t("login", current_lang), type="primary"):
                if self.verify_otp(aadhaar, otp_input):
                    # Login logic...
                    st.success(t("welcome", current_lang) + f" {name}!")
                    st.rerun()
                else:
                    st.error(t("invalid", current_lang) + " " + t("otp", current_lang))
    
    def show_main_app(self):
        """Show main application with multilingual navigation"""
        current_lang = st.session_state.language
        
        # Sidebar with multilingual labels
        with st.sidebar:
            user_name = st.session_state.user.get('name', t('user', current_lang))
            user_type = st.session_state.user.get('user_type', 'citizen')
            
            st.title(f"👋 {user_name}")
            
            if user_type == 'guest':
                st.warning(t('guest_mode', current_lang))
            elif user_type == 'admin':
                st.success(t('admin_mode', current_lang))
            
            st.markdown("---")
            
            # Navigation based on user type
            if user_type == 'admin':
                menu_items = {
                    t("admin_dashboard", current_lang): "admin_dashboard",
                    t("analytics", current_lang): "analytics",
                    t("user_management", current_lang): "user_management",
                    t("all_requests", current_lang): "all_requests",
                    t("payments", current_lang): "payments_admin",
                    t("documents", current_lang): "documents_admin",
                    t("system_settings", current_lang): "system_settings"
                }
            else:
                menu_items = {
                    t("dashboard", current_lang): "home",
                    t("new_request", current_lang): "new_request",
                    t("track_status", current_lang): "track_status",
                    t("pay_bills", current_lang): "payments",
                    t("documents", current_lang): "documents",
                    t("notifications", current_lang): "notifications",
                    t("voice_assistant", current_lang): "voice_assistant",
                    t("settings", current_lang): "settings"
                }
            
            for item, page in menu_items.items():
                if st.button(item, use_container_width=True, 
                           type="primary" if st.session_state.page == page else "secondary"):
                    st.session_state.page = page
                    st.rerun()
            
            st.markdown("---")
            
            # Emergency button for non-admin users
            if user_type != 'admin':
                if st.button("🚨 " + t("emergency", current_lang), 
                           type="secondary", use_container_width=True):
                    st.session_state.page = "emergency"
            
            # Logout button
            if st.button("🚪 " + t("logout", current_lang), 
                       type="secondary", use_container_width=True):
                st.session_state.clear()
                st.rerun()
        
        # Main content with multilingual pages
        pages = {
            'home': self.show_dashboard,
            'new_request': self.show_new_request,
            'track_status': self.show_track_status,
            'payments': self.show_payments,
            'documents': self.show_documents,
            'notifications': self.show_notifications,
            'voice_assistant': self.show_voice_assistant,
            'settings': self.show_settings,
            'emergency': self.show_emergency,
            'admin_dashboard': self.show_admin_dashboard,
            # ... other pages
        }
        
        pages.get(st.session_state.page, self.show_dashboard)()
    
    def show_new_request(self):
        """Show new service request form with multilingual support"""
        current_lang = st.session_state.language
        
        st.title("📝 " + t("new_request", current_lang))
        
        # Department selection with multilingual names
        dept_options = [
            self.get_department_name("electricity", current_lang),
            self.get_department_name("water", current_lang),
            self.get_department_name("gas", current_lang),
            self.get_department_name("waste", current_lang)
        ]
        
        selected_dept_display = st.selectbox(
            t("select_department", current_lang),
            dept_options
        )
        
        # Get department key from display name
        selected_dept_key = None
        for key, names in self.departments.items():
            if names.get(current_lang) == selected_dept_display:
                selected_dept_key = key
                break
        
        if selected_dept_key:
            # Service type selection
            service_options = self.get_service_types(selected_dept_key, current_lang)
            service_type = st.selectbox(
                t("service_type", current_lang),
                service_options
            )
            
            # Request form
            with st.form("request_form"):
                description = st.text_area(
                    t("description", current_lang),
                    height=150,
                    placeholder=t("describe_your_issue", current_lang) + "..."
                )
                
                # Location
                st.subheader("📍 " + t("location", current_lang))
                col1, col2 = st.columns(2)
                with col1:
                    address = st.text_input(t("address", current_lang))
                    landmark = st.text_input(t("landmark", current_lang) + " (" + t("optional", current_lang) + ")")
                with col2:
                    pincode = st.text_input(t("pincode", current_lang), max_chars=6)
                    zone = st.selectbox(t("zone", current_lang), ["Zone 1", "Zone 2", "Zone 3", "Zone 4"])
                
                # Priority
                priority_labels = {
                    "low": t("low", current_lang),
                    "medium": t("medium", current_lang),
                    "high": t("high", current_lang),
                    "emergency": t("emergency_priority", current_lang)
                }
                
                priority = st.select_slider(
                    t("priority_level", current_lang),
                    options=list(priority_labels.values()),
                    value=priority_labels["medium"]
                )
                
                # Document upload
                uploaded_files = st.file_uploader(
                    t("attach_documents", current_lang) + " (" + t("optional", current_lang) + ")",
                    accept_multiple_files=True,
                    type=['pdf', 'jpg', 'png']
                )
                
                # Contact preferences
                contact_methods = {
                    "phone": t("phone", current_lang),
                    "sms": "SMS",
                    "email": "Email",
                    "whatsapp": "WhatsApp"
                }
                
                contact_method = st.multiselect(
                    t("contact_method", current_lang),
                    list(contact_methods.values()),
                    default=[contact_methods["phone"]]
                )
                
                agree_terms = st.checkbox(t("terms_agree", current_lang))
                
                if st.form_submit_button(t("submit", current_lang), type="primary"):
                    if description and address and pincode and agree_terms:
                        # Process submission...
                        st.success("✅ " + t("request_submitted", current_lang))
                    else:
                        st.error(t("required_field", current_lang))
    
    def show_voice_assistant(self):
        """Show voice assistant interface"""
        current_lang = st.session_state.language
        self.voice_assistant.voice_interface(current_lang)
    
    def show_documents(self):
        """Show documents interface with photo capture option"""
        current_lang = st.session_state.language
        
        st.title("📄 " + t("documents", current_lang))
        
        # Photo capture section
        with st.expander("📸 " + t("photo_verification", current_lang)):
            photo = self.webcam.capture_photo_interface(current_lang)
            if photo:
                st.success(t("photo_verified", current_lang))
        
        # Rest of documents interface...
    
    def show_emergency(self):
        """Show emergency services with multilingual support"""
        current_lang = st.session_state.language
        
        st.title("🚨 " + t("emergency_services", current_lang))
        
        # Emergency contacts with multilingual labels
        emergency_contacts = [
            {"service": t("police", current_lang), "number": "100"},
            {"service": t("fire", current_lang), "number": "101"},
            {"service": t("ambulance", current_lang), "number": "102"},
            {"service": t("women_helpline", current_lang), "number": "1091"},
            {"service": t("child_helpline", current_lang), "number": "1098"},
            {"service": t("electricity", current_lang) + " " + t("emergency", current_lang), "number": "1912"},
            {"service": t("gas", current_lang) + " " + t("leak", current_lang), "number": "1906"}
        ]
        
        # Display contacts
        for contact in emergency_contacts:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{contact['service']}**")
            with col2:
                st.code(contact['number'], language=None)
        
        # Voice command for emergency
        st.markdown("---")
        st.subheader("🗣️ " + t("voice_command", current_lang) + " " + t("emergency", current_lang))
        
        if st.button("🎤 " + t("say_emergency", current_lang), use_container_width=True):
            self.voice_assistant.listen_and_process(
                st.session_state.language, 
                st.session_state.language
            )
    
    # ... rest of the methods with multilingual support ...

# Run the app
if __name__ == "__main__":
    # Page config with multilingual title
    st.set_page_config(
        page_title="SUVIDHA - Smart Urban Digital Helpdesk",
        page_icon="🏙️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Add custom CSS
    st.markdown("""
    <style>
        .main-header {
            background: linear-gradient(90deg, #1a2980 0%, #26d0ce 100%);
            color: white;
            padding: 2rem;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 2rem;
        }
        /* Add more styles as needed */
    </style>
    """, unsafe_allow_html=True)
    
    app = IntegratedSuvidha()
    app.run()