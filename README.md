# Employee Leave Management System

A comprehensive Python-based leave management system built with FastAPI that handles leave requests, approval workflows, balance tracking, and generates detailed reports.

## Features

### 1. Leave Request Management
- Submit leave requests with different types (sick, casual, earned, etc.)
- Validate leave balance before submission
- Check for overlapping leave requests
- Holiday conflict detection
- Comprehensive validation with detailed feedback

### 2. Approval Workflow
- Route requests to appropriate managers based on employee hierarchy
- Approve/reject requests with comments
- Handle delegation during manager absence
- Email notification simulation for all approval actions

### 3. Leave Balance Tracking
- Track different leave types with carry-forward rules
- Auto-credit monthly/yearly leave quotas
- Calculate remaining balance after each request
- Support for different leave policies per type

### 4. Reports and Analytics
- Generate leave history for employees
- Department-wise leave reports
- Comprehensive analytics and statistics
- Policy compliance tracking

### 5. Advanced Features
- Manager hierarchy and delegation system
- Holiday management
- Comprehensive business rule validation
- Email notification system
- Leave policy management

## System Architecture

### Database Models
- **Employee**: Employee information with manager hierarchy
- **LeaveType**: Different types of leave with specific rules
- **LeaveRequest**: Leave requests with approval workflow
- **LeaveBalance**: Employee leave balances per year
- **Holiday**: Company holidays and recurring events
- **LeaveDelegation**: Manager delegation assignments

### API Endpoints

#### Leave Request Management
- `POST /leave/requests` - Submit new leave request
- `GET /leave/requests/employee/{employee_id}` - Get employee's leave requests
- `GET /leave/requests/pending/{manager_id}` - Get pending requests for manager
- `PUT /leave/requests/{request_id}/approve` - Approve/reject leave request
- `GET /leave/requests/{request_id}` - Get specific leave request
- `PUT /leave/requests/{request_id}` - Update leave request
- `DELETE /leave/requests/{request_id}` - Cancel leave request

#### Leave Balance Management
- `GET /leave/balances/employee/{employee_id}` - Get employee leave balances
- `POST /leave/balances/initialize/{employee_id}` - Initialize leave balances

#### Validation and Policies
- `POST /leave/validate` - Validate leave request
- `POST /leave/validate/comprehensive` - Comprehensive validation
- `GET /leave/policy/summary/{employee_id}` - Get policy summary

#### Administrative Functions
- `POST /leave/types` - Create leave type
- `GET /leave/types` - Get all leave types
- `POST /leave/holidays` - Create holiday
- `GET /leave/holidays` - Get holidays
- `POST /leave/delegations` - Create delegation
- `POST /leave/reports` - Generate reports

## Installation and Setup

### Prerequisites
- Python 3.8+
- MySQL database
- pip package manager

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/Harendra62/leave_management
   cd leave
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   Create a `.env` file with the following variables:
   ```env
   MYSQL_USER=your_mysql_user
   MYSQL_PASSWORD=your_mysql_password
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_DB=leave_management
   ENV=development
   ```

4. **Initialize the database**
   ```bash
   python app/db/init_leave_data.py
   ```

5. **Start the application**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Access the API documentation**
   Open your browser and navigate to: `http://localhost:8000/app/v1/api/docs`

## Sample Data

The initialization script creates sample data including:

- **15 employees** with manager hierarchy (CEO → Directors → Managers → Employees)
- **7 leave types** with different rules and policies
- **10 holidays** for the current year
- **Leave balances** for all employees
- **3 leave delegations** for testing

### Sample Employee Hierarchy
```
CEO (John Smith)
├── HR Director (Sarah Johnson)
│   └── HR Manager (David Wilson)
│       ├── HR Specialist (Jennifer Martinez)
│       └── Recruiter (James Garcia)
├── IT Director (Michael Brown)
│   └── IT Manager (Lisa Anderson)
│       ├── Software Developer (Maria Rodriguez)
│       ├── System Administrator (William Lee)
│       └── QA Engineer (Patricia White)
└── Sales Director (Emily Davis)
    └── Sales Manager (Robert Taylor)
        ├── Sales Representative (Christopher Harris)
        ├── Account Manager (Linda Clark)
        └── Sales Representative (Daniel Lewis)
```

