# notifications_updated.py
import streamlit as st
from datetime import datetime
from translations import t

class IntegratedNotificationSystem:
    def __init__(self, db_connection):
        self.db = db_connection
    
    def add_notification(self, user_id, notification_type, title, message):
        """Add notification to database"""
        cursor = self.db.cursor()
        
        # Ensure notifications table exists
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
        
        cursor.execute('''
            INSERT INTO notifications (user_id, notification_type, title, message)
            VALUES (?, ?, ?, ?)
        ''', (user_id, notification_type, title, message))
        
        self.db.commit()
        return cursor.lastrowid
    
    def get_user_notifications(self, user_id, unread_only=False, limit=20):
        """Get notifications for a user"""
        cursor = self.db.cursor()
        
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
        cursor = self.db.cursor()
        cursor.execute('UPDATE notifications SET is_read=TRUE WHERE id=?', (notification_id,))
        self.db.commit()
    
    def mark_all_notifications_read(self, user_id):
        """Mark all notifications as read for a user"""
        cursor = self.db.cursor()
        cursor.execute('UPDATE notifications SET is_read=TRUE WHERE user_id=?', (user_id,))
        self.db.commit()
    
    def show_notifications_page(self, current_lang='en'):
        """Show notifications page"""
        st.title("🔔 " + t('notifications', current_lang))
        
        user_id = st.session_state.get('user', {}).get('id')
        if not user_id:
            st.error(t('login_required', current_lang))
            return
        
        # Get notifications
        notifications = self.get_user_notifications(user_id)
        
        if notifications:
            # Mark all as read button
            if st.button(t('mark_all_read', current_lang)):
                self.mark_all_notifications_read(user_id)
                st.success(t('all_marked_read', current_lang))
                st.rerun()
            
            # Display notifications
            unread_count = sum(1 for n in notifications if not n[5])  # is_read is index 5
            st.subheader(f"{unread_count} {t('unread_notifications', current_lang)}")
            
            for notif in notifications:
                icon = "📧" if not notif[5] else "✅"
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**{icon} {notif[3]}**")  # title
                    st.write(notif[4])  # message
                    st.caption(notif[6])  # created_at
                with col2:
                    if not notif[5]:
                        if st.button(t('mark_read', current_lang), key=f"read_{notif[0]}"):
                            self.mark_notification_read(notif[0])
                            st.rerun()
        else:
            st.info(t('no_notifications', current_lang))