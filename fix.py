from src.app import create_app
from src.models import db

app = create_app()

with app.app_context():
    print("⏳ Checking database tables...")
    db.create_all()
    print("✅ SUCCESS: Database tables (Expense & Revenue) created/updated!")
    print("   You can now run 'python main.py' without errors.")