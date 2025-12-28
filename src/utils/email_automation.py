import smtplib
import ssl
import threading
import time
import schedule
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime, timedelta
from flask import current_app
from src.models import db, Member

# --- CONFIGURATION ---
# Load SMTP credentials from environment variables instead of hard-coding them.
# Example (in .env or hosting config):
#   SMTP_SERVER=smtp.gmail.com
#   SMTP_PORT=465
#   GMAIL_USER=your_address@gmail.com
#   GMAIL_PASS=your_app_password
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 465))
GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_PASS = os.environ.get("GMAIL_PASS")

class EmailService:
    @staticmethod
    def _send_async(subject, recipient, body, attachments=None):
        """Internal function to handle the actual sending in a separate thread."""
        print(f"DEBUG: Starting email process for {recipient}...")
        
        if not recipient or 'example.com' in recipient or 'test.com' in recipient:
            print(f"EMAIL SKIPPED: Ignored test address {recipient}")
            return

        def send_task():
            try:
                msg = MIMEMultipart()
                msg['From'] = f"IronLifter Gym <{GMAIL_USER}>"
                msg['To'] = recipient
                msg['Subject'] = subject
                msg.attach(MIMEText(body, 'html'))

                if attachments:
                    for filename, file_data in attachments:
                        file_data.seek(0)
                        part = MIMEApplication(file_data.read(), Name=filename)
                        part['Content-Disposition'] = f'attachment; filename="{filename}"'
                        msg.attach(part)

                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
                    server.login(GMAIL_USER, GMAIL_PASS)
                    server.sendmail(GMAIL_USER, recipient, msg.as_string())
                print(f"SUCCESS: Email sent to {recipient}")
            except Exception as e:
                print(f"CRITICAL EMAIL ERROR: {str(e)}")

        thread = threading.Thread(target=send_task)
        thread.start()

    @staticmethod
    def send_staff_welcome(staff, password):
        """Trigger for new staff members"""
        subject = "Welcome to the IronLifter Team!"
        body = f"<h2>Welcome {staff.first_name}!</h2><p>Your login: {staff.email}<br>Password: {password}</p>"
        EmailService._send_async(subject, staff.email, body)

    @staticmethod
    def send_salary_slip(staff, amount, month_str, date_str):
        """Trigger for salary payments"""
        subject = f"Salary Slip - {month_str}"
        body = f"<p>Hi {staff.first_name}, your payment of ₹{amount} was processed on {date_str}.</p>"
        EmailService._send_async(subject, staff.email, body)

    @staticmethod
    def send_staff_status_change(staff, status):
        """Trigger for status updates"""
        subject = f"Account Update: {status}"
        body = f"<p>Your status has been updated to {status}.</p>"
        EmailService._send_async(subject, staff.email, body)

    # --- MEMBER EMAILS (used by member_routes) ---
    @staticmethod
    def send_welcome(member, plan, transaction=None):
        """Welcome email for new members."""
        if not member.email:
            return
        subject = "Welcome to IronLifter Gym"
        plan_name = plan.name if plan else 'your plan'
        body = f"""
        <h2>Welcome, {member.name}!</h2>
        <p>Thank you for joining <strong>IronLifter Gym</strong>.</p>
        <p>Your plan: <strong>{plan_name}</strong><br>
        Member ID: <strong>{member.member_code or member.id}</strong></p>
        <p>We look forward to seeing you in the gym.</p>
        """
        EmailService._send_async(subject, member.email, body)

    @staticmethod
    def send_renewal(member, plan, transaction=None):
        """Renewal confirmation email."""
        if not member.email:
            return
        subject = "Your IronLifter Membership has been renewed"
        plan_name = plan.name if plan else 'your plan'
        body = f"""
        <h2>Membership Renewed</h2>
        <p>Hi {member.name},</p>
        <p>Your membership has been renewed on <strong>{datetime.now().strftime('%d %b %Y')}</strong>.<br>
        Plan: <strong>{plan_name}</strong></p>
        """
        EmailService._send_async(subject, member.email, body)

    @staticmethod
    def send_status_change(member, status):
        """Status change (Active / Inactive) email."""
        if not member.email:
            return
        subject = f"Your IronLifter account status is now {status}"
        body = f"<p>Hi {member.name}, your membership status has been updated to <strong>{status}</strong>.</p>"
        EmailService._send_async(subject, member.email, body)
