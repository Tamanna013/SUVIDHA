# analytics_updated.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sqlite3
from translations import t

class LiveAnalyticsDashboard:
    def __init__(self, db_connection):
        self.db = db_connection
    
    def show_dashboard(self, current_lang='en'):
        """Show comprehensive analytics dashboard with live data"""
        st.title("📊 " + t('analytics', current_lang))
        
        # Date range selector
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(t('start_date', current_lang), 
                                      datetime.now() - timedelta(days=30))
        with col2:
            end_date = st.date_input(t('end_date', current_lang), datetime.now())
        
        # Get live data
        metrics = self.get_live_metrics(start_date, end_date)
        
        # Tabs for different analytics
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📈 " + t('overview', current_lang),
            "👥 " + t('citizen_analytics', current_lang),
            "🏢 " + t('department_performance', current_lang),
            "🔄 " + t('service_metrics', current_lang),
            "📱 " + t('channel_analytics', current_lang)
        ])
        
        with tab1:
            self.show_overview_analytics(metrics, current_lang)
        
        with tab2:
            self.show_citizen_analytics(start_date, end_date, current_lang)
        
        with tab3:
            self.show_department_analytics(start_date, end_date, current_lang)
        
        with tab4:
            self.show_service_analytics(start_date, end_date, current_lang)
        
        with tab5:
            self.show_channel_analytics(start_date, end_date, current_lang)
    
    def get_live_metrics(self, start_date, end_date):
        """Get live metrics from database"""
        cursor = self.db.cursor()
        
        # Total requests
        cursor.execute('''
            SELECT COUNT(*) as total_requests,
                   SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed_requests,
                   SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END) as pending_requests,
                   AVG(CASE WHEN actual_completion IS NOT NULL 
                       THEN julianday(actual_completion) - julianday(created_at) 
                       ELSE NULL END) as avg_resolution_days
            FROM service_requests 
            WHERE created_at BETWEEN ? AND ?
        ''', (start_date, end_date))
        
        request_metrics = cursor.fetchone()
        
        # User metrics
        cursor.execute('''
            SELECT COUNT(*) as total_users,
                   COUNT(DISTINCT CASE WHEN DATE(last_login) = DATE('now') THEN user_id END) as active_today,
                   AVG(CASE WHEN sr.user_id IS NOT NULL 
                       THEN (SELECT COUNT(*) FROM service_requests sr2 WHERE sr2.user_id = u.id) 
                       ELSE 0 END) as avg_requests_per_user
            FROM users u
            LEFT JOIN service_requests sr ON u.id = sr.user_id
            WHERE u.created_at BETWEEN ? AND ?
        ''', (start_date, end_date))
        
        user_metrics = cursor.fetchone()
        
        # Payment metrics
        cursor.execute('''
            SELECT SUM(amount) as total_revenue,
                   COUNT(*) as total_payments,
                   AVG(amount) as avg_payment_amount
            FROM payments 
            WHERE created_at BETWEEN ? AND ? AND status = 'Completed'
        ''', (start_date, end_date))
        
        payment_metrics = cursor.fetchone()
        
        # Satisfaction metrics
        cursor.execute('''
            SELECT AVG(feedback_rating) as avg_satisfaction,
                   COUNT(feedback_rating) as feedback_count
            FROM service_requests 
            WHERE feedback_rating IS NOT NULL 
            AND created_at BETWEEN ? AND ?
        ''', (start_date, end_date))
        
        satisfaction_metrics = cursor.fetchone()
        
        return {
            'requests': request_metrics,
            'users': user_metrics,
            'payments': payment_metrics,
            'satisfaction': satisfaction_metrics
        }
    
    def show_overview_analytics(self, metrics, current_lang='en'):
        """Show overview analytics with live data"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_requests = metrics['requests'][0] if metrics['requests'][0] else 0
            st.metric(t('total_requests', current_lang), f"{total_requests:,}")
        
        with col2:
            avg_resolution = metrics['requests'][3] if metrics['requests'][3] else 0
            st.metric(t('avg_resolution_time', current_lang), 
                     f"{avg_resolution:.1f} {t('days', current_lang)}")
        
        with col3:
            avg_satisfaction = metrics['satisfaction'][0] if metrics['satisfaction'][0] else 0
            st.metric(t('citizen_satisfaction', current_lang), 
                     f"{avg_satisfaction*20:.1f}%" if avg_satisfaction else "N/A")
        
        with col4:
            total_users = metrics['users'][0] if metrics['users'][0] else 0
            st.metric(t('total_users', current_lang), f"{total_users:,}")
        
        # Time series chart from actual data
        st.subheader(t('requests_over_time', current_lang))
        time_data = self.get_time_series_data()
        if not time_data.empty:
            fig = px.line(time_data, x='date', y='requests', 
                         title=t('daily_service_requests', current_lang))
            st.plotly_chart(fig, use_container_width=True)
    
    def show_citizen_analytics(self, start_date, end_date, current_lang='en'):
        """Show citizen analytics from actual database"""
        cursor = self.db.cursor()
        
        # Age distribution (simulated for now - in real app, store DOB)
        st.subheader(t('citizen_demographics', current_lang))
        
        # Language preference from actual data
        cursor.execute('''
            SELECT language, COUNT(*) as user_count
            FROM users 
            WHERE created_at BETWEEN ? AND ?
            GROUP BY language
            ORDER BY user_count DESC
        ''', (start_date, end_date))
        
        lang_data = cursor.fetchall()
        
        if lang_data:
            df_lang = pd.DataFrame(lang_data, columns=['language', 'users'])
            fig = px.bar(df_lang, x='language', y='users', 
                        color='language', 
                        title=t('language_usage', current_lang))
            st.plotly_chart(fig, use_container_width=True)
        
        # User engagement from actual data
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN request_count >= 10 THEN 'Power User (10+ requests)'
                    WHEN request_count >= 5 THEN 'Regular User (5-9 requests)'
                    WHEN request_count >= 2 THEN 'Occasional User (2-4 requests)'
                    ELSE 'New User (1 request)'
                END as user_category,
                COUNT(*) as user_count
            FROM (
                SELECT u.id, COUNT(sr.id) as request_count
                FROM users u
                LEFT JOIN service_requests sr ON u.id = sr.user_id
                WHERE u.created_at BETWEEN ? AND ?
                GROUP BY u.id
            ) user_stats
            GROUP BY user_category
        ''', (start_date, end_date))
        
        engagement_data = cursor.fetchall()
        
        if engagement_data:
            df_eng = pd.DataFrame(engagement_data, columns=['category', 'count'])
            fig = px.pie(df_eng, values='count', names='category',
                        title=t('user_engagement', current_lang))
            st.plotly_chart(fig, use_container_width=True)
    
    def show_department_analytics(self, start_date, end_date, current_lang='en'):
        """Show department performance from actual data"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            SELECT 
                department,
                COUNT(*) as total_requests,
                AVG(CASE WHEN actual_completion IS NOT NULL 
                    THEN julianday(actual_completion) - julianday(created_at) 
                    ELSE NULL END) as avg_resolution_days,
                AVG(feedback_rating) * 20 as satisfaction_percentage,
                SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END) as backlog_count
            FROM service_requests 
            WHERE created_at BETWEEN ? AND ?
            GROUP BY department
            ORDER BY total_requests DESC
        ''', (start_date, end_date))
        
        dept_data = cursor.fetchall()
        
        if dept_data:
            df = pd.DataFrame(dept_data, columns=[
                'department', 'total_requests', 'avg_resolution', 
                'satisfaction_percentage', 'backlog'
            ])
            
            st.dataframe(df.style.background_gradient(
                subset=['satisfaction_percentage'], cmap='RdYlGn'
            ), use_container_width=True)
            
            # Visualization
            fig = go.Figure(data=[
                go.Bar(name=t('total_requests', current_lang), 
                      x=df['department'], y=df['total_requests']),
                go.Bar(name=t('satisfaction', current_lang), 
                      x=df['department'], y=df['satisfaction_percentage'])
            ])
            fig.update_layout(barmode='group', 
                            title=t('department_comparison', current_lang))
            st.plotly_chart(fig, use_container_width=True)
    
    def get_time_series_data(self):
        """Get actual time series data from database"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            SELECT DATE(created_at) as date, COUNT(*) as requests
            FROM service_requests 
            WHERE created_at >= DATE('now', '-30 days')
            GROUP BY DATE(created_at)
            ORDER BY date
        ''')
        
        data = cursor.fetchall()
        
        if data:
            return pd.DataFrame(data, columns=['date', 'requests'])
        return pd.DataFrame()