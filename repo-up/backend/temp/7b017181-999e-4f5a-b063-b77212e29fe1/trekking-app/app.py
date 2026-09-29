# pyrefly: ignore [missing-import]
from flask import Flask, redirect, url_for, session

from database import init_db
from auth import auth_bp
from admin import admin_bp
from staff import staff_bp
from user import user_bp

app = Flask(__name__)
app.secret_key = "change-this-secret-key-before-any-real-deployment"

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(staff_bp)
app.register_blueprint(user_bp)


@app.route("/")
def index():
    # Send logged-in users straight to their dashboard; everyone else to login.
    role = session.get("role")
    if role == "admin":
        return redirect(url_for("admin.dashboard"))
    elif role == "staff":
        return redirect(url_for("staff.dashboard"))
    elif role == "trekker":
        return redirect(url_for("user.dashboard"))
    return redirect(url_for("auth.login"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
