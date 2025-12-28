from flask import render_template, request, redirect, url_for, flash, send_file, current_app, Response
from flask_login import login_required
from datetime import date, datetime, timedelta
from sqlalchemy import or_, cast, String
from . import members
from src.models import db, Member, Plan, Transaction, Measurement, Attendance
from src.utils.helpers import send_telegram_alert, generate_invoice_number, allowed_file
from src.utils.email_automation import EmailService
import os

@members.route("/")
@login_required
def list_members():
    page = request.args.get("page", 1, type=int)
    per_page = 10
    
    query = db.session.query(Member, Plan).outerjoin(Plan).order_by(Member.id.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    today = date.today()
    members_list = []
    for member, plan in pagination.items:
        days_left = 999
        if member.expiry_date:
            days_left = (member.expiry_date - today).days
        members_list.append({
            "id": member.id,
            "code": member.member_code,
            "name": member.name,
            "phone": member.phone,
            "email": member.email,
            "plan_name": plan.name if plan else "No Plan",
            "join_date": member.join_date,
            "expiry_date": member.expiry_date,
            "status": member.status,
            "photo_path": member.photo_path,
            "days_left": days_left
        })
        
    plans = Plan.query.filter_by(is_active=True).all()
    
    return render_template("members.html",
        active_page="members",
        members=members_list,
        pagination=pagination,
        plans=plans
    )

@members.route("/search")
@login_required
def search_members():
    query = request.args.get("q", "").strip()
    today = date.today()
    
    if not query:
        members_query = db.session.query(Member, Plan).outerjoin(Plan).order_by(Member.id.desc()).limit(10)
    else:
        members_query = db.session.query(Member, Plan).outerjoin(Plan).filter(
            or_(
                Member.name.ilike(f"%{query}%"),
                Member.phone.ilike(f"%{query}%"),
                Member.member_code.ilike(f"%{query}%")
            )
        ).order_by(Member.id.desc()).limit(10)
    
    members_list = []
    for member, plan in members_query:
        days_left = 999
        if member.expiry_date:
            days_left = (member.expiry_date - today).days
        members_list.append({
            "id": member.id,
            "code": member.member_code,
            "name": member.name,
            "phone": member.phone,
            "email": member.email,
            "plan_name": plan.name if plan else "No Plan",
            "join_date": member.join_date,
            "expiry_date": member.expiry_date,
            "status": member.status,
            "photo_path": member.photo_path,
            "days_left": days_left
        })
    
    return render_template("member_rows.html", members=members_list)

@members.route("/new", methods=["GET", "POST"])
@login_required
def new_member():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()
        dob_str = request.form.get("date_of_birth", "").strip()
        join_date_str = request.form.get("join_date", "").strip()
        plan_id = request.form.get("plan_id")

        if not all([name, phone, email, dob_str, join_date_str, plan_id]):
            flash("Please fill in all required fields.", "error")
            return redirect(url_for("members.new_member"))

        try:
            join_date = datetime.strptime(join_date_str, "%Y-%m-%d").date()
            date_of_birth = datetime.strptime(dob_str, "%Y-%m-%d").date()
        except ValueError:
            flash("Invalid date format.", "error")
            return redirect(url_for("members.new_member"))

        photo_filename = None
        if "photo" in request.files:
            file = request.files["photo"]
            if file and allowed_file(file.filename):
                import secrets
                token = secrets.token_hex(8)
                photo_filename = f"member_{token}.jpg"
                upload_path = os.path.join(current_app.static_folder, "uploads", "members")
                os.makedirs(upload_path, exist_ok=True)
                file.save(os.path.join(upload_path, photo_filename))

        plan = Plan.query.get(plan_id)
        if not plan:
            flash("Selected plan does not exist.", "error")
            return redirect(url_for("members.new_member"))
        
        member = Member(
            member_code=Member.generate_unique_code(),
            name=name,
            phone=phone,
            email=email,
            address=request.form.get("address"),
            gender=request.form.get("gender"),
            plan_id=plan.id,
            plan_price_at_join=plan.price,
            join_date=join_date,
            expiry_date=join_date + timedelta(days=plan.duration_days),
            emergency_contact_name=request.form.get("emergency_name"),
            emergency_contact_phone=request.form.get("emergency_phone"),
            emergency_contact_relation=request.form.get("emergency_relation"),
            notes=request.form.get("notes"),
            photo_path=photo_filename,
            date_of_birth=date_of_birth
        )
        
        db.session.add(member)
        db.session.commit()
        
        transaction = Transaction(
            member_id=member.id,
            plan_id=plan.id,
            amount=plan.price,
            date=join_date, 
            payment_method=request.form.get("payment_method", "Cash"),
            transaction_type="New Membership",
            invoice_number=generate_invoice_number()
        )
        db.session.add(transaction)
        db.session.commit()
        
        try:
            EmailService.send_welcome(member, plan, transaction)
        except Exception as e:
            print(f"Failed to send welcome email: {e}")

        flash(f"Member {member.name} added successfully!", "success")
        return redirect(url_for("members.list_members"))

    plans = Plan.query.filter_by(is_active=True).all()
    return render_template("new_member.html", plans=plans, now=datetime.now)


@members.route("/<int:id>")
@login_required
def view_member(id):
    member = Member.query.get_or_404(id)
    plan = Plan.query.get(member.plan_id) if member.plan_id else None

    attendance = Attendance.query.filter_by(member_id=member.id).order_by(Attendance.timestamp.desc()).limit(10).all()
    measurements = Measurement.query.filter_by(member_id=member.id).order_by(Measurement.date.desc()).limit(5).all()
    transactions = Transaction.query.filter_by(member_id=member.id).order_by(Transaction.date.desc()).limit(10).all()

    return render_template(
        "view_member.html",
        member=member,
        plan=plan,
        attendance=attendance,
        measurements=measurements,
        transactions=transactions,
    )


@members.route("/<int:id>/toggle_status", methods=["POST"])
@login_required
def toggle_status(id):
    member = Member.query.get_or_404(id)
    member.status = "Inactive" if member.status == "Active" else "Active"
    db.session.commit()
    flash(f"Member status updated to {member.status}.", "success")
    return redirect(url_for("members.view_member", id=member.id))


@members.route("/<int:id>/renew", methods=["POST"])
@login_required
def renew_member(id):
    member = Member.query.get_or_404(id)
    plan_id = request.form.get("plan_id")
    payment_method = request.form.get("payment_method", "Cash")
    join_date_str = request.form.get("join_date")

    plan = Plan.query.get(plan_id) if plan_id else None
    if not plan:
        flash("Selected plan does not exist.", "error")
        return redirect(url_for("members.view_member", id=member.id))

    try:
        join_date = datetime.strptime(join_date_str, "%Y-%m-%d").date() if join_date_str else date.today()
    except ValueError:
        join_date = date.today()

    member.plan_id = plan.id
    member.plan_price_at_join = plan.price
    member.join_date = join_date
    member.expiry_date = join_date + timedelta(days=plan.duration_days)
    member.status = "Active"

    db.session.add(
        Transaction(
            member_id=member.id,
            plan_id=plan.id,
            amount=plan.price,
            date=join_date,
            payment_method=payment_method,
            transaction_type="Renewal",
            invoice_number=generate_invoice_number(),
        )
    )
    db.session.commit()

    flash("Membership renewed successfully.", "success")
    return redirect(url_for("members.view_member", id=member.id))


@members.route("/<int:id>/edit", methods=["POST"])
@login_required
def edit_member(id):
    member = Member.query.get_or_404(id)

    member.name = request.form.get("name", member.name)
    member.phone = request.form.get("phone", member.phone)
    member.email = request.form.get("email", member.email)
    member.address = request.form.get("address", member.address)
    member.gender = request.form.get("gender", member.gender)
    member.notes = request.form.get("notes", member.notes)

    db.session.commit()
    flash("Member profile updated.", "success")
    return redirect(url_for("members.view_member", id=member.id))


@members.route("/<int:id>/measurement", methods=["POST"])
@login_required
def add_measurement(id):
    member = Member.query.get_or_404(id)

    def _to_float(v):
        try:
            return float(v) if v not in (None, "") else None
        except ValueError:
            return None

    measurement = Measurement(
        member_id=member.id,
        date=date.today(),
        weight=_to_float(request.form.get("weight")),
        height=_to_float(request.form.get("height")),
        chest=_to_float(request.form.get("chest")),
        waist=_to_float(request.form.get("waist")),
        hips=_to_float(request.form.get("hips")),
        biceps=_to_float(request.form.get("biceps")),
        thighs=_to_float(request.form.get("thighs")),
        body_fat=_to_float(request.form.get("body_fat")),
        notes=request.form.get("notes"),
    )
    db.session.add(measurement)
    db.session.commit()

    flash("Measurement recorded.", "success")
    return redirect(url_for("members.view_member", id=member.id))


@members.route("/<int:id>/delete", methods=["POST"])
@login_required
def delete_member(id):
    member = Member.query.get_or_404(id)
    db.session.delete(member)
    db.session.commit()
    flash("Member deleted.", "success")
    return redirect(url_for("members.list_members"))


@members.route("/invoice/<int:transaction_id>")
@login_required
def download_invoice(transaction_id):
    # Minimal stub: ensures template does not 500 due to missing route.
    # If you already have invoice generation elsewhere, we can wire it here.
    transaction = Transaction.query.get_or_404(transaction_id)
    return Response(
        f"Invoice download not implemented yet. Transaction ID: {transaction.id}",
        mimetype="text/plain",
    )
