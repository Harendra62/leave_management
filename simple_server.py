#!/usr/bin/env python3
"""
Simple server to test the leave management system
"""

import os
import sys
from datetime import datetime, date, timedelta

# Add the project root directory to the Python path
project_root = os.path.dirname(__file__)
sys.path.insert(0, project_root)

# Set timezone
os.environ['TZ'] = 'Europe/Dublin'

try:
    from fastapi import FastAPI, status
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from fastapi.openapi.utils import get_openapi
    
    app = FastAPI(
        title="Leave Management API",
        version="1.0.0",
        description="API for Employee Leave Management System",
        docs_url="/docs",
        redoc_url=None,
        openapi_url="/openapi.json",
    )

    @app.get("/api/health-check", include_in_schema=False)
    def health_check():
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Leave Management API is running", "status": "ok"}
        )

    @app.get("/")
    def root():
        return {"message": "Welcome to Leave Management System", "docs": "/docs"}

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title="Leave Management API",
            version="1.0.0",
            description="API for Employee Leave Management System",
            routes=app.routes,
        )
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi

    if __name__ == "__main__":
        import uvicorn
        print("Starting Leave Management System...")
        print("API Documentation will be available at: http://localhost:8000/docs")
        print("Health check endpoint: http://localhost:8000/api/health-check")
        uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please install the required packages:")
    print("pip install fastapi uvicorn")
    sys.exit(1)

