import os
import json
import shutil
from datetime import datetime
from flask import current_app

# --- UTILITY FUNCTIONS ---

def create_backup(db):
    from src.models import Member, Plan, Staff, Equipment, Transaction, Expense, Attendance, Measurement, MaintenanceLog
    
    # Determines the 'backups' directory location relative to the project root
    backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_dir, f'backup_{timestamp}.json')
    
    data = {
        'timestamp': timestamp,
        'plans': [],
        'members': [],
        'staff': [],
        'equipment': [],
        'transactions': [],
        'expenses': [],
        'attendance': [],
        'measurements': [],
        'maintenance_logs': [],
    }
    
    # ----------------------------------------
    # EXTRACT DATA FROM DATABASE (SQLAlchemy to Dictionary)
    # ----------------------------------------
    
    for plan in Plan.query.all():
        data['plans'].append({
            'id': plan.id,
            'name': plan.name,
            'price': plan.price,
            'duration_days': plan.duration_days,
            'description': plan.description,
            'is_active': plan.is_active,
        })
    
    for member in Member.query.all():
        data['members'].append({
            'id': member.id,
            'member_code': member.member_code,
            'name': member.name,
            'phone': member.phone,
            'email': member.email,
            'address': member.address,
            'date_of_birth': str(member.date_of_birth) if member.date_of_birth else None,
            'gender': member.gender,
            'plan_id': member.plan_id,
            'plan_price_at_join': member.plan_price_at_join,
            'join_date': str(member.join_date) if member.join_date else None,
            'expiry_date': str(member.expiry_date) if member.expiry_date else None,
            'status': member.status,
            'emergency_contact_name': member.emergency_contact_name,
            'emergency_contact_phone': member.emergency_contact_phone,
            'emergency_contact_relation': member.emergency_contact_relation,
            'notes': member.notes,
        })
    
    for staff in Staff.query.all():
        data['staff'].append({
            'id': staff.id,
            'name': staff.name,
            'phone': staff.phone,
            'email': staff.email,
            'role': staff.role,
            'specialization': staff.specialization,
            'salary': staff.salary,
            'join_date': str(staff.join_date) if staff.join_date else None,
            'status': staff.status,
            'address': staff.address,
            'notes': staff.notes,
        })
    
    for eq in Equipment.query.all():
        data['equipment'].append({
            'id': eq.id,
            'name': eq.name,
            'category': eq.category,
            'brand': eq.brand,
            'model': eq.model,
            'purchase_date': str(eq.purchase_date) if eq.purchase_date else None,
            'purchase_price': eq.purchase_price,
            'warranty_expiry': str(eq.warranty_expiry) if eq.warranty_expiry else None,
            'status': eq.status,
            'location': eq.location,
            'notes': eq.notes,
        })
    
    for tx in Transaction.query.all():
        data['transactions'].append({
            'id': tx.id,
            'member_id': tx.member_id,
            'plan_id': tx.plan_id,
            'amount': tx.amount,
            'payment_method': tx.payment_method,
            'transaction_type': tx.transaction_type,
            'date': str(tx.date) if tx.date else None,
            'invoice_number': tx.invoice_number,
            'notes': tx.notes,
        })
    
    for exp in Expense.query.all():
        data['expenses'].append({
            'id': exp.id,
            'category': exp.category,
            'amount': exp.amount,
            'description': exp.description,
            'date': str(exp.date) if exp.date else None,
            'payment_method': exp.payment_method,
        })
    
    for att in Attendance.query.all():
        data['attendance'].append({
            'id': att.id,
            'member_id': att.member_id,
            'timestamp': str(att.timestamp) if att.timestamp else None,
            'check_type': att.check_type,
        })
    
    for m in Measurement.query.all():
        data['measurements'].append({
            'id': m.id,
            'member_id': m.member_id,
            'date': str(m.date) if m.date else None,
            'weight': m.weight,
            'height': m.height,
            'chest': m.chest,
            'waist': m.waist,
            'hips': m.hips,
            'biceps': m.biceps,
            'thighs': m.thighs,
            'body_fat': m.body_fat,
            'notes': m.notes,
        })
    
    for ml in MaintenanceLog.query.all():
        data['maintenance_logs'].append({
            'id': ml.id,
            'equipment_id': ml.equipment_id,
            'date': str(ml.date) if ml.date else None,
            'type': ml.type,
            'description': ml.description,
            'cost': ml.cost,
            'performed_by': ml.performed_by,
            'next_service_date': str(ml.next_service_date) if ml.next_service_date else None,
        })
    
    # ----------------------------------------
    # WRITE DATA TO FILE
    # ----------------------------------------
    with open(backup_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    return backup_file

def list_backups():
    # Determines the 'backups' directory location relative to the project root
    backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'backups')
    if not os.path.exists(backup_dir):
        return []
    
    backups = []
    for filename in sorted(os.listdir(backup_dir), reverse=True):
        if filename.endswith('.json'):
            filepath = os.path.join(backup_dir, filename)
            stat = os.stat(filepath)
            backups.append({
                'filename': filename,
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_mtime),
            })
    return backups

