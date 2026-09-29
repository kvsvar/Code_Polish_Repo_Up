"""
admin.py
--------
Everything the Admin role can do:
- dashboard with counts
- create/edit/delete treks
- approve or blacklist staff registrations
- assign staff to a trek
- view all users/staff/treks/bookings
- search across treks/staff/users
- blacklist trekkers
"""

# pyrefly: ignore [missing-import]
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import get_db
from helpers import login_required, role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/dashboard")
@login_required
@role_required("admin")
def dashboard():
    db = get_db()
    trek_count = db.execute("SELECT COUNT(*) count FROM treks").fetchone()["count"]
    user_count = db.execute("SELECT COUNT(*) count FROM users WHERE role='trekker'").fetchone()["count"]
    staff_count = db.execute("SELECT COUNT(*) count FROM users WHERE role='staff'").fetchone()["count"]
    booking_count = db.execute("SELECT COUNT(*) count FROM bookings").fetchone()["count"]
    pending_staff = db.execute(
        "SELECT * FROM users WHERE role='staff' AND staff_status='pending'"
    ).fetchall()
    db.close()
    return render_template(
        "admin/dashboard.html",
        trek_count=trek_count,
        user_count=user_count,
        staff_count=staff_count,
        booking_count=booking_count,
        pending_staff=pending_staff,
    )


# ---------------- TREKS ----------------

@admin_bp.route("/treks")
@login_required
@role_required("admin")
def treks():
    db = get_db()
    search_query = request.args.get("q", "").strip()
    if search_query:
        treks = db.execute(
            """SELECT t.*, u.name AS staff_name FROM treks t
               LEFT JOIN users u ON u.id = t.assigned_staff_id
               WHERE t.name LIKE ? OR t.location LIKE ? OR t.id = ?""",
            (f"%{search_query}%", f"%{search_query}%", search_query if search_query.isdigit() else -1),
        ).fetchall()
    else:
        treks = db.execute(
            """SELECT t.*, u.name AS staff_name FROM treks t
               LEFT JOIN users u ON u.id = t.assigned_staff_id
               ORDER BY t.id DESC"""
        ).fetchall()
    db.close()
    return render_template("admin/treks.html", treks=treks, q=search_query)


