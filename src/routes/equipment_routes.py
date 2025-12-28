from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from datetime import date, datetime
from . import equipment
from src.models import db, Equipment, MaintenanceLog, Expense

@equipment.route('/')
@login_required
def list_equipment():
    all_equipment = Equipment.query.order_by(Equipment.id.desc()).all()
    return render_template('equipment.html',
        active_page='equipment',
        equipment=all_equipment 
    )

@equipment.route('/new', methods=['GET', 'POST'])
@login_required
def new_equipment():
    if request.method == 'POST':
        purchase_price = int(request.form.get('purchase_price', 0)) if request.form.get('purchase_price') else 0
        purchase_date_str = request.form.get('purchase_date')
        
        # FIX: Validate Purchase Date
        try:
            purchase_date_obj = datetime.strptime(purchase_date_str, '%Y-%m-%d').date() if purchase_date_str else date.today()
        except ValueError:
            flash('Invalid Purchase Date format.', 'error')
            return redirect(url_for('equipment.new_equipment'))

        eq = Equipment(
            name=request.form['name'],
            category=request.form.get('category'),
            brand=request.form.get('brand'),
            model=request.form.get('model'),
            purchase_price=purchase_price,
            purchase_date=purchase_date_obj,
            location=request.form.get('location'),
            status=request.form.get('status', 'Working'),
            notes=request.form.get('notes')
        )
        db.session.add(eq)
        
        if purchase_price > 0:
            investment = Expense(
                category='Equipment Purchase',
                amount=purchase_price,
                description=f"Asset Purchase: {eq.name} ({eq.brand or 'N/A'})",
                date=purchase_date_obj,
                payment_method='Cash'
            )
            db.session.add(investment)

        db.session.commit()
        flash(f'Equipment {eq.name} added successfully.', 'success')
        return redirect(url_for('equipment.list_equipment'))
    return render_template('new_equipment.html', active_page='equipment')

@equipment.route('/view/<int:id>')
@login_required
def view_equipment(id):
    eq = Equipment.query.get_or_404(id)
    logs = MaintenanceLog.query.filter_by(equipment_id=id).order_by(MaintenanceLog.date.desc()).all()
    return render_template('view_equipment.html', equipment=eq, maintenance_logs=logs)

@equipment.route('/toggle_status/<int:id>', methods=['POST'])
@login_required
def toggle_status(id):
    eq = Equipment.query.get_or_404(id)
    
    if eq.status == 'Working' or eq.status == 'Operational':
        eq.status = 'Maintenance'
        flash(f'Asset "{eq.name}" moved to Maintenance status.', 'warning')
    else:
        eq.status = 'Operational'
        flash(f'Asset "{eq.name}" marked as Operational.', 'success')
        
    db.session.commit()
    return redirect(url_for('equipment.list_equipment'))


@equipment.route('/maintenance/<int:id>', methods=['POST'])
@login_required
def add_maintenance(id):
    equip = Equipment.query.get_or_404(id)
    cost = float(request.form.get('cost', 0))
    description = request.form.get('description')
    
    # FIX: Validate Maintenance Date
    try:
        maintenance_date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid Date format.', 'error')
        return redirect(url_for('equipment.view_equipment', id=id))
    
    equip.status = 'Maintenance'
    
    expense = Expense(
        category='Maintenance',
        amount=cost,
        description=f"Repair: {equip.name} - {description}",
        date=maintenance_date,
        payment_method='Cash'
    )
    
    log = MaintenanceLog(
        equipment_id=id,
        date=maintenance_date,
        type='Repair',
        description=description,
        cost=cost,
        performed_by='Technician'
    )
    
    db.session.add(expense)
    db.session.add(log)
    db.session.commit()
    
    flash('Maintenance logged.', 'success')
    return redirect(url_for('equipment.view_equipment', id=id))