from flask import request, jsonify, current_app
from datetime import date, datetime, timedelta
from functools import wraps
from . import api
from src.models import db, Member, Plan, Attendance
from src.utils.helpers import send_telegram_alert

# Kiosk token decorator to ensure only authorized kiosk clients can call /api/checkin

def kiosk_token_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        expected = current_app.config.get('KIOSK_SECRET_TOKEN')
        provided = request.headers.get('X-Kiosk-Secret')
        if not expected or provided != expected:
            return jsonify({'success': False, 'message': 'Unauthorized kiosk'}), 401
        return f(*args, **kwargs)
    return wrapper

@api.route('/checkin', methods=['POST'])
@kiosk_token_required
def checkin():
    # 1. INPUT VALIDATION (ID or Phone)
    data = request.get_json()
    identifier = str(data.get('member_id', '')).strip()
    
    if not identifier:
        return jsonify({'success': False, 'message': 'Please enter Member ID or Phone'})

    # Try finding by member_code first (numeric or string), then by internal ID, then by phone
    member = Member.query.filter_by(member_code=identifier).first()

    if not member and identifier.isdigit():
        num = int(identifier)
        member = Member.query.get(num)
    
    # If not found by ID, try Phone
    if not member:
        member = Member.query.filter_by(phone=identifier).first()

    if not member:
        return jsonify({'success': False, 'message': 'Member not found'})
    
    if member.status != 'Active':
        return jsonify({'success': False, 'message': 'Access Denied: Account Inactive'})

    # 2. MEMBERSHIP LOGIC (The 4 States)
    days_left = 100
    if member.expiry_date:
        days_left = (member.expiry_date - date.today()).days

    # Use configurable grace period from config (default 3 if not set)
    grace_days = current_app.config.get('GRACE_PERIOD_DAYS', 3)

    success = True
    status_code = 'ok'  # ok, grace, due_soon, blocked
    title = f"WELCOME, {member.name.split(' ')[0].upper()}"
    message = f"Plan: {member.plan.name if member.plan else 'Standard'}"
    due_warning = None

    # STATE 1: BLOCKED (Overdue > grace_days)
    if days_left < -grace_days:
        success = False
        status_code = 'blocked'
        title = "ACCESS DENIED"
        if days_left == -1:
            message = "Membership expired yesterday"
        else:
            message = "Membership expired"
        if days_left == -1:
            due_warning = "Your plan expired yesterday. Please renew at the desk."
        else:
            due_warning = f"Your plan expired {abs(days_left)} days ago. Please renew at the desk."

    # STATE 2: GRACE PERIOD (expired but within configured grace window)
    elif days_left < 0:
        status_code = 'grace'
        title = "ACCESS GRANTED" 
        if days_left == -1:
            due_warning = "⚠ NOTE: Your plan expired yesterday. Please renew soon!"
        else:
            due_warning = f"⚠ NOTE: Your plan expired {abs(days_left)} day(s) ago. Please renew soon!"

    # STATE 3: UPCOMING DUE (Due in next 3 days)
    elif days_left <= 3:
        status_code = 'due_soon'
        if days_left == 0:
            days_str = "today"
        elif days_left == 1:
            days_str = "tomorrow"
        else:
            days_str = f"in {days_left} days"
        due_warning = f"👋 Just a heads up! Your membership renews {days_str}."

    # STATE 4: STANDARD WELCOME -> status_code remains 'ok'

    # 3. PREVENT DOUBLE TAPS (1 Hour Cooldown)
    if success:
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent = Attendance.query.filter(
            Attendance.member_id == member.id,
            Attendance.timestamp >= one_hour_ago
        ).first()
        
        if recent:
            return jsonify({
                'success': False, 
                'message': f"Already checked in at {recent.timestamp.strftime('%I:%M %p')}"
            })
        
        new_attendance = Attendance(member_id=member.id)
        db.session.add(new_attendance)
        db.session.commit()
        
        try:
            alert_msg = f"✅ KIOSK: {member.name}"
            if due_warning: alert_msg += f"\n⚠ {due_warning}"
            send_telegram_alert(alert_msg)
        except:
            pass

    # 4. PREPARE PHOTO URL
    photo_url = '/static/img/default_user.png'
    if member.photo_path:
        photo_url = f"/static/uploads/{member.photo_path}"

    return jsonify({
        'success': success,
        'status': status_code,
        'member_name': member.name,
        'photo_url': photo_url,
        'plan': member.plan.name if member.plan else 'N/A',
        'message': message,
        'due_warning': due_warning,
        'days_left': days_left
    })
