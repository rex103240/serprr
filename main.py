import multiprocessing
import tkinter as tk
import socket
import webbrowser
from waitress import serve
from threading import Timer
from src.app import app  # Import your structured app

# ==========================================
# 🖥️ SPLASH SCREEN LOGIC
# ==========================================
def show_splash_screen():
    try:
        root = tk.Tk()
        width, height = 600, 380
        
        # Remove window border (Make it look like a floating graphic)
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
        tk.Label(root, text="LICENSED TO: IRONLIFTER GYM", font=("Segoe UI", 12), fg='#666666', bg='#0F0F0F').pack()

        # --- FIND MOBILE IP ---
        # This trick finds your real WiFi IP address for the phone
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            ip_text = f"MOBILE ACCESS:  {local_ip}:5000"
        except: 
            ip_text = "MOBILE ACCESS: Check Network"

        # Show IP in a green box so you can see it easily
        ip_frame = tk.Frame(root, bg='#1A1A1A', bd=1, relief="flat")
        ip_frame.pack(pady=20, ipadx=10, ipady=5)
        tk.Label(ip_frame, text=ip_text, font=("Consolas", 14, "bold"), fg='#00FF00', bg='#1A1A1A').pack()

        # Loading Bar Animation
        canvas = tk.Canvas(root, width=600, height=4, bg='#222', highlightthickness=0)
        canvas.pack(side='bottom')
        
        def animate_bar(w=0):
            if w < 600:
                canvas.delete("all")
                canvas.create_rectangle(0, 0, w, 4, fill='#D4AF37', width=0)
                root.after(6, lambda: animate_bar(w+5)) # Speed of loading
            else: 
                root.destroy() # Close splash when full

        animate_bar()
        root.mainloop()
    except Exception as e: 
        print(f"Splash Failed: {e}")

# ==========================================
# 🚀 MAIN LAUNCHER
# ==========================================
if __name__ == '__main__':
    # Required for Windows executables
    multiprocessing.freeze_support()

    # 1. Run Splash Screen (Blocks until animation finishes)
    # This stays EXACTLY the same. It runs first.
    splash_process = multiprocessing.Process(target=show_splash_screen)
    splash_process.start()
    splash_process.join()

    # 2. Open Browser Automatically after 1.5 seconds
    # This also stays the same.
    def open_browser():
        webbrowser.open_new('http://127.0.0.1:5000')

    Timer(1.5, open_browser).start()

    # 3. Start the Server (The Upgrade)
    print("--- IRONLIFTER SERVER STARTED (PRODUCTION MODE) ---")
    print("Running on http://0.0.0.0:5000")
    

  
    serve(app, host='0.0.0.0', port=5000, threads=8)