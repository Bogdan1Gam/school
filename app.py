# DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://schoolapi:SreJ22Sc7uVWu4G1hCBMt40lFVNAAtvH@dpg-d27rqveuk2gs73ejb530-a/schoolapi_738o")

import os
from datetime import timedelta

from flask import Flask, request, jsonify, session as flask_session
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash

from models import Base, Judet, User   # importăm modelele

# ---------------- Config ----------------
DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL, future=True)
Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", os.urandom(32))
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=True,  # True în producție pe HTTPS
    PERMANENT_SESSION_LIFETIME=timedelta(days=7),
)

SESSION_KEY = "user_id"


# ---------------- Helpers ----------------
def current_user(db):
    uid = flask_session.get(SESSION_KEY)
    if not uid:
        return None
    return db.get(User, uid)


def login_user(user: User):
    flask_session[SESSION_KEY] = user.id
    flask_session.permanent = True


def logout_user():
    flask_session.pop(SESSION_KEY, None)


# ---------------- Routes ----------------
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not username or not email or not password:
        return jsonify({"message": "username, email și password sunt obligatorii"}), 400
    if len(password) < 6:
        return jsonify({"message": "parola prea scurtă (minim 6 caractere)"}), 400

    pwd_hash = generate_password_hash(password)

    with Session() as db:
        # verifică unicitatea
        if db.execute(select(User).where(User.username == username)).scalar_one_or_none():
            return jsonify({"message": "username deja folosit"}), 409
        if db.execute(select(User).where(User.email == email)).scalar_one_or_none():
            return jsonify({"message": "email deja folosit"}), 409

        user = User(username=username, email=email, hashed_password=pwd_hash)
        db.add(user)
        db.commit()
        db.refresh(user)

    return jsonify({
        "message": "înregistrat",
        "user": {"id": user.id, "username": user.username, "email": user.email}
    }), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify({"message": "username și password sunt obligatorii"}), 400

    with Session() as db:
        user = db.execute(select(User).where(User.username == username)).scalar_one_or_none()
        if not user or not check_password_hash(user.hashed_password, password):
            return jsonify({"message": "credențiale invalide"}), 401

        login_user(user)
        return jsonify({
            "message": "autentificat",
            "user": {"id": user.id, "username": user.username, "email": user.email}
        })


@app.route("/logout", methods=["POST"])
def logout():
    logout_user()
    return jsonify({"message": "delogat"})


@app.route("/me", methods=["GET"])
def me():
    with Session() as db:
        user = current_user(db)
        if not user:
            return jsonify({"message": "neautentificat"}), 401
        return jsonify({
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
        })


@app.route("/judete", methods=["GET"])
def get_judete():
    with Session() as db:
        judete = db.query(Judet).all()
        return jsonify({"judete": [j.nume for j in judete]})


# ---------------- Main ----------------
if __name__ == "__main__":
    app.run()