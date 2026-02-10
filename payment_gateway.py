# payment_gateway_updated.py
import streamlit as st
from datetime import datetime
import qrcode
from translations import t

class IntegratedPaymentGateway:
    def __init__(self, db_connection):
        self.db = db_connection
        
    def show_payment_page(self, current_lang='en'):
        """Show payment page with live data"""
        st.title("💳 " + t('pay_bills', current_lang))
        
        user_id = st.session_state.get('user', {}).get('id')
        if not user_id:
            st.error(t('login_required', current_lang))
            return
        
        # Get user's pending bills from database
        pending_bills = self.get_pending_bills(user_id)
        
        if pending_bills:
            st.subheader("📋 " + t('pending_bills', current_lang))
            
            for bill in pending_bills:
                with st.expander(f"{bill[1]} - ₹{bill[3]:,.2f} - {t('due', current_lang)}: {bill[4]}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**{t('bill_id', current_lang)}:** {bill[0]}")
                        st.write(f"**{t('bill_number', current_lang)}:** {bill[2]}")
                        st.write(f"**{t('amount', current_lang)}:** ₹{bill[3]:,.2f}")
                    with col2:
                        st.write(f"**{t('due_date', current_lang)}:** {bill[4]}")
                        st.write(f"**{t('status', current_lang)}:** {bill[5]}")
                    
                    if st.button(t('pay_now', current_lang), key=f"pay_{bill[0]}"):
                        st.session_state['selected_bill'] = {
                            'payment_id': bill[0],
                            'bill_type': bill[1],
                            'bill_number': bill[2],
                            'amount': bill[3],
                            'due_date': bill[4]
                        }
                        st.session_state['payment_page'] = 'make_payment'
                        st.rerun()
        else:
            st.info(t('no_pending_bills', current_lang))
        
        # Payment history
        st.subheader("📜 " + t('payment_history', current_lang))
        self.show_payment_history(user_id, current_lang)
    
    def get_pending_bills(self, user_id):
        """Get pending bills from database"""
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT payment_id, bill_type, bill_number, amount, due_date, status
            FROM payments 
            WHERE user_id=? AND status IN ('Pending', 'Overdue')
            ORDER BY due_date ASC
        ''', (user_id,))
        return cursor.fetchall()
    
    def show_payment_history(self, user_id, current_lang='en'):
        """Show payment history"""
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT payment_id, bill_type, amount, payment_method, status, 
                   transaction_id, created_at, completed_at
            FROM payments 
            WHERE user_id=?
            ORDER BY created_at DESC
            LIMIT 20
        ''', (user_id,))
        
        payments = cursor.fetchall()
        
        if payments:
            import pandas as pd
            
            # Create DataFrame
            df = pd.DataFrame(payments, columns=[
                t('payment_id', current_lang),
                t('bill_type', current_lang),
                t('amount', current_lang),
                t('payment_method', current_lang),
                t('status', current_lang),
                t('transaction_id', current_lang),
                t('created', current_lang),
                t('completed', current_lang)
            ])
            
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Summary
            total_paid = sum([p[2] for p in payments if p[4] == 'Completed'])
            successful_payments = len([p for p in payments if p[4] == 'Completed'])
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric(t('total_paid', current_lang), f"₹{total_paid:,.2f}")
            with col2:
                st.metric(t('successful_payments', current_lang), successful_payments)
        else:
            st.info(t('no_payment_history', current_lang))
    
    def show_make_payment(self, current_lang='en'):
        """Show make payment interface"""
        if 'selected_bill' not in st.session_state:
            st.error(t('no_bill_selected', current_lang))
            st.session_state['payment_page'] = 'bills'
            st.rerun()
            return
        
        bill = st.session_state.selected_bill
        
        st.title(f"💳 {t('pay', current_lang)} {bill['bill_type']}")
        
        # Bill summary
        col1, col2 = st.columns(2)
        with col1:
            st.metric(t('bill_amount', current_lang), f"₹{bill['amount']:,.2f}")
        with col2:
            st.metric(t('due_date', current_lang), bill['due_date'])
        
        # Payment method selection
        payment_methods = [
            t('upi', current_lang),
            t('card', current_lang),
            t('net_banking', current_lang),
            t('wallet', current_lang),
            t('cash', current_lang)
        ]
        
        selected_method = st.selectbox(
            t('select_payment_method', current_lang),
            payment_methods
        )
        
        if selected_method == t('upi', current_lang):
            self.show_upi_payment(bill, current_lang)
        elif selected_method == t('card', current_lang):
            self.show_card_payment(bill, current_lang)
        elif selected_method == t('cash', current_lang):
            self.show_cash_payment(bill, current_lang)
    
    def show_upi_payment(self, bill, current_lang='en'):
        """Show UPI payment interface"""
        st.subheader("🌟 " + t('upi_payment', current_lang))
        
        # Generate UPI QR
        upi_id = "suvidha.gov@axisbank"
        upi_string = f"upi://pay?pa={upi_id}&pn=SUVIDHA&am={bill['amount']}&tn={bill['payment_id']}"
        qr = qrcode.make(upi_string)
        
        col1, col2 = st.columns(2)
        with col1:
            st.image(qr, caption=t('scan_to_pay', current_lang), use_column_width=True)
        with col2:
            st.write(f"**{t('instructions', current_lang)}:**")
            st.write(f"1. {t('open_upi_app', current_lang)}")
            st.write(f"2. {t('tap_scan_pay', current_lang)}")
            st.write(f"3. {t('scan_qr_code', current_lang)}")
            st.write(f"4. {t('enter_upi_pin', current_lang)}")
            
            if st.button(t('confirm_payment', current_lang), type="primary"):
                # Process payment
                transaction_id = f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}"
                self.process_payment(bill['payment_id'], 'UPI', transaction_id, bill['amount'])
                
                st.success(f"✅ {t('payment_successful', current_lang)}")
                st.balloons()
                
                # Show receipt
                self.show_payment_receipt({
                    'payment_id': bill['payment_id'],
                    'transaction_id': transaction_id,
                    'amount': bill['amount'],
                    'method': 'UPI',
                    'bill_type': bill['bill_type']
                }, current_lang)
    
    def process_payment(self, payment_id, method, transaction_id, amount):
        """Process payment and update database"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            UPDATE payments 
            SET status=?, payment_method=?, transaction_id=?, completed_at=?
            WHERE payment_id=?
        ''', ('Completed', method, transaction_id, datetime.now(), payment_id))
        
        self.db.commit()
        
        # Add notification
        user_id = st.session_state.get('user', {}).get('id')
        if user_id:
            from notifications_updated import IntegratedNotificationSystem
            notif_system = IntegratedNotificationSystem(self.db)
            notif_system.add_notification(
                user_id,
                'payment_completed',
                'Payment Successful',
                f'Payment of ₹{amount:,.2f} completed successfully'
            )
    
    def show_payment_receipt(self, payment_data, current_lang='en'):
        """Show payment receipt"""
        st.markdown("---")
        st.subheader("📄 " + t('payment_receipt', current_lang))
        
        receipt_text = f"""
        SUVIDHA {t('payment_receipt', current_lang)}
        ==========================================
        {t('transaction_id', current_lang)}: {payment_data['transaction_id']}
        {t('payment_id', current_lang)}: {payment_data['payment_id']}
        {t('date_time', current_lang)}: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        {t('payment_method', current_lang)}: {payment_data['method']}
        {t('amount_paid', current_lang)}: ₹{payment_data['amount']:,.2f}
        {t('bill_type', current_lang)}: {payment_data['bill_type']}
        {t('status', current_lang)}: {t('successful', current_lang)}
        {t('citizen', current_lang)}: {st.session_state.get('user', {}).get('name', 'N/A')}
        {t('contact', current_lang)}: {st.session_state.get('user', {}).get('phone', 'N/A')}
        """
        
        st.text(receipt_text)
        
        st.download_button(
            "📥 " + t('download_receipt', current_lang),
            receipt_text,
            file_name=f"receipt_{payment_data['transaction_id']}.txt",
            mime="text/plain"
        )
        
        if st.button("← " + t('back_to_payments', current_lang)):
            st.session_state['payment_page'] = 'bills'
            st.rerun()