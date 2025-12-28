import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///gym.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
    
    SECRET_KEY = os.environ.get("SESSION_SECRET", "ironlifter-secret-key-2024")
    
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")
    
    KIOSK_SECRET_TOKEN = os.environ.get("KIOSK_SECRET", "ironlifter_kiosk_secret_99")
    GRACE_PERIOD_DAYS = int(os.environ.get("GRACE_PERIOD", 5))
    
    TELEGRAM_TOKEN = os.environ.get("TG_TOKEN", "")
    TELEGRAM_CHAT_ID = os.environ.get("TG_CHAT_ID", "")
    
    LICENSE_HOLDER = os.environ.get("LICENSE_HOLDER", "IRONLIFTER GYM")
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
