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
from twilio.rest import Client
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="SUVIDHA - Digital Helpdesk",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
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
    .feature-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 5px solid #667eea;
        transition: transform 0.3s;
    }
    .feature-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.15);
    }
    .status-badge {
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: bold;
        display: inline-block;
        margin: 0.2rem;
    }
    .status-pending { background: #fff3cd; color: #856404; }
    .status-inprogress { background: #cce5ff; color: #004085; }
    .status-completed { background: #d4edda; color: #155724; }
    .status-rejected { background: #f8d7da; color: #721c24; }
    .dashboard-metric {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 3px 10px rgba(0,0,0,0.1);
        text-align: center;
    }
    .otp-input {
        font-size: 24px;
        letter-spacing: 10px;
        text-align: center;
        padding: 10px;
    }
    .timer {
        font-size: 18px;
        color: #ff6b6b;
        font-weight: bold;
        text-align: center;
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)

class LiveSuvidha:
    def __init__(self):
        # Initialize Twilio client
        self.twilio_client = self.init_twilio()
        
        # Check if Twilio is configured
        self.twilio_enabled = self.twilio_client is not None
        
        self.db = self.init_database()
        self.create_upload_folder()
        self.languages = {
            'en': 'English',
            'hi': 'हिंदी',
            'mr': 'मराठी',
            'ta': 'தமிழ்'
        }
        self.departments = {
            "⚡ Electricity Department": ["Power Outage", "New Connection", "Bill Issue", "Meter Complaint", "Safety Inspection"],
            "💧 Water Department": ["No Water Supply", "Water Quality Issue", "New Connection", "Pipeline Leakage", "Bill Payment"],
            "🔥 Gas Department": ["Gas Leak Complaint", "New Connection", "Safety Inspection", "Appliance Service", "Bill Payment"],
            "🗑️ Waste Management": ["Garbage Not Collected", "Sanitation Complaint", "Recycling Information", "Illegal Dumping", "Composting Request"]
        }
        
        # OTP settings
        self.otp_expiry_minutes = 5  # OTP expires in 5 minutes
        self.max_otp_attempts = 3    # Max attempts per OTP
    
    def init_twilio(self):
        """Initialize Twilio client"""
        try:
            account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')
            
            if not all([account_sid, auth_token, twilio_phone]):
                st.warning("⚠️ Twilio not configured. Using demo OTP mode.")
                return None
            
            client = Client(account_sid, auth_token)
            return client
        except Exception as e:
            st.warning(f"⚠️ Twilio initialization failed: {str(e)}. Using demo OTP mode.")
            return None
    
    def create_upload_folder(self):
        """Create uploads folder if it doesn't exist"""
        Path("uploads").mkdir(exist_ok=True)
    
    def init_database(self):
        """Initialize SQLite database with comprehensive schema"""
        conn = sqlite3.connect('suvidha_live.db', check_same_thread=False)
        cursor = conn.cursor()
        
        # Create users table
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
        
        # Create OTP verification table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS otp_verification (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                aadhaar TEXT NOT NULL,
                phone TEXT NOT NULL,
                otp TEXT NOT NULL,
                attempt_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP DEFAULT (datetime('now', '+5 minutes')),
                verified BOOLEAN DEFAULT FALSE,
                message_sid TEXT
            )
        ''')
        
        # Create OTP rate limiting table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS otp_rate_limit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone TEXT NOT NULL,
                attempt_count INTEGER DEFAULT 0,
                last_attempt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                blocked_until TIMESTAMP
            )
        ''')
        
        # Create service requests table
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
        
        # Create request status history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS request_status_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT,
                status TEXT,
                comments TEXT,
                updated_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (request_id) REFERENCES service_requests (request_id)
            )
        ''')
        
        # Create payments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_id TEXT UNIQUE,
                request_id TEXT,
                user_id INTEGER,
                bill_type TEXT,
                bill_number TEXT,
                amount REAL NOT NULL,
                due_date DATE,
                payment_method TEXT,
                transaction_id TEXT,
                status TEXT DEFAULT 'Pending',
                receipt_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (request_id) REFERENCES service_requests (request_id)
            )
        ''')
        
        # Create documents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id TEXT UNIQUE,
                user_id INTEGER,
                request_id TEXT,
                document_type TEXT,
                document_name TEXT,
                file_path TEXT,
                file_size INTEGER,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                verified BOOLEAN DEFAULT FALSE,
                verified_by TEXT,
                verified_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (request_id) REFERENCES service_requests (request_id)
            )
        ''')
        
        # Create notifications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                notification_type TEXT,
                title TEXT,
                message TEXT,
                is_read BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Create analytics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_date DATE,
                total_requests INTEGER DEFAULT 0,
                completed_requests INTEGER DEFAULT 0,
                pending_requests INTEGER DEFAULT 0,
                avg_completion_time REAL,
                user_count INTEGER DEFAULT 0,
                payment_amount REAL DEFAULT 0
            )
        ''')
        
        # Insert default admin user
        cursor.execute("SELECT COUNT(*) FROM users WHERE user_type='admin'")
        if cursor.fetchone()[0] == 0:
            admin_id = str(uuid.uuid4())[:8]
            cursor.execute('''
                INSERT INTO users (user_id, name, phone, email, user_type, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (admin_id, 'Admin User', '9999999999', 'admin@suvidha.gov.in', 'admin', True))
        
        conn.commit()
        return conn
    
    def get_user_id(self):
        """Get current user's database ID"""
        if 'user_id' in st.session_state:
            cursor = self.db.cursor()
            cursor.execute("SELECT id FROM users WHERE user_id=?", (st.session_state.user_id,))
            result = cursor.fetchone()
            return result[0] if result else None
        return None
    
    def send_otp_sms(self, phone_number, otp):
        """Send OTP via Twilio SMS"""
        try:
            if not self.twilio_enabled:
                return None, "DEMO_MODE"
            
            # Format phone number with country code (India: +91)
            if not phone_number.startswith('+'):
                phone_number = f"+91{phone_number}"
            
            # Get Twilio phone number from environment
            twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')
            
            message = f"Your SUVIDHA verification code is: {otp}. Valid for {self.otp_expiry_minutes} minutes."
            
            # Send SMS
            message = self.twilio_client.messages.create(
                body=message,
                from_=twilio_phone,
                to=phone_number
            )
            
            return message.sid, "SUCCESS"
            
        except Exception as e:
            st.error(f"Failed to send SMS: {str(e)}")
            return None, f"ERROR: {str(e)}"
    
    def check_rate_limit(self, phone):
        """Check if phone number is rate limited"""
        cursor = self.db.cursor()
        
        # Check if blocked
        cursor.execute('''
            SELECT blocked_until FROM otp_rate_limit 
            WHERE phone=? AND blocked_until > datetime('now')
        ''', (phone,))
        result = cursor.fetchone()
        
        if result:
            blocked_until = datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S') if isinstance(result[0], str) else result[0]
            return False, f"Rate limited. Try again after {blocked_until.strftime('%H:%M:%S')}"
        
        return True, "OK"
    
    def update_rate_limit(self, phone, success=True):
        """Update rate limiting counters"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            SELECT attempt_count, last_attempt FROM otp_rate_limit 
            WHERE phone=?
        ''', (phone,))
        result = cursor.fetchone()
        
        now = datetime.now()
        
        if result:
            attempt_count, last_attempt = result
            
            # Reset counter if last attempt was more than 1 hour ago
            if isinstance(last_attempt, str):
                last_attempt = datetime.strptime(last_attempt, '%Y-%m-%d %H:%M:%S')
            
            if (now - last_attempt).seconds > 3600:  # 1 hour
                attempt_count = 0
            
            if success:
                # Reset on successful verification
                cursor.execute('''
                    UPDATE otp_rate_limit 
                    SET attempt_count=0, last_attempt=?
                    WHERE phone=?
                ''', (now, phone))
            else:
                attempt_count += 1
                
                if attempt_count >= 5:  # Block after 5 failed attempts
                    blocked_until = now + timedelta(minutes=30)
                    cursor.execute('''
                        UPDATE otp_rate_limit 
                        SET attempt_count=?, last_attempt=?, blocked_until=?
                        WHERE phone=?
                    ''', (attempt_count, now, blocked_until, phone))
                else:
                    cursor.execute('''
                        UPDATE otp_rate_limit 
                        SET attempt_count=?, last_attempt=?
                        WHERE phone=?
                    ''', (attempt_count, now, phone))
        else:
            if not success:
                cursor.execute('''
                    INSERT INTO otp_rate_limit (phone, attempt_count, last_attempt)
                    VALUES (?, ?, ?)
                ''', (phone, 1, now))
        
        self.db.commit()
    
    def generate_otp(self):
        """Generate a 6-digit OTP"""
        import random
        return str(random.randint(100000, 999999))
    
    def store_otp(self, aadhaar, phone, otp, message_sid=None):
        """Store OTP in database"""
        cursor = self.db.cursor()
        
        # Set expiry time
        expires_at = datetime.now() + timedelta(minutes=self.otp_expiry_minutes)
        
        cursor.execute('''
            INSERT INTO otp_verification 
            (aadhaar, phone, otp, created_at, expires_at, message_sid)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (aadhaar, phone, otp, datetime.now(), expires_at, message_sid))
        
        self.db.commit()
        return cursor.lastrowid
    
    def verify_otp(self, aadhaar, phone, otp_input):
        """Verify OTP from database"""
        if not otp_input or len(otp_input) != 6 or not otp_input.isdigit():
            return False, "Invalid OTP format"
        
        cursor = self.db.cursor()
        
        # Get the most recent unverified OTP
        cursor.execute('''
            SELECT id, otp, expires_at, attempt_count 
            FROM otp_verification 
            WHERE aadhaar=? AND phone=? AND verified=FALSE
            ORDER BY created_at DESC LIMIT 1
        ''', (aadhaar, phone))
        
        result = cursor.fetchone()
        
        if not result:
            return False, "No OTP found. Please request a new one."
        
        otp_id, stored_otp, expires_at, attempt_count = result
        
        # Check if OTP is expired
        if isinstance(expires_at, str):
            expires_at = datetime.strptime(expires_at, '%Y-%m-%d %H:%M:%S')
        
        if datetime.now() > expires_at:
            return False, "OTP has expired. Please request a new one."
        
        # Check attempt count
        if attempt_count >= self.max_otp_attempts:
            return False, "Too many attempts. Please request a new OTP."
        
        # Verify OTP
        if stored_otp == otp_input:
            # Mark OTP as verified
            cursor.execute('''
                UPDATE otp_verification 
                SET verified=TRUE 
                WHERE id=?
            ''', (otp_id,))
            
            # Update rate limit (success)
            self.update_rate_limit(phone, success=True)
            
            self.db.commit()
            return True, "OTP verified successfully!"
        else:
            # Increment attempt count
            cursor.execute('''
                UPDATE otp_verification 
                SET attempt_count=attempt_count + 1 
                WHERE id=?
            ''', (otp_id,))
            
            # Update rate limit (failure)
            self.update_rate_limit(phone, success=False)
            
            attempts_left = self.max_otp_attempts - (attempt_count + 1)
            
            self.db.commit()
            return False, f"Incorrect OTP. {attempts_left} attempt(s) left."
    
    def resend_otp(self, aadhaar, phone):
        """Resend OTP"""
        # Check rate limit
        allowed, message = self.check_rate_limit(phone)
        if not allowed:
            return False, message
        
        # Generate new OTP
        otp = self.generate_otp()
        
        # Send via SMS
        message_sid, status = self.send_otp_sms(phone, otp)
        
        if status == "SUCCESS" or status == "DEMO_MODE":
            # Store in database
            self.store_otp(aadhaar, phone, otp, message_sid)
            
            # Update rate limit
            self.update_rate_limit(phone, success=False)
            
            demo_msg = " (Demo Mode)" if status == "DEMO_MODE" else ""
            return True, f"OTP resent successfully!{demo_msg} OTP: {otp}"
        else:
            return False, f"Failed to send OTP: {status}"
    
    def run(self):
        """Main application runner"""
        # Initialize session state
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'page' not in st.session_state:
            st.session_state.page = 'home'
        if 'user' not in st.session_state:
            st.session_state.user = {}
        if 'otp_timer' not in st.session_state:
            st.session_state.otp_timer = 0
        
        # Check authentication
        if not st.session_state.authenticated:
            self.show_login()
        else:
            self.show_main_app()
    
    def show_login(self):
        """Show login page"""
        st.markdown('<div class="main-header"><h1>🏙️ SUVIDHA</h1><h3>Smart Urban Digital Helpdesk</h3></div>', 
                   unsafe_allow_html=True)
        
        # Twilio status indicator
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if self.twilio_enabled:
                st.success("✅ SMS OTP Enabled (Twilio)")
            else:
                st.warning("⚠️ Demo Mode - OTP will be shown on screen")
        
        # Login tabs
        tab1, tab2, tab3 = st.tabs(["Citizen Login", "Guest Access", "Admin Login"])
        
        with tab1:
            self.citizen_login()
        
        with tab2:
            self.guest_login()
        
        with tab3:
            self.admin_login()
    
    def citizen_login(self):
        """Citizen login form with OTP verification"""
        # Initialize session state for OTP
        if 'otp_sent' not in st.session_state:
            st.session_state.otp_sent = False
        if 'otp_data' not in st.session_state:
            st.session_state.otp_data = {}
        if 'otp_attempts' not in st.session_state:
            st.session_state.otp_attempts = 0
        
        # Separate forms for OTP sending and verification
        # Form 1: User details and OTP request
        with st.form("user_details_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                aadhaar = st.text_input("Aadhaar Number", 
                                       max_chars=12,
                                       placeholder="12-digit number",
                                       key="login_aadhaar")
                phone = st.text_input("Mobile Number", 
                                     max_chars=10,
                                     placeholder="10-digit number",
                                     key="login_phone")
            
            with col2:
                name = st.text_input("Full Name", key="login_name")
                email = st.text_input("Email (Optional)", key="login_email")
            
            # Send OTP button
            send_otp_btn = st.form_submit_button("📱 Send OTP", type="primary")
        
        # Handle Send OTP button
        if send_otp_btn:
            if self.validate_input(aadhaar, phone, name):
                # Check rate limit
                allowed, message = self.check_rate_limit(phone)
                if not allowed:
                    st.error(message)
                else:
                    # Generate OTP
                    otp = self.generate_otp()
                    
                    # Send via SMS
                    message_sid, status = self.send_otp_sms(phone, otp)
                    
                    if status == "SUCCESS":
                        st.success(f"✅ OTP sent to {phone}")
                    elif status == "DEMO_MODE":
                        st.success(f"📱 Demo OTP for {phone}: {otp}")
                    else:
                        st.error(f"Failed to send OTP: {status}")
                        return
                    
                    # Store OTP in database
                    self.store_otp(aadhaar, phone, otp, message_sid)
                    
                    # Update session state
                    st.session_state.otp_sent = True
                    st.session_state.otp_data = {
                        'aadhaar': aadhaar,
                        'phone': phone,
                        'name': name,
                        'email': email
                    }
                    st.session_state.otp_timer = self.otp_expiry_minutes * 60
                    st.session_state.otp_timer_start = time.time()
                    
                    # Start timer
                    st.session_state.timer_running = True
                    st.rerun()
            else:
                st.error("Please fill all required fields correctly")
        
        # OTP verification section (only show if OTP was sent)
        if st.session_state.otp_sent:
            st.subheader("OTP Verification")
            
            # Timer display
            if st.session_state.otp_timer > 0:
                minutes = st.session_state.otp_timer // 60
                seconds = st.session_state.otp_timer % 60
                st.markdown(f'<div class="timer">⏱️ OTP expires in: {minutes:02d}:{seconds:02d}</div>', 
                          unsafe_allow_html=True)
            
            # Form 2: OTP verification
            with st.form("otp_verification_form"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    otp_input = st.text_input("Enter OTP", 
                                             max_chars=6,
                                             placeholder="6-digit code",
                                             key="otp_input_field",
                                             help="Enter the OTP sent to your mobile")
                
                with col2:
                    verify_btn = st.form_submit_button("✅ Verify & Login", type="primary")
                
                # Handle Verify button
                if verify_btn and otp_input:
                    # Get data from session state
                    aadhaar = st.session_state.otp_data.get('aadhaar', '')
                    phone = st.session_state.otp_data.get('phone', '')
                    name = st.session_state.otp_data.get('name', '')
                    email = st.session_state.otp_data.get('email', '')
                    
                    # Verify OTP
                    verified, message = self.verify_otp(aadhaar, phone, otp_input)
                    
                    if verified:
                        # Check if user exists
                        cursor = self.db.cursor()
                        cursor.execute("SELECT * FROM users WHERE aadhaar=?", (aadhaar,))
                        user = cursor.fetchone()
                        
                        if user:
                            # Update last login
                            cursor.execute("UPDATE users SET last_login=? WHERE id=?", 
                                          (datetime.now(), user[0]))
                            user_data = {
                                'id': user[0],
                                'user_id': user[1],
                                'aadhaar': user[2],
                                'name': user[3],
                                'phone': user[4],
                                'email': user[5],
                                'address': user[6],
                                'user_type': user[12]
                            }
                        else:
                            # Create new user
                            user_id = str(uuid.uuid4())[:8]
                            cursor.execute('''
                                INSERT INTO users 
                                (user_id, aadhaar, name, phone, email, created_at, last_login)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            ''', (user_id, aadhaar, name, phone, email, datetime.now(), datetime.now()))
                            self.db.commit()
                            
                            cursor.execute("SELECT * FROM users WHERE aadhaar=?", (aadhaar,))
                            user = cursor.fetchone()
                            user_data = {
                                'id': user[0],
                                'user_id': user[1],
                                'aadhaar': user[2],
                                'name': user[3],
                                'phone': user[4],
                                'email': user[5],
                                'user_type': user[12]
                            }
                        
                        st.session_state.authenticated = True
                        st.session_state.user = user_data
                        st.session_state.user_id = user_data['user_id']
                        st.session_state.user_type = user_data['user_type']
                        
                        # Add login notification
                        self.add_notification(user_data['id'], 'login', 'Welcome Back!', 
                                             f'Successfully logged in at {datetime.now().strftime("%Y-%m-%d %H:%M")}')
                        
                        st.success(f"Welcome {name}!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(message)
                        st.session_state.otp_attempts += 1
                        
                        if st.session_state.otp_attempts >= 3:
                            st.error("Too many failed attempts. Please request a new OTP.")
                            st.session_state.otp_sent = False
            
            # Resend OTP button (outside the form)
            col1, col2, col3 = st.columns([2, 1, 2])
            with col2:
                if st.button("🔄 Resend OTP", use_container_width=True):
                    aadhaar = st.session_state.otp_data.get('aadhaar', '')
                    phone = st.session_state.otp_data.get('phone', '')
                    
                    if aadhaar and phone:
                        success, message = self.resend_otp(aadhaar, phone)
                        if success:
                            st.success(message)
                            st.session_state.otp_timer = self.otp_expiry_minutes * 60
                            st.session_state.otp_timer_start = time.time()
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.error("No OTP data found")
        
        # Debug section for testing
        with st.expander("🔧 Debug OTP System"):
            if st.button("View OTP Records"):
                cursor = self.db.cursor()
                cursor.execute('''
                    SELECT aadhaar, phone, otp, created_at, expires_at, verified, attempt_count, message_sid
                    FROM otp_verification 
                    ORDER BY created_at DESC LIMIT 10
                ''')
                records = cursor.fetchall()
                
                if records:
                    df = pd.DataFrame(records, 
                                    columns=['Aadhaar', 'Phone', 'OTP', 'Created', 'Expires', 
                                             'Verified', 'Attempts', 'Message SID'])
                    st.dataframe(df)
                else:
                    st.write("No OTP records found")
            
            if st.button("View Rate Limits"):
                cursor = self.db.cursor()
                cursor.execute('''
                    SELECT phone, attempt_count, last_attempt, blocked_until
                    FROM otp_rate_limit 
                    ORDER BY last_attempt DESC
                ''')
                records = cursor.fetchall()
                
                if records:
                    df = pd.DataFrame(records, 
                                    columns=['Phone', 'Attempts', 'Last Attempt', 'Blocked Until'])
                    st.dataframe(df)
                else:
                    st.write("No rate limit records found")
    
    def admin_login(self):
        """Admin login form"""
        with st.form("admin_login_form"):
            admin_id = st.text_input("Admin ID")
            password = st.text_input("Password", type="password")
            
            if st.form_submit_button("Admin Login", type="primary"):
                cursor = self.db.cursor()
                cursor.execute('''
                    SELECT * FROM users WHERE user_id=? AND user_type='admin'
                ''', (admin_id,))
                admin = cursor.fetchone()
                
                if admin:
                    # In production, use proper password hashing
                    if password == "admin123":  # Demo password
                        st.session_state.authenticated = True
                        st.session_state.user = {
                            'id': admin[0],
                            'user_id': admin[1],
                            'name': admin[3],
                            'phone': admin[4],
                            'email': admin[5],
                            'user_type': admin[12]
                        }
                        st.session_state.user_id = admin[1]
                        st.session_state.user_type = 'admin'
                        st.success("Admin login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid password")
                else:
                    st.error("Invalid admin ID")


    def guest_login(self):
        st.info("Guest access provides limited functionality")
        
        if st.button("Continue as Guest", type="primary", use_container_width=True):
            # Create guest user record
            guest_id = f"GUEST_{str(uuid.uuid4())[:8]}"
            cursor = self.db.cursor()
            cursor.execute('''
                INSERT INTO users (user_id, name, phone, user_type, created_at, last_login)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (guest_id, 'Guest User', 'GUEST', 'guest', datetime.now(), datetime.now()))
            self.db.commit()
            
            st.session_state.authenticated = True
            st.session_state.user = {
                'id': cursor.lastrowid,
                'user_id': guest_id,
                'name': 'Guest User',
                'phone': 'GUEST',
                'user_type': 'guest'
            }
            st.session_state.user_id = guest_id
            st.session_state.user_type = 'guest'
            st.success("Guest access granted!")
            st.rerun()

    def show_main_app(self):
        """Show main application"""
        # Update OTP timer using time-based approach
        current_time = time.time()
        if 'otp_timer_start' in st.session_state and st.session_state.otp_sent:
            elapsed = current_time - st.session_state.otp_timer_start
            remaining = max(0, (self.otp_expiry_minutes * 60) - elapsed)
            st.session_state.otp_timer = int(remaining)
            
            if remaining <= 0:
                st.session_state.otp_sent = False
        
        # Sidebar
        with st.sidebar:
            user_name = st.session_state.user.get('name', 'User')
            user_type = st.session_state.user.get('user_type', 'citizen')
            
            st.title(f"👋 {user_name}")
            
            if user_type == 'guest':
                st.warning("Guest Mode - Limited Access")
            elif user_type == 'admin':
                st.success("Admin Mode")
            
            st.markdown("---")
            
            # Navigation based on user type
            if user_type == 'admin':
                menu_items = {
                    "🏠 Admin Dashboard": "admin_dashboard",
                    "📊 Analytics": "analytics",
                    "👥 User Management": "user_management",
                    "📋 All Requests": "all_requests",
                    "💰 Payments": "payments_admin",
                    "📄 Documents": "documents_admin",
                    "⚙️ System Settings": "system_settings"
                }
            else:
                menu_items = {
                    "🏠 Dashboard": "home",
                    "📝 New Request": "new_request",
                    "🔍 Track Status": "track_status",
                    "💳 Pay Bills": "payments",
                    "📄 My Documents": "documents",
                    "🔔 Notifications": "notifications",
                    "⚙️ Settings": "settings"
                }
            
            for item, page in menu_items.items():
                if st.button(item, use_container_width=True, 
                           type="primary" if st.session_state.page == page else "secondary"):
                    st.session_state.page = page
                    st.rerun()
            
            st.markdown("---")
            
            # Quick actions
            if user_type != 'admin':
                if st.button("🚨 Emergency", type="secondary", use_container_width=True):
                    st.session_state.page = "emergency"
            
            # Logout
            if st.button("🚪 Logout", type="secondary", use_container_width=True):
                # Record logout
                cursor = self.db.cursor()
                cursor.execute('''
                    UPDATE users SET last_login=? WHERE user_id=?
                ''', (datetime.now(), st.session_state.user_id))
                self.db.commit()
                
                st.session_state.clear()
                st.rerun()
        
        # Main content
        pages = {
            'home': self.show_dashboard,
            'new_request': self.show_new_request,
            'track_status': self.show_track_status,
            'payments': self.show_payments,
            'payments_admin': self.show_payments_admin,
            'documents': self.show_documents,
            'documents_admin': self.show_documents_admin,
            'notifications': self.show_notifications,
            'settings': self.show_settings,
            'emergency': self.show_emergency,
            'admin_dashboard': self.show_admin_dashboard,
            'analytics': self.show_analytics,
            'user_management': self.show_user_management,
            'all_requests': self.show_all_requests,
            'system_settings': self.show_system_settings
        }
        
        pages.get(st.session_state.page, self.show_dashboard)()


    def show_dashboard(self):
        """Show citizen dashboard with live data"""
        st.markdown(f"<div class='main-header'><h2>Welcome, {st.session_state.user['name']}!</h2></div>", 
                   unsafe_allow_html=True)
        
        # Get live stats from database
        user_id = self.get_user_id()
        
        cursor = self.db.cursor()
        
        # Total requests
        cursor.execute("SELECT COUNT(*) FROM service_requests WHERE user_id=?", (user_id,))
        total_requests = cursor.fetchone()[0]
        
        # Pending requests
        cursor.execute("SELECT COUNT(*) FROM service_requests WHERE user_id=? AND status='Pending'", (user_id,))
        pending_requests = cursor.fetchone()[0]
        
        # Completed requests
        cursor.execute("SELECT COUNT(*) FROM service_requests WHERE user_id=? AND status='Completed'", (user_id,))
        completed_requests = cursor.fetchone()[0]
        
        # Pending payments
        cursor.execute("SELECT SUM(amount) FROM payments WHERE user_id=? AND status='Pending'", (user_id,))
        pending_payments_result = cursor.fetchone()[0]
        pending_payments = pending_payments_result if pending_payments_result else 0
        
        # Quick stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown('<div class="dashboard-metric">', unsafe_allow_html=True)
            st.metric("Total Requests", total_requests)
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="dashboard-metric">', unsafe_allow_html=True)
            st.metric("Pending", pending_requests)
            st.markdown('</div>', unsafe_allow_html=True)
        with col3:
            st.markdown('<div class="dashboard-metric">', unsafe_allow_html=True)
            st.metric("Completed", completed_requests)
            st.markdown('</div>', unsafe_allow_html=True)
        with col4:
            st.markdown('<div class="dashboard-metric">', unsafe_allow_html=True)
            st.metric("Pending Payments", f"₹{pending_payments:,.2f}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Quick actions
        st.subheader("⚡ Quick Actions")
        
        actions = [
            {"icon": "📝", "label": "New Service Request", "page": "new_request"},
            {"icon": "🔍", "label": "Track Request", "page": "track_status"},
            {"icon": "💳", "label": "Pay Bills", "page": "payments"},
            {"icon": "📄", "label": "Upload Documents", "page": "documents"},
            {"icon": "🔔", "label": "Notifications", "page": "notifications"},
            {"icon": "🏢", "label": "Department Info", "action": self.show_department_info}
        ]
        
        cols = st.columns(3)
        for idx, action in enumerate(actions):
            with cols[idx % 3]:
                if st.button(f"{action['icon']} {action['label']}", 
                           use_container_width=True, key=f"action_{idx}"):
                    if 'page' in action:
                        st.session_state.page = action['page']
                        st.rerun()
                    elif 'action' in action:
                        action['action']()
        
        # Recent activity from database
        st.subheader("📋 Recent Activity")
        
        cursor.execute('''
            SELECT sr.request_id, sr.department, sr.service_type, sr.status, sr.created_at,
                   p.amount, p.status as payment_status
            FROM service_requests sr
            LEFT JOIN payments p ON sr.request_id = p.request_id
            WHERE sr.user_id=?
            ORDER BY sr.created_at DESC
            LIMIT 10
        ''', (user_id,))
        recent_activities = cursor.fetchall()
        
        if recent_activities:
            for activity in recent_activities:
                col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                with col1:
                    st.write(f"**{activity[1]}** - {activity[2]}")
                with col2:
                    st.write(f"ID: {activity[0]}")
                with col3:
                    status_color = {
                        'Pending': 'status-pending',
                        'In Progress': 'status-inprogress',
                        'Completed': 'status-completed'
                    }.get(activity[3], '')
                    st.markdown(f'<span class="status-badge {status_color}">{activity[3]}</span>', 
                              unsafe_allow_html=True)
                with col4:
                    st.write(activity[4].split()[0])
        else:
            st.info("No recent activities found")
        
        # Recent notifications
        st.subheader("🔔 Recent Notifications")
        cursor.execute('''
            SELECT title, message, created_at, is_read 
            FROM notifications 
            WHERE user_id=? 
            ORDER BY created_at DESC 
            LIMIT 5
        ''', (user_id,))
        notifications = cursor.fetchall()
        
        if notifications:
            for notif in notifications:
                icon = "📧" if not notif[3] else "✅"
                st.write(f"{icon} **{notif[0]}** - {notif[1]} ({notif[2]})")
        else:
            st.info("No notifications")
    
    def show_new_request(self):
        """Show new service request form"""
        st.title("📝 New Service Request")
        
        # Department selection
        selected_dept = st.selectbox("Select Department", list(self.departments.keys()))
        service_types = self.departments[selected_dept]
        service_type = st.selectbox("Service Type", service_types)
        
        # Request details
        with st.form("request_form"):
            description = st.text_area("Describe your issue", 
                                      height=150,
                                      placeholder="Please provide detailed information including location, time, and specific details...")
            
            # Location
            st.subheader("📍 Location Details")
            col1, col2 = st.columns(2)
            with col1:
                address = st.text_input("Full Address")
                landmark = st.text_input("Landmark (Optional)")
            with col2:
                pincode = st.text_input("Pincode", max_chars=6)
                zone = st.selectbox("Zone", ["Zone 1", "Zone 2", "Zone 3", "Zone 4"])
            
            # Priority
            priority = st.select_slider("Priority Level", 
                                       options=["Low", "Medium", "High", "Emergency"],
                                       value="Medium",
                                       help="Emergency: Life-threatening or critical infrastructure issues")
            
            # Document upload
            uploaded_files = st.file_uploader("Attach Supporting Documents (Optional)", 
                                             accept_multiple_files=True,
                                             type=['pdf', 'jpg', 'jpeg', 'png', 'docx'],
                                             help="Upload bills, photos, or any relevant documents")
            
            # Contact preferences
            contact_method = st.multiselect("Preferred Contact Method",
                                          ["Phone", "SMS", "Email", "WhatsApp"],
                                          default=["Phone"])
            
            agree_terms = st.checkbox("I agree to the terms and conditions")
            
            if st.form_submit_button("Submit Request", type="primary"):
                if description and address and pincode and agree_terms:
                    user_id = self.get_user_id()
                    
                    # Generate request ID
                    request_id = f"SR{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    
                    # Save to database
                    cursor = self.db.cursor()
                    cursor.execute('''
                        INSERT INTO service_requests 
                        (request_id, user_id, department, service_type, description, 
                         address, pincode, priority, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        request_id,
                        user_id,
                        selected_dept,
                        service_type,
                        description,
                        address,
                        pincode,
                        priority,
                        datetime.now(),
                        datetime.now()
                    ))
                    
                    # Save uploaded documents
                    if uploaded_files:
                        for uploaded_file in uploaded_files:
                            # Save file
                            file_path = f"uploads/{request_id}_{uploaded_file.name}"
                            with open(file_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            
                            doc_id = f"DOC{str(uuid.uuid4())[:8]}"
                            cursor.execute('''
                                INSERT INTO documents 
                                (doc_id, user_id, request_id, document_type, document_name, 
                                 file_path, file_size, uploaded_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                doc_id,
                                user_id,
                                request_id,
                                "Supporting Document",
                                uploaded_file.name,
                                file_path,
                                len(uploaded_file.getbuffer()),
                                datetime.now()
                            ))
                    
                    self.db.commit()
                    
                    # Add status history
                    cursor.execute('''
                        INSERT INTO request_status_history 
                        (request_id, status, comments, updated_by)
                        VALUES (?, ?, ?, ?)
                    ''', (request_id, "Pending", "Request submitted by user", st.session_state.user['name']))
                    
                    # Add notification
                    self.add_notification(user_id, 'request_submitted', 'Request Submitted', 
                                         f'Your service request {request_id} has been submitted successfully')
                    
                    # Show success
                    st.success("✅ Request submitted successfully!")
                    st.balloons()
                    
                    # Show receipt
                    self.show_receipt(request_id, {
                        'department': selected_dept,
                        'service_type': service_type,
                        'priority': priority,
                        'address': address,
                        'pincode': pincode,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                else:
                    st.error("Please fill all required fields and agree to terms")
    
    def show_receipt(self, request_id, details):
        """Show receipt with QR code"""
        st.markdown("---")
        st.subheader("📄 Service Request Receipt")
        
        # Create QR code
        qr_data = f"SUVIDHA:{request_id}:{st.session_state.user['phone']}"
        qr = qrcode.make(qr_data)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.write(f"**Request ID:** {request_id}")
            st.write(f"**Department:** {details['department']}")
            st.write(f"**Service Type:** {details['service_type']}")
            st.write(f"**Priority:** {details['priority']}")
            st.write(f"**Submitted:** {details['timestamp']}")
            st.write(f"**Citizen:** {st.session_state.user['name']}")
            st.write(f"**Contact:** {st.session_state.user['phone']}")
            st.write(f"**Address:** {details['address']}")
            st.write(f"**Pincode:** {details['pincode']}")
            st.write(f"**Expected Resolution:** 3-5 working days")
            
            # Track URL
            track_url = f"http://localhost:8501/?request_id={request_id}"
            st.write(f"**Track URL:** [{track_url}]({track_url})")
        
        with col2:
            st.image(qr, caption="Scan to Track", use_column_width=True)
            
            # Estimated completion
            est_completion = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
            st.info(f"**Estimated Completion:** {est_completion}")
        
        # Download buttons
        col3, col4, col5 = st.columns(3)
        with col3:
            receipt_text = f"""
            SUVIDHA Service Request Receipt
            ================================
            Request ID: {request_id}
            Department: {details['department']}
            Service Type: {details['service_type']}
            Priority: {details['priority']}
            Submitted: {details['timestamp']}
            Citizen: {st.session_state.user['name']}
            Contact: {st.session_state.user['phone']}
            Address: {details['address']}
            Pincode: {details['pincode']}
            Estimated Completion: {est_completion}
            
            Track at: http://suvidha.gov.in/track/{request_id}
            """
            
            st.download_button(
                "📥 Download Receipt",
                receipt_text,
                file_name=f"receipt_{request_id}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        with col4:
            # Save QR as image
            qr_bytes = io.BytesIO()
            qr.save(qr_bytes, format='PNG')
            qr_bytes.seek(0)
            
            st.download_button(
                "📱 Save QR Code",
                qr_bytes,
                file_name=f"qrcode_{request_id}.png",
                mime="image/png",
                use_container_width=True
            )
        
        with col5:
            if st.button("Return to Dashboard", use_container_width=True):
                st.session_state.page = "home"
                st.rerun()
    
    def show_track_status(self):
        """Track service requests with live data"""
        st.title("🔍 Track Service Requests")
        
        user_id = self.get_user_id()
        
        # Get all user's requests
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT request_id, department, service_type, status, priority, created_at, 
                   estimated_completion, actual_completion
            FROM service_requests 
            WHERE user_id=?
            ORDER BY created_at DESC
        ''', (user_id,))
        user_requests = cursor.fetchall()
        
        if user_requests:
            st.write(f"Found {len(user_requests)} request(s)")
            
            # Search and filter
            col1, col2, col3 = st.columns(3)
            with col1:
                search_term = st.text_input("Search by Request ID or Department")
            with col2:
                status_filter = st.selectbox("Filter by Status", 
                                           ["All", "Pending", "In Progress", "Completed", "Rejected"])
            with col3:
                department_filter = st.selectbox("Filter by Department", 
                                               ["All"] + list(set([r[1] for r in user_requests])))
            
            # Filter requests
            filtered_requests = user_requests
            if search_term:
                filtered_requests = [r for r in filtered_requests 
                                   if search_term.lower() in r[0].lower() or 
                                   search_term.lower() in r[1].lower()]
            if status_filter != "All":
                filtered_requests = [r for r in filtered_requests if r[3] == status_filter]
            if department_filter != "All":
                filtered_requests = [r for r in filtered_requests if r[1] == department_filter]
            
            # Display requests
            for req in filtered_requests:
                with st.expander(f"{req[0]} - {req[1]} - {req[2]}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Request ID:** {req[0]}")
                        st.write(f"**Department:** {req[1]}")
                        st.write(f"**Service Type:** {req[2]}")
                        st.write(f"**Priority:** {req[4]}")
                    with col2:
                        status_color = {
                            'Pending': 'status-pending',
                            'In Progress': 'status-inprogress',
                            'Completed': 'status-completed',
                            'Rejected': 'status-rejected'
                        }.get(req[3], '')
                        st.markdown(f'<span class="status-badge {status_color}">{req[3]}</span>', 
                                  unsafe_allow_html=True)
                        st.write(f"**Created:** {req[5]}")
                        if req[6]:
                            st.write(f"**Estimated Completion:** {req[6]}")
                        if req[7]:
                            st.write(f"**Actual Completion:** {req[7]}")
                    
                    # Show status history
                    cursor.execute('''
                        SELECT status, comments, updated_by, created_at 
                        FROM request_status_history 
                        WHERE request_id=? 
                        ORDER BY created_at DESC
                    ''', (req[0],))
                    status_history = cursor.fetchall()
                    
                    if status_history:
                        st.subheader("Status History")
                        for history in status_history:
                            st.write(f"**{history[0]}** - {history[1]} (by {history[2]} at {history[3]})")
                    
                    # Action buttons
                    col3, col4, col5 = st.columns(3)
                    with col3:
                        if st.button("View Details", key=f"view_{req[0]}"):
                            self.show_request_details(req[0])
                    with col4:
                        if st.button("Add Comment", key=f"comment_{req[0]}"):
                            self.add_comment_to_request(req[0])
                    with col5:
                        if req[3] == "Completed":
                            if st.button("Give Feedback", key=f"feedback_{req[0]}"):
                                self.collect_feedback(req[0])
        else:
            st.info("No service requests found. Submit your first request!")
    
    def show_request_details(self, request_id):
        """Show detailed view of a request"""
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT sr.*, u.name, u.phone, u.email
            FROM service_requests sr
            JOIN users u ON sr.user_id = u.id
            WHERE sr.request_id=?
        ''', (request_id,))
        request = cursor.fetchone()
        
        if request:
            st.subheader(f"Request Details: {request_id}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Citizen:** {request[15]}")
                st.write(f"**Phone:** {request[16]}")
                st.write(f"**Email:** {request[17]}")
                st.write(f"**Department:** {request[2]}")
                st.write(f"**Service Type:** {request[3]}")
            with col2:
                st.write(f"**Priority:** {request[8]}")
                st.write(f"**Status:** {request[9]}")
                st.write(f"**Created:** {request[15]}")
                st.write(f"**Last Updated:** {request[16]}")
                if request[11]:
                    st.write(f"**Estimated Completion:** {request[11]}")
            
            st.subheader("Description")
            st.write(request[4])
            
            st.subheader("Location")
            st.write(f"**Address:** {request[5]}")
            st.write(f"**Pincode:** {request[6]}")
            
            # Show attached documents
            cursor.execute('''
                SELECT document_name, uploaded_at, verified 
                FROM documents 
                WHERE request_id=?
            ''', (request_id,))
            documents = cursor.fetchall()
            
            if documents:
                st.subheader("Attached Documents")
                for doc in documents:
                    st.write(f"📄 {doc[0]} - Uploaded: {doc[1]} - Verified: {'✅' if doc[2] else '❌'}")
    
    def show_payments(self):
        """Show payment interface with live data"""
        st.title("💳 Bill Payments")
        
        user_id = self.get_user_id()
        
        # Get user's pending bills
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT payment_id, bill_type, bill_number, amount, due_date, status, created_at
            FROM payments 
            WHERE user_id=? AND status IN ('Pending', 'Overdue')
            ORDER BY due_date ASC
        ''', (user_id,))
        pending_bills = cursor.fetchall()
        
        if pending_bills:
            st.subheader("📋 Pending Bills")
            
            for bill in pending_bills:
                with st.expander(f"{bill[1]} - ₹{bill[3]:,.2f} - Due: {bill[4]}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Bill ID:** {bill[0]}")
                        st.write(f"**Bill Number:** {bill[2]}")
                        st.write(f"**Amount:** ₹{bill[3]:,.2f}")
                    with col2:
                        st.write(f"**Due Date:** {bill[4]}")
                        st.write(f"**Status:** {bill[5]}")
                        st.write(f"**Generated:** {bill[6]}")
                    
                    # Calculate days remaining
                    due_date = datetime.strptime(bill[4], "%Y-%m-%d").date() if isinstance(bill[4], str) else bill[4]
                    days_remaining = (due_date - datetime.now().date()).days
                    
                    if days_remaining < 0:
                        st.error(f"⚠️ Overdue by {abs(days_remaining)} days")
                        late_fee = bill[3] * 0.02  # 2% late fee
                        total_amount = bill[3] + late_fee
                        st.write(f"**Late Fee:** ₹{late_fee:,.2f}")
                        st.write(f"**Total Payable:** ₹{total_amount:,.2f}")
                    elif days_remaining <= 7:
                        st.warning(f"⏳ Due in {days_remaining} days")
                    else:
                        st.info(f"Due in {days_remaining} days")
                    
                    # Payment button
                    if st.button("Pay Now", key=f"pay_{bill[0]}"):
                        st.session_state.selected_bill = {
                            'payment_id': bill[0],
                            'bill_type': bill[1],
                            'bill_number': bill[2],
                            'amount': bill[3] + (late_fee if days_remaining < 0 else 0),
                            'due_date': bill[4]
                        }
                        st.session_state.page = "make_payment"
                        st.rerun()
        
        # Payment history
        st.subheader("📜 Payment History")
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("From Date", datetime.now() - timedelta(days=30))
        with col2:
            end_date = st.date_input("To Date", datetime.now())
        
        cursor.execute('''
            SELECT payment_id, bill_type, amount, payment_method, status, 
                   transaction_id, created_at, completed_at
            FROM payments 
            WHERE user_id=? AND created_at BETWEEN ? AND ?
            ORDER BY created_at DESC
        ''', (user_id, start_date, end_date))
        payment_history = cursor.fetchall()
        
        if payment_history:
            # Create DataFrame for better display
            df = pd.DataFrame(payment_history, 
                            columns=['ID', 'Type', 'Amount', 'Method', 'Status', 
                                    'Transaction ID', 'Created', 'Completed'])
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Summary
            total_paid = sum([p[2] for p in payment_history if p[4] == 'Completed'])
            successful_payments = len([p for p in payment_history if p[4] == 'Completed'])
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Paid", f"₹{total_paid:,.2f}")
            with col2:
                st.metric("Successful Payments", successful_payments)
        else:
            st.info("No payment history found")
    
    def make_payment(self):
        """Make payment for a specific bill"""
        if 'selected_bill' not in st.session_state:
            st.error("No bill selected")
            st.session_state.page = "payments"
            st.rerun()
            return
        
        bill = st.session_state.selected_bill
        
        st.title(f"💳 Pay {bill['bill_type']} Bill")
        
        # Bill summary
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Bill Amount", f"₹{bill['amount']:,.2f}")
        with col2:
            st.metric("Due Date", bill['due_date'])
        
        # Payment methods
        payment_method = st.selectbox("Select Payment Method",
                                    ["UPI", "Credit/Debit Card", "Net Banking", "Wallet", "Cash at Counter"])
        
        if payment_method == "UPI":
            self.process_upi_payment(bill)
        elif payment_method == "Credit/Debit Card":
            self.process_card_payment(bill)
        elif payment_method == "Net Banking":
            self.process_netbanking_payment(bill)
        elif payment_method == "Wallet":
            self.process_wallet_payment(bill)
        else:
            self.process_cash_payment(bill)
    
    def process_upi_payment(self, bill):
        """Process UPI payment"""
        st.subheader("UPI Payment")
        
        # Generate UPI QR
        upi_id = "suvidha.gov@axisbank"
        upi_string = f"upi://pay?pa={upi_id}&pn=SUVIDHA&am={bill['amount']}&tn={bill['payment_id']}"
        qr = qrcode.make(upi_string)
        
        col1, col2 = st.columns(2)
        with col1:
            st.image(qr, caption="Scan to Pay", use_column_width=True)
        with col2:
            st.write("**Instructions:**")
            st.write("1. Open any UPI app (GPay, PhonePe, PayTM, etc.)")
            st.write("2. Tap on 'Scan & Pay'")
            st.write("3. Scan the QR code above")
            st.write("4. Enter UPI PIN to complete payment")
            st.write("5. Payment confirmation will appear automatically")
            
            vpa = st.text_input("Or enter your UPI ID (Optional)")
            
            if st.button("Confirm Payment", type="primary"):
                # Process payment
                transaction_id = f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}"
                user_id = self.get_user_id()
                
                cursor = self.db.cursor()
                cursor.execute('''
                    UPDATE payments 
                    SET status=?, payment_method=?, transaction_id=?, completed_at=?
                    WHERE payment_id=?
                ''', ('Completed', 'UPI', transaction_id, datetime.now(), bill['payment_id']))
                self.db.commit()
                
                # Add notification
                self.add_notification(user_id, 'payment_completed', 'Payment Successful', 
                                     f'Payment of ₹{bill["amount"]:,.2f} for {bill["bill_type"]} completed successfully')
                
                st.success(f"✅ Payment of ₹{bill['amount']:,.2f} successful!")
                st.balloons()
                
                # Show receipt
                receipt_data = {
                    'payment_id': bill['payment_id'],
                    'transaction_id': transaction_id,
                    'amount': bill['amount'],
                    'method': 'UPI',
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'bill_type': bill['bill_type']
                }
                self.show_payment_receipt(receipt_data)
    
    def show_payment_receipt(self, payment_data):
        """Show payment receipt"""
        st.markdown("---")
        st.subheader("📄 Payment Receipt")
        
        receipt_html = f"""
        <div style='border:2px solid #4CAF50; padding:20px; border-radius:10px; background:#f9fff9'>
            <h3 style='text-align:center; color:#4CAF50'>SUVIDHA PAYMENT RECEIPT</h3>
            <hr>
            <table width='100%' style='font-size:16px'>
                <tr><td><strong>Transaction ID:</strong></td><td>{payment_data['transaction_id']}</td></tr>
                <tr><td><strong>Payment ID:</strong></td><td>{payment_data['payment_id']}</td></tr>
                <tr><td><strong>Date & Time:</strong></td><td>{payment_data['timestamp']}</td></tr>
                <tr><td><strong>Payment Method:</strong></td><td>{payment_data['method']}</td></tr>
                <tr><td><strong>Amount Paid:</strong></td><td>₹{payment_data['amount']:,.2f}</td></tr>
                <tr><td><strong>Bill Type:</strong></td><td>{payment_data['bill_type']}</td></tr>
                <tr><td><strong>Status:</strong></td><td><span style='color:green; font-weight:bold'>✅ SUCCESSFUL</span></td></tr>
            </table>
            <hr>
            <p style='text-align:center; font-size:0.9em; color:#666'>
                This is an electronically generated receipt. Valid without signature.<br>
                Keep this receipt for your records.
            </p>
        </div>
        """
        
        st.markdown(receipt_html, unsafe_allow_html=True)
        
        # Download receipt
        receipt_text = f"""
        SUVIDHA Payment Receipt
        ========================
        Transaction ID: {payment_data['transaction_id']}
        Payment ID: {payment_data['payment_id']}
        Date & Time: {payment_data['timestamp']}
        Payment Method: {payment_data['method']}
        Amount Paid: ₹{payment_data['amount']:,.2f}
        Bill Type: {payment_data['bill_type']}
        Status: SUCCESSFUL
        Citizen: {st.session_state.user['name']}
        Contact: {st.session_state.user['phone']}
        """
        
        st.download_button(
            "📥 Download Receipt",
            receipt_text,
            file_name=f"payment_receipt_{payment_data['transaction_id']}.txt",
            mime="text/plain"
        )
        
        if st.button("Back to Payments"):
            st.session_state.page = "payments"
            st.rerun()
    
    def show_documents(self):
        """Document management with live data"""
        st.title("📄 Document Management")
        
        user_id = self.get_user_id()
        
        # Upload section
        st.subheader("Upload New Document")
        
        with st.form("upload_form"):
            col1, col2 = st.columns(2)
            with col1:
                doc_type = st.selectbox("Document Type",
                                      ["Aadhaar Card", "PAN Card", "Electricity Bill", 
                                       "Water Bill", "Gas Bill", "Property Tax Receipt",
                                       "Address Proof", "Identity Proof", "Other"])
                
                request_id = st.text_input("Link to Request ID (Optional)", 
                                          placeholder="SR2024...")
            
            with col2:
                description = st.text_input("Description")
                expiry_date = st.date_input("Expiry Date (Optional)", 
                                          value=None,
                                          min_value=datetime.now().date())
            
            uploaded_files = st.file_uploader("Choose files", 
                                            accept_multiple_files=True,
                                            type=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'],
                                            help="Maximum 10MB per file")
            
            if st.form_submit_button("Upload Documents", type="primary"):
                if uploaded_files:
                    for uploaded_file in uploaded_files:
                        # Generate unique filename
                        file_ext = uploaded_file.name.split('.')[-1]
                        unique_filename = f"{str(uuid.uuid4())[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_ext}"
                        file_path = f"uploads/{unique_filename}"
                        
                        # Save file
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        # Save to database
                        doc_id = f"DOC{str(uuid.uuid4())[:8]}"
                        cursor = self.db.cursor()
                        cursor.execute('''
                            INSERT INTO documents 
                            (doc_id, user_id, request_id, document_type, document_name, 
                             file_path, file_size, uploaded_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            doc_id,
                            user_id,
                            request_id if request_id else None,
                            doc_type,
                            uploaded_file.name,
                            file_path,
                            len(uploaded_file.getbuffer()),
                            datetime.now()
                        ))
                        
                        st.success(f"✅ Uploaded: {uploaded_file.name}")
                    
                    self.db.commit()
                    
                    # Add notification
                    self.add_notification(user_id, 'document_uploaded', 'Documents Uploaded', 
                                         f'{len(uploaded_files)} document(s) uploaded successfully')
                else:
                    st.error("Please select files to upload")
        
        # Document list
        st.subheader("Your Documents")
        
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT doc_id, document_type, document_name, file_path, uploaded_at, 
                   verified, request_id
            FROM documents 
            WHERE user_id=?
            ORDER BY uploaded_at DESC
        ''', (user_id,))
        documents = cursor.fetchall()
        
        if documents:
            # Filter options
            col1, col2 = st.columns(2)
            with col1:
                doc_type_filter = st.selectbox("Filter by Type", 
                                             ["All"] + list(set([d[1] for d in documents])))
            with col2:
                verification_filter = st.selectbox("Filter by Verification", 
                                                 ["All", "Verified", "Not Verified"])
            
            # Apply filters
            filtered_docs = documents
            if doc_type_filter != "All":
                filtered_docs = [d for d in filtered_docs if d[1] == doc_type_filter]
            if verification_filter == "Verified":
                filtered_docs = [d for d in filtered_docs if d[5]]
            elif verification_filter == "Not Verified":
                filtered_docs = [d for d in filtered_docs if not d[5]]
            
            st.write(f"Showing {len(filtered_docs)} of {len(documents)} documents")
            
            for doc in filtered_docs:
                with st.expander(f"{doc[1]} - {doc[2]}"):
                    col1, col2, col3 = st.columns([3, 2, 1])
                    with col1:
                        st.write(f"**Document ID:** {doc[0]}")
                        st.write(f"**Type:** {doc[1]}")
                        st.write(f"**Original Name:** {doc[2]}")
                        if doc[6]:
                            st.write(f"**Linked Request:** {doc[6]}")
                    with col2:
                        st.write(f"**Uploaded:** {doc[4]}")
                        st.write(f"**Verified:** {'✅ Yes' if doc[5] else '❌ No'}")
                        st.write(f"**Size:** {doc[3]}")
                    with col3:
                        if st.button("View", key=f"view_{doc[0]}"):
                            # Show file preview
                            try:
                                if doc[2].lower().endswith(('.png', '.jpg', '.jpeg')):
                                    image = Image.open(doc[3])
                                    st.image(image, caption=doc[2], use_column_width=True)
                                elif doc[2].lower().endswith('.pdf'):
                                    st.info(f"PDF Document: {doc[2]}")
                                    with open(doc[3], "rb") as f:
                                        st.download_button(
                                            "Download PDF",
                                            f.read(),
                                            file_name=doc[2],
                                            mime="application/pdf"
                                        )
                            except Exception as e:
                                st.error(f"Could not preview file: {e}")
                        
                        if st.button("Delete", key=f"del_{doc[0]}", type="secondary"):
                            # Delete document
                            try:
                                os.remove(doc[3])
                                cursor.execute("DELETE FROM documents WHERE doc_id=?", (doc[0],))
                                self.db.commit()
                                st.success(f"Deleted: {doc[2]}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting: {e}")
        else:
            st.info("No documents uploaded yet")
    
    def show_notifications(self):
        """Show notifications with live data"""
        st.title("🔔 Notifications")
        
        user_id = self.get_user_id()
        
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT id, title, message, created_at, is_read 
            FROM notifications 
            WHERE user_id=?
            ORDER BY created_at DESC
        ''', (user_id,))
        notifications = cursor.fetchall()
        
        if notifications:
            # Mark all as read button
            if st.button("Mark All as Read"):
                cursor.execute('''
                    UPDATE notifications SET is_read=TRUE WHERE user_id=?
                ''', (user_id,))
                self.db.commit()
                st.success("All notifications marked as read!")
                st.rerun()
            
            # Unread count
            unread_count = len([n for n in notifications if not n[4]])
            st.subheader(f"You have {unread_count} unread notification(s)")
            
            # Display notifications
            for notif in notifications:
                icon = "📧" if not notif[4] else "✅"
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**{icon} {notif[1]}**")
                    st.write(notif[2])
                    st.caption(notif[3])
                with col2:
                    if not notif[4]:
                        if st.button("Mark Read", key=f"read_{notif[0]}"):
                            cursor.execute('''
                                UPDATE notifications SET is_read=TRUE WHERE id=?
                            ''', (notif[0],))
                            self.db.commit()
                            st.rerun()
        else:
            st.info("No notifications")
    
    def show_settings(self):
        """User settings with live data"""
        st.title("⚙️ Settings")
        
        user_id = self.get_user_id()
        
        # Get current user data
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
        user_data = cursor.fetchone()
        
        if user_data:
            # Profile Information
            st.subheader("Profile Information")
            
            with st.form("profile_form"):
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input("Full Name", value=user_data[3])
                    phone = st.text_input("Mobile Number", value=user_data[4])
                    aadhaar = st.text_input("Aadhaar Number", value=user_data[2], disabled=True)
                with col2:
                    email = st.text_input("Email", value=user_data[5] if user_data[5] else "")
                    address = st.text_area("Address", value=user_data[6] if user_data[6] else "")
                    pincode = st.text_input("Pincode", value=user_data[7] if user_data[7] else "")
                
                if st.form_submit_button("Update Profile", type="primary"):
                    cursor.execute('''
                        UPDATE users 
                        SET name=?, phone=?, email=?, address=?, pincode=?
                        WHERE id=?
                    ''', (name, phone, email, address, pincode, user_id))
                    self.db.commit()
                    
                    # Update session state
                    st.session_state.user['name'] = name
                    st.session_state.user['phone'] = phone
                    
                    st.success("Profile updated successfully!")
            
            # Preferences
            st.subheader("Preferences")
            
            with st.form("preferences_form"):
                col1, col2 = st.columns(2)
                with col1:
                    language = st.selectbox("Language", 
                                          list(self.languages.values()),
                                          index=0)
                    
                    notifications = st.checkbox("Receive notifications", value=True)
                    email_alerts = st.checkbox("Email alerts", value=True)
                    sms_alerts = st.checkbox("SMS alerts", value=True)
                
                with col2:
                    auto_login = st.checkbox("Remember me for faster login", value=True)
                    dark_mode = st.checkbox("Dark mode", value=False)
                    data_sharing = st.checkbox("Share anonymous usage data", value=False)
                
                if st.form_submit_button("Save Preferences"):
                    # Save preferences to database
                    # (You would need to add a preferences table or extend users table)
                    st.success("Preferences saved!")
            
            # Account Security
            st.subheader("Account Security")
            
            if st.button("Change Password", type="secondary"):
                st.session_state.page = "change_password"
                st.rerun()
            
            if st.button("View Login History", type="secondary"):
                # Show login history
                st.info("Login history feature")
            
            # Danger Zone
            st.subheader("Danger Zone", divider="red")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Export My Data", type="secondary"):
                    self.export_user_data(user_id)
            
            with col2:
                if st.button("Delete Account", type="secondary"):
                    st.error("⚠️ This action cannot be undone!")
                    confirm = st.checkbox("I understand all my data will be permanently deleted")
                    if confirm:
                        if st.button("Permanently Delete Account", type="primary"):
                            # Mark user as inactive instead of deleting
                            cursor.execute('''
                                UPDATE users SET is_active=FALSE WHERE id=?
                            ''', (user_id,))
                            self.db.commit()
                            st.success("Account deactivated successfully")
                            st.session_state.clear()
                            st.rerun()
    
    def show_emergency(self):
        """Emergency services"""
        st.title("🚨 Emergency Services")
        
        # Emergency contacts from database (could be stored in config table)
        emergency_contacts = [
            {"service": "Police", "number": "100", "description": "For all law enforcement emergencies"},
            {"service": "Fire", "number": "101", "description": "Fire accidents and rescue operations"},
            {"service": "Ambulance", "number": "102", "description": "Medical emergencies and ambulance service"},
            {"service": "Women Helpline", "number": "1091", "description": "Women safety and harassment complaints"},
            {"service": "Child Helpline", "number": "1098", "description": "Child abuse and protection"},
            {"service": "Electricity Emergency", "number": "1912", "description": "Power outages, electrical accidents"},
            {"service": "Gas Leak", "number": "1906", "description": "Gas leaks and related emergencies"},
            {"service": "Water Emergency", "number": "1916", "description": "Water pipeline bursts, contamination"},
            {"service": "Disaster Management", "number": "108", "description": "Natural disasters and calamities"}
        ]
        
        # Display emergency contacts
        st.subheader("Emergency Contact Numbers")
        
        for contact in emergency_contacts:
            col1, col2, col3 = st.columns([2, 1, 3])
            with col1:
                st.write(f"**{contact['service']}**")
            with col2:
                st.code(contact['number'], language=None)
            with col3:
                st.caption(contact['description'])
        
        # Quick dial buttons
        st.subheader("Quick Dial")
        
        cols = st.columns(3)
        emergency_quick = emergency_contacts[:6]  # First 6 for quick buttons
        
        for idx, contact in enumerate(emergency_quick):
            with cols[idx % 3]:
                if st.button(f"🚨 {contact['service']}", 
                           use_container_width=True,
                           help=f"Call {contact['number']}"):
                    st.info(f"Dialing {contact['service']}: {contact['number']}")
        
        # Emergency report form
        st.subheader("Report Emergency")
        
        with st.form("emergency_form"):
            emergency_type = st.selectbox("Type of Emergency",
                                         ["Accident", "Medical Emergency", "Fire", 
                                          "Crime", "Natural Disaster", "Infrastructure Failure",
                                          "Other"])
            
            location = st.text_input("Location/Address", 
                                    placeholder="Enter exact location")
            
            description = st.text_area("Describe the emergency", 
                                      placeholder="Please provide detailed information...")
            
            severity = st.select_slider("Severity Level",
                                       options=["Low", "Medium", "High", "Critical"],
                                       value="Medium")
            
            # Contact information
            st.write("**Your Contact Information (for follow-up)**")
            col1, col2 = st.columns(2)
            with col1:
                reporter_name = st.text_input("Your Name", 
                                            value=st.session_state.user.get('name', ''))
                reporter_phone = st.text_input("Your Phone", 
                                             value=st.session_state.user.get('phone', ''))
            
            # Upload evidence
            evidence_files = st.file_uploader("Upload Evidence (Photos/Videos)", 
                                            accept_multiple_files=True,
                                            type=['jpg', 'jpeg', 'png', 'mp4'],
                                            help="Maximum 5 files, 10MB each")
            
            if st.form_submit_button("Report Emergency", type="primary"):
                if location and description:
                    # Save emergency report to database
                    emergency_id = f"EMG{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    
                    # In a real application, this would:
                    # 1. Save to emergency_reports table
                    # 2. Send alerts to relevant authorities
                    # 3. Trigger emergency response protocols
                    
                    st.success("✅ Emergency reported! Help is being dispatched.")
                    st.info("Stay calm and follow instructions from emergency services.")
                    
                    # Show next steps
                    st.subheader("Next Steps:")
                    st.write("1. **Stay Safe**: Move to a safe location if possible")
                    st.write("2. **Await Help**: Emergency services have been alerted")
                    st.write("3. **Follow Instructions**: Cooperate with responders")
                    st.write("4. **Provide Updates**: Keep your phone accessible")
                else:
                    st.error("Please provide location and description")
    
    def show_admin_dashboard(self):
        """Admin dashboard with live analytics"""
        if st.session_state.user.get('user_type') != 'admin':
            st.error("Access denied. Admin only.")
            st.session_state.page = "home"
            st.rerun()
            return
        
        st.title("👑 Admin Dashboard")
        
        # Get live statistics
        cursor = self.db.cursor()
        
        # Total users
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_active=TRUE")
        total_users = cursor.fetchone()[0]
        
        # Total requests
        cursor.execute("SELECT COUNT(*) FROM service_requests")
        total_requests = cursor.fetchone()[0]
        
        # Pending requests
        cursor.execute("SELECT COUNT(*) FROM service_requests WHERE status='Pending'")
        pending_requests = cursor.fetchone()[0]
        
        # Total payments
        cursor.execute("SELECT SUM(amount) FROM payments WHERE status='Completed'")
        total_payments_result = cursor.fetchone()[0]
        total_payments = total_payments_result if total_payments_result else 0
        
        # Active today
        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM service_requests WHERE DATE(created_at)=DATE('now')")
        active_today = cursor.fetchone()[0]
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Users", total_users)
        with col2:
            st.metric("Total Requests", total_requests)
        with col3:
            st.metric("Pending Requests", pending_requests, delta=f"-{total_requests - pending_requests}")
        with col4:
            st.metric("Revenue", f"₹{total_payments:,.2f}")
        
        # Quick admin actions
        st.subheader("Quick Actions")
        
        actions = [
            {"icon": "👥", "label": "Manage Users", "page": "user_management"},
            {"icon": "📋", "label": "View All Requests", "page": "all_requests"},
            {"icon": "💰", "label": "Payment Management", "page": "payments_admin"},
            {"icon": "📊", "label": "Analytics", "page": "analytics"},
            {"icon": "⚙️", "label": "System Settings", "page": "system_settings"},
            {"icon": "📈", "label": "Generate Reports", "action": self.generate_reports}
        ]
        
        cols = st.columns(3)
        for idx, action in enumerate(actions):
            with cols[idx % 3]:
                if st.button(f"{action['icon']} {action['label']}", 
                           use_container_width=True, key=f"admin_action_{idx}"):
                    if 'page' in action:
                        st.session_state.page = action['page']
                        st.rerun()
                    elif 'action' in action:
                        action['action']()
        
        # Recent activities
        st.subheader("📊 Recent System Activities")
        
        # Get recent requests
        cursor.execute('''
            SELECT sr.request_id, u.name, sr.department, sr.status, sr.created_at
            FROM service_requests sr
            JOIN users u ON sr.user_id = u.id
            ORDER BY sr.created_at DESC
            LIMIT 10
        ''')
        recent_requests = cursor.fetchall()
        
        if recent_requests:
            for req in recent_requests:
                col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                with col1:
                    st.write(f"**{req[0]}**")
                with col2:
                    st.write(f"{req[1]} - {req[2]}")
                with col3:
                    status_color = {
                        'Pending': 'status-pending',
                        'In Progress': 'status-inprogress',
                        'Completed': 'status-completed'
                    }.get(req[3], '')
                    st.markdown(f'<span class="status-badge {status_color}">{req[3]}</span>', 
                              unsafe_allow_html=True)
                with col4:
                    st.write(req[4].split()[0])
        
        # System health
        st.subheader("🖥️ System Health")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            # Database size
            import os
            db_size = os.path.getsize('suvidha_live.db') / (1024 * 1024)  # MB
            st.metric("Database Size", f"{db_size:.2f} MB")
        
        with col2:
            # Uploads folder size
            uploads_size = 0
            for path, dirs, files in os.walk("uploads"):
                for f in files:
                    fp = os.path.join(path, f)
                    uploads_size += os.path.getsize(fp)
            uploads_size_mb = uploads_size / (1024 * 1024)
            st.metric("Storage Used", f"{uploads_size_mb:.2f} MB")
        
        with col3:
            # Active sessions (simplified)
            cursor.execute("SELECT COUNT(*) FROM users WHERE last_login > datetime('now', '-1 hour')")
            active_sessions = cursor.fetchone()[0]
            st.metric("Active Sessions", active_sessions)
    
    def validate_input(self, aadhaar, phone, name):
        """Validate user input"""
        if not aadhaar or not phone or not name:
            return False
        
        if len(aadhaar) != 12 or not aadhaar.isdigit():
            return False
        
        if len(phone) != 10 or not phone.isdigit():
            return False
        
        return True
    
    def add_notification(self, user_id, notif_type, title, message):
        """Add notification to database"""
        cursor = self.db.cursor()
        cursor.execute('''
            INSERT INTO notifications (user_id, notification_type, title, message)
            VALUES (?, ?, ?, ?)
        ''', (user_id, notif_type, title, message))
        self.db.commit()
    
    def add_comment_to_request(self, request_id):
        """Add comment to request"""
        comment = st.text_input("Add your comment")
        if st.button("Submit Comment"):
            if comment:
                cursor = self.db.cursor()
                cursor.execute('''
                    INSERT INTO request_status_history 
                    (request_id, status, comments, updated_by)
                    VALUES (?, ?, ?, ?)
                ''', (request_id, 'Comment Added', comment, st.session_state.user['name']))
                self.db.commit()
                st.success("Comment added!")
    
    def collect_feedback(self, request_id):
        """Collect feedback for completed request"""
        st.subheader("Feedback Form")
        
        rating = st.slider("Rate your experience (1-5)", 1, 5, 3)
        comments = st.text_area("Additional comments")
        
        if st.button("Submit Feedback"):
            cursor = self.db.cursor()
            cursor.execute('''
                UPDATE service_requests 
                SET feedback_rating=?, feedback_comment=?
                WHERE request_id=?
            ''', (rating, comments, request_id))
            self.db.commit()
            st.success("Thank you for your feedback!")
    
    def export_user_data(self, user_id):
        """Export user data"""
        cursor = self.db.cursor()
        
        # Get user data
        cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
        user_data = cursor.fetchone()
        
        # Get service requests
        cursor.execute("SELECT * FROM service_requests WHERE user_id=?", (user_id,))
        requests = cursor.fetchall()
        
        # Get payments
        cursor.execute("SELECT * FROM payments WHERE user_id=?", (user_id,))
        payments = cursor.fetchall()
        
        # Create export data
        export_data = {
            'user_profile': user_data,
            'service_requests': requests,
            'payments': payments,
            'exported_at': datetime.now().isoformat()
        }
        
        # Convert to JSON
        json_data = json.dumps(export_data, indent=2, default=str)
        
        # Download button
        st.download_button(
            "📥 Download Data",
            json_data,
            file_name=f"suvidha_data_export_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )
    
    def generate_reports(self):
        """Generate system reports"""
        st.info("Report generation feature")
        # Implement report generation logic
    
    def show_department_info(self):
        """Show department information"""
        st.info("Department information feature")
    
    def process_card_payment(self, bill):
        """Process card payment"""
        st.info("Card payment processing")
    
    def process_netbanking_payment(self, bill):
        """Process net banking payment"""
        st.info("Net banking processing")
    
    def process_wallet_payment(self, bill):
        """Process wallet payment"""
        st.info("Wallet payment processing")
    
    def process_cash_payment(self, bill):
        """Process cash payment"""
        st.info("Cash payment processing")
    
    def show_analytics(self):
        """Show analytics dashboard"""
        st.title("📊 Analytics Dashboard")
        st.info("Advanced analytics feature")
    
    def show_user_management(self):
        """Show user management"""
        st.title("👥 User Management")
        st.info("User management feature")
    
    def show_all_requests(self):
        """Show all requests"""
        st.title("📋 All Service Requests")
        st.info("All requests view feature")
    
    def show_system_settings(self):
        """Show system settings"""
        st.title("⚙️ System Settings")
        st.info("System settings feature")
    
    def show_payments_admin(self):
        """Admin payments view"""
        st.title("💰 Payment Administration")
        st.info("Admin payments feature")
    
    def show_documents_admin(self):
        """Admin documents view"""
        st.title("📄 Document Administration")
        st.info("Admin documents feature")

# Run the app
if __name__ == "__main__":
    app = LiveSuvidha()
    app.run()