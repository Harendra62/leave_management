#!/bin/bash

# Leave Management System Startup Script

echo "Starting Leave Management System..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed. Please install Python 3.8+ and try again."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "pip3 is required but not installed. Please install pip3 and try again."
    exit 1
fi

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
else
    echo "requirements.txt not found. Please ensure you're in the correct directory."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Creating .env file with default values..."
    cat > .env << EOF
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=leave_management
ENV=development
TIMEZONE=Europe/Dublin
EOF
    echo "Please update the .env file with your database credentials."
fi

# Initialize database if init script exists
if [ -f "app/db/init_leave_data.py" ]; then
    echo "Initializing database with sample data..."
    python3 app/db/init_leave_data.py
fi

# Start the application
echo "Starting FastAPI application..."
echo "API Documentation will be available at: http://localhost:8000/leave/v1/api/docs"
echo "Health check endpoint: http://localhost:8000/api/health-check"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
