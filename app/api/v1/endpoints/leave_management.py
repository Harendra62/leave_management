from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from app.db.session import get_db
from app.services.leave_management import LeaveRequestService, LeaveBalanceService, LeaveValidationService
from app.schemas.leave_management import (
    LeaveRequestCreate, LeaveRequestUpdate, LeaveRequestWithDetails,
    LeaveApprovalRequest, LeaveApprovalResponse, LeaveBalanceWithDetails,
    EmployeeLeaveSummary, LeaveReportRequest, LeaveReportResponse
)
from app.models import Employee, LeaveRequest, LeaveStatus
from app.schemas.leave_management import Employee as EmployeeSchema
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/leave", tags=["Leave Management"])

# Employee Endpoints
@router.get("/employees", response_model=List[EmployeeSchema])
def get_employees(
    active_only: Optional[bool] = Query(
        None,
        description="Deprecated. Use is_active instead.",
        include_in_schema=False
    ),
    is_active: Optional[bool] = Query(None, description="Filter by active status: true for active, false for inactive, omit for all"),
    db: Session = Depends(get_db)
):
    """Get employees with optional active status filtering.

    - is_active=true  -> only active
    - is_active=false -> only inactive
    - is_active omitted -> all employees
    - active_only kept for backward compatibility (true behaves like is_active=true)
    """
    try:
        query = db.query(Employee)

        if is_active is not None:
            query = query.filter(Employee.is_active == is_active)
        elif active_only:
            query = query.filter(Employee.is_active == True)

        return query.order_by(Employee.id.asc()).all()
    except Exception as e:
        logger.error(f"Error fetching employees: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

# Leave Request Endpoints
@router.post("/requests", response_model=LeaveRequestWithDetails, status_code=status.HTTP_201_CREATED)
def create_leave_request(
    employee_id: Optional[int] = Query(None, description="Deprecated. Use employee_code.", include_in_schema=False),
    employee_code: Optional[str] = Query(None, description="Alphanumeric employee code, e.g., EMP008"),
    leave_request: LeaveRequestCreate = None,
    db: Session = Depends(get_db)
):
    """Submit a new leave request. Accepts either employee_id (int) or employee_code (str)."""
    try:
        # Resolve employee by code if provided, otherwise use id
        resolved_employee_id = employee_id
        if employee_code is not None:
            employee = db.query(Employee).filter(Employee.employee_id == employee_code).first()
            if not employee:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found for provided code")
            resolved_employee_id = employee.id
        
        if resolved_employee_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide either employee_id or employee_code")

        service = LeaveRequestService(db)
        success, message, db_request = service.create_leave_request(resolved_employee_id, leave_request)
        
        if not success:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
        
        # Return the request with related data
        return db_request
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating leave request: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/requests/employee/{employee_id}", response_model=List[LeaveRequestWithDetails])
def get_employee_leave_requests(
    employee_id: str,
    year: Optional[int] = Query(None, description="Filter by year"),
    db: Session = Depends(get_db)
):
    """Get all leave requests for an employee. Accepts numeric ID or employee code."""
    try:
        # Resolve numeric id or employee code
        resolved_employee_id: Optional[int]
        if employee_id.isdigit():
            resolved_employee_id = int(employee_id)
        else:
            employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
            if not employee:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
            resolved_employee_id = employee.id

        service = LeaveRequestService(db)
        requests = service.get_employee_leave_requests(resolved_employee_id, year)
        return requests
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching employee leave requests: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/requests/employee/by-code/{employee_code}", response_model=List[LeaveRequestWithDetails])
def get_employee_leave_requests_by_code(
    employee_code: str,
    year: Optional[int] = Query(None, description="Filter by year"),
    db: Session = Depends(get_db)
):
    """Get all leave requests for an employee by employee code."""
    try:
        employee = db.query(Employee).filter(Employee.employee_id == employee_code).first()
        if not employee:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
        service = LeaveRequestService(db)
        requests = service.get_employee_leave_requests(employee.id, year)
        return requests
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching employee leave requests by code: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/requests/pending/{manager_id}", response_model=List[LeaveRequestWithDetails])
def get_pending_requests_for_manager(
    manager_id: int,
    db: Session = Depends(get_db)
):
    """Get all pending leave requests for a manager to approve"""
    try:
        service = LeaveRequestService(db)
        requests = service.get_pending_requests_for_manager(manager_id)
        return requests
    except Exception as e:
        logger.error(f"Error fetching pending requests: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.put("/requests/{request_id}/approve", response_model=LeaveApprovalResponse)
def approve_leave_request(
    request_id: int,
    approver_id: int,
    approval_data: LeaveApprovalRequest,
    db: Session = Depends(get_db)
):
    """Approve or reject a leave request"""
    try:
        service = LeaveRequestService(db)
        success, message = service.approve_leave_request(request_id, approver_id, approval_data)
        
        if not success:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
        
        # Get the updated request
        updated_request = db.query(LeaveRequest).filter(LeaveRequest.id == request_id).first()
        
        return LeaveApprovalResponse(
            success=True,
            message=message,
            leave_request=updated_request
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving leave request: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/requests/{request_id}", response_model=LeaveRequestWithDetails)
def get_leave_request(
    request_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific leave request by ID"""
    try:
        request = db.query(LeaveRequest).filter(LeaveRequest.id == request_id).first()
        if not request:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found")
        
        return request
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching leave request: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.put("/requests/{request_id}", response_model=LeaveRequestWithDetails)
def update_leave_request(
    request_id: int,
    leave_request_update: LeaveRequestUpdate,
    db: Session = Depends(get_db)
):
    """Update a leave request (only if pending)"""
    try:
        request = db.query(LeaveRequest).filter(LeaveRequest.id == request_id).first()
        if not request:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found")
        
        if request.status != LeaveStatus.PENDING:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending requests can be updated")
        
        # Update fields
        for field, value in leave_request_update.dict(exclude_unset=True).items():
            setattr(request, field, value)
        
        # Recalculate total days if dates changed
        if leave_request_update.start_date or leave_request_update.end_date:
            request.total_days = (request.end_date - request.start_date).days + 1
        
        db.commit()
        db.refresh(request)
        
        return request
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating leave request: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.delete("/requests/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_leave_request(
    request_id: int,
    db: Session = Depends(get_db)
):
    """Cancel a leave request (only if pending)"""
    try:
        request = db.query(LeaveRequest).filter(LeaveRequest.id == request_id).first()
        if not request:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found")
        
        if request.status != LeaveStatus.PENDING:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending requests can be cancelled")
        
        request.status = LeaveStatus.CANCELLED
        db.commit()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling leave request: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

# Leave Balance Endpoints
@router.get("/balances/employee/{employee_id}", response_model=List[LeaveBalanceWithDetails])
def get_employee_leave_balances(
    employee_id: int,
    year: Optional[int] = Query(None, description="Filter by year"),
    db: Session = Depends(get_db)
):
    """Get leave balances for an employee"""
    try:
        service = LeaveBalanceService(db)
        balances = service.get_employee_leave_balances(employee_id, year)
        return balances
    except Exception as e:
        logger.error(f"Error fetching leave balances: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/balances/employee/by-code/{employee_code}", response_model=List[LeaveBalanceWithDetails])
def get_employee_leave_balances_by_code(
    employee_code: str,
    year: Optional[int] = Query(None, description="Filter by year"),
    db: Session = Depends(get_db)
):
    """Get leave balances for an employee by employee code."""
    try:
        employee = db.query(Employee).filter(Employee.employee_id == employee_code).first()
        if not employee:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
        service = LeaveBalanceService(db)
        balances = service.get_employee_leave_balances(employee.id, year)
        return balances
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching leave balances by code: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.post("/balances/initialize/{employee_id}", response_model=List[LeaveBalanceWithDetails])
def initialize_employee_leave_balances(
    employee_id: int,
    year: int = Query(description="Year to initialize balances for"),
    db: Session = Depends(get_db)
):
    """Initialize leave balances for an employee for a specific year"""
    try:
        service = LeaveBalanceService(db)
        balances = service.initialize_employee_leave_balances(employee_id, year)
        return balances
    except Exception as e:
        logger.error(f"Error initializing leave balances: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

# Validation Endpoints
@router.post("/validate")
def validate_leave_request(
    employee_id: Optional[int] = Query(None, description="Deprecated. Use employee_code.", include_in_schema=False),
    employee_code: Optional[str] = Query(None, description="Alphanumeric employee code, e.g., EMP008"),
    leave_request: LeaveRequestCreate = None,
    db: Session = Depends(get_db)
):
    """Validate a leave request without creating it. Accepts either employee_id (int) or employee_code (str)."""
    try:
        resolved_employee_id = employee_id
        if employee_code is not None:
            employee = db.query(Employee).filter(Employee.employee_id == employee_code).first()
            if not employee:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found for provided code")
            resolved_employee_id = employee.id
        
        if resolved_employee_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide either employee_id or employee_code")

        service = LeaveValidationService(db)
        is_valid, message = service.validate_leave_request(resolved_employee_id, leave_request)
        
        return {
            "is_valid": is_valid,
            "message": message,
            "employee_id": resolved_employee_id,
            "requested_dates": f"{leave_request.start_date} to {leave_request.end_date}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating leave request: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

# Summary Endpoints
@router.get("/summary/employee/{employee_id}", response_model=EmployeeLeaveSummary)
def get_employee_leave_summary(
    employee_id: int,
    year: Optional[int] = Query(None, description="Filter by year"),
    db: Session = Depends(get_db)
):
    """Get comprehensive leave summary for an employee"""
    try:
        if not year:
            year = datetime.now().year
        
        # Get employee
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
        
        # Get leave balances
        balance_service = LeaveBalanceService(db)
        leave_balances = balance_service.get_employee_leave_balances(employee_id, year)
        
        # Get leave requests
        request_service = LeaveRequestService(db)
        all_requests = request_service.get_employee_leave_requests(employee_id, year)
        
        # Calculate statistics
        total_requests = len(all_requests)
        approved_requests = len([r for r in all_requests if r.status == LeaveStatus.APPROVED])
        pending_requests = len([r for r in all_requests if r.status == LeaveStatus.PENDING])
        
        return EmployeeLeaveSummary(
            employee=employee,
            leave_balances=leave_balances,
            total_requests_this_year=total_requests,
            approved_requests_this_year=approved_requests,
            pending_requests=pending_requests
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching employee leave summary: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/summary/employee/by-code/{employee_code}", response_model=EmployeeLeaveSummary)
def get_employee_leave_summary_by_code(
    employee_code: str,
    year: Optional[int] = Query(None, description="Filter by year"),
    db: Session = Depends(get_db)
):
    """Get comprehensive leave summary for an employee by employee code."""
    try:
        if not year:
            year = datetime.now().year
        employee = db.query(Employee).filter(Employee.employee_id == employee_code).first()
        if not employee:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
        balance_service = LeaveBalanceService(db)
        leave_balances = balance_service.get_employee_leave_balances(employee.id, year)
        request_service = LeaveRequestService(db)
        all_requests = request_service.get_employee_leave_requests(employee.id, year)
        total_requests = len(all_requests)
        approved_requests = len([r for r in all_requests if r.status == LeaveStatus.APPROVED])
        pending_requests = len([r for r in all_requests if r.status == LeaveStatus.PENDING])
        return EmployeeLeaveSummary(
            employee=employee,
            leave_balances=leave_balances,
            total_requests_this_year=total_requests,
            approved_requests_this_year=approved_requests,
            pending_requests=pending_requests
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching employee leave summary by code: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
