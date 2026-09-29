"""
auth.py
-------
Registration and login/logout for Staff and Trekkers.
Admin never registers here - it's seeded in database.py.

Sessions store: user_id, name, role. That's all downstream routes
need to know who's logged in and what they're allowed to do.
"""

# pyrefly: ignore [missing-import]
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
# pyrefly: ignore [missing-import]
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        contact = request.form.get("contact", "").strip()
        role = request.form["role"]  # 'staff' or 'trekker' only - form restricts this

        if role not in ("staff", "trekker"):
            flash("Invalid role.", "danger")
            return redirect(url_for("auth.register"))

        db = get_db()
        existing_user = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing_user:
            flash("An account with that email already exists.", "danger")
            db.close()
            return redirect(url_for("auth.register"))

        # Staff need admin approval before they can log in and see their
        # dashboard; trekkers can use the app immediately.
        staff_status = "pending" if role == "staff" else None

        db.execute(
            """INSERT INTO users (name, email, password_hash, role, contact, staff_status)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (name, email, generate_password_hash(password), role, contact, staff_status),
        )
        db.commit()
        db.close()

        if role == "staff":
            flash("Registered! Your account needs admin approval before you can log in.", "info")
        else:
            flash("Registration successful. You can now log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        db.close()

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password.", "danger")
            return redirect(url_for("auth.login"))

        if user["role"] == "staff" and user["staff_status"] != "approved":
            if user["staff_status"] == "blacklisted":
                flash("Your staff account has been blacklisted.", "danger")
            else:
                flash("Your staff account is still awaiting admin approval.", "warning")
            return redirect(url_for("auth.login"))

        if user["role"] == "trekker" and user["is_blacklisted"]:
            flash("Your account has been blacklisted.", "danger")
            return redirect(url_for("auth.login"))

        # Set up the session - this is all "logged in" means here
        session["user_id"] = user["id"]
        session["name"] = user["name"]
        session["role"] = user["role"]

        if user["role"] == "admin":
            return redirect(url_for("admin.dashboard"))
        elif user["role"] == "staff":
            return redirect(url_for("staff.dashboard"))
        else:
            return redirect(url_for("user.dashboard"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("auth.login"))
