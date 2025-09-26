from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime, date
from app.db.session import get_db
from app.models import LeaveType, Holiday, LeaveDelegation, Employee, LeaveRequest, LeaveStatus
from app.schemas.leave_management import (
    LeaveTypeCreate, LeaveTypeUpdate, LeaveType as LeaveTypeSchema,
    HolidayCreate, HolidayUpdate, Holiday as HolidaySchema,
    LeaveDelegationCreate, LeaveDelegationUpdate, LeaveDelegationWithDetails,
    LeaveReportRequest, LeaveReportResponse
)
from app.services.leave_management import LeaveRequestService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/leave", tags=["Leave Management - Admin"])

# Leave Type Management
@router.post("/types", response_model=LeaveTypeSchema, status_code=status.HTTP_201_CREATED)
def create_leave_type(
    leave_type: LeaveTypeCreate,
    db: Session = Depends(get_db)
):
    """Create a new leave type"""
    try:
        # Check if leave type already exists
        existing = db.query(LeaveType).filter(LeaveType.name == leave_type.name).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Leave type with this name already exists")
        
        db_leave_type = LeaveType(**leave_type.dict())
        db.add(db_leave_type)
        db.commit()
        db.refresh(db_leave_type)
        
        return db_leave_type
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating leave type: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/types", response_model=List[LeaveTypeSchema])
def get_leave_types(
    active_only: bool = Query(True, description="Return only active leave types"),
    db: Session = Depends(get_db)
):
    """Get all leave types"""
    try:
        query = db.query(LeaveType)
        if active_only:
            query = query.filter(LeaveType.is_active == True)
        
        return query.all()
    except Exception as e:
        logger.error(f"Error fetching leave types: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/types/{type_id}", response_model=LeaveTypeSchema)
