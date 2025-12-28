import sqlite3
import datetime
import webbrowser
import os
import sys
import random
import requests 
import socket
import functools
import multiprocessing
import uuid 
import json 
import tkinter as tk
from threading import Timer
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response, session

# ==========================================
# 🔧 CONFIGURATION & SECRETS
# ==========================================
app = Flask(__name__)
app.secret_key = 'RAMU'

# Admin Credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password123"

# --- LICENSE CONFIGURATION ---

LICENSE_FILE = "license.dat"
# NOTE: Ensure the URL has quotes "" around it!
LICENSE_SERVER_URL = "https://praful102.pythonanywhere.com/verify"

def verify_license_online(key):
    """Talks to PythonAnywhere to validate key"""
    hwid = get_hwid()
    
    # We use the variable defined at the top
    print(f"[DEBUG] Connecting to: {LICENSE_SERVER_URL}") 

    try:
        # SENDING THE REQUEST
        response = requests.post(LICENSE_SERVER_URL, json={"key": key, "hwid": hwid}, timeout=10)
        
        # DEBUG: Print what the server actually replied
        print(f"[DEBUG] Server Status: {response.status_code}")
        print(f"[DEBUG] Server Text: {response.text}")

        if response.status_code == 200:
            return True, "Verified"
        else:
            # If server crashes, this prevents the app from crashing too
            try:
                msg = response.json().get('message', 'Invalid Key')
            except:
                msg = f"Server returned error code: {response.status_code}"
            return False, msg

    except requests.exceptions.ConnectionError:
        return False, "Connection Failed: No Internet or Server Offline"
    except Exception as e:
        return False, f"Error: {str(e)}"

# API Security
KIOSK_SECRET_TOKEN = "ironlifter_kiosk_secret_99"

# Telegram Config (Replace with your keys)
TELEGRAM_TOKEN = os.environ.get('TG_TOKEN', '8469837865:AAFi6PVFw85Av7V5fNa0znFJ3oegDIKLBBQ')
TELEGRAM_CHAT_ID = os.environ.get('TG_CHAT_ID', '-5034684928')

# Business Logic
GRACE_PERIOD_DAYS = 5
LICENSE_HOLDER = "IRONLIFTER GYM"
DB_NAME = 'gym_database_v2.db'

if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(application_path, DB_NAME)

# ==========================================
# 🛡️ LICENSING & SECURITY SYSTEM
# ==========================================
def get_hwid():
    """Get unique machine fingerprint"""
    try:
        # Windows specific UUID
        if os.name == 'nt':
            cmd = subprocess.check_output('wmic csproduct get uuid', shell=True)
            return str(cmd).split('\\r\\n')[1].strip()
        else:
            # Fallback for Mac/Linux (just in case)
            return str(uuid.getnode())
    except:
        return "UNKNOWN-HWID"

def verify_license_online(key):
    """Talks to PythonAnywhere to validate key"""
    hwid = get_hwid()
    try:
        response = requests.post(LICENSE_SERVER_URL, json={"key": key, "hwid": hwid}, timeout=5)
        if response.status_code == 200:
            return True, "Verified"
        else:
            return False, response.json().get('message', 'Invalid Key')
    except requests.exceptions.ConnectionError:
        # OFFLINE MODE LOGIC could go here (Checking last_verified date)
        # For now, we will return False if no internet during INITIAL activation
        return False, "No Internet Connection"

