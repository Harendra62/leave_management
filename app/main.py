import os
import time
import platform

# Set Dublin timezone globally
os.environ['TZ'] = 'Europe/Dublin'
# time.tzset() is not available on Windows
if platform.system() != 'Windows':
    time.tzset()  # Apply timezone change immediately

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import api_router
from app.core.middleware import add_global_exception_handlers
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

app = FastAPI(
    title="Leave Management API",
    version="1.0.0",
    description="API for Employee Leave Management System",
    docs_url="/app/v1/api/docs",
    redoc_url=None,
    openapi_url="/app/v1/api/openapi.json",
)

@app.get("/api/health-check", include_in_schema=False)
def health_check():
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Leave Management API is running", "status": "ok"}
    )

app.include_router(api_router, prefix="/app/v1/api")

add_global_exception_handlers(app)

# Add CORS middleware to allow requests from every origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
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
