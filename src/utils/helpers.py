import os
import requests
from datetime import datetime, date
from functools import wraps
from flask import current_app, flash, redirect, url_for
from flask_login import current_user

# --- IMPROVED: SAFELY HANDLE BAD DATES ---
def format_date(value, format='%d-%m-%Y'):
    if value is None:
        return ''
    
    # If it's already a string (common after JSON imports)
    if isinstance(value, str):
        try:
            # Try to convert standard SQL date string to your display format
            date_obj = datetime.strptime(value, '%Y-%m-%d')
            return date_obj.strftime(format)
        except:
            # If conversion fails, JUST RETURN THE STRING. Do not crash.
            return value
            
    # If it's a real Python date object, format it normally
    try:
        return value.strftime(format)
    except:
        return str(value)

def format_datetime(value, format='%d-%m-%Y %H:%M'):
    if value is None:
        return ''
    if isinstance(value, str):
        return value
    return value.strftime(format)

# --- IMPROVED: SAFELY HANDLE STRING NUMBERS ---
def format_currency(value):
    if value is None:
        return '₹0'
    try:
        # Convert to float first to handle strings like "1500" or "1500.00"
        num_val = float(value)
        return f'₹{int(num_val):,}'
    except:
        # If it's text (like "Free"), just return it
        return str(value)

def allowed_file(filename):
    if not filename:
        return False
    
    allowed = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif'})
    
    # Use werkzeug's secure_filename to sanitize
    from werkzeug.utils import secure_filename
    safe_filename = secure_filename(filename)
    
    if not safe_filename:
        return False
    
    # Check extension
    return '.' in safe_filename and safe_filename.rsplit('.', 1)[1].lower() in allowed

def secure_upload_file(file, upload_folder, max_size_mb=5):
    """Securely upload a file with validation"""
    if not file or file.filename == '':
        return None
    
    import os
    import secrets
    from PIL import Image
    from werkzeug.utils import secure_filename
    
    # Validate file
    if not allowed_file(file.filename):
        raise ValueError("File type not allowed")
    
    # Check file size
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Reset position
    
    max_size_bytes = max_size_mb * 1024 * 1024
    if size > max_size_bytes:
        raise ValueError(f"File size exceeds {max_size_mb}MB limit")
    
    # Generate secure filename
    filename = secure_filename(file.filename)
    token = secrets.token_hex(8)
    name, ext = os.path.splitext(filename)
    secure_name = f"{token}_{name}{ext}"
    
    # Create upload directory if it doesn't exist
    os.makedirs(upload_folder, exist_ok=True)
    
    file_path = os.path.join(upload_folder, secure_name)
    
    # For images, validate and optimize
    if ext.lower() in ['.png', '.jpg', '.jpeg', '.gif']:
        try:
            # Open and validate image
            img = Image.open(file)
            img.verify()  # Verify it's a valid image
            
            # Re-open for saving (verify() closes the file)
            file.seek(0)
            img = Image.open(file)
            
            # Convert to RGB if necessary (for JPEG compatibility)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Resize if too large (max 1200x1200)
            max_size = (1200, 1200)
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save optimized image
            save_ext = 'JPEG' if ext.lower() in ['.jpg', '.jpeg'] else ext.upper().replace('.', '')
            img.save(file_path, save_ext, quality=85, optimize=True)
            
        except Exception as e:
            raise ValueError(f"Invalid image file: {str(e)}")
    else:
        # For non-image files, just save directly
        file.save(file_path)
    
    return secure_name

def send_telegram_alert(message):
    token = current_app.config.get('TELEGRAM_TOKEN')
    chat_id = current_app.config.get('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        return False
    
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
        requests.post(url, data=data, timeout=2)
        return True
    except:
        return False

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required.', 'error')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def generate_invoice_number():
    now = datetime.now()
    return f"INV-{now.strftime('%Y%m%d%H%M%S')}"

def calculate_age(birth_date):
    if not birth_date:
        return None
    
    # Handle if birth_date comes in as a string
    if isinstance(birth_date, str):
        try:
            birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
        except:
            return 0
            
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))