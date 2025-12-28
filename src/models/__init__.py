import secrets
import string
from flask_login import UserMixin
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import inspect, text

# 1. Import db from extensions
from src.extensions import db

# Constants
MEMBER_CODE_LENGTH = 5

# 2. Import Staff models from the separate file
# (We import StaffAttendance, not Attendance)
from .staff import Staff, SalaryPayment, StaffAttendance

# --- USERS ---
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='staff')
    name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# --- GYM CORE ---
class Plan(db.Model):
    __tablename__ = 'plans'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    duration_days = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    members = db.relationship('Member', backref='plan', lazy='dynamic')

class Member(db.Model):
    __tablename__ = 'members'
    id = db.Column(db.Integer, primary_key=True)
    # Public-facing 5-digit member code (e.g. 12345). Unique and indexed.
    member_code = db.Column(db.String(MEMBER_CODE_LENGTH), unique=True, index=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    photo_path = db.Column(db.String(255))
    emergency_contact_name = db.Column(db.String(100))
    emergency_contact_phone = db.Column(db.String(20))
    emergency_contact_relation = db.Column(db.String(50))
    plan_id = db.Column(db.Integer, db.ForeignKey('plans.id'))
    plan_price_at_join = db.Column(db.Integer)
    join_date = db.Column(db.Date, default=date.today)
    expiry_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='Active')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # Note: 'Attendance' here refers to MEMBER attendance (defined below), 
    # which is different from StaffAttendance (imported above).
    attendance_logs = db.relationship('Attendance', backref='member', lazy='dynamic', cascade="all, delete-orphan")
    measurements = db.relationship('Measurement', backref='member', lazy='dynamic', cascade="all, delete-orphan")
    transactions = db.relationship('Transaction', backref='member', lazy='dynamic', cascade="all, delete-orphan")
    
    def calculate_expiry(self):
        if self.join_date and self.plan:
            return self.join_date + timedelta(days=self.plan.duration_days)
        return None
    
    def days_remaining(self):
        if self.expiry_date:
            return (self.expiry_date - date.today()).days
        return 0
    
    def is_expired(self):
        return self.days_remaining() < 0

    @staticmethod
    def generate_unique_code():
        """Generate a unique 5-digit numeric member_code (10000-99999)."""
        while True:
            code = str(secrets.randbelow(90000) + 10000)  # 10000-99999
            if not Member.query.filter_by(member_code=code).first():
                return code

class Measurement(db.Model):
    __tablename__ = 'measurements'
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    date = db.Column(db.Date, default=date.today)
    weight = db.Column(db.Float)
    height = db.Column(db.Float)
    chest = db.Column(db.Float)
    waist = db.Column(db.Float)
    hips = db.Column(db.Float)
    biceps = db.Column(db.Float)
    thighs = db.Column(db.Float)
    body_fat = db.Column(db.Float)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# This is MEMBER Attendance (separate from StaffAttendance)
class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=True)
    # Removing staff_id from here since staff track their attendance in the 'staff_attendance' table
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    check_type = db.Column(db.String(10), default='in')
    date = db.Column(db.Date, default=date.today)
    status = db.Column(db.String(20)) 

# --- EQUIPMENT ---
class Equipment(db.Model):
    __tablename__ = 'equipment'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    brand = db.Column(db.String(50))
    model = db.Column(db.String(50))
    purchase_date = db.Column(db.Date)
    purchase_price = db.Column(db.Integer)
    warranty_expiry = db.Column(db.Date)
    status = db.Column(db.String(20), default='Working')
    location = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    maintenance_logs = db.relationship('MaintenanceLog', backref='equipment', lazy='dynamic', cascade="all, delete-orphan")

class MaintenanceLog(db.Model):
    __tablename__ = 'maintenance_logs'
    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    date = db.Column(db.Date, default=date.today)
    type = db.Column(db.String(50))
    description = db.Column(db.Text)
    cost = db.Column(db.Integer, default=0)
    performed_by = db.Column(db.String(100))
    next_service_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# --- FINANCE ---
class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'))
    plan_id = db.Column(db.Integer, db.ForeignKey('plans.id'))
    amount = db.Column(db.Integer, nullable=False)
    payment_method = db.Column(db.String(50), default='Cash')
    transaction_type = db.Column(db.String(50), default='Membership')
    date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    invoice_number = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Expense(db.Model):
    __tablename__ = 'expenses'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    payment_method = db.Column(db.String(50))
    date = db.Column(db.Date, default=date.today)

class Revenue(db.Model):
    __tablename__ = 'revenue'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, default=date.today)

def init_db(app):
    with app.app_context():
        db.create_all()

        # Ensure the member_code column exists in the members table (for existing SQLite DBs)
        try:
            inspector = inspect(db.engine)
            cols = [c['name'] for c in inspector.get_columns('members')]
            if 'member_code' not in cols:
                print("INFO: Adding member_code column to members table...")
                db.session.execute(text("ALTER TABLE members ADD COLUMN member_code VARCHAR(5)"))
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"WARNING: Could not ensure member_code column exists: {e}")

        # Ensure every member has a unique 5-digit member_code
        missing_codes = Member.query.filter((Member.member_code == None) | (Member.member_code == '')).all()
        if missing_codes:
            print(f"INFO: Assigning member_code for {len(missing_codes)} existing members...")
            for m in missing_codes:
                m.member_code = Member.generate_unique_code()
            db.session.commit()

        if not User.query.filter_by(role='admin').first():
            # For security, do NOT fall back to hard-coded defaults here.
            # Require ADMIN_USERNAME and ADMIN_PASSWORD to be set via
            # environment variables / .env (see Config in src.config).
            admin_username = app.config.get('ADMIN_USERNAME')
            admin_password = app.config.get('ADMIN_PASSWORD')

            if not admin_username or not admin_password:
                print("SECURITY WARNING: No admin user exists and ADMIN_USERNAME/ADMIN_PASSWORD are not set. "
                      "Skipping automatic admin creation. Set these values and rerun init_db, "
                      "or create an admin user manually via the application.")
                return
            
            admin = User(
                username=admin_username,
                email='admin@ironlifter.com',
                role='admin'
            )
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
            print(f"INFO: Admin account '{admin_username}' initialized successfully.")
