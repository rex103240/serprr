from src.app import create_app
from src.models import db, Member, Plan, Transaction
from datetime import date, timedelta
import random

app = create_app()

with app.app_context():
    # Ensure we have a plan
    plan = Plan.query.first()
    if not plan:
        plan = Plan(name="Standard", price=1000, duration_days=30)
        db.session.add(plan)
        db.session.commit()

    print("Generating 50 dummy members...")
    
    for i in range(1, 51):
        # Create Dummy Member
        join_date = date.today() - timedelta(days=random.randint(0, 365))
        member = Member(
            member_code=Member.generate_unique_code(),
            name=f"Test Member {i}",
            phone=f"98765432{i:02d}",
            email=f"member{i}@test.com",
            plan_id=plan.id,
            plan_price_at_join=plan.price,
            join_date=join_date,
            expiry_date=join_date + timedelta(days=30),
            status='Active'
        )
        db.session.add(member)
    
    db.session.commit()
    print("✅ Success! Added 50 members.")