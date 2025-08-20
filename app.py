# DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://schoolapi:SreJ22Sc7uVWu4G1hCBMt40lFVNAAtvH@dpg-d27rqveuk2gs73ejb530-a/schoolapi_738o")
import os
import datetime
import smtplib
from email.mime.text import MIMEText

from flask import Flask, request, jsonify
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.functions import current_user
from werkzeug.security import generate_password_hash, check_password_hash
import jwt

from models import Base, Judet, User

# ---------------- Config ----------------
DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL, future=True)
Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

app = Flask(__name__)
JWT_SECRET = os.getenv("JWT_SECRET", "super-secret")  # 🔑 setează în Render
JWT_ALGO = "HS256"
JWT_EXPIRE = 60 * 60 * 24  # 24 ore

# ---------------- Helpers ----------------
def create_jwt(payload, expires_in=JWT_EXPIRE):
    payload["exp"] = datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)

def decode_jwt(token):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def send_email(to_email, subject, body):
    sender = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")

    msg = MIMEText(body, "html")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, [to_email], msg.as_string())

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
        if db.execute(select(User).where(User.username == username)).scalar_one_or_none():
            return jsonify({"message": "username deja folosit"}), 409
        if db.execute(select(User).where(User.email == email)).scalar_one_or_none():
            return jsonify({"message": "email deja folosit"}), 409

        user = User(username=username, email=email, hashed_password=pwd_hash, confirmed=False)
        db.add(user)
        db.commit()
        db.refresh(user)

        # Creează token de confirmare
        token = create_jwt({"email": user.email}, expires_in=3600)
        confirm_url = f"{request.host_url}confirm/{token}"

        # Trimite email
        send_email(
            email,
            "Confirmă-ți contul",
            f"<p>Salut {username},</p><p>Confirmă contul apăsând linkul:</p><a href='{confirm_url}'>Confirmă</a>"
        )

    return jsonify({"message": "înregistrat. verifică emailul pentru confirmare"}), 201

@app.route("/confirm/<token>")
def confirm_email(token):
    data = decode_jwt(token)
    if not data:
        return jsonify({"message": "token invalid sau expirat"}), 400

    email = data.get("email")
    with Session() as db:
        user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if not user:
            return jsonify({"message": "utilizator inexistent"}), 404
        if user.confirmed:
            return jsonify({"message": "deja confirmat"}), 200

        user.confirmed = True
        db.commit()

    return jsonify({"message": "cont confirmat cu succes"}), 200

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify({"message": "username și password obligatorii"}), 400

    with Session() as db:
        user = db.execute(select(User).where(User.username == username)).scalar_one_or_none()
        if not user or not check_password_hash(user.hashed_password, password):
            return jsonify({"message": "credențiale invalide"}), 401
        if not user.confirmed:
            return jsonify({"message": "trebuie să confirmi emailul înainte de login"}), 403

        token = create_jwt({"user_id": user.id})
        return jsonify({
            "message": "autentificat",
            "token": token,
            "user": {"id": user.id, "username": user.username, "email": user.email}
        })

@app.route("/me", methods=["GET"])
def me():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"message": "token lipsă"}), 401

    token = auth.split(" ", 1)[1]
    data = decode_jwt(token)
    if not data:
        return jsonify({"message": "token invalid sau expirat"}), 401

    with Session() as db:
        user = db.get(User, data.get("user_id"))
        if not user:
            return jsonify({"message": "utilizator inexistent"}), 404

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
        user = current_user(db)
        if not user:
            return jsonify({"message": "neautentificat"}), 401  # acces interzis
        judete = db.query(Judet).all()
        return jsonify({"judete": [j.nume for j in judete]})

# ---------------- Main ----------------
if __name__ == "__main__":
    app.run()