@admin_bp.route("/treks/new", methods=["GET", "POST"])
@login_required
@role_required("admin")
def new_trek():
    db = get_db()
    if request.method == "POST":
        name = request.form["name"].strip()
        location = request.form["location"].strip()
        difficulty = request.form["difficulty"]
        duration_days = int(request.form["duration_days"])
        total_slots = int(request.form["total_slots"])
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")

        if duration_days <= 0:
            flash("Duration must be > 0.", "danger")
            return render_template("admin/trek_form.html", trek=None)
        if total_slots <= 0:
            flash("Slots must be > 0.", "danger")
            return render_template("admin/trek_form.html", trek=None)
        if start_date and end_date and start_date > end_date:
            flash("End date cannot be before start date.", "danger")
            return render_template("admin/trek_form.html", trek=None)

        db.execute(
            """INSERT INTO treks (name, location, difficulty, duration_days,
               available_slots, total_slots, start_date, end_date)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, location, difficulty, duration_days, total_slots, total_slots, start_date, end_date),
        )
        db.commit()
        db.close()
        flash("Trek created.", "success")
        return redirect(url_for("admin.treks"))
    db.close()
    return render_template("admin/trek_form.html", trek=None)


@admin_bp.route("/treks/<int:trek_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin")
def edit_trek(trek_id):
    db = get_db()
    trek = db.execute("SELECT * FROM treks WHERE id = ?", (trek_id,)).fetchone()
    if trek is None:
        db.close()
        flash("Trek not found.", "danger")
        return redirect(url_for("admin.treks"))

    if request.method == "POST":
        name = request.form["name"].strip()
        location = request.form["location"].strip()
        difficulty = request.form["difficulty"]
        duration_days = int(request.form["duration_days"])
        total_slots = int(request.form["total_slots"])
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")

        if duration_days <= 0:
            flash("Duration must be > 0.", "danger")
            return render_template("admin/trek_form.html", trek=trek)
        if total_slots <= 0:
            flash("Slots must be > 0.", "danger")
            return render_template("admin/trek_form.html", trek=trek)
        if start_date and end_date and start_date > end_date:
            flash("End date cannot be before start date.", "danger")
            return render_template("admin/trek_form.html", trek=trek)

        # Keep available_slots consistent if total_slots changes:
        # shift available by the same delta as total.
        delta = total_slots - trek["total_slots"]
        new_available = max(0, trek["available_slots"] + delta)

        db.execute(
            """UPDATE treks SET name=?, location=?, difficulty=?, duration_days=?,
               total_slots=?, available_slots=?, start_date=?, end_date=? WHERE id=?""",
            (name, location, difficulty, duration_days, total_slots, new_available,
             start_date, end_date, trek_id),
        )
        db.commit()
        db.close()
        flash("Trek updated.", "success")
        return redirect(url_for("admin.treks"))

    db.close()
    return render_template("admin/trek_form.html", trek=trek)


@admin_bp.route("/treks/<int:trek_id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_trek(trek_id):
    db = get_db()
    db.execute("DELETE FROM treks WHERE id = ?", (trek_id,))
    db.commit()
    db.close()
    flash("Trek deleted.", "info")
    return redirect(url_for("admin.treks"))


@admin_bp.route("/treks/<int:trek_id>/assign", methods=["GET", "POST"])
@login_required
@role_required("admin")
def assign_staff(trek_id):
    db = get_db()
    trek = db.execute("SELECT * FROM treks WHERE id = ?", (trek_id,)).fetchone()
    staff_list = db.execute(
        "SELECT * FROM users WHERE role='staff' AND staff_status='approved'"
    ).fetchall()

    if request.method == "POST":
        staff_id = request.form["staff_id"]
        # Approving a trek's staff assignment also opens it for booking.
        db.execute(
            "UPDATE treks SET assigned_staff_id = ?, status = 'Open' WHERE id = ?",
            (staff_id, trek_id),
        )
        db.commit()
        db.close()
        flash("Staff assigned and trek opened.", "success")
        return redirect(url_for("admin.treks"))

    db.close()
    return render_template("admin/assign_staff.html", trek=trek, staff_list=staff_list)


# ---------------- STAFF APPROVAL ----------------

@admin_bp.route("/staff")
@login_required
@role_required("admin")
def staff_list():
    db = get_db()
    search_query = request.args.get("q", "").strip()
    if search_query:
        staff = db.execute(
            "SELECT * FROM users WHERE role='staff' AND (name LIKE ? OR id = ?)",
            (f"%{search_query}%", search_query if search_query.isdigit() else -1),
        ).fetchall()
    else:
        staff = db.execute("SELECT * FROM users WHERE role='staff' ORDER BY id DESC").fetchall()
    db.close()
    return render_template("admin/staff.html", staff=staff, q=search_query)


@admin_bp.route("/staff/<int:staff_id>/approve", methods=["POST"])
@login_required
@role_required("admin")
def approve_staff(staff_id):
    db = get_db()
    db.execute("UPDATE users SET staff_status = 'approved' WHERE id = ?", (staff_id,))
    db.commit()
    db.close()
    flash("Staff approved.", "success")
    return redirect(url_for("admin.staff_list"))


@admin_bp.route("/staff/<int:staff_id>/blacklist", methods=["POST"])
@login_required
@role_required("admin")
def blacklist_staff(staff_id):
    db = get_db()
    db.execute("UPDATE users SET staff_status = 'blacklisted' WHERE id = ?", (staff_id,))
    db.commit()
    db.close()
    flash("Staff blacklisted.", "info")
    return redirect(url_for("admin.staff_list"))


# ---------------- USERS (TREKKERS) ----------------

@admin_bp.route("/users")
@login_required
@role_required("admin")
def users_list():
    db = get_db()
    search_query = request.args.get("q", "").strip()
    if search_query:
        users = db.execute(
            "SELECT * FROM users WHERE role='trekker' AND (name LIKE ? OR id = ?)",
            (f"%{search_query}%", search_query if search_query.isdigit() else -1),
        ).fetchall()
    else:
        users = db.execute("SELECT * FROM users WHERE role='trekker' ORDER BY id DESC").fetchall()
    db.close()
    return render_template("admin/users.html", users=users, q=search_query)


@admin_bp.route("/users/<int:user_id>/blacklist", methods=["POST"])
@login_required
@role_required("admin")
def blacklist_user(user_id):
    db = get_db()
    db.execute("UPDATE users SET is_blacklisted = 1 WHERE id = ?", (user_id,))
    db.commit()
    db.close()
    flash("User blacklisted.", "info")
    return redirect(url_for("admin.users_list"))


@admin_bp.route("/users/<int:user_id>/unblacklist", methods=["POST"])
@login_required
@role_required("admin")
def unblacklist_user(user_id):
    db = get_db()
    db.execute("UPDATE users SET is_blacklisted = 0 WHERE id = ?", (user_id,))
    db.commit()
    db.close()
    flash("User unblocked.", "success")
    return redirect(url_for("admin.users_list"))


# ---------------- BOOKINGS (VIEW ALL) ----------------

@admin_bp.route("/bookings")
@login_required
@role_required("admin")
def bookings():
    db = get_db()
    bookings = db.execute(
        """SELECT b.*, u.name AS user_name, t.name AS trek_name
           FROM bookings b
           JOIN users u ON u.id = b.user_id
           JOIN treks t ON t.id = b.trek_id
           ORDER BY b.id DESC"""
    ).fetchall()
    db.close()
    return render_template("admin/bookings.html", bookings=bookings)
