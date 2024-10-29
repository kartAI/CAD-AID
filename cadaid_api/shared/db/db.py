import sqlite3
import sqlalchemy
from sqlalchemy.orm import sessionmaker, Session

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declarative_base
from dataclasses import dataclass

Base = declarative_base()

@dataclass
class Metadata(Base):
    __tablename__ = 'metadata'

    filename: str = Column(String, primary_key=True)
    drawing_types: str
    bbox: str
    confidence: float
    cardinal_direction: str = None
    scale: str = None
    room_names: str = None
    is_correct: bool = Column(bool, default=False) 


engine = create_engine('sqlite:///metadata.db')
Base.metadata.create_all(engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()