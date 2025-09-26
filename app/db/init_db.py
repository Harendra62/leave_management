import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from app.core.config import get_settings

from app.models import Base
# Add other Base imports if you have more models

settings = get_settings()
DATABASE_URL = settings.SQLALCHEMY_DATABASE_URI

def init_db():
    engine = create_engine(DATABASE_URL)
    
    Base.metadata.create_all(bind=engine)
    # Repeat for other Base.metadata if needed

if __name__ == "__main__":
    init_db()
    print("Database tables created.") 