def show_activation_window():
    """
    A simple popup asking for the License Key. 
    Blocks the app until a valid key is entered.
    """
    root = tk.Tk()
    root.title("Ironlifter Activation")
    root.geometry("400x250")
    root.configure(bg="#1A1A1A")
    
    # Center it
    x = (root.winfo_screenwidth()/2) - 200
    y = (root.winfo_screenheight()/2) - 125
    root.geometry('+%d+%d' % (x, y))

    tk.Label(root, text="ACTIVATION REQUIRED", font=("Segoe UI", 16, "bold"), fg="#D4AF37", bg="#1A1A1A").pack(pady=20)
    tk.Label(root, text="Please enter your Product Key:", fg="white", bg="#1A1A1A").pack()
    
    entry_key = tk.Entry(root, width=30, font=("Consolas", 12))
    entry_key.pack(pady=10)
    
    status_label = tk.Label(root, text="", fg="red", bg="#1A1A1A")
    status_label.pack(pady=5)

    def on_activate():
        key = entry_key.get().strip()
        status_label.config(text="Verifying...", fg="yellow")
        root.update()
        
        is_valid, message = verify_license_online(key)
        
        if is_valid:
            # SAVE THE KEY LOCALLY
            with open(LICENSE_FILE, 'w') as f:
                f.write(key)
            status_label.config(text="Success! Starting...", fg="#00FF00")
            root.after(1000, root.destroy) # Close window and continue app
        else:
            status_label.config(text=f"Error: {message}", fg="red")

    tk.Button(root, text="ACTIVATE", command=on_activate, bg="#D4AF37", fg="black", font=("Segoe UI", 10, "bold")).pack(pady=20)
    
    root.protocol("WM_DELETE_WINDOW", sys.exit) # Exit app if they close the window
    root.mainloop()

def check_startup_license():
    """
    Runs at startup. 
    1. Checks if license file exists.
    2. If not, shows Activation Window.
    3. If yes, runs background check (optional: strictly enforce online check here).
    """
    if not os.path.exists(LICENSE_FILE):
        # No license found? HALT and show activation.
        show_activation_window()
    else:
        # License found. Read it.
        with open(LICENSE_FILE, 'r') as f:
            stored_key = f.read().strip()
        
        # OPTIONAL: Run a "Silent Check" in background here
        # For now, we assume if the file is there, let them in (Offline Mode support)
        print(f"[Ironlifter] License found: {stored_key}")

# ==========================================
# 🖥️ ORIGINAL SPLASH SCREEN
# ==========================================
def show_splash_screen():
    try:
        root = tk.Tk()
        width, height = 600, 380
        root.overrideredirect(True) 
        
        # Center on screen
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width/2) - (width/2)
        y = (screen_height/2) - (height/2)
        root.geometry('%dx%d+%d+%d' % (width, height, x, y))
        root.configure(bg='#0F0F0F')
        
        # UI Elements
        tk.Label(root, text="IRONLIFTER", font=("Segoe UI", 42, "bold"), fg='#FFFFFF', bg='#0F0F0F').pack(pady=(45, 0))
        tk.Label(root, text="YOUR GYM'S DIGITAL PARTNER", font=("Segoe UI", 10, "bold"), fg='#D4AF37', bg='#0F0F0F').pack(pady=(5, 20))
        tk.Label(root, text="LICENSED TO:", font=("Segoe UI", 9), fg='#666666', bg='#0F0F0F').pack()
        tk.Label(root, text=LICENSE_HOLDER, font=("Segoe UI", 16, "bold"), fg='#FFFFFF', bg='#0F0F0F').pack(pady=(0, 20))

        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            ip_text = f"MOBILE IP:  {local_ip}:5000"
        except: ip_text = "MOBILE ACCESS: Check Network"

        ip_frame = tk.Frame(root, bg='#1A1A1A', bd=1, relief="flat")
        ip_frame.pack(pady=5, ipadx=10, ipady=3)
        tk.Label(ip_frame, text=ip_text, font=("Consolas", 10, "bold"), fg='#00FF00', bg='#1A1A1A').pack()

        # Original Animation Logic
        canvas = tk.Canvas(root, width=600, height=4, bg='#222', highlightthickness=0)
        canvas.pack(side='bottom')
        
        def animate_bar(w=0):
            if w < 600:
                canvas.delete("all")
                canvas.create_rectangle(0, 0, w, 4, fill='#D4AF37', width=0)
                root.after(15, lambda: animate_bar(w+4))
            else: 
                root.destroy()

        animate_bar()
        root.mainloop()
    except Exception as e: 
        print(f"Splash Failed: {e}")

# ==========================================
# 🔐 AUTHENTICATION
# ==========================================
def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def kiosk_token_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('X-Kiosk-Secret')
        if token != KIOSK_SECRET_TOKEN:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        return f(*args, **kwargs)
    return decorated_function

