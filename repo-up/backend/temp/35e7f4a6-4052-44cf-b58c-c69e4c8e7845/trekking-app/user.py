"""
user.py
-------
Trekker role: browse open treks, search/filter, book a trek, view
booking history, edit profile.

Two business rules enforced here (both required by the spec):
- a trek can only be booked while its status is 'Open'
- a booking can only be made while available_slots > 0, and the
  slot count is decremented inside the same request that creates
  the booking, so two bookings can't both slip through on the last slot.
"""

# pyrefly: ignore [missing-import]
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from datetime import datetime
from database import get_db
from helpers import login_required, role_required

user_bp = Blueprint("user", __name__, url_prefix="/user")


@user_bp.route("/dashboard")
@login_required
@role_required("trekker")
def dashboard():
    db = get_db()
    user_id = session["user_id"]
    open_treks = db.execute(
        "SELECT * FROM treks WHERE status = 'Open' ORDER BY id DESC"
    ).fetchall()
    my_bookings = db.execute(
        """SELECT b.*, t.name AS trek_name, t.status AS trek_status FROM bookings b
           JOIN treks t ON t.id = b.trek_id
           WHERE b.user_id = ? ORDER BY b.id DESC""",
        (user_id,),
    ).fetchall()
    db.close()
    return render_template("user/dashboard.html", open_treks=open_treks, my_bookings=my_bookings)


@user_bp.route("/treks")
@login_required
@role_required("trekker")
def browse_treks():
    db = get_db()
    search_query = request.args.get("q", "").strip()
    difficulty = request.args.get("difficulty", "").strip()
    location = request.args.get("location", "").strip()

    query = "SELECT * FROM treks WHERE status = 'Open'"
    params = []
    if search_query:
        query += " AND name LIKE ?"
        params.append(f"%{search_query}%")
    if difficulty:
        query += " AND difficulty = ?"
        params.append(difficulty)
    if location:
        query += " AND location LIKE ?"
        params.append(f"%{location}%")
    query += " ORDER BY id DESC"

    treks = db.execute(query, params).fetchall()
    db.close()
    return render_template(
        "user/browse_treks.html", treks=treks, q=search_query, difficulty=difficulty, location=location
    )


@user_bp.route("/treks/<int:trek_id>/book", methods=["POST"])
@login_required
@role_required("trekker")
def book_trek(trek_id):
    db = get_db()
    user_id = session["user_id"]
    trek = db.execute("SELECT * FROM treks WHERE id = ?", (trek_id,)).fetchone()

    if trek is None:
        db.close()
        flash("Trek not found.", "danger")
        return redirect(url_for("user.browse_treks"))

    if trek["status"] != "Open":
        db.close()
        flash("This trek isn't open for booking.", "warning")
        return redirect(url_for("user.browse_treks"))

    if trek["available_slots"] <= 0:
        db.close()
        flash("No slots left on this trek.", "warning")
        return redirect(url_for("user.browse_treks"))

    existing_booking = db.execute(
        "SELECT id FROM bookings WHERE user_id=? AND trek_id=? AND status='Booked'",
        (user_id, trek_id),
    ).fetchone()
    if existing_booking:
        db.close()
        flash("You've already booked this trek.", "info")
        return redirect(url_for("user.browse_treks"))

    # Atomic update for concurrency
    result = db.execute("""
        UPDATE treks
        SET available_slots = available_slots - 1
        WHERE id = ?
        AND status = 'Open'
        AND available_slots > 0
    """, (trek_id,))

    if result.rowcount == 0:
        db.close()
        flash("No slots left or trek not open.", "warning")
        return redirect(url_for("user.browse_treks"))

    db.execute(
        "INSERT INTO bookings (user_id, trek_id, booking_date, status) VALUES (?, ?, ?, 'Booked')",
        (user_id, trek_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    db.commit()
    db.close()
    flash("Trek booked!", "success")
    return redirect(url_for("user.dashboard"))


@user_bp.route("/bookings/<int:booking_id>/cancel", methods=["POST"])
@login_required
@role_required("trekker")
def cancel_booking(booking_id):
    db = get_db()
    booking = db.execute(
        "SELECT * FROM bookings WHERE id = ? AND user_id = ?",
        (booking_id, session["user_id"]),
    ).fetchone()

    if booking is None or booking["status"] != "Booked":
        db.close()
        flash("Booking can't be cancelled.", "danger")
        return redirect(url_for("user.dashboard"))

    db.execute("UPDATE bookings SET status = 'Cancelled' WHERE id = ?", (booking_id,))
    # returning the slot to the pool
    db.execute(
        "UPDATE treks SET available_slots = available_slots + 1 WHERE id = ?",
        (booking["trek_id"],),
    )
    db.commit()
    db.close()
    flash("Booking cancelled.", "info")
    return redirect(url_for("user.dashboard"))


@user_bp.route("/profile", methods=["GET", "POST"])
@login_required
@role_required("trekker")
def profile():
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()

    if request.method == "POST":
        name = request.form["name"].strip()
        contact = request.form.get("contact", "").strip()
        db.execute("UPDATE users SET name = ?, contact = ? WHERE id = ?",
                   (name, contact, session["user_id"]))
        db.commit()
        session["name"] = name
        db.close()
        flash("Profile updated.", "success")
        return redirect(url_for("user.profile"))

    db.close()
    return render_template("user/profile.html", user=user)
