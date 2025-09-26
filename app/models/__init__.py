from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Leave Management Models
from .employee import Employee
from .leave_type import LeaveType
from .leave_request import LeaveRequest, LeaveStatus
from .leave_balance import LeaveBalance
from .holiday import Holiday
from .leave_delegation import LeaveDelegation
