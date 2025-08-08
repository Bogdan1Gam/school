from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

Base = declarative_base()

class Judet(Base):
    __tablename__ = 'judete'
    id = Column(Integer, primary_key=True)
    nume = Column(String, nullable=False)