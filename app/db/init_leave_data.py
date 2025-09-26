
import sys
import os
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session

# Add the project root directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

from app.db.session import SessionLocal, engine
from app.models import Base, Employee, LeaveType, LeaveBalance, Holiday, LeaveDelegation
from app.services.leave_management import LeaveBalanceService

def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

def create_sample_employees(db: Session):
    """Create sample employees with manager hierarchy"""
    print("Creating sample employees...")
    
    # Create CEO (no manager)
    ceo = Employee(
        employee_id="EMP001",
        first_name="John",
        last_name="Smith",
        email="john.smith@company.com",
        department="Executive",
        position="CEO",
        manager_id=None,
        hire_date=date(2020, 1, 15),
        is_active=True
    )
    db.add(ceo)
    db.flush()  # Get the ID
    
    # Create Department Heads
    hr_head = Employee(
        employee_id="EMP002",
        first_name="Sarah",
        last_name="Johnson",
        email="sarah.johnson@company.com",
        department="Human Resources",
        position="HR Director",
        manager_id=ceo.id,
        hire_date=date(2020, 3, 1),
        is_active=True
    )
    db.add(hr_head)
    db.flush()
    
    it_head = Employee(
        employee_id="EMP003",
        first_name="Michael",
        last_name="Brown",
        email="michael.brown@company.com",
        department="Information Technology",
        position="IT Director",
        manager_id=ceo.id,
        hire_date=date(2020, 2, 15),
        is_active=True
    )
    db.add(it_head)
    db.flush()
    
    sales_head = Employee(
        employee_id="EMP004",
        first_name="Emily",
        last_name="Davis",
        email="emily.davis@company.com",
        department="Sales",
        position="Sales Director",
        manager_id=ceo.id,
        hire_date=date(2020, 4, 1),
        is_active=True
    )
    db.add(sales_head)
    db.flush()
    
    # Create Managers
    hr_manager = Employee(
        employee_id="EMP005",
        first_name="David",
        last_name="Wilson",
        email="david.wilson@company.com",
        department="Human Resources",
        position="HR Manager",
        manager_id=hr_head.id,
        hire_date=date(2021, 1, 10),
        is_active=True
    )
    db.add(hr_manager)
    db.flush()
    
    it_manager = Employee(
        employee_id="EMP006",
        first_name="Lisa",
        last_name="Anderson",
        email="lisa.anderson@company.com",
        department="Information Technology",
        position="IT Manager",
        manager_id=it_head.id,
        hire_date=date(2021, 2, 1),
        is_active=True
    )
    db.add(it_manager)
    db.flush()
    
    sales_manager = Employee(
        employee_id="EMP007",
        first_name="Robert",
        last_name="Taylor",
        email="robert.taylor@company.com",
        department="Sales",
        position="Sales Manager",
        manager_id=sales_head.id,
        hire_date=date(2021, 3, 15),
        is_active=True
    )
    db.add(sales_manager)
    db.flush()
    
    # Create Regular Employees
    employees_data = [
        ("EMP008", "Jennifer", "Martinez", "jennifer.martinez@company.com", "Human Resources", "HR Specialist", hr_manager.id, date(2021, 6, 1)),
        ("EMP009", "James", "Garcia", "james.garcia@company.com", "Human Resources", "Recruiter", hr_manager.id, date(2021, 8, 15)),
        ("EMP010", "Maria", "Rodriguez", "maria.rodriguez@company.com", "Information Technology", "Software Developer", it_manager.id, date(2021, 5, 1)),
        ("EMP011", "William", "Lee", "william.lee@company.com", "Information Technology", "System Administrator", it_manager.id, date(2021, 7, 1)),
        ("EMP012", "Patricia", "White", "patricia.white@company.com", "Information Technology", "QA Engineer", it_manager.id, date(2021, 9, 1)),
        ("EMP013", "Christopher", "Harris", "christopher.harris@company.com", "Sales", "Sales Representative", sales_manager.id, date(2021, 4, 1)),
        ("EMP014", "Linda", "Clark", "linda.clark@company.com", "Sales", "Account Manager", sales_manager.id, date(2021, 6, 15)),
        ("EMP015", "Daniel", "Lewis", "daniel.lewis@company.com", "Sales", "Sales Representative", sales_manager.id, date(2021, 10, 1)),
    ]
    
    for emp_id, first_name, last_name, email, dept, pos, mgr_id, hire_date in employees_data:
        employee = Employee(
            employee_id=emp_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            department=dept,
            position=pos,
            manager_id=mgr_id,
            hire_date=hire_date,
            is_active=True
        )
        db.add(employee)
    
    db.commit()
    print(f"Created {len(employees_data) + 7} sample employees")

