from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, func, Boolean

Base = declarative_base()

class Judet(Base):
    __tablename__ = "judete"

    id = Column(Integer, primary_key=True)
    nume = Column(String, nullable=False)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(150), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    confirmed = Column(Boolean, default=False)

    def __repr__(self):
        return f"<User id={self.id} username={self.username} email={self.email}>"