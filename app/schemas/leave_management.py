from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime, date
from enum import Enum

class LeaveStatusEnum(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

# Employee Schemas
class EmployeeBase(BaseModel):
    employee_id: str
    first_name: str
    last_name: str
    email: EmailStr
    department: str
    position: str
    manager_id: Optional[int] = None
    hire_date: date

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    department: Optional[str] = None
    position: Optional[str] = None
    manager_id: Optional[int] = None
    is_active: Optional[bool] = None

class Employee(EmployeeBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Leave Type Schemas
class LeaveTypeBase(BaseModel):
    name: str
    description: Optional[str] = None
    max_days_per_year: Optional[int] = None
    max_consecutive_days: Optional[int] = None
    requires_approval: bool = True
    requires_medical_certificate: bool = False
    carry_forward_enabled: bool = False
    max_carry_forward_days: Optional[int] = None

class LeaveTypeCreate(LeaveTypeBase):
    pass

class LeaveTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    max_days_per_year: Optional[int] = None
    max_consecutive_days: Optional[int] = None
    requires_approval: Optional[bool] = None
    requires_medical_certificate: Optional[bool] = None
    carry_forward_enabled: Optional[bool] = None
    max_carry_forward_days: Optional[int] = None
    is_active: Optional[bool] = None

class LeaveType(LeaveTypeBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Leave Request Schemas
class LeaveRequestBase(BaseModel):
    leave_type_id: int
    start_date: date
    end_date: date
    reason: Optional[str] = None
    medical_certificate_url: Optional[str] = None
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('End date must be after start date')
        return v

class LeaveRequestCreate(LeaveRequestBase):
    pass

class LeaveRequestUpdate(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    reason: Optional[str] = None
    status: Optional[LeaveStatusEnum] = None
    rejection_reason: Optional[str] = None
    medical_certificate_url: Optional[str] = None

class LeaveRequest(LeaveRequestBase):
    id: int
    employee_id: int
    total_days: int
    status: LeaveStatusEnum
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class LeaveRequestWithDetails(LeaveRequest):
    employee: Employee
    leave_type: LeaveType
    approver: Optional[Employee] = None

# Leave Balance Schemas
class LeaveBalanceBase(BaseModel):
    leave_type_id: int
    year: int
    total_allocated: float
    total_used: float
    total_carried_forward: float
    remaining_balance: float

class LeaveBalanceCreate(LeaveBalanceBase):
    employee_id: int

class LeaveBalanceUpdate(BaseModel):
    total_allocated: Optional[float] = None
    total_used: Optional[float] = None
    total_carried_forward: Optional[float] = None
    remaining_balance: Optional[float] = None

class LeaveBalance(LeaveBalanceBase):
    id: int
    employee_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class LeaveBalanceWithDetails(LeaveBalance):
    employee: Employee
    leave_type: LeaveType

# Holiday Schemas
class HolidayBase(BaseModel):
    name: str
    date: date
    is_recurring: bool = False
    description: Optional[str] = None

class HolidayCreate(HolidayBase):
    pass

class HolidayUpdate(BaseModel):
    name: Optional[str] = None
    date: Optional[date] = None
    is_recurring: Optional[bool] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class Holiday(HolidayBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Leave Delegation Schemas
class LeaveDelegationBase(BaseModel):
    manager_id: int
    delegate_id: int
    start_date: date
    end_date: date
    reason: Optional[str] = None
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('End date must be after start date')
        return v

class LeaveDelegationCreate(LeaveDelegationBase):
    pass

class LeaveDelegationUpdate(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    reason: Optional[str] = None
    is_active: Optional[bool] = None

class LeaveDelegation(LeaveDelegationBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class LeaveDelegationWithDetails(LeaveDelegation):
    manager: Employee
    delegate: Employee

# Approval Schemas
class LeaveApprovalRequest(BaseModel):
    status: LeaveStatusEnum
    comments: Optional[str] = None

class LeaveApprovalResponse(BaseModel):
    success: bool
    message: str
    leave_request: Optional[LeaveRequestWithDetails] = None

# Report Schemas
class LeaveReportRequest(BaseModel):
    employee_id: Optional[int] = None
    department: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    leave_type_id: Optional[int] = None
    status: Optional[LeaveStatusEnum] = None

class LeaveReportResponse(BaseModel):
    total_requests: int
    approved_requests: int
    rejected_requests: int
    pending_requests: int
    leave_requests: List[LeaveRequestWithDetails]

class EmployeeLeaveSummary(BaseModel):
    employee: Employee
    leave_balances: List[LeaveBalanceWithDetails]
    total_requests_this_year: int
    approved_requests_this_year: int
    pending_requests: int
