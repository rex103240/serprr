from flask import render_template, request, jsonify
from flask_login import login_required
from datetime import date, datetime, timedelta
from sqlalchemy import func, and_
from dateutil.relativedelta import relativedelta
from . import reports
from src.models import db, Member, Plan, Transaction, Attendance

@reports.route('/')
@login_required
def analytics():
    today = date.today()
    current_month_start = today.replace(day=1)
    
    # --- 1. KPI CARDS DATA (Static) ---
    new_members_count = Member.query.filter(Member.join_date >= current_month_start).count()
    
    renewals_count = Transaction.query.filter(
        Transaction.date >= current_month_start,
        Transaction.transaction_type == 'Renewal'
    ).count()
    
    thirty_days_ago = today - timedelta(days=30)
    dropouts_count = Member.query.filter(
        Member.expiry_date >= thirty_days_ago,
        Member.expiry_date < today
    ).count()
    
    total_active_valid = Member.query.filter(
        Member.status == 'Active', 
        Member.expiry_date >= today
    ).count()
    
    unique_attendees = db.session.query(func.count(func.distinct(Attendance.member_id))).filter(
        Attendance.timestamp >= current_month_start
    ).scalar() or 0
    
    avg_attendance = 0
    if total_active_valid > 0:
        avg_attendance = round((unique_attendees / total_active_valid) * 100)

    # --- 2. CHART DATA: 1 MONTH (DAILY TREND) ---
    # FIXED: Now uses a time range (Start of Day to End of Day) so it catches all times.
    daily_trends = []
    for i in range(29, -1, -1):
        day_cursor = today - timedelta(days=i)
        
        # Create strict timestamps for the entire day
        day_start = datetime.combine(day_cursor, datetime.min.time()) # 00:00:00
        day_end = datetime.combine(day_cursor, datetime.max.time())   # 23:59:59
        
        day_revenue = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.date >= day_start,
            Transaction.date <= day_end
        ).scalar() or 0
        
        daily_trends.append({
            'label': day_cursor.strftime('%d %b'), 
            'revenue': day_revenue
        })

    # --- 3. CHART DATA: 12 MONTHS (MONTHLY TREND) ---
    monthly_trends = []
    for i in range(11, -1, -1):
        date_cursor = today - relativedelta(months=i)
        start_date = date_cursor.replace(day=1)
        end_date = (start_date + relativedelta(months=1)) - timedelta(days=1)
        
        month_revenue = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).scalar() or 0
        
        monthly_trends.append({
            'label': start_date.strftime('%b %Y'), 
            'revenue': month_revenue
        })

    # --- 4. CHART DATA: PLAN DISTRIBUTION ---
    plan_dist_query = db.session.query(Plan.name, func.count(Member.id))\
        .join(Member)\
        .filter(
            Member.status == 'Active',
            Member.expiry_date >= today
        )\
        .group_by(Plan.name).all()
        
    plan_distribution = [{'name': p[0], 'count': p[1]} for p in plan_dist_query]

    return render_template('reports.html',
        active_page='reports',
        new_members_count=new_members_count,
        renewals_count=renewals_count,
        dropouts_count=dropouts_count,
        avg_attendance=avg_attendance,
        daily_trends=daily_trends,     
        monthly_trends=monthly_trends, 
        plan_distribution=plan_distribution
    )