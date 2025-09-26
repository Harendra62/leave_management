from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Use SQLite for easier setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./leave_management.db")

# Create engine with SQLite-specific settings
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 