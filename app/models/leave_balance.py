from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models import Base

class LeaveBalance(Base):
    __tablename__ = "leave_balances"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    leave_type_id = Column(Integer, ForeignKey("leave_types.id"), nullable=False)
    year = Column(Integer, nullable=False)
    total_allocated = Column(Numeric(5, 2), default=0)  # Total days allocated for the year
    total_used = Column(Numeric(5, 2), default=0)  # Total days used
    total_carried_forward = Column(Numeric(5, 2), default=0)  # Days carried from previous year
    remaining_balance = Column(Numeric(5, 2), nullable=False)  # Calculated field
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    employee = relationship("Employee", back_populates="leave_balances")
    leave_type = relationship("LeaveType", back_populates="leave_balances")
    
    def __repr__(self):
        return f"<LeaveBalance(id={self.id}, employee_id={self.employee_id}, year={self.year}, remaining={self.remaining_balance})>"
