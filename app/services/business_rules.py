from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, date, timedelta
from app.models import Employee, LeaveType, LeaveRequest, LeaveBalance, Holiday, LeaveDelegation, LeaveStatus
from app.schemas.leave_management import LeaveRequestCreate
import logging

logger = logging.getLogger(__name__)

class BusinessRuleValidationService:
    """Service for comprehensive business rule validation"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def validate_leave_request_comprehensive(self, employee_id: int, leave_request: LeaveRequestCreate) -> Dict[str, Any]:
        """Comprehensive validation of leave request with detailed results"""
        
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": [],
            "validation_details": {}
        }
        
        # Get employee
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            validation_result["is_valid"] = False
            validation_result["errors"].append("Employee not found")
            return validation_result
        
        # Get leave type
        leave_type = self.db.query(LeaveType).filter(LeaveType.id == leave_request.leave_type_id).first()
        if not leave_type:
            validation_result["is_valid"] = False
            validation_result["errors"].append("Invalid leave type")
            return validation_result
        
        # Calculate requested days
        requested_days = (leave_request.end_date - leave_request.start_date).days + 1
        
        # 1. Date validation
        date_validation = self._validate_dates(leave_request.start_date, leave_request.end_date)
        validation_result["validation_details"]["date_validation"] = date_validation
        if not date_validation["is_valid"]:
            validation_result["is_valid"] = False
            validation_result["errors"].extend(date_validation["errors"])
        
        # 2. Leave type specific validation
        leave_type_validation = self._validate_leave_type_rules(leave_type, requested_days, leave_request)
        validation_result["validation_details"]["leave_type_validation"] = leave_type_validation
        if not leave_type_validation["is_valid"]:
            validation_result["is_valid"] = False
            validation_result["errors"].extend(leave_type_validation["errors"])
        
        # 3. Balance validation
        balance_validation = self._validate_leave_balance(employee_id, leave_request.leave_type_id, requested_days)
        validation_result["validation_details"]["balance_validation"] = balance_validation
        if not balance_validation["is_valid"]:
            validation_result["is_valid"] = False
            validation_result["errors"].extend(balance_validation["errors"])
        
        # 4. Conflict validation
        conflict_validation = self._validate_conflicts(employee_id, leave_request.start_date, leave_request.end_date)
        validation_result["validation_details"]["conflict_validation"] = conflict_validation
        if not conflict_validation["is_valid"]:
            validation_result["is_valid"] = False
            validation_result["errors"].extend(conflict_validation["errors"])
        
        # 5. Holiday validation
        holiday_validation = self._validate_holidays(leave_request.start_date, leave_request.end_date)
        validation_result["validation_details"]["holiday_validation"] = holiday_validation
        if not holiday_validation["is_valid"]:
            validation_result["is_valid"] = False
            validation_result["errors"].extend(holiday_validation["errors"])
        
        # 6. Business rules validation
        business_rules_validation = self._validate_business_rules(employee, leave_request, requested_days)
        validation_result["validation_details"]["business_rules_validation"] = business_rules_validation
        if not business_rules_validation["is_valid"]:
            validation_result["is_valid"] = False
            validation_result["errors"].extend(business_rules_validation["errors"])
        
        # 7. Generate suggestions
        suggestions = self._generate_suggestions(employee, leave_type, leave_request, requested_days)
        validation_result["suggestions"] = suggestions
        
        return validation_result
    
    def _validate_dates(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Validate date logic"""
        result = {"is_valid": True, "errors": [], "warnings": []}
        
        # Check if start date is in the past
        if start_date < date.today():
            result["is_valid"] = False
            result["errors"].append("Start date cannot be in the past")
        
        # Check if end date is before start date
        if end_date < start_date:
            result["is_valid"] = False
            result["errors"].append("End date cannot be before start date")
        
        # Check if dates are too far in the future (more than 1 year)
        if start_date > date.today() + timedelta(days=365):
            result["warnings"].append("Start date is more than 1 year in the future")
        
        # Check if request is for weekend only
        if start_date.weekday() >= 5 and end_date.weekday() >= 5:
            result["warnings"].append("Request appears to be for weekend only")
        
        return result
    
    def _validate_leave_type_rules(self, leave_type: LeaveType, requested_days: int, leave_request: LeaveRequestCreate) -> Dict[str, Any]:
        """Validate leave type specific rules"""
        result = {"is_valid": True, "errors": [], "warnings": []}
        
        # Check max consecutive days
        if leave_type.max_consecutive_days and requested_days > leave_type.max_consecutive_days:
            result["is_valid"] = False
            result["errors"].append(f"Request exceeds maximum consecutive days ({leave_type.max_consecutive_days})")
        
        # Check if medical certificate is required
        if leave_type.requires_medical_certificate and not leave_request.medical_certificate_url:
            result["is_valid"] = False
            result["errors"].append("Medical certificate is required for this leave type")
        
        # Check if reason is provided for certain leave types
        if leave_type.name.lower() in ["sick leave", "emergency leave"] and not leave_request.reason:
            result["warnings"].append("Reason is recommended for this leave type")
        
        return result
    
    def _validate_leave_balance(self, employee_id: int, leave_type_id: int, requested_days: int) -> Dict[str, Any]:
        """Validate leave balance"""
        result = {"is_valid": True, "errors": [], "warnings": [], "balance_info": {}}
        
        current_year = date.today().year
        balance = self.db.query(LeaveBalance).filter(
            and_(
                LeaveBalance.employee_id == employee_id,
                LeaveBalance.leave_type_id == leave_type_id,
                LeaveBalance.year == current_year
            )
        ).first()
        
        if not balance:
            result["is_valid"] = False
            result["errors"].append("No leave balance found for this leave type")
            return result
        
        result["balance_info"] = {
            "total_allocated": float(balance.total_allocated),
            "total_used": float(balance.total_used),
            "total_carried_forward": float(balance.total_carried_forward),
            "remaining_balance": float(balance.remaining_balance)
        }
        
        if balance.remaining_balance < requested_days:
            result["is_valid"] = False
            result["errors"].append(f"Insufficient balance. Available: {balance.remaining_balance}, Requested: {requested_days}")
        elif balance.remaining_balance < requested_days + 5:
            result["warnings"].append("Low balance remaining after this request")
        
        return result
    
    def _validate_conflicts(self, employee_id: int, start_date: date, end_date: date) -> Dict[str, Any]:
        """Validate for overlapping requests"""
        result = {"is_valid": True, "errors": [], "warnings": [], "conflicts": []}
        
        overlapping_requests = self.db.query(LeaveRequest).filter(
            and_(
                LeaveRequest.employee_id == employee_id,
                LeaveRequest.status.in_([LeaveStatus.PENDING, LeaveStatus.APPROVED]),
                or_(
                    and_(LeaveRequest.start_date <= start_date, LeaveRequest.end_date >= start_date),
                    and_(LeaveRequest.start_date <= end_date, LeaveRequest.end_date >= end_date),
                    and_(LeaveRequest.start_date >= start_date, LeaveRequest.end_date <= end_date)
                )
            )
        ).all()
        
        if overlapping_requests:
            result["is_valid"] = False
            result["errors"].append(f"Found {len(overlapping_requests)} overlapping request(s)")
            result["conflicts"] = [
                {
                    "id": req.id,
                    "start_date": req.start_date,
                    "end_date": req.end_date,
                    "status": req.status.value,
                    "leave_type": req.leave_type.name
                }
                for req in overlapping_requests
            ]
        
        return result
    
    def _validate_holidays(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Validate for holiday conflicts"""
        result = {"is_valid": True, "errors": [], "warnings": [], "holidays": []}
        
        conflicting_holidays = self.db.query(Holiday).filter(
            and_(
                Holiday.is_active == True,
                Holiday.date >= start_date,
                Holiday.date <= end_date
            )
        ).all()
        
        if conflicting_holidays:
            result["is_valid"] = False
            result["errors"].append(f"Request conflicts with {len(conflicting_holidays)} holiday(s)")
            result["holidays"] = [
                {
                    "name": holiday.name,
                    "date": holiday.date,
                    "description": holiday.description
                }
                for holiday in conflicting_holidays
            ]
        
        return result
    
    def _validate_business_rules(self, employee: Employee, leave_request: LeaveRequestCreate, requested_days: int) -> Dict[str, Any]:
        """Validate business rules"""
        result = {"is_valid": True, "errors": [], "warnings": []}
        
        # Check if employee is active
        if not employee.is_active:
            result["is_valid"] = False
            result["errors"].append("Employee is not active")
        
        # Check probation period (assuming 90 days)
        hire_date = employee.hire_date.date() if hasattr(employee.hire_date, 'date') else employee.hire_date
        probation_end = hire_date + timedelta(days=90)
        if date.today() < probation_end:
            result["warnings"].append("Employee is still in probation period")
        
        # Check if request is for too many days (more than 30)
        if requested_days > 30:
            result["warnings"].append("Request is for more than 30 days - may require special approval")
        
        # Check if request is during peak business period (example: December)
        if leave_request.start_date.month == 12:
            result["warnings"].append("Request is during peak business period")
        
        return result
    
    def _generate_suggestions(self, employee: Employee, leave_type: LeaveType, leave_request: LeaveRequestCreate, requested_days: int) -> List[str]:
        """Generate suggestions for the leave request"""
        suggestions = []
        
        # Suggest alternative dates if there are conflicts
        if leave_request.start_date.weekday() >= 5:  # Weekend
            suggestions.append("Consider starting on a weekday to maximize work days")
        
        # Suggest shorter duration if balance is low
        current_year = date.today().year
        balance = self.db.query(LeaveBalance).filter(
            and_(
                LeaveBalance.employee_id == employee.id,
                LeaveBalance.leave_type_id == leave_type.id,
                LeaveBalance.year == current_year
            )
        ).first()
        
        if balance and balance.remaining_balance < requested_days + 5:
            suggestions.append("Consider splitting the leave into smaller periods")
        
        # Suggest advance notice
        days_advance = (leave_request.start_date - date.today()).days
        if days_advance < 7:
            suggestions.append("Consider giving more advance notice for better planning")
        
        return suggestions

class LeavePolicyService:
    """Service for managing leave policies and rules"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_leave_policy_summary(self, employee_id: int) -> Dict[str, Any]:
        """Get comprehensive leave policy summary for an employee"""
        
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            return {"error": "Employee not found"}
        
        current_year = date.today().year
        
        # Get all leave types and balances
        leave_balances = self.db.query(LeaveBalance).join(LeaveType).filter(
            and_(
                LeaveBalance.employee_id == employee_id,
                LeaveBalance.year == current_year
            )
        ).all()
        
        # Get leave requests for current year
        # SQLite doesn't have year() function, so we'll filter by date range
        year_start = date(current_year, 1, 1)
        year_end = date(current_year, 12, 31)
        leave_requests = self.db.query(LeaveRequest).filter(
            and_(
                LeaveRequest.employee_id == employee_id,
                LeaveRequest.start_date >= year_start,
                LeaveRequest.start_date <= year_end
            )
        ).all()
        
        # Calculate statistics
        total_requests = len(leave_requests)
        approved_requests = len([r for r in leave_requests if r.status == LeaveStatus.APPROVED])
        pending_requests = len([r for r in leave_requests if r.status == LeaveStatus.PENDING])
        rejected_requests = len([r for r in leave_requests if r.status == LeaveStatus.REJECTED])
        
        # Calculate total days used
        total_days_used = sum([r.total_days for r in leave_requests if r.status == LeaveStatus.APPROVED])
        
        return {
            "employee": {
                "id": employee.id,
                "name": f"{employee.first_name} {employee.last_name}",
                "department": employee.department,
                "position": employee.position,
                "hire_date": employee.hire_date.isoformat() if hasattr(employee.hire_date, 'isoformat') else str(employee.hire_date),
                "is_active": employee.is_active
            },
            "leave_balances": [
                {
                    "leave_type": balance.leave_type.name,
                    "total_allocated": float(balance.total_allocated),
                    "total_used": float(balance.total_used),
                    "total_carried_forward": float(balance.total_carried_forward),
                    "remaining_balance": float(balance.remaining_balance),
                    "carry_forward_enabled": balance.leave_type.carry_forward_enabled,
                    "max_carry_forward": balance.leave_type.max_carry_forward_days
                }
                for balance in leave_balances
            ],
            "statistics": {
                "total_requests": total_requests,
                "approved_requests": approved_requests,
                "pending_requests": pending_requests,
                "rejected_requests": rejected_requests,
                "total_days_used": total_days_used,
                "approval_rate": (approved_requests / total_requests * 100) if total_requests > 0 else 0
            },
            "policy_rules": {
                "max_consecutive_days": max([b.leave_type.max_consecutive_days or 0 for b in leave_balances]),
                "requires_advance_notice": True,
                "medical_certificate_required": any([b.leave_type.requires_medical_certificate for b in leave_balances]),
                "probation_period_days": 90
            }
        }
