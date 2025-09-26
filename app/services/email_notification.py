from typing import Optional, Dict, Any
from datetime import datetime
from app.models import LeaveRequest, Employee, LeaveStatus
from app.schemas.leave_management import LeaveRequestWithDetails
import logging

logger = logging.getLogger(__name__)

class EmailNotificationService:
    """Service for simulating email notifications for leave management"""
    
    def __init__(self):
        self.notification_log = []
    
    def send_leave_request_notification(self, leave_request: LeaveRequestWithDetails, manager: Employee) -> bool:
        """Send notification to manager about new leave request"""
        try:
            subject = f"New Leave Request from {leave_request.employee.first_name} {leave_request.employee.last_name}"
            message = self._generate_leave_request_email(leave_request, manager)
            
            # Simulate email sending
            notification = {
                "type": "leave_request",
                "to": manager.email,
                "subject": subject,
                "message": message,
                "timestamp": datetime.utcnow(),
                "leave_request_id": leave_request.id,
                "employee_id": leave_request.employee_id
            }
            
            self.notification_log.append(notification)
            logger.info(f"Email notification sent to {manager.email} for leave request {leave_request.id}")
            
            return True
        except Exception as e:
            logger.error(f"Error sending leave request notification: {str(e)}")
            return False
    
    def send_leave_approval_notification(self, leave_request: LeaveRequestWithDetails, approver: Employee) -> bool:
        """Send notification to employee about leave request approval/rejection"""
        try:
            status_text = "approved" if leave_request.status == LeaveStatus.APPROVED else "rejected"
            subject = f"Leave Request {status_text.title()}"
            message = self._generate_approval_email(leave_request, approver)
            
            # Simulate email sending
            notification = {
                "type": "leave_approval",
                "to": leave_request.employee.email,
                "subject": subject,
                "message": message,
                "timestamp": datetime.utcnow(),
                "leave_request_id": leave_request.id,
                "employee_id": leave_request.employee_id,
                "status": leave_request.status.value
            }
            
            self.notification_log.append(notification)
            logger.info(f"Email notification sent to {leave_request.employee.email} for leave request {leave_request.id}")
            
            return True
        except Exception as e:
            logger.error(f"Error sending leave approval notification: {str(e)}")
            return False
    
    def send_leave_balance_reminder(self, employee: Employee, leave_balances: list) -> bool:
        """Send reminder about leave balance"""
        try:
            subject = "Leave Balance Reminder"
            message = self._generate_balance_reminder_email(employee, leave_balances)
            
            # Simulate email sending
            notification = {
                "type": "balance_reminder",
                "to": employee.email,
                "subject": subject,
                "message": message,
                "timestamp": datetime.utcnow(),
                "employee_id": employee.id
            }
            
            self.notification_log.append(notification)
            logger.info(f"Leave balance reminder sent to {employee.email}")
            
            return True
        except Exception as e:
            logger.error(f"Error sending leave balance reminder: {str(e)}")
            return False
    
    def send_delegation_notification(self, manager: Employee, delegate: Employee, delegation_period: str) -> bool:
        """Send notification about leave delegation"""
        try:
            subject = f"Leave Delegation Assignment - {delegation_period}"
            message = self._generate_delegation_email(manager, delegate, delegation_period)
            
            # Simulate email sending to delegate
            notification = {
                "type": "delegation_assignment",
                "to": delegate.email,
                "subject": subject,
                "message": message,
                "timestamp": datetime.utcnow(),
                "manager_id": manager.id,
                "delegate_id": delegate.id
            }
            
            self.notification_log.append(notification)
            logger.info(f"Delegation notification sent to {delegate.email}")
            
            return True
        except Exception as e:
            logger.error(f"Error sending delegation notification: {str(e)}")
            return False
    
    def _generate_leave_request_email(self, leave_request: LeaveRequestWithDetails, manager: Employee) -> str:
        """Generate email content for leave request notification"""
        return f"""
Dear {manager.first_name} {manager.last_name},

A new leave request has been submitted by {leave_request.employee.first_name} {leave_request.employee.last_name}.

Leave Details:
- Employee: {leave_request.employee.first_name} {leave_request.employee.last_name} ({leave_request.employee.employee_id})
- Department: {leave_request.employee.department}
- Leave Type: {leave_request.leave_type.name}
- Start Date: {leave_request.start_date.strftime('%Y-%m-%d')}
- End Date: {leave_request.end_date.strftime('%Y-%m-%d')}
- Total Days: {leave_request.total_days}
- Reason: {leave_request.reason or 'Not specified'}

Please review and approve/reject this request through the leave management system.

Best regards,
Leave Management System
        """.strip()
    
    def _generate_approval_email(self, leave_request: LeaveRequestWithDetails, approver: Employee) -> str:
        """Generate email content for leave approval notification"""
        status_text = "approved" if leave_request.status == LeaveStatus.APPROVED else "rejected"
        approver_name = f"{approver.first_name} {approver.last_name}"
        
        message = f"""
Dear {leave_request.employee.first_name} {leave_request.employee.last_name},

Your leave request has been {status_text} by {approver_name}.

Leave Details:
- Leave Type: {leave_request.leave_type.name}
- Start Date: {leave_request.start_date.strftime('%Y-%m-%d')}
- End Date: {leave_request.end_date.strftime('%Y-%m-%d')}
- Total Days: {leave_request.total_days}
- Status: {leave_request.status.value.title()}
"""
        
        if leave_request.status == LeaveStatus.REJECTED and leave_request.rejection_reason:
            message += f"- Rejection Reason: {leave_request.rejection_reason}\n"
        
        message += """
Please contact your manager if you have any questions.

Best regards,
Leave Management System
        """.strip()
        
        return message
    
    def _generate_balance_reminder_email(self, employee: Employee, leave_balances: list) -> str:
        """Generate email content for leave balance reminder"""
        current_year = datetime.now().year
        
        message = f"""
Dear {employee.first_name} {employee.last_name},

This is a reminder about your leave balances for {current_year}:

"""
        
        for balance in leave_balances:
            message += f"- {balance.leave_type.name}: {balance.remaining_balance} days remaining\n"
        
        message += f"""
Total leave requests this year: {sum(len([b for b in leave_balances if b.total_used > 0]) for _ in [1])}

Please plan your leave requests accordingly and ensure you have sufficient balance for your planned time off.

Best regards,
Leave Management System
        """.strip()
        
        return message
    
    def _generate_delegation_email(self, manager: Employee, delegate: Employee, delegation_period: str) -> str:
        """Generate email content for delegation notification"""
        return f"""
Dear {delegate.first_name} {delegate.last_name},

You have been assigned as a leave approver for {manager.first_name} {manager.last_name} during the following period:

{delegation_period}

During this time, you will be responsible for:
- Reviewing and approving/rejecting leave requests from {manager.first_name}'s subordinates
- Ensuring proper leave balance validation
- Maintaining leave policy compliance

Please log into the leave management system to review any pending requests.

Best regards,
Leave Management System
        """.strip()
    
    def get_notification_history(self, limit: int = 100) -> list:
        """Get notification history"""
        return self.notification_log[-limit:] if limit else self.notification_log
    
    def get_notifications_by_type(self, notification_type: str) -> list:
        """Get notifications by type"""
        return [n for n in self.notification_log if n["type"] == notification_type]
    
    def get_notifications_by_employee(self, employee_id: int) -> list:
        """Get notifications related to a specific employee"""
        return [n for n in self.notification_log if n.get("employee_id") == employee_id]
    
    def clear_notification_log(self):
        """Clear notification history (for testing purposes)"""
        self.notification_log.clear()
        logger.info("Notification log cleared")

# Global instance
email_service = EmailNotificationService()
