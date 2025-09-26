from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models import Base
import enum

class LeaveStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class LeaveRequest(Base):
    __tablename__ = "leave_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    leave_type_id = Column(Integer, ForeignKey("leave_types.id"), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    total_days = Column(Integer, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(Enum(LeaveStatus), default=LeaveStatus.PENDING)
    approved_by = Column(Integer, ForeignKey("employees.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    medical_certificate_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    employee = relationship("Employee", foreign_keys=[employee_id], back_populates="leave_requests")
    leave_type = relationship("LeaveType", back_populates="leave_requests")
    approver = relationship("Employee", foreign_keys=[approved_by], back_populates="approvals")
    
    def __repr__(self):
        return f"<LeaveRequest(id={self.id}, employee_id={self.employee_id}, status='{self.status.value}')>"
