# pyrefly: ignore [missing-import]
from sqlite3 import dbapi2
# pyrefly: ignore [missing-import]
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import get_db
from helpers import login_required, role_required

staff_bp = Blueprint("staff", __name__, url_prefix="/staff")


@staff_bp.route("/dashboard")
@login_required
@role_required("staff")
def dashboard():
    db = get_db()
    staff_id = session["user_id"]
    treks = db.execute(
        "SELECT * FROM treks WHERE assigned_staff_id = ? ORDER BY id DESC", (staff_id,)
    ).fetchall()

    # participant counts per trek, for the dashboard summary
    trek_counts = {}
    for trek in treks:
        booking_count = db.execute(
            "SELECT COUNT(*) count FROM bookings WHERE trek_id = ? AND status = 'Booked'",
            (trek["id"],),
        ).fetchone()["count"]
        trek_counts[trek["id"]] = booking_count
    db.close()
    return render_template("staff/dashboard.html", treks=treks, trek_counts=trek_counts)


@staff_bp.route("/treks/<int:trek_id>/update", methods=["GET", "POST"])
@login_required
@role_required("staff")
def update_trek(trek_id):
    db = get_db()
    trek = db.execute(
        "SELECT * FROM treks WHERE id = ? AND assigned_staff_id = ?",
        (trek_id, session["user_id"]),
    ).fetchone()

    if trek is None:
        db.close()
        flash("That trek isn't assigned to you.", "danger")
        return redirect(url_for("staff.dashboard"))

    if request.method == "POST":
        available_slots = int(request.form["available_slots"])
        status = request.form["status"]

        # Can't set available slots higher than total capacity
        available_slots = min(available_slots, trek["total_slots"])

        db.execute("""
            UPDATE treks
            SET available_slots = ?, status = ?
            WHERE id = ? AND assigned_staff_id = ?
        """, (available_slots, status, trek_id, session["user_id"]))

        if status == "Completed":
            db.execute("""
                UPDATE bookings
                SET status = 'Completed'
                WHERE trek_id = ?
                AND status = 'Booked'
            """, (trek_id,))

        db.commit()
        db.close()
        flash("Trek updated.", "success")
        return redirect(url_for("staff.dashboard"))

    db.close()
    return render_template("staff/update_trek.html", trek=trek)


@staff_bp.route("/treks/<int:trek_id>/participants")
@login_required
@role_required("staff")
def participants(trek_id):
    db = get_db()
    trek = db.execute(
        "SELECT * FROM treks WHERE id = ? AND assigned_staff_id = ?",
        (trek_id, session["user_id"]),
    ).fetchone()

    if trek is None:
        db.close()
        flash("That trek isn't assigned to you.", "danger")
        return redirect(url_for("staff.dashboard"))

    bookings = db.execute(
        """SELECT b.*, u.name AS user_name, u.contact FROM bookings b
           JOIN users u ON u.id = b.user_id
           WHERE b.trek_id = ? ORDER BY b.id DESC""",
        (trek_id,),
    ).fetchall()
    db.close()
    return render_template("staff/participants.html", trek=trek, bookings=bookings)
