from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models import Base

class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String(50), unique=True, index=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    department = Column(String(100), nullable=False)
    position = Column(String(100), nullable=False)
    manager_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    hire_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    manager = relationship("Employee", remote_side=[id], backref="subordinates")
    leave_requests = relationship("LeaveRequest", foreign_keys="LeaveRequest.employee_id", back_populates="employee")
    leave_balances = relationship("LeaveBalance", back_populates="employee")
    approvals = relationship("LeaveRequest", foreign_keys="LeaveRequest.approved_by", back_populates="approver")
    
    def __repr__(self):
        return f"<Employee(id={self.id}, employee_id='{self.employee_id}', name='{self.first_name} {self.last_name}')>"