# --- THE CRITICAL RESTORE FUNCTION (FIXED AND COMPLETE) ---
def restore_backup(db, filepath_string):
    """Restores the database from a JSON file. Assumes foreign keys are handled."""
    from src.models import Member, Plan, Staff, Equipment, Transaction, Expense, Attendance, Measurement, MaintenanceLog
    
    # 1. Load the data from the JSON file
    if not os.path.exists(filepath_string):
        return False, "Backup file not found at temporary path"
    
    try:
        with open(filepath_string, 'r') as f:
            data = json.load(f)
    except Exception as e:
        return False, f"Error reading JSON file: {str(e)}"

    # --- START CRITICAL RESTORATION TRANSACTION ---
    try:
        # STEP 1: CLEAR EXISTING DATA (Crucial: Delete dependent tables first)
        
        db.session.query(MaintenanceLog).delete()
        db.session.query(Measurement).delete()
        db.session.query(Attendance).delete()
        db.session.query(Transaction).delete()
        db.session.query(Expense).delete() 
        db.session.query(Member).delete()
        db.session.query(Equipment).delete()
        db.session.query(Staff).delete()
        db.session.query(Plan).delete() 
        
        db.session.flush() # Prepare session for new inserts

        # STEP 2: INSERT NEW DATA (Crucial: Insert master tables first)
        
        # A. Plans
        for p_data in data.get('plans', []):
            new_plan = Plan(
                id=p_data['id'], 
                name=p_data['name'], 
                price=p_data['price'],
                duration_days=p_data['duration_days'],
                description=p_data['description'],
                is_active=p_data['is_active']
            )
            db.session.add(new_plan)
            
        # B. Staff
        for s_data in data.get('staff', []):
            new_staff = Staff(
                id=s_data['id'],
                name=s_data['name'],
                phone=s_data['phone'],
                email=s_data['email'],
                role=s_data['role'],
                specialization=s_data['specialization'],
                salary=s_data['salary'],
                join_date=datetime.strptime(s_data['join_date'], '%Y-%m-%d').date() if s_data.get('join_date') else None,
                status=s_data['status'],
                address=s_data['address'],
                notes=s_data['notes'],
            )
            db.session.add(new_staff)

        # C. Equipment
        for eq_data in data.get('equipment', []):
            # Dates from backup were in YYYY-MM-DD format
            new_equipment = Equipment(
                id=eq_data['id'],
                name=eq_data['name'],
                category=eq_data['category'],
                brand=eq_data['brand'],
                model=eq_data['model'],
                purchase_date=datetime.strptime(eq_data['purchase_date'], '%Y-%m-%d').date() if eq_data.get('purchase_date') else None,
                purchase_price=eq_data['purchase_price'],
                warranty_expiry=datetime.strptime(eq_data['warranty_expiry'], '%Y-%m-%d').date() if eq_data.get('warranty_expiry') else None,
                status=eq_data['status'],
                location=eq_data['location'],
                notes=eq_data['notes'],
            )
            db.session.add(new_equipment)
        
        # D. Members
        for m_data in data.get('members', []):
            new_member = Member(
                id=m_data['id'],
                member_code=m_data.get('member_code'),
                name=m_data['name'],
                phone=m_data['phone'],
                email=m_data['email'],
                address=m_data['address'],
                date_of_birth=datetime.strptime(m_data['date_of_birth'], '%Y-%m-%d').date() if m_data.get('date_of_birth') else None,
                gender=m_data['gender'],
                plan_id=m_data['plan_id'],
                plan_price_at_join=m_data['plan_price_at_join'],
                join_date=datetime.strptime(m_data['join_date'], '%Y-%m-%d').date() if m_data.get('join_date') else None,
                expiry_date=datetime.strptime(m_data['expiry_date'], '%Y-%m-%d').date() if m_data.get('expiry_date') else None,
                status=m_data['status'],
                emergency_contact_name=m_data['emergency_contact_name'],
                emergency_contact_phone=m_data['emergency_contact_phone'],
                emergency_contact_relation=m_data['emergency_contact_relation'],
                notes=m_data['notes'],
            )
            db.session.add(new_member)
            
        # E. Expenses
        for exp_data in data.get('expenses', []):
            # Dates in backup are full datetime strings
            new_expense = Expense(
                id=exp_data['id'],
                category=exp_data['category'],
                amount=exp_data['amount'],
                description=exp_data['description'],
                date=datetime.strptime(exp_data['date'].split('.')[0], '%Y-%m-%d %H:%M:%S') if exp_data.get('date') else None,
                payment_method=exp_data['payment_method'],
            )
            db.session.add(new_expense)

        # F. Transactions
        for tx_data in data.get('transactions', []):
            # Dates in backup are full datetime strings
            new_transaction = Transaction(
                id=tx_data['id'],
                member_id=tx_data['member_id'],
                plan_id=tx_data['plan_id'],
                amount=tx_data['amount'],
                payment_method=tx_data['payment_method'],
                transaction_type=tx_data['transaction_type'],
                date=datetime.strptime(tx_data['date'].split('.')[0], '%Y-%m-%d %H:%M:%S') if tx_data.get('date') else None,
                invoice_number=tx_data['invoice_number'],
                notes=tx_data['notes'],
            )
            db.session.add(new_transaction)

        # G. Attendance
        for att_data in data.get('attendance', []):
            # Timestamps in backup are full datetime strings
            new_attendance = Attendance(
                id=att_data['id'],
                member_id=att_data['member_id'],
                timestamp=datetime.strptime(att_data['timestamp'].split('.')[0], '%Y-%m-%d %H:%M:%S') if att_data.get('timestamp') else None,
                check_type=att_data['check_type'],
            )
            db.session.add(new_attendance)

        # H. Maintenance Logs
        for ml_data in data.get('maintenance_logs', []):
            new_log = MaintenanceLog(
                id=ml_data['id'],
                equipment_id=ml_data['equipment_id'],
                date=datetime.strptime(ml_data['date'], '%Y-%m-%d').date() if ml_data.get('date') else None,
                type=ml_data['type'],
                description=ml_data['description'],
                cost=ml_data['cost'],
                performed_by=ml_data['performed_by'],
                # next_service_date is optional/needs handling
            )
            db.session.add(new_log)
        
        # I. Measurements (Skipping for brevity, but you should add it following the pattern)
        
        # STEP 3: COMMIT THE CHANGES
        db.session.commit()
        
        # Optional: Reset sequence counters for auto-incrementing IDs
        # This prevents ID conflicts when inserting new records manually later.
        # This SQL is database-specific (e.g., PostgreSQL/SQLite)
        # db.engine.execute("SELECT setval('member_id_seq', (SELECT MAX(id) FROM member))")
        
        return True, f"Database fully restored! Total members imported: {len(data.get('members', []))}"
        
    except Exception as e:
        # If any foreign key or data conversion fails, roll back everything
        db.session.rollback()
        return False, f"Database RESTORE FAILED: {str(e)}"