def create_sample_leave_types(db: Session):
    """Create sample leave types"""
    print("Creating sample leave types...")
    
    leave_types_data = [
        ("Sick Leave", "Leave for illness or medical appointments", 10, 5, True, True, False, None),
        ("Casual Leave", "General purpose leave for personal reasons", 12, 10, True, False, False, None),
        ("Earned Leave", "Annual vacation leave", 21, 15, True, False, True, 5),
        ("Maternity Leave", "Leave for maternity purposes", 90, 90, True, True, False, None),
        ("Paternity Leave", "Leave for paternity purposes", 15, 15, True, False, False, None),
        ("Emergency Leave", "Leave for emergency situations", 3, 3, False, False, False, None),
        ("Compensatory Leave", "Leave earned through overtime work", None, 5, True, False, True, 2),
    ]
    
    for name, desc, max_yearly, max_consecutive, requires_approval, requires_medical, carry_forward, max_carry_forward in leave_types_data:
        leave_type = LeaveType(
            name=name,
            description=desc,
            max_days_per_year=max_yearly,
            max_consecutive_days=max_consecutive,
            requires_approval=requires_approval,
            requires_medical_certificate=requires_medical,
            carry_forward_enabled=carry_forward,
            max_carry_forward_days=max_carry_forward,
            is_active=True
        )
        db.add(leave_type)
    
    db.commit()
    print(f"Created {len(leave_types_data)} leave types")

def create_sample_holidays(db: Session):
    """Create sample holidays"""
    print("Creating sample holidays...")
    
    current_year = datetime.now().year
    
    holidays_data = [
        ("New Year's Day", date(current_year, 1, 1), True, "New Year celebration"),
        ("Martin Luther King Jr. Day", date(current_year, 1, 15), True, "Federal holiday"),
        ("Presidents' Day", date(current_year, 2, 19), True, "Federal holiday"),
        ("Memorial Day", date(current_year, 5, 27), True, "Federal holiday"),
        ("Independence Day", date(current_year, 7, 4), True, "Independence Day"),
        ("Labor Day", date(current_year, 9, 2), True, "Federal holiday"),
        ("Columbus Day", date(current_year, 10, 14), True, "Federal holiday"),
        ("Veterans Day", date(current_year, 11, 11), True, "Federal holiday"),
        ("Thanksgiving Day", date(current_year, 11, 28), True, "Federal holiday"),
        ("Christmas Day", date(current_year, 12, 25), True, "Christmas celebration"),
    ]
    
    for name, holiday_date, is_recurring, description in holidays_data:
        holiday = Holiday(
            name=name,
            date=holiday_date,
            is_recurring=is_recurring,
            description=description,
            is_active=True
        )
        db.add(holiday)
    
    db.commit()
    print(f"Created {len(holidays_data)} holidays")

def initialize_leave_balances(db: Session):
    """Initialize leave balances for all employees"""
    print("Initializing leave balances for all employees...")
    
    balance_service = LeaveBalanceService(db)
    current_year = datetime.now().year
    
    # Get all employees
    employees = db.query(Employee).filter(Employee.is_active == True).all()
    
    for employee in employees:
        balance_service.initialize_employee_leave_balances(employee.id, current_year)
    
    print(f"Initialized leave balances for {len(employees)} employees")

def create_sample_delegations(db: Session):
    """Create sample leave delegations"""
    print("Creating sample leave delegations...")
    
    # Get some managers and their subordinates
    hr_manager = db.query(Employee).filter(Employee.employee_id == "EMP005").first()
    it_manager = db.query(Employee).filter(Employee.employee_id == "EMP006").first()
    sales_manager = db.query(Employee).filter(Employee.employee_id == "EMP007").first()
    
    # Create delegations for vacation periods
    delegations_data = [
        (hr_manager.id, it_manager.id, date(2024, 6, 1), date(2024, 6, 15), "HR Manager vacation delegation"),
        (it_manager.id, sales_manager.id, date(2024, 7, 1), date(2024, 7, 10), "IT Manager vacation delegation"),
        (sales_manager.id, hr_manager.id, date(2024, 8, 1), date(2024, 8, 7), "Sales Manager vacation delegation"),
    ]
    
    for manager_id, delegate_id, start_date, end_date, reason in delegations_data:
        delegation = LeaveDelegation(
            manager_id=manager_id,
            delegate_id=delegate_id,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
            is_active=True
        )
        db.add(delegation)
    
    db.commit()
    print(f"Created {len(delegations_data)} leave delegations")

def main():
    """Main initialization function"""
    print("Starting Leave Management System database initialization...")
    
    # Create tables
    create_tables()
    
    # Create sample data
    db = SessionLocal()
    try:
        create_sample_employees(db)
        create_sample_leave_types(db)
        create_sample_holidays(db)
        initialize_leave_balances(db)
        create_sample_delegations(db)
        
        print("\n" + "="*50)
        print("Database initialization completed successfully!")
        print("="*50)
        print("\nSample data created:")
        print("- 15 employees with manager hierarchy")
        print("- 7 different leave types")
        print("- 10 holidays for current year")
        print("- Leave balances for all employees")
        print("- 3 leave delegations")
        print("\nYou can now start using the Leave Management System!")
        
    except Exception as e:
        print(f"Error during initialization: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
