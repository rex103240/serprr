from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required
from datetime import date, datetime, timedelta, time
from sqlalchemy import func
from src.models import db, Member, Plan, Attendance, Transaction

# --- Define the Blueprint ---
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def dashboard():
    today = date.today()
    today_start = datetime.combine(today, time.min)
    today_end = datetime.combine(today, time.max)
    
    # --- 1. COUNTS ---
    total_members = Member.query.count()
    
    # FIX: Filter by status AND expiry_date to ensure we only count truly active members
    # (Previously it counted expired members if their status wasn't manually updated)
    active_members = Member.query.filter(
        Member.status == 'Active',
        Member.expiry_date >= today
    ).count()
    
    # --- 2. ATTENDANCE ---
    checkins_today = Attendance.query.filter(
        Attendance.timestamp.between(today_start, today_end)
    ).count()
    
    # --- 3. UPCOMING DUES ---
    seven_days_out = today + timedelta(days=7)
    
    expiring_soon = db.session.query(Member, Plan).join(Plan).filter(
        Member.status == 'Active',
        Member.expiry_date <= seven_days_out,
        Member.expiry_date >= (today - timedelta(days=30))
    ).order_by(Member.expiry_date.asc()).all()

    upcoming_dues = []
    for member, plan in expiring_soon:
        upcoming_dues.append({
            'id': member.id,
            'name': member.name,
            'plan_name': plan.name,
            'expiry_date': member.expiry_date,
            'days_left': (member.expiry_date - today).days
        })
    
    # --- 4. LIVE FEED ---
    todays_checkins = db.session.query(Attendance, Member, Plan).join(
        Member, Attendance.member_id == Member.id
    ).outerjoin(
        Plan, Member.plan_id == Plan.id
    ).filter(
        Attendance.timestamp.between(today_start, today_end)
    ).order_by(Attendance.timestamp.desc()).limit(20).all()
    
    checkin_list = []
    for att, member, plan in todays_checkins:
        ts = att.timestamp
        if isinstance(ts, str):
            try: ts = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
            except: ts = datetime.now()

        checkin_list.append({
            'time': ts.strftime('%I:%M %p'),
            'name': member.name,
            'plan_name': plan.name if plan else 'N/A'
        })

    # --- 5. MONTHLY REVENUE ---
    first_of_month = today.replace(day=1)
    current_month_revenue = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.date >= first_of_month
    ).scalar() or 0
    
    return render_template('dashboard.html',
        active_page='dashboard',
        total_members=total_members,
        active_members=active_members,
        checkins_today=checkins_today,
        upcoming_dues=upcoming_dues,
        todays_checkins=checkin_list,
        current_month_revenue=f"{current_month_revenue:,.2f}"
    )

@main_bp.route('/attendance')
@login_required
def attendance():
    selected_date = request.args.get('date', date.today().strftime('%Y-%m-%d'))
    try:
        filter_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    except:
        filter_date = date.today()
        selected_date = filter_date.strftime('%Y-%m-%d')
        
    day_start = datetime.combine(filter_date, time.min)
    day_end = datetime.combine(filter_date, time.max)
    
    logs = db.session.query(Attendance, Member, Plan).join(
        Member, Attendance.member_id == Member.id
    ).outerjoin(
        Plan, Member.plan_id == Plan.id
    ).filter(
        Attendance.timestamp.between(day_start, day_end)
    ).order_by(Attendance.timestamp.desc()).all()
    
    attendance_logs = []
    for att, member, plan in logs:
        ts = att.timestamp
        if isinstance(ts, str):
            try: ts = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
            except: ts = datetime.now()

        attendance_logs.append({
            'member_id': member.id,
            'member_name': member.name, 
            'plan_name': plan.name if plan else 'N/A',
            'timestamp': ts 
        })
    
    return render_template('attendance.html',
        active_page='attendance',
        logs=attendance_logs,
        selected_date=selected_date
    )

@main_bp.route('/checkin_manual', methods=['POST'])
@login_required
def checkin_manual():
    identifier = request.form.get('identifier')
    
    # Try finding member by member_code, then by ID, then by Phone
    member = None
    if identifier:
        member = Member.query.filter_by(member_code=identifier).first()

    if not member and identifier and identifier.isdigit():
        member = Member.query.get(int(identifier))
    
    if not member:
        member = Member.query.filter_by(phone=identifier).first()
        
    if member:
        new_attendance = Attendance(member_id=member.id, timestamp=datetime.now())
        db.session.add(new_attendance)
        db.session.commit()
        flash(f'Checked in: {member.name}', 'success')
    else:
        flash('Member not found.', 'danger')
        
    return redirect(url_for('main.attendance'))

@main_bp.route('/kiosk')
def kiosk_mode(): 
    api_secret = current_app.config.get('KIOSK_SECRET_TOKEN', '')
    return render_template('kiosk.html', api_secret=api_secret)


@main_bp.route("/test")
def test():
    return "Test route working"