def get_leave_type(
    type_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific leave type"""
    try:
        leave_type = db.query(LeaveType).filter(LeaveType.id == type_id).first()
        if not leave_type:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave type not found")
        
        return leave_type
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching leave type: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.put("/types/{type_id}", response_model=LeaveTypeSchema)
def update_leave_type(
    type_id: int,
    leave_type_update: LeaveTypeUpdate,
    db: Session = Depends(get_db)
):
  
    try:
        leave_type = db.query(LeaveType).filter(LeaveType.id == type_id).first()
        if not leave_type:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave type not found")
        
        # Update fields
        for field, value in leave_type_update.dict(exclude_unset=True).items():
            setattr(leave_type, field, value)
        
        db.commit()
        db.refresh(leave_type)
        
        return leave_type
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating leave type: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

# Holiday Management
@router.post("/holidays", response_model=HolidaySchema, status_code=status.HTTP_201_CREATED)
def create_holiday(
    holiday: HolidayCreate,
    db: Session = Depends(get_db)
):
    """Create a new holiday"""
    try:
        db_holiday = Holiday(**holiday.dict())
        db.add(db_holiday)
        db.commit()
        db.refresh(db_holiday)
        
        return db_holiday
    except Exception as e:
        logger.error(f"Error creating holiday: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/holidays", response_model=List[HolidaySchema])
def get_holidays(
    year: Optional[int] = Query(None, description="Filter by year"),
    active_only: Optional[bool] = Query(None, description="Deprecated. Use is_active instead.", include_in_schema=False),
    is_active: Optional[bool] = Query(None, description="Filter by active status: true for active, false for inactive, omit for all"),
    db: Session = Depends(get_db)
):
    
    try:
        query = db.query(Holiday)
        
        if is_active is not None:
            query = query.filter(Holiday.is_active == is_active)
        elif active_only:
            query = query.filter(Holiday.is_active == True)
        
        if year:
            # Cross-DB compatible year filter using date range
            year_start = date(year, 1, 1)
            year_end = date(year, 12, 31)
            query = query.filter(and_(Holiday.date >= year_start, Holiday.date <= year_end))
        
        return query.order_by(Holiday.date).all()
    except Exception as e:
        logger.error(f"Error fetching holidays: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.put("/holidays/{holiday_id}", response_model=HolidaySchema)
def update_holiday(
    holiday_id: int,
    holiday_update: HolidayUpdate,
    db: Session = Depends(get_db)
):
    """Update a holiday"""
    try:
        holiday = db.query(Holiday).filter(Holiday.id == holiday_id).first()
        if not holiday:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holiday not found")
        
        # Update fields
        for field, value in holiday_update.dict(exclude_unset=True).items():
            setattr(holiday, field, value)
        
        db.commit()
        db.refresh(holiday)
        
        return holiday
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating holiday: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.delete("/holidays/{holiday_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_holiday(
    holiday_id: int,
    db: Session = Depends(get_db)
):
    """Delete a holiday"""
    try:
        holiday = db.query(Holiday).filter(Holiday.id == holiday_id).first()
        if not holiday:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holiday not found")
        
        db.delete(holiday)
        db.commit()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting holiday: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

# Leave Delegation Management
@router.post("/delegations", response_model=LeaveDelegationWithDetails, status_code=status.HTTP_201_CREATED)
def create_leave_delegation(
    delegation: LeaveDelegationCreate,
    db: Session = Depends(get_db)
):
    """Create a new leave delegation"""
    try:
        # Validate that manager and delegate exist
        manager = db.query(Employee).filter(Employee.id == delegation.manager_id).first()
        delegate = db.query(Employee).filter(Employee.id == delegation.delegate_id).first()
        
        if not manager:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manager not found")
        if not delegate:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delegate not found")
        
        db_delegation = LeaveDelegation(**delegation.dict())
        db.add(db_delegation)
        db.commit()
        db.refresh(db_delegation)
        
        return db_delegation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating leave delegation: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/delegations", response_model=List[LeaveDelegationWithDetails])
def get_leave_delegations(
    manager_id: Optional[int] = Query(None, description="Filter by manager ID"),
    active_only: bool = Query(True, description="Return only active delegations"),
    db: Session = Depends(get_db)
):
    """Get all leave delegations"""
    try:
        query = db.query(LeaveDelegation)
        
        if manager_id:
            query = query.filter(LeaveDelegation.manager_id == manager_id)
        
        if active_only:
            query = query.filter(LeaveDelegation.is_active == True)
        
        return query.order_by(LeaveDelegation.start_date.desc()).all()
    except Exception as e:
        logger.error(f"Error fetching leave delegations: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.put("/delegations/{delegation_id}", response_model=LeaveDelegationWithDetails)
def update_leave_delegation(
    delegation_id: int,
    delegation_update: LeaveDelegationUpdate,
    db: Session = Depends(get_db)
):
    """Update a leave delegation"""
    try:
        delegation = db.query(LeaveDelegation).filter(LeaveDelegation.id == delegation_id).first()
        if not delegation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave delegation not found")
        
        # Update fields
        for field, value in delegation_update.dict(exclude_unset=True).items():
            setattr(delegation, field, value)
        
        db.commit()
        db.refresh(delegation)
        
        return delegation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating leave delegation: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

# Reports and Analytics
@router.post("/reports", response_model=LeaveReportResponse)
def generate_leave_report(
    report_request: LeaveReportRequest,
    db: Session = Depends(get_db)
):
    """Generate comprehensive leave reports"""
    try:
        service = LeaveRequestService(db)
        
        # Build query based on filters
        query = db.query(LeaveRequest)
        
        if report_request.employee_id:
            query = query.filter(LeaveRequest.employee_id == report_request.employee_id)
        
        if report_request.department:
            query = query.join(Employee, LeaveRequest.employee_id == Employee.id).filter(Employee.department == report_request.department)
        
        if report_request.start_date:
            query = query.filter(LeaveRequest.start_date >= report_request.start_date)
        
        if report_request.end_date:
            query = query.filter(LeaveRequest.end_date <= report_request.end_date)
        
        if report_request.leave_type_id:
            query = query.filter(LeaveRequest.leave_type_id == report_request.leave_type_id)
        
        if report_request.status:
            query = query.filter(LeaveRequest.status == report_request.status)
        
        # Execute query
        leave_requests = query.order_by(LeaveRequest.created_at.desc()).all()
        
        # Calculate statistics
        total_requests = len(leave_requests)
        approved_requests = len([r for r in leave_requests if r.status.value == "approved"])
        rejected_requests = len([r for r in leave_requests if r.status.value == "rejected"])
        pending_requests = len([r for r in leave_requests if r.status.value == "pending"])
        
        return LeaveReportResponse(
            total_requests=total_requests,
            approved_requests=approved_requests,
            rejected_requests=rejected_requests,
            pending_requests=pending_requests,
            leave_requests=leave_requests
        )
    except Exception as e:
        logger.error(f"Error generating leave report: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/reports/department/{department}", response_model=LeaveReportResponse)
def get_department_leave_report(
    department: str,
    year: Optional[int] = Query(None, description="Filter by year"),
    db: Session = Depends(get_db)
):
    """Get leave report for a specific department"""
    try:
        query = db.query(LeaveRequest).join(Employee, LeaveRequest.employee_id == Employee.id).filter(Employee.department == department)
        
        if year:
            year_start = date(year, 1, 1)
            year_end = date(year, 12, 31)
            query = query.filter(
                and_(
                    LeaveRequest.start_date >= year_start,
                    LeaveRequest.start_date <= year_end
                )
            )
        
        leave_requests = query.order_by(LeaveRequest.created_at.desc()).all()
        
        # Calculate statistics
        total_requests = len(leave_requests)
        approved_requests = len([r for r in leave_requests if r.status.value == "approved"])
        rejected_requests = len([r for r in leave_requests if r.status.value == "rejected"])
        pending_requests = len([r for r in leave_requests if r.status.value == "pending"])
        
        return LeaveReportResponse(
            total_requests=total_requests,
            approved_requests=approved_requests,
            rejected_requests=rejected_requests,
            pending_requests=pending_requests,
            leave_requests=leave_requests
        )
    except Exception as e:
        logger.error(f"Error generating department leave report: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
