from flask import render_template, request, redirect, url_for, flash, send_file, current_app
from flask_login import login_required, current_user
from datetime import date
from . import settings
from src.models import db, User
from src.utils.helpers import admin_required
from src.utils.backup import create_backup, list_backups, restore_backup

@settings.route('/')
@login_required
@admin_required
def index():
    backups = list_backups()
    users = User.query.all() if current_user.role == 'admin' else []
    
    return render_template('settings.html',
        active_page='settings',
        backups=backups,
        users=users
    )

@settings.route('/backup', methods=['POST'])
@login_required
@admin_required
def create_backup_route():
    try:
        backup_file = create_backup(db)
        flash(f'Backup created successfully!', 'success')
    except Exception as e:
        flash(f'Backup failed: {str(e)}', 'error')
    
    return redirect(url_for('settings.index'))
@settings.route('/backup/restore', methods=['POST'])
@login_required
@admin_required
def restore_backup_route():
    # 1. Check if a file was uploaded in the form
    if 'backup_file' not in request.files:
        flash('No file part in the request.', 'error')
        return redirect(url_for('settings.index'))
    
    file = request.files['backup_file']
    
    # 2. Check if the filename is empty
    if file.filename == '':
        flash('No selected file.', 'error')
        return redirect(url_for('settings.index'))
    
    # 3. Process the file if it exists and has a JSON extension
    if file and file.filename.endswith('.json'):
        try:
            # Save the uploaded file temporarily
            import os
            
            # Use the 'instance' folder which is often used for app-specific data
            upload_dir = os.path.join(current_app.instance_path, 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            temp_filepath = os.path.join(upload_dir, file.filename)
            file.save(temp_filepath)
            
            # CALL THE CORE RESTORE LOGIC
            restore_backup(db, temp_filepath)
            
            # Clean up the temporary file
            os.remove(temp_filepath) 
            
            flash(f'Database restored successfully from {file.filename}!', 'success')
            
            # Important: The application needs to be restarted to fully reload the session data
            return redirect(url_for('settings.index', message='RESTART_REQUIRED'))

        except Exception as e:
            flash(f'Restore failed: {str(e)}', 'error')
            return redirect(url_for('settings.index'))
            
    flash('Invalid file format. Must be a .json file.', 'error')
    return redirect(url_for('settings.index'))

@settings.route('/backup/download/<filename>')
@login_required
@admin_required
def download_backup(filename):
    import os
    backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'backups')
    filepath = os.path.join(backup_dir, filename)
    
    if not os.path.exists(filepath):
        flash('Backup file not found.', 'error')
        return redirect(url_for('settings.index'))
    
    return send_file(filepath, as_attachment=True)

@settings.route('/user/new', methods=['POST'])
@login_required
@admin_required
def create_user():
    username = request.form['username']
    
    if User.query.filter_by(username=username).first():
        flash('Username already exists.', 'error')
        return redirect(url_for('settings.index'))
    
    user = User(
        username=username,
        role=request.form.get('role', 'staff'),
        name=request.form.get('name'),
        email=request.form.get('email'),
        phone=request.form.get('phone')
    )
    user.set_password(request.form['password'])
    
    db.session.add(user)
    db.session.commit()
    
    flash(f'User {username} created!', 'success')
    return redirect(url_for('settings.index'))

@settings.route('/user/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_user(id):
    if id == current_user.id:
        flash('Cannot delete your own account.', 'error')
        return redirect(url_for('settings.index'))
    
    user = User.query.get_or_404(id)
    username = user.username
    
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {username} deleted.', 'success')
    return redirect(url_for('settings.index'))

@settings.route('/password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form['current_password']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']
    
    if not current_user.check_password(current_password):
        flash('Current password is incorrect.', 'error')
        return redirect(url_for('settings.index'))
    
    if new_password != confirm_password:
        flash('New passwords do not match.', 'error')
        return redirect(url_for('settings.index'))
    
    if len(new_password) < 6:
        flash('Password must be at least 6 characters.', 'error')
        return redirect(url_for('settings.index'))
    
    current_user.set_password(new_password)
    db.session.commit()
    
    flash('Password changed successfully!', 'success')
    return redirect(url_for('settings.index'))
