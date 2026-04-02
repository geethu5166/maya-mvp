from flask import Blueprint, render_template_string, request, redirect, url_for, session
from functools import wraps
import hashlib

auth = Blueprint("auth", __name__)

USERNAME = "vaultrap"
PASSWORD_HASH = hashlib.sha256("maya@2026".encode()).hexdigest()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated

@auth.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if username == USERNAME and password_hash == PASSWORD_HASH:
            session["logged_in"] = True
            return redirect(url_for("index"))
        else:
            error = "Invalid credentials. Access denied."
    return render_template_string(open("/root/maya-mvp/dashboard/templates/login.html").read(), error=error)

@auth.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
