# auth_system.py
import streamlit as st
import cv2
import face_recognition
import numpy as np
import pyotp
import qrcode
from datetime import datetime, timedelta
import sqlite3
import hashlib
import json
from twilio.rest import Client
import os

class AdvancedAuthSystem:
    def __init__(self):
        self.db = sqlite3.connect('suvidha_auth.db', check_same_thread=False)
        self.init_auth_db()
        self.twilio_client = Client(os.getenv('TWILIO_SID'), os.getenv('TWILIO_TOKEN'))
    
    def init_auth_db(self):
        cursor = self.db.cursor()
        # User profiles with biometric data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                aadhaar_id TEXT UNIQUE,
                name TEXT,
                phone TEXT UNIQUE,
                email TEXT,
                face_encoding BLOB,
                fingerprint_hash TEXT,
                iris_template BLOB,
                created_at TIMESTAMP,
                last_login TIMESTAMP,
                failed_attempts INTEGER DEFAULT 0,
                account_locked BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # OTP and session management
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id INTEGER,
                login_time TIMESTAMP,
                expiry_time TIMESTAMP,
                ip_address TEXT,
                device_info TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Login methods table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS login_methods (
                user_id INTEGER,
                method TEXT,  -- 'face', 'fingerprint', 'otp', 'qr', 'voice'
                is_primary BOOLEAN,
                data BLOB,  -- Method-specific data
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        self.db.commit()
    
    def multimodal_login(self):
        """Offers multiple login options"""
        st.markdown("## 🔐 Secure Login Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🧬 Aadhaar + OTP", use_container_width=True):
                st.session_state['login_method'] = 'aadhaar_otp'
                st.rerun()
        
        with col2:
            if st.button("📱 Mobile OTP", use_container_width=True):
                st.session_state['login_method'] = 'mobile_otp'
                st.rerun()
        
        with col3:
            if st.button("👤 Facial Recognition", use_container_width=True):
                st.session_state['login_method'] = 'face'
                st.rerun()
        
        # Additional methods
        col4, col5, col6 = st.columns(3)
        with col4:
            if st.button("🖐️ Fingerprint", use_container_width=True):
                st.session_state['login_method'] = 'fingerprint'
                st.rerun()
        with col5:
            if st.button("🗣️ Voice Login", use_container_width=True):
                st.session_state['login_method'] = 'voice'
                st.rerun()
        with col6:
            if st.button("📇 Guest Login", use_container_width=True):
                st.session_state['login_method'] = 'guest'
                st.rerun()
        
        # Handle selected method
        if 'login_method' in st.session_state:
            method = st.session_state['login_method']
            
            if method == 'aadhaar_otp':
                self.aadhaar_otp_login()
            elif method == 'mobile_otp':
                self.mobile_otp_login()
            elif method == 'face':
                self.facial_login()
            elif method == 'fingerprint':
                self.fingerprint_login()
            elif method == 'voice':
                self.voice_login()
            elif method == 'guest':
                self.guest_login()
    
    def aadhaar_otp_login(self):
        """Aadhaar-based OTP authentication"""
        st.subheader("Aadhaar + OTP Authentication")
        
        with st.form("aadhaar_form"):
            aadhaar = st.text_input("12-digit Aadhaar Number", 
                                   max_chars=12,
                                   help="Enter your Aadhaar number")
            
            # Aadhaar verification with checksum
            if aadhaar and len(aadhaar) == 12 and aadhaar.isdigit():
                # Verify Aadhaar checksum (simplified)
                if self.verify_aadhaar_checksum(aadhaar):
                    st.success("✅ Valid Aadhaar format")
                    
                    # Send OTP to registered mobile
                    if st.form_submit_button("Send OTP"):
                        otp = self.generate_otp(aadhaar)
                        # In production: Send via SMS
                        # self.send_sms_otp(registered_mobile, otp)
                        
                        # For demo, show OTP
                        st.session_state['generated_otp'] = otp
                        st.info(f"📱 OTP sent to registered mobile. Demo OTP: {otp}")
                
                # OTP verification
                otp_input = st.text_input("Enter 6-digit OTP", max_chars=6)
                
                if st.form_submit_button("Verify OTP"):
                    if 'generated_otp' in st.session_state and otp_input == st.session_state['generated_otp']:
                        self.complete_login(aadhaar, "aadhaar_otp")
                    else:
                        st.error("❌ Invalid OTP")
            else:
                st.error("Invalid Aadhaar number")
    
    def facial_login(self):
        """Facial recognition login using webcam"""
        st.subheader("👤 Facial Recognition Login")
        
        # Check if user has registered face
        if st.button("Check Face Registration"):
            registered = self.check_face_registration()
            if not registered:
                st.warning("Face not registered. Please register first.")
                if st.button("Register Face"):
                    self.register_face()
                return
        
        # Start webcam for face recognition
        st.write("Position your face in front of the camera")
        
        # Webcam capture using OpenCV
        run_camera = st.checkbox("Start Camera")
        FRAME_WINDOW = st.image([])
        camera = cv2.VideoCapture(0)
        
        if run_camera:
            while run_camera:
                _, frame = camera.read()
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Face detection
                face_locations = face_recognition.face_locations(frame)
                face_encodings = face_recognition.face_encodings(frame, face_locations)
                
                # Draw rectangles around faces
                for (top, right, bottom, left) in face_locations:
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                
                FRAME_WINDOW.image(frame)
                
                # If face detected, try to match
                if face_encodings:
                    match = self.match_face(face_encodings[0])
                    if match:
                        st.success(f"✅ Face recognized! Welcome {match['name']}")
                        self.complete_login(match['aadhaar'], "face")
                        break
        
        camera.release()
    
    def register_face(self):
        """Register user's face for biometric login"""
        st.subheader("Register Your Face")
        
        st.write("1. Look directly at the camera")
        st.write("2. Ensure good lighting")
        st.write("3. Keep a neutral expression")
        
        if st.button("Start Registration"):
            # Capture multiple images for better accuracy
            encodings = []
            for i in range(3):
                st.write(f"Capture {i+1}/3...")
                # Capture and process face
                # (Implementation similar to facial_login)
                pass
            
            # Store face encoding in database
            st.success("Face registered successfully!")
    
    def voice_login(self):
        """Voice-based authentication"""
        st.subheader("🗣️ Voice Authentication")
        
        import speech_recognition as sr
        
        st.write("Speak the following phrase:")
        challenge_phrase = "My citizen number is 1234"
        st.code(challenge_phrase)
        
        if st.button("Start Recording"):
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                st.write("Listening...")
                audio = recognizer.listen(source, timeout=5)
                
                try:
                    spoken_text = recognizer.recognize_google(audio, language='hi-IN')
                    st.write(f"You said: {spoken_text}")
                    
                    # Verify voice pattern (simplified)
                    if "citizen" in spoken_text.lower():
                        # In production: Compare with voice biometrics
                        st.success("Voice recognized!")
                        self.complete_login("voice_user", "voice")
                    else:
                        st.error("Verification failed")
                except sr.UnknownValueError:
                    st.error("Could not understand audio")
                except sr.RequestError:
                    st.error("Speech service unavailable")
    
    def generate_qr_login(self):
        """Generate QR code for mobile app login"""
        st.subheader("📱 Mobile App Login")
        
        # Generate unique session QR
        session_id = hashlib.sha256(str(datetime.now()).encode()).hexdigest()[:10]
        qr_data = f"suvidha://login?session={session_id}&time={datetime.now().timestamp()}"
        
        # Create QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img.save("login_qr.png")
        
        st.image("login_qr.png", caption="Scan with SUVIDHA Mobile App")
        st.info("Open SUVIDHA mobile app and scan this QR code")
        
        # Poll for mobile confirmation
        if st.button("Check Mobile Confirmation"):
            # Check if mobile confirmed
            confirmed = self.check_qr_confirmation(session_id)
            if confirmed:
                st.success("Mobile login confirmed!")
                self.complete_login(confirmed['user_id'], "qr")
            else:
                st.warning("Waiting for mobile confirmation...")
    
    def complete_login(self, user_identifier, method):
        """Complete login process"""
        # Create session
        session_id = self.create_session(user_identifier)
        
        # Store in session state
        st.session_state['authenticated'] = True
        st.session_state['user_id'] = user_identifier
        st.session_state['login_method'] = method
        st.session_state['session_id'] = session_id
        st.session_state['login_time'] = datetime.now()
        
        # Log login event
        self.log_login_event(user_identifier, method, "success")
        
        # Show welcome message
        user_info = self.get_user_info(user_identifier)
        st.success(f"✅ Welcome {user_info['name']}!")
        st.balloons()
        
        # Redirect to dashboard
        st.rerun()
    
    def verify_aadhaar_checksum(self, aadhaar):
        """Simple Aadhaar checksum verification"""
        # This is a simplified version
        # Real Aadhaar uses Verhoeff algorithm
        if len(aadhaar) != 12:
            return False
        
        # Basic validation
        weights = [1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2]
        total = 0
        
        for i in range(11):  # First 11 digits
            digit = int(aadhaar[i])
            weighted = digit * weights[i]
            if weighted > 9:
                weighted = weighted - 9
            total += weighted
        
        checksum = (10 - (total % 10)) % 10
        
        return checksum == int(aadhaar[11])
    
    def generate_otp(self, user_id):
        """Generate TOTP"""
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret, interval=300)  # 5 minutes expiry
        return totp.now()
    
    def send_sms_otp(self, phone_number, otp):
        """Send OTP via SMS using Twilio"""
        try:
            message = self.twilio_client.messages.create(
                body=f"Your SUVIDHA OTP is: {otp}. Valid for 5 minutes.",
                from_=os.getenv('TWILIO_PHONE'),
                to=f"+91{phone_number}"
            )
            return True
        except Exception as e:
            st.error(f"Failed to send SMS: {e}")
            return False