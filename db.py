import os
import json
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash


with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

engine = create_engine(config["db_url"], connect_args={"check_same_thread": False} if "sqlite" in config["db_url"] else {})


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

class LogEntry(Base):
    __tablename__ = "log_entries"
    id = Column(Integer, primary_key=True, index=True)
    ip = Column(String(50), index=True)
    timestamp = Column(DateTime, index=True)
    method = Column(String(10))
    url = Column(Text)
    status = Column(Integer)
    size = Column(Integer)

class DownloadedContent(Base):
    __tablename__ = "downloaded_content"
    id = Column(Integer, primary_key=True, index=True)
    url = Column(Text, nullable=False)
    filename = Column(String(255))
    size = Column(Integer)
    content = Column(Text)
    downloaded_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    if not db.query(User).filter(User.username == "admin").first():
        admin = User(username="admin", password_hash=generate_password_hash("admin123"))
        db.add(admin)
        db.commit()
    db.close()

if __name__ == "__main__":
    init_db()
    print("База данных успешно инициализирована.")