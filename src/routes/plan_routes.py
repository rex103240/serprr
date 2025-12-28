from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from . import plans
from src.models import db, Plan, Member
from src.utils.helpers import admin_required

@plans.route('/')
@login_required
def list_plans():
    all_plans = Plan.query.order_by(Plan.id).all()
    return render_template('plans.html',
        active_page='plans',
        plans=all_plans
    )

@plans.route('/create', methods=['POST'])
@login_required
def create_plan():
    duration_value = int(request.form['duration_value'])
    duration_unit = int(request.form['duration_unit'])
    total_days = duration_value * duration_unit
    
    plan = Plan(
        name=request.form['name'],
        price=int(request.form['price']),
        duration_days=total_days,
        description=request.form.get('description')
    )
    
    db.session.add(plan)
    db.session.commit()
    
    flash(f'Plan "{plan.name}" created successfully!', 'success')
    return redirect(url_for('plans.list_plans'))

@plans.route('/edit/<int:id>', methods=['POST'])
@login_required
def edit_plan(id):
    plan = Plan.query.get_or_404(id)
    
    plan.name = request.form['name']
    plan.price = int(request.form['price'])
    
    if request.form.get('duration_value') and request.form.get('duration_unit'):
        duration_value = int(request.form['duration_value'])
        duration_unit = int(request.form['duration_unit'])
        plan.duration_days = duration_value * duration_unit
    
    plan.description = request.form.get('description')
    plan.is_active = request.form.get('is_active') == 'on'
    
    db.session.commit()
    
    flash(f'Plan "{plan.name}" updated!', 'success')
    return redirect(url_for('plans.list_plans'))

@plans.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_plan(id):
    plan = Plan.query.get_or_404(id)
    
    member_count = Member.query.filter_by(plan_id=id).count()
    if member_count > 0:
        flash(f'Cannot delete plan. {member_count} members are using it.', 'error')
        return redirect(url_for('plans.list_plans'))
    
    name = plan.name
    db.session.delete(plan)
    db.session.commit()
    
    flash(f'Plan "{name}" deleted.', 'success')
    return redirect(url_for('plans.list_plans'))
