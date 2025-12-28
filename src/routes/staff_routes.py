from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from src.models import db, Staff, SalaryPayment, StaffAttendance, User
from datetime import datetime
from src.utils.email_automation import EmailService
from src.utils.staff_manager import StaffManager 

staff_routes = Blueprint('staff', __name__)

@staff_routes.route('/')
@login_required
def list_staff():
    staff_members = Staff.query.all()
    return render_template('staff.html', active_page='staff', staff=staff_members)

@staff_routes.route('/new', methods=['GET', 'POST'])
@login_required
def new_staff():
    if request.method == 'POST':
        success, message = StaffManager.create_staff_account(request.form)
        if success:
            flash(message, 'success')
            return redirect(url_for('staff.list_staff'))
        else:
            flash(message, 'error')
            return redirect(url_for('staff.new_staff'))
    return render_template('new_staff.html', now=datetime.now)

@staff_routes.route('/view/<int:id>')
@login_required
def view_staff(id):
    staff = Staff.query.get_or_404(id)
    payments = SalaryPayment.query.filter_by(staff_id=id).order_by(SalaryPayment.payment_date.desc()).all()
    attendance = StaffAttendance.query.filter_by(staff_id=id).order_by(StaffAttendance.date.desc()).limit(30).all()
    
    return render_template('view_staff.html', 
                           staff=staff, 
                           payments=payments, 
                           attendance=attendance, 
                           now=datetime.now())

@staff_routes.route('/edit/<int:id>', methods=['POST'])
@login_required
def edit_staff(id):
    staff = Staff.query.get_or_404(id)
    if 'name' in request.form:
        parts = request.form['name'].strip().split(' ', 1)
        staff.first_name = parts[0]
        if len(parts) > 1:
            staff.last_name = parts[1]
    staff.email = request.form.get('email', staff.email)
    staff.phone = request.form.get('phone', staff.phone)
    staff.position = request.form.get('position', staff.position)
    if request.form.get('salary'):
        staff.salary = request.form['salary']
    db.session.commit()
    flash('Staff details updated successfully', 'success')
    return redirect(url_for('staff.view_staff', id=id))

# --- NEW EXPLICIT STATUS ROUTES ---
@staff_routes.route('/set_leave/<int:id>', methods=['POST'])
@login_required
def set_leave(id):
    staff = Staff.query.get_or_404(id)
    # Toggle only between Active and On Leave
    staff.status = 'On Leave' if staff.status == 'Active' else 'Active'
    db.session.commit()
    EmailService.send_staff_status_change(staff, staff.status)
    flash(f'Staff status updated to {staff.status}', 'info')
    return redirect(url_for('staff.view_staff', id=id))

@staff_routes.route('/deactivate/<int:id>', methods=['POST'])
@login_required
def deactivate_staff(id):
    staff = Staff.query.get_or_404(id)
    # Jump directly to Inactive and disable login
    staff.status = 'Inactive'
    linked_user = User.query.filter_by(username=staff.email).first()
    if linked_user:
        linked_user.is_active = False
    db.session.commit()
    EmailService.send_staff_status_change(staff, 'Inactive')
    flash('Staff member deactivated and login access disabled.', 'warning')
    return redirect(url_for('staff.view_staff', id=id))

@staff_routes.route('/reactivate/<int:id>', methods=['POST'])
@login_required
def reactivate_staff(id):
    staff = Staff.query.get_or_404(id)
    staff.status = 'Active'
    
    # Re-enable system login for the user account
    linked_user = User.query.filter_by(username=staff.email).first()
    if linked_user:
        linked_user.is_active = True
        
    db.session.commit()
    EmailService.send_staff_status_change(staff, 'Active')
    flash('Staff member reactivated and login access restored.', 'success')
    return redirect(url_for('staff.view_staff', id=id))


@staff_routes.route('/add_salary/<int:id>', methods=['POST'])
@login_required
def add_salary(id):
    staff = Staff.query.get_or_404(id)
    amount = request.form.get('amount')
    if not amount:
        flash('Payment failed: Amount was not provided.', 'danger')
        return redirect(url_for('staff.view_staff', id=id))
    date_str = request.form.get('payment_date', datetime.now().strftime('%Y-%m-%d'))
    pay_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    month_str = pay_date.strftime('%B %Y')
    payment = SalaryPayment(
        staff_id=id, amount=float(amount),
        payment_date=pay_date,
        notes=request.form.get('notes', f"Salary for {month_str}")
    )
    db.session.add(payment)
    db.session.commit()
    EmailService.send_salary_slip(staff, amount, month_str, date_str)
    flash('Salary payment recorded & email sent!', 'success')
    return redirect(url_for('staff.view_staff', id=id))

@staff_routes.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_staff(id):
    staff = Staff.query.get_or_404(id)
    linked_user = User.query.filter_by(username=staff.email).first()
    if linked_user:
        db.session.delete(linked_user)
    db.session.delete(staff)
    db.session.commit()
    flash('Staff member deleted.', 'success')
    return redirect(url_for('staff.list_staff'))

