# models.py
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from pydantic import BaseModel, EmailStr
from datetime import datetime

Base = declarative_base()

# ---------- SQLAlchemy Models ----------
class Judet(Base):
    __tablename__ = 'judete'
    id = Column(Integer, primary_key=True, index=True)
    nume = Column(String, nullable=False)


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ---------- Pydantic Schemas ----------
class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserOut(UserBase):
    id: int
    confirmed: bool
    created_at: datetime | None

    class Config:
        orm_mode = True


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    message: str
    token: str
    user: UserOut


class JudetOut(BaseModel):
    id: int
    nume: str

    class Config:
        orm_mode = True