from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
from datetime import datetime, date
import calendar
from sqlalchemy import func, and_
from src.models import db, Expense, Transaction, Member, Plan  # Import Member and Plan

finance_bp = Blueprint('finance', __name__)

@finance_bp.route('/')
@login_required
def finance_dashboard():
    # 1. GET MONTH FILTER
    filter_month = request.args.get('filter_month')
    if not filter_month:
        filter_month = date.today().strftime('%Y-%m')

    # 2. CALCULATE DATE RANGE
    try:
        year, month = map(int, filter_month.split('-'))
        _, last_day = calendar.monthrange(year, month)
        start_date = date(year, month, 1)
        end_date = date(year, month, last_day)
        
        # Format month for display (e.g., "January 2025")
        month_display = datetime(year, month, 1).strftime('%B %Y')
    except ValueError:
        start_date = date.today().replace(day=1)
        end_date = date.today()
        month_display = date.today().strftime('%B %Y')

    # 3. CALCULATE TOTALS
    total_revenue = db.session.query(func.sum(Transaction.amount)).filter(
        and_(Transaction.date >= start_date, Transaction.date <= end_date)
    ).scalar() or 0
    
    total_expenses = db.session.query(func.sum(Expense.amount)).filter(
        and_(Expense.date >= start_date, Expense.date <= end_date)
    ).scalar() or 0

    # 4. FETCH TRANSACTIONS WITH PLAN NAMES
    # We join Transaction -> Member -> Plan to get the plan name
    transactions_data = db.session.query(
        Transaction.date,
        Transaction.amount,
        Member.name.label('member_name'),
        Plan.name.label('plan_name')
    ).join(Member, Transaction.member_id == Member.id)\
     .outerjoin(Plan, Member.plan_id == Plan.id)\
     .filter(and_(Transaction.date >= start_date, Transaction.date <= end_date))\
     .order_by(Transaction.date.desc())\
     .all()

    # 5. FETCH EXPENSES
    expenses = Expense.query.filter(
        and_(Expense.date >= start_date, Expense.date <= end_date)
    ).order_by(Expense.date.desc()).all()

    return render_template(
        'finance.html',
        active_page='finance',
        total_revenue=total_revenue,
        total_expenses=total_expenses,
        profit=total_revenue - total_expenses,
        income=total_revenue, 
        expense=total_expenses, 
        expenses=expenses,
        transactions=transactions_data, # Passing the joined data
        selected_month=filter_month,
        month_display=month_display, # Passing formatted month name
        now=datetime.now()
    )

@finance_bp.route('/add_expense', methods=['POST'])
@login_required
def add_expense():
    try:
        # FIX: Convert input to Integer to match the new Model type
        # We use int(float()) to safely handle "50.0" strings without crashing
        amount = int(float(request.form.get('amount', 0)))
        
        description = request.form.get('description', '')
        category = request.form.get('category', 'Other')
        exp_date_str = request.form.get('date')
        
        if exp_date_str:
            exp_date = datetime.strptime(exp_date_str, '%Y-%m-%d').date()
        else:
            exp_date = date.today()
        
        # Validation: prevent negative expense
        if amount < 0:
            raise ValueError("Expense amount cannot be negative.")

        new_expense = Expense(
            amount=amount,
            description=description,
            category=category,
            payment_method="Cash",
            date=exp_date
        )
        db.session.add(new_expense)
        db.session.commit()
        flash('Expense recorded successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding expense: {str(e)}', 'danger')
        
    return redirect(url_for('finance.finance_dashboard'))