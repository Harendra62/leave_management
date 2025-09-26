from fastapi import Request, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import request_validation_exception_handler
from sqlalchemy.exc import IntegrityError
import logging


def add_global_exception_handlers(app: FastAPI):
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        print(f"DEBUG: Validation Error on {request.method} {request.url}")
        print(f"DEBUG: Validation Error Details: {exc.errors()}")
        try:
            body = await request.body()
            print(f"DEBUG: Request Body: {body.decode('utf-8')}")
        except Exception as e:
            print(f"DEBUG: Could not read request body: {e}")
        return await request_validation_exception_handler(request, exc)

    @app.exception_handler(IntegrityError)
    async def db_integrity_exception_handler(request: Request, exc: IntegrityError):
        # Example: handle title too long or other DB constraint errors
        logging.error(f"DB IntegrityError: {exc}")
        return JSONResponse(
            status_code=400,
            content={"detail": "Database error: likely a field is too long or violates constraints."}
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logging.error(f"Unhandled Exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected error occurred."}
        )
