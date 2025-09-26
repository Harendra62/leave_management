from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models import Base

class Holiday(Base):
    __tablename__ = "holidays"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    date = Column(DateTime, nullable=False)
    is_recurring = Column(Boolean, default=False)  # For annual holidays
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Holiday(id={self.id}, name='{self.name}', date='{self.date}')>"
