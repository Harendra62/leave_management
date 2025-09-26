from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.db.session import get_db
from app.services.business_rules import BusinessRuleValidationService, LeavePolicyService
from app.schemas.leave_management import LeaveRequestCreate
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/leave", tags=["Leave Management - Validation & Policies"])

@router.post("/validate/comprehensive")
def comprehensive_leave_validation(
    employee_id: int,
    leave_request: LeaveRequestCreate,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Perform comprehensive validation of a leave request"""
    try:
        validation_service = BusinessRuleValidationService(db)
        result = validation_service.validate_leave_request_comprehensive(employee_id, leave_request)
        return result
    except Exception as e:
        logger.error(f"Error in comprehensive validation: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/policy/summary/{employee_id}")
def get_leave_policy_summary(
    employee_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get comprehensive leave policy summary for an employee"""
    try:
        policy_service = LeavePolicyService(db)
        result = policy_service.get_leave_policy_summary(employee_id)
        return result
    except Exception as e:
        logger.error(f"Error getting leave policy summary: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
