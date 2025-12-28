from src.extensions import db
from datetime import datetime

class Staff(db.Model):
    __tablename__ = 'staff'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    position = db.Column(db.String(50))
    salary = db.Column(db.Float)
    hire_date = db.Column(db.Date, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Active') # Added status field
    
    # Relationships
    salary_payments = db.relationship('SalaryPayment', backref='staff', lazy=True)
    attendance = db.relationship('StaffAttendance', backref='staff', lazy=True)

    # --- MAGIC PROPERTIES (Fixes HTML Crashes) ---
    @property
    def name(self):
        """Allows {{ staff.name }} to work in HTML"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def role(self):
        """Allows {{ staff.role }} to work (maps to position)"""
        return self.position

    @property
    def join_date(self):
        """Allows {{ staff.join_date }} to work (maps to hire_date)"""
        return self.hire_date

    def __repr__(self):
        return f'<Staff {self.first_name} {self.last_name}>'

class SalaryPayment(db.Model):
    __tablename__ = 'salary_payments'
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.Date, default=datetime.utcnow)
    notes = db.Column(db.String(255))
    
    # Helper for HTML to display description
    @property
    def description(self):
        return self.notes or "Salary Payment"
        
    @property
    def date(self):
        return self.payment_date

class StaffAttendance(db.Model):
    __tablename__ = 'staff_attendance'
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False) # e.g., 'Present', 'Absent'