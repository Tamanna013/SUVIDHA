import streamlit as st
from database import Database

class AuthSystem:
    def __init__(self):
        self.db = Database()
    
    def citizen_login(self):
        """Simplified Aadhaar-based authentication"""
        st.subheader("Citizen Authentication")
        
        with st.form("auth_form"):
            aadhaar = st.text_input("Aadhaar Number (12 digits)", 
                                   placeholder="Enter 12-digit Aadhaar")
            name = st.text_input("Full Name")
            phone = st.text_input("Phone Number")
            
            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("Login/Register")
            with col2:
                guest = st.form_submit_button("Continue as Guest")
        
        if submit and aadhaar and name and phone:
            if len(aadhaar) == 12 and aadhaar.isdigit():
                # Check if citizen exists
                citizen = self.db.get_citizen_by_aadhaar(aadhaar)
                if not citizen:
                    # Register new citizen
                    self.db.add_citizen(
                        aadhaar=aadhaar,
                        name=name,
                        phone=phone,
                        email="",
                        address="",
                        language="English"
                    )
                    st.success("New account created successfully!")
                else:
                    st.success(f"Welcome back, {citizen[2]}!")
                
                st.session_state['authenticated'] = True
                st.session_state['aadhaar'] = aadhaar
                st.session_state['name'] = name
                st.rerun()
            else:
                st.error("Please enter valid 12-digit Aadhaar number")
        
        if guest:
            st.session_state['authenticated'] = True
            st.session_state['aadhaar'] = "GUEST"
            st.session_state['name'] = "Guest User"
            st.rerun()
    
    def logout(self):
        st.session_state['authenticated'] = False
        st.session_state['aadhaar'] = None
        st.session_state['name'] = None
        st.rerun()