## API Usage Examples

### Submit a Leave Request
```bash
curl -X POST "http://localhost:8000/app/v1/api/leave/requests?employee_id=8" \
  -H "Content-Type: application/json" \
  -d '{
    "leave_type_id": 1,
    "start_date": "2024-06-15",
    "end_date": "2024-06-17",
    "reason": "Family vacation"
  }'
```

### Get Employee Leave Requests
```bash
curl -X GET "http://localhost:8000/app/v1/api/leave/requests/employee/8?year=2024"
```

### Approve a Leave Request
```bash
curl -X PUT "http://localhost:8000/app/v1/api/leave/requests/1/approve?approver_id=5" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "approved",
    "comments": "Approved for family vacation"
  }'
```

### Get Leave Balances
```bash
curl -X GET "http://localhost:8000/app/v1/api/leave/balances/employee/8"
```

### Comprehensive Validation
```bash
curl -X POST "http://localhost:8000/app/v1/api/leave/validate/comprehensive" \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": 8,
    "leave_request": {
      "leave_type_id": 1,
      "start_date": "2024-06-15",
      "end_date": "2024-06-17",
      "reason": "Family vacation"
    }
  }'
```

## Business Rules and Validation

### Leave Request Validation
- **Date Validation**: Start date cannot be in the past, end date must be after start date
- **Balance Check**: Sufficient leave balance must be available
- **Conflict Detection**: No overlapping requests allowed
- **Holiday Conflicts**: Requests cannot conflict with company holidays
- **Leave Type Rules**: Respects maximum consecutive days and other type-specific rules
- **Business Rules**: Considers probation period, advance notice, etc.

### Leave Types and Rules
- **Sick Leave**: 10 days/year, max 5 consecutive, requires medical certificate
- **Casual Leave**: 12 days/year, max 10 consecutive
- **Earned Leave**: 21 days/year, max 15 consecutive, carry-forward enabled
- **Maternity Leave**: 90 days/year, max 90 consecutive
- **Paternity Leave**: 15 days/year, max 15 consecutive
- **Emergency Leave**: 3 days/year, max 3 consecutive, no approval required
- **Compensatory Leave**: Unlimited, max 5 consecutive, carry-forward enabled

### Approval Workflow
1. Employee submits leave request
2. System validates request against business rules
3. Request is routed to employee's manager
4. Manager receives email notification
5. Manager approves/rejects with comments
6. Employee receives email notification
7. If approved, leave balance is updated

## Email Notifications

The system includes a comprehensive email notification service that simulates:
- Leave request notifications to managers
- Approval/rejection notifications to employees
- Leave balance reminders
- Delegation assignment notifications

All notifications are logged and can be retrieved for testing purposes.

## Testing the System

### Health Check
```bash
curl -X GET "http://localhost:8000/api/health-check"
```

### Sample Workflow Test
1. Submit a leave request for an employee
2. Check pending requests for the manager
3. Approve/reject the request
4. Verify leave balance update
5. Check email notifications

## Database Schema

The system uses MySQL with the following main tables:
- `employees` - Employee information and hierarchy
- `leave_types` - Leave type definitions and rules
- `leave_requests` - Leave requests and approval workflow
- `leave_balances` - Employee leave balances per year
- `holidays` - Company holidays
- `leave_delegations` - Manager delegation assignments

## Future Enhancements

- Integration with calendar systems
- Mobile application support
- Advanced reporting and analytics
- Integration with HR systems
- Automated leave accrual
- Multi-company support
- Advanced approval workflows
- Leave request templates
- Bulk operations support

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
