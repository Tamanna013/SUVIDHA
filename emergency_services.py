# emergency_services_updated.py
import streamlit as st
from translations import t
import json
from datetime import datetime
import sqlite3

class LiveEmergencyServices:
    def __init__(self, db_connection):
        self.db = db_connection
        
    def show_emergency_dashboard(self, current_lang='en'):
        """Show emergency services dashboard with live data"""
        st.title("🚨 " + t('emergency_services', current_lang))
        
        # Get emergency contacts from database or config
        emergency_contacts = self.get_emergency_contacts(current_lang)
        
        # Quick emergency buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🚓 " + t('police', current_lang), 
                        use_container_width=True, type="secondary"):
                self.show_police_services(current_lang)
        with col2:
            if st.button("🚒 " + t('fire', current_lang), 
                        use_container_width=True, type="secondary"):
                self.show_fire_services(current_lang)
        with col3:
            if st.button("🚑 " + t('ambulance', current_lang), 
                        use_container_width=True, type="secondary"):
                self.show_ambulance_services(current_lang)
        
        # Utility emergencies
        col4, col5, col6 = st.columns(3)
        with col4:
            if st.button("⚡ " + t('electricity', current_lang), 
                        use_container_width=True):
                self.show_electricity_emergency(current_lang)
        with col5:
            if st.button("🔥 " + t('gas', current_lang), 
                        use_container_width=True):
                self.show_gas_emergency(current_lang)
        with col6:
            if st.button("💧 " + t('water', current_lang), 
                        use_container_width=True):
                self.show_water_emergency(current_lang)
        
        # Emergency contacts
        st.subheader("📞 " + t('emergency_contacts', current_lang))
        
        for contact in emergency_contacts:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{contact['service']}**")
                if contact.get('description'):
                    st.caption(contact['description'])
            with col2:
                st.code(contact['number'], language=None)
        
        # Emergency report form
        st.markdown("---")
        self.show_emergency_report_form(current_lang)
    
    def get_emergency_contacts(self, current_lang='en'):
        """Get emergency contacts from database"""
        cursor = self.db.cursor()
        
        # In production, this would come from a database table
        # For now, use multilingual contacts
        contacts = [
            {
                'service': t('police', current_lang),
                'number': '100',
                'description': t('police_description', current_lang)
            },
            {
                'service': t('fire', current_lang),
                'number': '101',
                'description': t('fire_description', current_lang)
            },
            {
                'service': t('ambulance', current_lang),
                'number': '102',
                'description': t('ambulance_description', current_lang)
            },
            {
                'service': t('women_helpline', current_lang),
                'number': '1091',
                'description': t('women_helpline_description', current_lang)
            },
            {
                'service': t('child_helpline', current_lang),
                'number': '1098',
                'description': t('child_helpline_description', current_lang)
            },
            {
                'service': t('electricity_emergency', current_lang),
                'number': '1912',
                'description': t('electricity_emergency_description', current_lang)
            },
            {
                'service': t('gas_leak_emergency', current_lang),
                'number': '1906',
                'description': t('gas_leak_emergency_description', current_lang)
            }
        ]
        
        return contacts
    
    def show_emergency_report_form(self, current_lang='en'):
        """Show emergency report form with multilingual support"""
        st.subheader("📝 " + t('report_emergency', current_lang))
        
        with st.form("emergency_report_form"):
            # Emergency type
            emergency_types = [
                t('accident', current_lang),
                t('medical_emergency', current_lang),
                t('fire_emergency', current_lang),
                t('crime_emergency', current_lang),
                t('natural_disaster', current_lang),
                t('other_emergency', current_lang)
            ]
            
            emergency_type = st.selectbox(
                t('emergency_type', current_lang),
                emergency_types
            )
            
            # Location
            location = st.text_input(
                t('location', current_lang),
                placeholder=t('enter_location', current_lang)
            )
            
            # Description
            description = st.text_area(
                t('description', current_lang),
                placeholder=t('describe_emergency', current_lang),
                height=100
            )
            
            # Severity
            severity_options = [
                t('low_severity', current_lang),
                t('medium_severity', current_lang),
                t('high_severity', current_lang),
                t('critical_severity', current_lang)
            ]
            
            severity = st.select_slider(
                t('severity_level', current_lang),
                options=severity_options,
                value=severity_options[1]
            )
            
            # Contact information
            st.write("**" + t('your_contact_info', current_lang) + "**")
            col1, col2 = st.columns(2)
            with col1:
                reporter_name = st.text_input(
                    t('your_name', current_lang),
                    value=st.session_state.get('user', {}).get('name', '')
                )
            with col2:
                reporter_phone = st.text_input(
                    t('your_phone', current_lang),
                    value=st.session_state.get('user', {}).get('phone', '')
                )
            
            # Evidence upload
            evidence_files = st.file_uploader(
                t('upload_evidence', current_lang),
                accept_multiple_files=True,
                type=['jpg', 'png', 'mp4'],
                help=t('evidence_help', current_lang)
            )
            
            if st.form_submit_button("🚨 " + t('report_emergency', current_lang), type="primary"):
                if location and description:
                    # Save emergency report to database
                    self.save_emergency_report({
                        'emergency_type': emergency_type,
                        'location': location,
                        'description': description,
                        'severity': severity,
                        'reporter_name': reporter_name,
                        'reporter_phone': reporter_phone,
                        'timestamp': datetime.now()
                    })
                    
                    st.success("✅ " + t('emergency_reported', current_lang))
                    st.info(t('emergency_instructions', current_lang))
                    
                    # Show next steps based on severity
                    if 'critical' in severity.lower() or 'high' in severity.lower():
                        st.warning("⚠️ " + t('call_emergency_now', current_lang))
                        st.write(t('emergency_procedures', current_lang))
                else:
                    st.error(t('fill_required_fields', current_lang))
    
    def save_emergency_report(self, report_data):
        """Save emergency report to database"""
        cursor = self.db.cursor()
        
        # Create emergency_reports table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emergency_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id TEXT UNIQUE,
                user_id INTEGER,
                emergency_type TEXT,
                location TEXT,
                description TEXT,
                severity TEXT,
                reporter_name TEXT,
                reporter_phone TEXT,
                status TEXT DEFAULT 'Reported',
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        report_id = f"EMG{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        cursor.execute('''
            INSERT INTO emergency_reports 
            (report_id, user_id, emergency_type, location, description, 
             severity, reporter_name, reporter_phone, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            report_id,
            st.session_state.get('user', {}).get('id'),
            report_data['emergency_type'],
            report_data['location'],
            report_data['description'],
            report_data['severity'],
            report_data['reporter_name'],
            report_data['reporter_phone'],
            report_data['timestamp'],
            report_data['timestamp']
        ))
        
        self.db.commit()
        return report_id