from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Tuple
from datetime import datetime, date, timedelta
from app.models import Employee, LeaveType, LeaveRequest, LeaveBalance, Holiday, LeaveDelegation, LeaveStatus
from app.schemas.leave_management import (
    LeaveRequestCreate, LeaveRequestUpdate, LeaveApprovalRequest,
    LeaveBalanceCreate, LeaveBalanceUpdate, EmployeeLeaveSummary
)
from app.services.email_notification import email_service
import logging

logger = logging.getLogger(__name__)

class LeaveValidationService:
    """Service for validating leave requests"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def validate_leave_request(self, employee_id: int, leave_request: LeaveRequestCreate) -> Tuple[bool, str]:
        """Validate a leave request for conflicts and business rules"""
        
        # Check for overlapping requests
        overlap_check = self._check_overlapping_requests(employee_id, leave_request.start_date, leave_request.end_date)
        if not overlap_check[0]:
            return False, overlap_check[1]
        
        # Check for holiday conflicts
        holiday_check = self._check_holiday_conflicts(leave_request.start_date, leave_request.end_date)
        if not holiday_check[0]:
            return False, holiday_check[1]
        
        # Check leave balance
        balance_check = self._check_leave_balance(employee_id, leave_request.leave_type_id, leave_request.start_date, leave_request.end_date)
        if not balance_check[0]:
            return False, balance_check[1]
        
        # Check leave type rules
        rules_check = self._check_leave_type_rules(leave_request.leave_type_id, leave_request.start_date, leave_request.end_date)
        if not rules_check[0]:
            return False, rules_check[1]
        
        return True, "Leave request is valid"
    
    def _check_overlapping_requests(self, employee_id: int, start_date: date, end_date: date) -> Tuple[bool, str]:
        """Check for overlapping leave requests"""
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
            return False, f"Overlapping leave request found. You have {len(overlapping_requests)} conflicting request(s)."
        
        return True, "No overlapping requests found"
    
    def _check_holiday_conflicts(self, start_date: date, end_date: date) -> Tuple[bool, str]:
        """Check for holiday conflicts"""
        conflicting_holidays = self.db.query(Holiday).filter(
            and_(
                Holiday.is_active == True,
                Holiday.date >= start_date,
                Holiday.date <= end_date
            )
        ).all()
        
        if conflicting_holidays:
            holiday_names = [h.name for h in conflicting_holidays]
            return False, f"Holiday conflicts detected: {', '.join(holiday_names)}"
        
        return True, "No holiday conflicts"
    
    def _check_leave_balance(self, employee_id: int, leave_type_id: int, start_date: date, end_date: date) -> Tuple[bool, str]:
        """Check if employee has sufficient leave balance"""
        current_year = datetime.now().year
        
        # Get current balance
        balance = self.db.query(LeaveBalance).filter(
            and_(
                LeaveBalance.employee_id == employee_id,
                LeaveBalance.leave_type_id == leave_type_id,
                LeaveBalance.year == current_year
            )
        ).first()
        
        if not balance:
            return False, "No leave balance found for this leave type"
        
        # Calculate requested days
        requested_days = (end_date - start_date).days + 1
        
        if balance.remaining_balance < requested_days:
            return False, f"Insufficient leave balance. Available: {balance.remaining_balance} days, Requested: {requested_days} days"
        
        return True, "Sufficient leave balance available"
    
    def _check_leave_type_rules(self, leave_type_id: int, start_date: date, end_date: date) -> Tuple[bool, str]:
        """Check leave type specific rules"""
        leave_type = self.db.query(LeaveType).filter(LeaveType.id == leave_type_id).first()
        
        if not leave_type or not leave_type.is_active:
            return False, "Invalid or inactive leave type"
        
        requested_days = (end_date - start_date).days + 1
        
        # Check max consecutive days
        if leave_type.max_consecutive_days and requested_days > leave_type.max_consecutive_days:
            return False, f"Request exceeds maximum consecutive days allowed ({leave_type.max_consecutive_days} days)"
        
        return True, "Leave type rules satisfied"

class LeaveRequestService:
    """Service for managing leave requests"""
    
    def __init__(self, db: Session):
        self.db = db
        self.validation_service = LeaveValidationService(db)
    
    def create_leave_request(self, employee_id: int, leave_request: LeaveRequestCreate) -> Tuple[bool, str, Optional[LeaveRequest]]:
        """Create a new leave request"""
        
        # Validate the request
        is_valid, message = self.validation_service.validate_leave_request(employee_id, leave_request)
        if not is_valid:
            return False, message, None
        
        # Calculate total days
        total_days = (leave_request.end_date - leave_request.start_date).days + 1
        
        # Create the request
        db_request = LeaveRequest(
            employee_id=employee_id,
            leave_type_id=leave_request.leave_type_id,
            start_date=leave_request.start_date,
            end_date=leave_request.end_date,
            total_days=total_days,
            reason=leave_request.reason,
            medical_certificate_url=leave_request.medical_certificate_url,
            status=LeaveStatus.PENDING
        )
        
        self.db.add(db_request)
        self.db.commit()
        self.db.refresh(db_request)
        
        # Send notification to manager
        self._send_leave_request_notification(db_request)
        
        return True, "Leave request created successfully", db_request
    
    def get_employee_leave_requests(self, employee_id: int, year: Optional[int] = None) -> List[LeaveRequest]:
        """Get all leave requests for an employee"""
        query = self.db.query(LeaveRequest).filter(LeaveRequest.employee_id == employee_id)

        if year:
            # Use date range filtering for cross-DB compatibility (SQLite/Postgres)
            year_start = date(year, 1, 1)
            year_end = date(year, 12, 31)
            # Include any request that overlaps the year range
            query = query.filter(
                and_(
                    LeaveRequest.start_date <= year_end,
                    LeaveRequest.end_date >= year_start
                )
            )

        return query.order_by(LeaveRequest.created_at.desc()).all()
    
    def get_pending_requests_for_manager(self, manager_id: int) -> List[LeaveRequest]:
        """Get all pending requests that need approval from a specific manager"""
        
        # Get all subordinates
        subordinates = self.db.query(Employee).filter(Employee.manager_id == manager_id).all()
        subordinate_ids = [emp.id for emp in subordinates]
        
        if not subordinate_ids:
            return []
        
        # Get pending requests from subordinates
        return self.db.query(LeaveRequest).filter(
            and_(
                LeaveRequest.employee_id.in_(subordinate_ids),
                LeaveRequest.status == LeaveStatus.PENDING
            )
        ).order_by(LeaveRequest.created_at.desc()).all()
    
    def approve_leave_request(self, request_id: int, approver_id: int, approval_data: LeaveApprovalRequest) -> Tuple[bool, str]:
        """Approve or reject a leave request"""
        
        # Get the request
        leave_request = self.db.query(LeaveRequest).filter(LeaveRequest.id == request_id).first()
        if not leave_request:
            return False, "Leave request not found"
        
        if leave_request.status != LeaveStatus.PENDING:
            return False, "Leave request is not pending"
        
        # Normalize incoming status (Pydantic enum) to model enum
        try:
            incoming_status_value = approval_data.status.value if hasattr(approval_data.status, 'value') else str(approval_data.status)
            new_status = LeaveStatus(incoming_status_value)
        except Exception:
            return False, "Invalid status provided"

        # Only approved/rejected are valid transitions here
        if new_status == LeaveStatus.PENDING:
            return False, "Invalid status for approval. Use approved or rejected."
        if new_status == LeaveStatus.CANCELLED:
            return False, "Invalid status for approval. Cannot cancel via approval endpoint."

        # Update the request
        leave_request.status = new_status
        leave_request.approved_by = approver_id
        leave_request.approved_at = datetime.utcnow()
        
        if new_status == LeaveStatus.REJECTED:
            leave_request.rejection_reason = approval_data.comments
        
        # If approved, update leave balance
        if new_status == LeaveStatus.APPROVED:
            self._update_leave_balance(leave_request)
        
        self.db.commit()
        
        # Send notification to employee
        self._send_leave_approval_notification(leave_request)
        
        return True, f"Leave request {new_status.value} successfully"
    
    def _update_leave_balance(self, leave_request: LeaveRequest):
        """Update leave balance when a request is approved"""
        current_year = datetime.now().year
        
        balance = self.db.query(LeaveBalance).filter(
            and_(
                LeaveBalance.employee_id == leave_request.employee_id,
                LeaveBalance.leave_type_id == leave_request.leave_type_id,
                LeaveBalance.year == current_year
            )
        ).first()
        
        if balance:
            balance.total_used += leave_request.total_days
            balance.remaining_balance = balance.total_allocated + balance.total_carried_forward - balance.total_used
            self.db.commit()
            logger.info(f"Updated leave balance for employee {leave_request.employee_id}: used {balance.total_used}, remaining {balance.remaining_balance}")
        else:
            logger.warning(f"No balance found for employee {leave_request.employee_id}, leave type {leave_request.leave_type_id}, year {current_year}")
    
    def _send_leave_request_notification(self, leave_request):
        """Send notification to manager about new leave request"""
        try:
            # Get the manager
            manager = self.db.query(Employee).filter(Employee.id == leave_request.employee.manager_id).first()
            if manager:
                email_service.send_leave_request_notification(leave_request, manager)
        except Exception as e:
            logger.error(f"Error sending leave request notification: {str(e)}")
    
    def _send_leave_approval_notification(self, leave_request):
        """Send notification to employee about leave approval/rejection"""
        try:
            approver = self.db.query(Employee).filter(Employee.id == leave_request.approved_by).first()
            if approver:
                email_service.send_leave_approval_notification(leave_request, approver)
        except Exception as e:
            logger.error(f"Error sending leave approval notification: {str(e)}")

class LeaveBalanceService:
    """Service for managing leave balances"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_employee_leave_balances(self, employee_id: int, year: Optional[int] = None) -> List[LeaveBalance]:
        """Get leave balances for an employee"""
        if not year:
            year = datetime.now().year
        
        return self.db.query(LeaveBalance).filter(
            and_(
                LeaveBalance.employee_id == employee_id,
                LeaveBalance.year == year
            )
        ).all()
    
    def initialize_employee_leave_balances(self, employee_id: int, year: int) -> List[LeaveBalance]:
        """Initialize leave balances for a new employee or new year"""
        
        # Get all active leave types
        leave_types = self.db.query(LeaveType).filter(LeaveType.is_active == True).all()
        
        balances = []
        for leave_type in leave_types:
            # Check if balance already exists
            existing_balance = self.db.query(LeaveBalance).filter(
                and_(
                    LeaveBalance.employee_id == employee_id,
                    LeaveBalance.leave_type_id == leave_type.id,
                    LeaveBalance.year == year
                )
            ).first()
            
            if not existing_balance:
                # Create new balance
                balance = LeaveBalance(
                    employee_id=employee_id,
                    leave_type_id=leave_type.id,
                    year=year,
                    total_allocated=leave_type.max_days_per_year or 0,
                    total_used=0,
                    total_carried_forward=0,
                    remaining_balance=leave_type.max_days_per_year or 0
                )
                self.db.add(balance)
                balances.append(balance)
        
        self.db.commit()
        return balances
    
    def process_carry_forward(self, year: int) -> int:
        """Process carry forward for all employees for a given year"""
        
        processed_count = 0
        
        # Get all employees
        employees = self.db.query(Employee).filter(Employee.is_active == True).all()
        
        for employee in employees:
            # Get previous year balances
            prev_year_balances = self.db.query(LeaveBalance).filter(
                and_(
                    LeaveBalance.employee_id == employee.id,
                    LeaveBalance.year == year - 1
                )
            ).all()
            
            for prev_balance in prev_year_balances:
                # Get leave type to check carry forward rules
                leave_type = self.db.query(LeaveType).filter(LeaveType.id == prev_balance.leave_type_id).first()
                
                if leave_type and leave_type.carry_forward_enabled:
                    # Calculate carry forward amount
                    carry_forward_amount = min(
                        prev_balance.remaining_balance,
                        leave_type.max_carry_forward_days or prev_balance.remaining_balance
                    )
                    
                    if carry_forward_amount > 0:
                        # Get or create current year balance
                        current_balance = self.db.query(LeaveBalance).filter(
                            and_(
                                LeaveBalance.employee_id == employee.id,
                                LeaveBalance.leave_type_id == leave_type.id,
                                LeaveBalance.year == year
                            )
                        ).first()
                        
                        if not current_balance:
                            current_balance = LeaveBalance(
                                employee_id=employee.id,
                                leave_type_id=leave_type.id,
                                year=year,
                                total_allocated=leave_type.max_days_per_year or 0,
                                total_used=0,
                                total_carried_forward=carry_forward_amount,
                                remaining_balance=(leave_type.max_days_per_year or 0) + carry_forward_amount
                            )
                            self.db.add(current_balance)
                        else:
                            current_balance.total_carried_forward = carry_forward_amount
                            current_balance.remaining_balance = current_balance.total_allocated + carry_forward_amount - current_balance.total_used
                        
                        processed_count += 1
        
        self.db.commit()
        return processed_count
