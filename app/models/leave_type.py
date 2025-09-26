from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models import Base

class LeaveType(Base):
    __tablename__ = "leave_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)  # sick, casual, earned, etc.
    description = Column(Text, nullable=True)
    max_days_per_year = Column(Integer, nullable=True)  # None for unlimited
    max_consecutive_days = Column(Integer, nullable=True)  # None for unlimited
    requires_approval = Column(Boolean, default=True)
    requires_medical_certificate = Column(Boolean, default=False)
    carry_forward_enabled = Column(Boolean, default=False)
    max_carry_forward_days = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    leave_requests = relationship("LeaveRequest", back_populates="leave_type")
    leave_balances = relationship("LeaveBalance", back_populates="leave_type")
    
    def __repr__(self):
        return f"<LeaveType(id={self.id}, name='{self.name}')>"
