import secrets
from datetime import datetime
from src.models import db, Staff, User
from src.utils.email_automation import EmailService

class StaffManager:
    @staticmethod
    def create_staff_account(form_data):
        """
        Handles the complete flow of onboarding a new staff member:
        1. Validates if the email is free.
        2. Creates the Staff Profile (HR data).
        3. Generates a secure random password.
        4. Creates the User Login (System access).
        5. Triggers the Welcome Email.
        
        Returns: (Success: bool, Message: str)
        """
        email = form_data['email']
        name = form_data['name']
        
        # --- FIX: Split Full Name into First & Last Name ---
        name_parts = name.strip().split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        # ---------------------------------------------------
        
        # 1. Validation: Check if email already has a login
        if User.query.filter_by(username=email).first():
            return False, "Error: A user with this email already exists."
        
        # 2. Security: Generate Random Password (8 chars)
        generated_password = secrets.token_hex(4) # e.g., 'f8a1b2c9'
        
        try:
            # 3. Create Staff Profile (For Salary/Attendance)
            # We use first_name and last_name here to match the database model
            new_staff = Staff(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=form_data['phone'],
                position=form_data['role'],
                salary=form_data['salary'],
                hire_date=datetime.strptime(form_data['join_date'], '%Y-%m-%d').date()
            )
            db.session.add(new_staff)
            
            # 4. Create User Login (For Dashboard Access)
            # User model still uses a single 'name' field
            new_user = User(
                username=email,
                name=name,
                email=email,
                phone=form_data['phone'],
                role='staff'
            )
            new_user.set_password(generated_password)
            db.session.add(new_user)
            
            # Commit both records in one transaction
            db.session.commit()
            
            # 5. Send Welcome Email
            try:
                EmailService.send_staff_welcome(new_staff, generated_password)
            except Exception as e:
                print(f"WARNING: Staff created but email failed: {e}")
                return True, f"Staff added (Login: {email} / Pwd: {generated_password}), but email failed."
            
            return True, f"Staff added successfully! Login credentials sent to {email}"
            
        except Exception as e:
            db.session.rollback() # Undo changes if anything fails
            return False, f"Database Error: {str(e)}"