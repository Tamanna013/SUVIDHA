# database_updated.py
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import json

class ComprehensiveDatabase:
    def __init__(self, db_name='suvidha_comprehensive.db'):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_comprehensive_tables()
    
    def create_comprehensive_tables(self):
        """Create all tables for the comprehensive system"""
        cursor = self.conn.cursor()
        
        # 1. Users table
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
                user_type TEXT DEFAULT 'citizen',
                photo_path TEXT
            )
        ''')
        
        # 2. Service requests table
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
                feedback_rating INTEGER CHECK(feedback_rating >= 1 AND feedback_rating <= 5),
                feedback_comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # 3. Request status history
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
        
        # 4. Payments table
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
        
        # 5. Documents table
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
        
        # 6. Notifications table
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
        
        # 7. Analytics table (for precomputed metrics)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_date DATE UNIQUE,
                total_requests INTEGER DEFAULT 0,
                completed_requests INTEGER DEFAULT 0,
                pending_requests INTEGER DEFAULT 0,
                avg_completion_time REAL,
                user_count INTEGER DEFAULT 0,
                new_users INTEGER DEFAULT 0,
                payment_amount REAL DEFAULT 0,
                satisfaction_score REAL
            )
        ''')
        
        # 8. Departments table (for department info)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dept_key TEXT UNIQUE,
                name_en TEXT,
                name_hi TEXT,
                name_mr TEXT,
                name_ta TEXT,
                contact TEXT,
                working_hours TEXT,
                services_json TEXT
            )
        ''')
        
        # Insert default departments
        self.insert_default_departments()
        
        # 9. System settings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT UNIQUE,
                setting_value TEXT,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert default settings
        default_settings = [
            ('system_name', 'SUVIDHA', 'Application name'),
            ('support_email', 'support@suvidha.gov.in', 'Support email'),
            ('support_phone', '1800-123-456', 'Support phone number'),
            ('version', '1.0.0', 'System version'),
            ('maintenance_mode', 'false', 'Maintenance mode flag')
        ]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO system_settings (setting_key, setting_value, description)
            VALUES (?, ?, ?)
        ''', default_settings)
        
        self.conn.commit()
    
    def insert_default_departments(self):
        """Insert default department data"""
        cursor = self.conn.cursor()
        
        departments = [
            ('electricity', 'Electricity Department', 'बिजली विभाग', 'वीज विभाग', 'மின்சார துறை', 
             '1912', '24/7 Emergency, 9 AM - 6 PM Regular', 
             json.dumps(['Power Outage', 'New Connection', 'Bill Issue', 'Meter Complaint', 'Safety Inspection'])),
            
            ('water', 'Water Department', 'जल विभाग', 'पाणी विभाग', 'நீர் துறை',
             '1916', '24/7 Emergency, 8 AM - 8 PM Regular',
             json.dumps(['No Water Supply', 'Water Quality Issue', 'New Connection', 'Pipeline Leakage', 'Bill Payment'])),
            
            ('gas', 'Gas Department', 'गैस विभाग', 'गॅस विभाग', 'எரிவாயு துறை',
             '1906', '24/7 Emergency, 8 AM - 8 PM Regular',
             json.dumps(['Gas Leak Complaint', 'New Connection', 'Safety Check', 'Appliance Service', 'Bill Payment'])),
            
            ('waste', 'Waste Management', 'कचरा प्रबंधन', 'कचरा व्यवस्थापन', 'குப்பை மேலாண்மை',
             '155304', '6 AM - 10 PM',
             json.dumps(['Garbage Not Collected', 'Sanitation Complaint', 'Recycling Information', 'Illegal Dumping', 'Composting Request']))
        ]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO departments 
            (dept_key, name_en, name_hi, name_mr, name_ta, contact, working_hours, services_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', departments)
        
        self.conn.commit()
    
    # User management methods
    def create_user(self, user_data):
        """Create a new user"""
        cursor = self.conn.cursor()
        
        user_id = user_data.get('user_id', f"USER_{datetime.now().strftime('%Y%m%d%H%M%S')}")
        
        cursor.execute('''
            INSERT INTO users 
            (user_id, aadhaar, name, phone, email, address, pincode, language, created_at, last_login)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            user_data.get('aadhaar'),
            user_data.get('name'),
            user_data.get('phone'),
            user_data.get('email'),
            user_data.get('address'),
            user_data.get('pincode'),
            user_data.get('language', 'en'),
            datetime.now(),
            datetime.now()
        ))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def get_user_by_aadhaar(self, aadhaar):
        """Get user by Aadhaar number"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE aadhaar=?', (aadhaar,))
        return cursor.fetchone()
    
    def get_user_by_id(self, user_id):
        """Get user by user_id"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id=?', (user_id,))
        return cursor.fetchone()
    
    def update_user_last_login(self, user_id):
        """Update user's last login time"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE users SET last_login=? WHERE user_id=?
        ''', (datetime.now(), user_id))
        self.conn.commit()
    
    # Service request methods
    def create_service_request(self, request_data):
        """Create a new service request"""
        cursor = self.conn.cursor()
        
        request_id = f"SR{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        cursor.execute('''
            INSERT INTO service_requests 
            (request_id, user_id, department, service_type, description, 
             address, pincode, language, priority, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            request_id,
            request_data.get('user_id'),
            request_data.get('department'),
            request_data.get('service_type'),
            request_data.get('description'),
            request_data.get('address'),
            request_data.get('pincode'),
            request_data.get('language', 'en'),
            request_data.get('priority', 'Medium'),
            request_data.get('status', 'Pending'),
            datetime.now(),
            datetime.now()
        ))
        
        # Add to status history
        cursor.execute('''
            INSERT INTO request_status_history 
            (request_id, status, comments, updated_by)
            VALUES (?, ?, ?, ?)
        ''', (request_id, 'Pending', 'Request submitted', request_data.get('user_name', 'System')))
        
        self.conn.commit()
        return request_id
    
    def get_user_requests(self, user_id, limit=50):
        """Get all requests for a user"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM service_requests 
            WHERE user_id=? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (user_id, limit))
        return cursor.fetchall()
    
    def get_request_by_id(self, request_id):
        """Get request by request_id"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT sr.*, u.name, u.phone, u.email
            FROM service_requests sr
            JOIN users u ON sr.user_id = u.id
            WHERE sr.request_id=?
        ''', (request_id,))
        return cursor.fetchone()
    
    def update_request_status(self, request_id, status, comments="", updated_by="System"):
        """Update request status"""
        cursor = self.conn.cursor()
        
        # Update request
        cursor.execute('''
            UPDATE service_requests 
            SET status=?, updated_at=?
            WHERE request_id=?
        ''', (status, datetime.now(), request_id))
        
        # Add to history
        cursor.execute('''
            INSERT INTO request_status_history 
            (request_id, status, comments, updated_by)
            VALUES (?, ?, ?, ?)
        ''', (request_id, status, comments, updated_by))
        
        self.conn.commit()
    
    # Analytics methods
    def get_daily_metrics(self, date=None):
        """Get metrics for a specific date"""
        if date is None:
            date = datetime.now().date()
        
        cursor = self.conn.cursor()
        
        # Check if precomputed metrics exist
        cursor.execute('SELECT * FROM analytics WHERE metric_date=?', (date,))
        existing = cursor.fetchone()
        
        if existing:
            return existing
        
        # Compute metrics
        cursor.execute('''
            SELECT 
                COUNT(*) as total_requests,
                SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed_requests,
                SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END) as pending_requests,
                AVG(CASE WHEN actual_completion IS NOT NULL 
                    THEN julianday(actual_completion) - julianday(created_at) 
                    ELSE NULL END) as avg_completion_time,
                COUNT(DISTINCT user_id) as active_users,
                (SELECT COUNT(*) FROM users WHERE DATE(created_at) = ?) as new_users,
                (SELECT SUM(amount) FROM payments WHERE DATE(created_at) = ? AND status='Completed') as payment_amount,
                AVG(feedback_rating) as satisfaction_score
            FROM service_requests 
            WHERE DATE(created_at) = ?
        ''', (date, date, date))
        
        metrics = cursor.fetchone()
        
        # Store in analytics table
        cursor.execute('''
            INSERT INTO analytics 
            (metric_date, total_requests, completed_requests, pending_requests, 
             avg_completion_time, user_count, new_users, payment_amount, satisfaction_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (date, *metrics))
        
        self.conn.commit()
        return metrics
    
    # Payment methods
    def create_payment(self, payment_data):
        """Create a new payment record"""
        cursor = self.conn.cursor()
        
        payment_id = f"PAY{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        cursor.execute('''
            INSERT INTO payments 
            (payment_id, request_id, user_id, bill_type, bill_number, 
             amount, due_date, payment_method, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            payment_id,
            payment_data.get('request_id'),
            payment_data.get('user_id'),
            payment_data.get('bill_type'),
            payment_data.get('bill_number'),
            payment_data.get('amount'),
            payment_data.get('due_date'),
            payment_data.get('payment_method'),
            payment_data.get('status', 'Pending'),
            datetime.now()
        ))
        
        self.conn.commit()
        return payment_id
    
    def update_payment_status(self, payment_id, status, transaction_id=None):
        """Update payment status"""
        cursor = self.conn.cursor()
        
        update_data = [status, datetime.now() if status == 'Completed' else None, payment_id]
        if transaction_id:
            cursor.execute('''
                UPDATE payments 
                SET status=?, transaction_id=?, completed_at=?
                WHERE payment_id=?
            ''', (status, transaction_id, datetime.now() if status == 'Completed' else None, payment_id))
        else:
            cursor.execute('''
                UPDATE payments 
                SET status=?, completed_at=?
                WHERE payment_id=?
            ''', (status, datetime.now() if status == 'Completed' else None, payment_id))
        
        self.conn.commit()
    
    def get_user_payments(self, user_id):
        """Get all payments for a user"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM payments 
            WHERE user_id=? 
            ORDER BY created_at DESC
        ''', (user_id,))
        return cursor.fetchall()
    
    # Document methods
    def save_document(self, doc_data):
        """Save document metadata"""
        cursor = self.conn.cursor()
        
        doc_id = f"DOC{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        cursor.execute('''
            INSERT INTO documents 
            (doc_id, user_id, request_id, document_type, document_name, 
             file_path, file_size, uploaded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            doc_id,
            doc_data.get('user_id'),
            doc_data.get('request_id'),
            doc_data.get('document_type'),
            doc_data.get('document_name'),
            doc_data.get('file_path'),
            doc_data.get('file_size'),
            datetime.now()
        ))
        
        self.conn.commit()
        return doc_id
    
    def get_user_documents(self, user_id):
        """Get all documents for a user"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM documents 
            WHERE user_id=? 
            ORDER BY uploaded_at DESC
        ''', (user_id,))
        return cursor.fetchall()
    
    # Notification methods
    def add_notification(self, notification_data):
        """Add a new notification"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO notifications 
            (user_id, notification_type, title, message)
            VALUES (?, ?, ?, ?)
        ''', (
            notification_data.get('user_id'),
            notification_data.get('notification_type'),
            notification_data.get('title'),
            notification_data.get('message')
        ))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def get_user_notifications(self, user_id, unread_only=False, limit=20):
        """Get notifications for a user"""
        cursor = self.conn.cursor()
        
        if unread_only:
            cursor.execute('''
                SELECT * FROM notifications 
                WHERE user_id=? AND is_read=FALSE
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (user_id, limit))
        else:
            cursor.execute('''
                SELECT * FROM notifications 
                WHERE user_id=?
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (user_id, limit))
        
        return cursor.fetchall()
    
    def mark_notification_read(self, notification_id):
        """Mark notification as read"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE notifications SET is_read=TRUE WHERE id=?
        ''', (notification_id,))
        self.conn.commit()
    
    def mark_all_notifications_read(self, user_id):
        """Mark all notifications as read for a user"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE notifications SET is_read=TRUE WHERE user_id=?
        ''', (user_id,))
        self.conn.commit()
    
    # Department methods
    def get_department_info(self, dept_key, language='en'):
        """Get department information in specified language"""
        cursor = self.conn.cursor()
        
        if language == 'en':
            name_col = 'name_en'
        elif language == 'hi':
            name_col = 'name_hi'
        elif language == 'mr':
            name_col = 'name_mr'
        elif language == 'ta':
            name_col = 'name_ta'
        else:
            name_col = 'name_en'
        
        cursor.execute(f'''
            SELECT dept_key, {name_col} as name, contact, working_hours, services_json
            FROM departments 
            WHERE dept_key=?
        ''', (dept_key,))
        
        result = cursor.fetchone()
        if result:
            return {
                'key': result[0],
                'name': result[1],
                'contact': result[2],
                'working_hours': result[3],
                'services': json.loads(result[4]) if result[4] else []
            }
        return None
    
    def get_all_departments(self, language='en'):
        """Get all departments in specified language"""
        cursor = self.conn.cursor()
        
        if language == 'en':
            name_col = 'name_en'
        elif language == 'hi':
            name_col = 'name_hi'
        elif language == 'mr':
            name_col = 'name_mr'
        elif language == 'ta':
            name_col = 'name_ta'
        else:
            name_col = 'name_en'
        
        cursor.execute(f'''
            SELECT dept_key, {name_col} as name, contact, working_hours
            FROM departments 
            ORDER BY {name_col}
        ''')
        
        return cursor.fetchall()
    
    # System settings
    def get_setting(self, key):
        """Get system setting"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT setting_value FROM system_settings WHERE setting_key=?', (key,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    def update_setting(self, key, value):
        """Update system setting"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE system_settings 
            SET setting_value=?, updated_at=?
            WHERE setting_key=?
        ''', (value, datetime.now(), key))
        self.conn.commit()