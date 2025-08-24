from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: str | None

class LocatieCreate(BaseModel):
    nume: str
    adresa: str

class LocatieUpdate(BaseModel):
    nume: str | None = None
    adresa: str | None = None

class LocatieOut(BaseModel):
    id: int
    nume: str
    adresa: str