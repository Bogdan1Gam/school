# DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://schoolapi:SreJ22Sc7uVWu4G1hCBMt40lFVNAAtvH@dpg-d27rqveuk2gs73ejb530-a/schoolapi_738o")
from fastapi import FastAPI, Depends, HTTPException, Header, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import User, Judet, Locatie
from schemas import UserCreate, UserLogin, UserOut, LocatieCreate, LocatieUpdate, LocatieOut
from auth import create_jwt, decode_jwt, hash_password, verify_password
from email_utils import send_email

Base.metadata.create_all(bind=engine)
app = FastAPI(title="School API")

# ---------------- Helpers ----------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token lipsă")
    if authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
    else:
        token = authorization
    data = decode_jwt(token)
    if not data:
        raise HTTPException(status_code=401, detail="Token invalid / expirat")
    user = db.get(User, data.get("user_id"))
    if not user:
        raise HTTPException(status_code=404, detail="Utilizator inexistent")
    return user

# ---------------- Routes ----------------
@app.post("/register")
def register(user: UserCreate, request: Request, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=409, detail="Username deja folosit")
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=409, detail="Email deja folosit")
    if len(user.password) < 6:
        raise HTTPException(status_code=400, detail="Parola prea scurta (minim 6 caractere)")

    hashed = hash_password(user.password)
    new_user = User(username=user.username, email=user.email, hashed_password=hashed)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_jwt({"email": new_user.email}, expires_in=3600)
    confirm_url = f"{request.base_url}confirm/{token}"  # URL dinamic
    send_email(new_user.email, "Confirmă contul", f"<p>Salut {user.username}</p><a href='{confirm_url}'>Confirmă</a>")

    return JSONResponse({"message": "Înregistrat. Verifică emailul pentru confirmare"}, status_code=201)

@app.get("/confirm/{token}")
def confirm_email(token: str, db: Session = Depends(get_db)):
    data = decode_jwt(token)
    if not data:
        raise HTTPException(status_code=400, detail="Token invalid sau expirat")
    email = data.get("email")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilizator inexistent")
    if user.confirmed:
        return {"message": "Deja confirmat"}
    user.confirmed = True
    db.commit()
    return {"message": "Cont confirmat cu succes"}

@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Credențiale invalide")
    if not db_user.confirmed:
        raise HTTPException(status_code=403, detail="Trebuie să confirmi emailul înainte de login")
    token = create_jwt({"user_id": db_user.id})
    return {"message": "Autentificat", "token": token, "user": {"id": db_user.id, "username": db_user.username, "email": db_user.email}}

@app.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return UserOut(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        created_at=current_user.created_at.isoformat() if current_user.created_at else None
    )

@app.get("/judete")
def get_judete(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    judete = db.query(Judet).all()
    return {"judete": [j.nume for j in judete]}

@app.post("/locatii", response_model=LocatieOut)
def create_locatie(loc: LocatieCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if db.query(Locatie).filter(Locatie.nume == loc.nume).first():
        raise HTTPException(status_code=409, detail="Nume deja folosit")
    if db.query(Locatie).filter(Locatie.adresa == loc.adresa).first():
        raise HTTPException(status_code=409, detail="Adresa deja folosita")
    new_loc = Locatie(nume=loc.nume, adresa=loc.adresa)
    db.add(new_loc)
    db.commit()
    db.refresh(new_loc)
    return new_loc

@app.get("/locatii", response_model=list[LocatieOut])
def get_locatii(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    locatii = db.query(Locatie).all()
    return locatii

@app.put("/locatii/{loc_id}", response_model=LocatieOut)
def update_locatie(loc_id: int, loc: LocatieUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    locatie = db.get(Locatie, loc_id)
    if not locatie:
        raise HTTPException(status_code=404, detail="Locatie inexistentă")
    if loc.nume:
        locatie.nume = loc.nume
    if loc.adresa:
        locatie.adresa = loc.adresa
    db.commit()
    db.refresh(locatie)
    return locatie

@app.delete("/locatii/{loc_id}")
def delete_locatie(loc_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    locatie = db.get(Locatie, loc_id)
    if not locatie:
        raise HTTPException(status_code=404, detail="Locatie inexistentă")
    db.delete(locatie)
    db.commit()
    return {"message": "Locatie stearsa cu succes"}