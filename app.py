# DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://schoolapi:SreJ22Sc7uVWu4G1hCBMt40lFVNAAtvH@dpg-d27rqveuk2gs73ejb530-a/schoolapi_738o")
import os
import datetime
import smtplib
from email.mime.text import MIMEText

from fastapi import FastAPI, HTTPException, Depends, Request, Header
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
import jwt

from passlib.context import CryptContext
from models import Base, Judet, User

# ---------------- Config ----------------
DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL, future=True)
Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

app = FastAPI()

JWT_SECRET = os.getenv("JWT_SECRET", "super-secret")
JWT_ALGO = "HS256"
JWT_EXPIRE = 60 * 60 * 24  # 24 ore

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---------------- Helpers ----------------
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_jwt(payload: dict, expires_in=JWT_EXPIRE) -> str:
    payload["exp"] = datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)

def decode_jwt(token: str):
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

# ---------------- Dependency ----------------
def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token lipsă")
    token = authorization.split(" ", 1)[1]
    data = decode_jwt(token)
    if not data:
        raise HTTPException(status_code=401, detail="Token invalid sau expirat")
    with Session() as db:
        user = db.get(User, data.get("user_id"))
        if not user:
            raise HTTPException(status_code=404, detail="Utilizator inexistent")
        return user

# ---------------- Routes ----------------
@app.post("/register")
def register(request: Request, data: dict):
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not username or not email or not password:
        raise HTTPException(status_code=400, detail="username, email și password sunt obligatorii")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="parola prea scurtă (minim 6 caractere)")

    hashed_password = hash_password(password)

    with Session() as db:
        if db.execute(select(User).where(User.username == username)).scalar_one_or_none():
            raise HTTPException(status_code=409, detail="username deja folosit")
        if db.execute(select(User).where(User.email == email)).scalar_one_or_none():
            raise HTTPException(status_code=409, detail="email deja folosit")

        user = User(username=username, email=email, hashed_password=hashed_password, confirmed=False)
        db.add(user)
        db.commit()
        db.refresh(user)

        token = create_jwt({"email": user.email}, expires_in=3600)
        confirm_url = f"{str(request.base_url)}confirm/{token}"

        send_email(
            email,
            "Confirmă-ți contul",
            f"<p>Salut {username},</p><p>Confirmă contul apăsând linkul:</p><a href='{confirm_url}'>Confirmă</a>"
        )

    return JSONResponse({"message": "înregistrat. verifică emailul pentru confirmare"}, status_code=201)

@app.get("/confirm/{token}")
def confirm_email(token: str):
    data = decode_jwt(token)
    if not data:
        raise HTTPException(status_code=400, detail="token invalid sau expirat")

    email = data.get("email")
    with Session() as db:
        user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="utilizator inexistent")
        if user.confirmed:
            return {"message": "deja confirmat"}

        user.confirmed = True
        db.commit()

    return {"message": "cont confirmat cu succes"}

@app.post("/login")
def login(data: dict):
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        raise HTTPException(status_code=400, detail="username și password obligatorii")

    with Session() as db:
        user = db.execute(select(User).where(User.username == username)).scalar_one_or_none()
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=401, detail="credențiale invalide")
        if not user.confirmed:
            raise HTTPException(status_code=403, detail="trebuie să confirmi emailul înainte de login")

        token = create_jwt({"user_id": user.id})
        return {
            "message": "autentificat",
            "token": token,
            "user": {"id": user.id, "username": user.username, "email": user.email}
        }

@app.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None
        }
    }

@app.get("/judete")
def get_judete(current_user: User = Depends(get_current_user)):
    with Session() as db:
        judete = db.query(Judet).all()
        return {"judete": [j.nume for j in judete]}