from sqlalchemy import Column, Integer, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models import Base

class LeaveDelegation(Base):
    __tablename__ = "leave_delegations"
    
    id = Column(Integer, primary_key=True, index=True)
    manager_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    delegate_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    reason = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    manager = relationship("Employee", foreign_keys=[manager_id])
    delegate = relationship("Employee", foreign_keys=[delegate_id])
    
    def __repr__(self):
        return f"<LeaveDelegation(id={self.id}, manager_id={self.manager_id}, delegate_id={self.delegate_id})>"