# ==========================================
# 🗄️ DATABASE
# ==========================================
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
                    price INTEGER NOT NULL, duration_days INTEGER NOT NULL
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS members (
                    id INTEGER PRIMARY KEY, name TEXT NOT NULL, phone TEXT, email TEXT,
                    plan_id INTEGER, plan_price_at_join INTEGER, join_date DATE,
                    status TEXT DEFAULT 'Active', days_saved_on_pause INTEGER DEFAULT 0,
                    FOREIGN KEY(plan_id) REFERENCES plans(id)
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, member_id INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(member_id) REFERENCES members(id)
                )''')
    c.execute('SELECT count(*) FROM plans')
    if c.fetchone()[0] == 0:
        c.executemany('INSERT INTO plans (name, price, duration_days) VALUES (?,?,?)', 
                      [('Monthly Standard', 1500, 30), ('Quarterly Saver', 4000, 90), 
                       ('Annual Pro', 12000, 365), ('Daily Pass', 200, 1)])
    conn.commit()
    conn.close()

app.jinja_env.filters['format_date'] = lambda v: datetime.datetime.strptime(str(v), '%Y-%m-%d').strftime('%d-%m-%Y') if v else ""

def calculate_expiry(join_date_str, duration_days):
    try:
        join_date = datetime.datetime.strptime(join_date_str, '%Y-%m-%d').date()
        expiry_date = join_date + datetime.timedelta(days=duration_days)
        days_remaining = (expiry_date - datetime.date.today()).days
        return days_remaining, expiry_date
    except:
        return 0, datetime.date.today()

def send_telegram_alert(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, data=data, timeout=2) 
    except: pass

def update_expired_members():
    conn = get_db_connection()
    active = conn.execute('SELECT m.id, m.name, m.join_date, p.duration_days FROM members m JOIN plans p ON m.plan_id = p.id WHERE m.status="Active"').fetchall()
    for m in active:
        days_left, _ = calculate_expiry(m['join_date'], m['duration_days'])
        if days_left < -GRACE_PERIOD_DAYS:
            conn.execute("UPDATE members SET status='Inactive' WHERE id=?", (m['id'],))
    conn.commit()
    conn.close()

# ==========================================
# 🚦 ROUTES
# ==========================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USERNAME and request.form['password'] == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid Username or Password', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    update_expired_members()
    conn = get_db_connection()
    today = datetime.date.today()
    total = conn.execute('SELECT COUNT(*) FROM members').fetchone()[0]
    active = conn.execute("SELECT COUNT(*) FROM members WHERE status='Active'").fetchone()[0]
    checkins = conn.execute("SELECT COUNT(*) FROM attendance WHERE date(timestamp) = ?", (today,)).fetchone()[0]
    dues_query = conn.execute('SELECT m.name, p.name as plan_name, m.join_date, p.duration_days FROM members m JOIN plans p ON m.plan_id = p.id WHERE m.status="Active"').fetchall()
    upcoming = []
    for m in dues_query:
        days, expiry = calculate_expiry(m['join_date'], m['duration_days'])
        if days <= 7: upcoming.append({'name': m['name'], 'plan_name': m['plan_name'], 'expiry_date': expiry, 'days_left': days})
    all_members = conn.execute('SELECT * FROM members ORDER BY id DESC LIMIT 50').fetchall()
    conn.close()
    return render_template('dashboard.html', active_page='dashboard', total_members=total, active_members=active, checkins_today=checkins, upcoming_dues=upcoming, all_members_list=all_members)

@app.route('/members')
@login_required
def members():
    conn = get_db_connection()
    members = conn.execute('SELECT m.*, p.name as plan_name, p.duration_days FROM members m LEFT JOIN plans p ON m.plan_id = p.id ORDER BY m.id DESC').fetchall()
    plans = conn.execute('SELECT * FROM plans').fetchall()
    conn.close()
    return render_template('members.html', active_page='members', members=members, plans=plans)

@app.route('/members/new', methods=('GET', 'POST'))
@login_required
def new_member():
    conn = get_db_connection()
    if request.method == 'POST':
        new_id = int(request.form.get('custom_id')) if request.form.get('custom_id') else random.randint(1000, 9999)
        if conn.execute('SELECT id FROM members WHERE id = ?', (new_id,)).fetchone():
            flash(f'ID {new_id} already exists!', 'error')
            return redirect(url_for('new_member'))
        plan = conn.execute('SELECT * FROM plans WHERE id = ?', (request.form['plan_id'],)).fetchone()
        conn.execute('INSERT INTO members (id, name, phone, email, plan_id, plan_price_at_join, join_date) VALUES (?,?,?,?,?,?,?)', 
                     (new_id, request.form['name'], request.form['phone'], request.form['email'], plan['id'], plan['price'], request.form['join_date']))
        conn.commit()
        send_telegram_alert(f"🆕 **NEW MEMBER**\nName: {request.form['name']}\nID: #{new_id}")
        flash(f"Member {request.form['name']} added successfully!", 'success')
        return redirect(url_for('members'))
    plans = conn.execute('SELECT * FROM plans').fetchall()
    conn.close()
    return render_template('new_member.html', active_page='members', plans=plans, today=datetime.date.today())

@app.route('/plans', methods=('GET', 'POST'))
@login_required
def manage_plans():
    conn = get_db_connection()
    if request.method == 'POST':
        total_days = int(request.form['duration_value']) * int(request.form['duration_unit'])
        conn.execute('INSERT INTO plans (name, price, duration_days) VALUES (?, ?, ?)', (request.form['name'], int(request.form['price']), total_days))
        conn.commit()
        flash('Plan created successfully!', 'success')
        return redirect(url_for('manage_plans'))
    plans = conn.execute('SELECT * FROM plans').fetchall()
    conn.close()
    return render_template('plans.html', active_page='plans', plans=plans)

@app.route('/plans/delete/<int:id>', methods=['POST'])
@login_required
def delete_plan(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM plans WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Plan deleted.', 'success')
    return redirect(url_for('manage_plans'))

@app.route('/api/checkin', methods=['POST'])
@kiosk_token_required
def api_checkin():
    try: member_id = int(request.json.get('member_id'))
    except: return jsonify({'success': False, 'message': 'Invalid ID'})
    conn = get_db_connection()
    member = conn.execute('SELECT m.*, p.name as plan_name, p.duration_days FROM members m JOIN plans p ON m.plan_id = p.id WHERE m.id = ?', (member_id,)).fetchone()
    if not member:
        conn.close()
        return jsonify({'success': False, 'message': 'Member Not Found'})
    if member['status'] != 'Active':
        conn.close()
        send_telegram_alert(f"🚫 **DENIED**\n{member['name']} (Inactive)")
        return jsonify({'success': False, 'message': 'Membership Inactive'})
    days_left, _ = calculate_expiry(member['join_date'], member['duration_days'])
    if days_left < -GRACE_PERIOD_DAYS:
        conn.close()
        return jsonify({'success': False, 'message': 'Plan Expired. Please Pay.'})
    if conn.execute("SELECT 1 FROM attendance WHERE member_id=? AND date(timestamp)=?", (member_id, datetime.date.today())).fetchone():
        conn.close()
        return jsonify({'success': False, 'message': 'Already Checked In'})
    conn.execute('INSERT INTO attendance (member_id) VALUES (?)', (member_id,))
    conn.commit()
    conn.close()
    warning = f"Fees Due in {days_left} days" if days_left <= 7 else None
    send_telegram_alert(f"✅ **CHECK-IN**\n{member['name']}\nPlan: {member['plan_name']}")
    return jsonify({'success': True, 'member_name': member['name'], 'plan': member['plan_name'], 'due_warning': warning})

@app.route('/kiosk')
def kiosk():
    return render_template('kiosk.html', kiosk_mode=True, api_secret=KIOSK_SECRET_TOKEN)

# ==========================================
# 🚀 LAUNCHER
# ==========================================
if __name__ == '__main__':
    multiprocessing.freeze_support()
    
    # 1. DATABASE INIT
    init_db()

    # 2. LICENSE CHECK (The New Gatekeeper)
    # This will BLOCK the app if no license is found
    check_startup_license() 

    # 3. SPLASH SCREEN
    splash_process = multiprocessing.Process(target=show_splash_screen)
    splash_process.start()
    splash_process.join()  

    # 4. OPEN BROWSER
    def open_browser():
        webbrowser.open_new('http://127.0.0.1:5000/login')
    
    Timer(1, open_browser).start()
    
    # 5. START SERVER
    print("--- IRONLIFTER IS RUNNING ---")
    app.run(debug=False, host='0.0.0.0', port=5000)