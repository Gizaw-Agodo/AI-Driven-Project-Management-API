import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.utils.exceptions import ( AppException)
from app.core.errors import create_error_response

# Configure logger
logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    
    # 🎓 BASE EXCEPTION HANDLER 
    @app.exception_handler(AppException)
    async def app_exception_handler( request: Request, exc: AppException ) -> JSONResponse:
        
        return JSONResponse(
            status_code=exc.status_code,
            content=create_error_response(
                message=exc.message,
                status_code=exc.status_code
            )
        )
    
    # 🎓 PYDANTIC VALIDATION ERRORS
    @app.exception_handler(RequestValidationError)
    async def request_validation_exception_handler(
        request: Request,
        exc: RequestValidationError
    ) -> JSONResponse:
        
        
       
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=create_error_response(
                message="Invalid request data",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        )
    
    # 🎓 DATABASE ERRORS
    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(
        request: Request,
        exc: IntegrityError
    ) -> JSONResponse:
        
        error_message = "Database constraint violation"
        
        if "unique constraint" in str(exc).lower():
            error_message = "A record with this information already exists"
        elif "foreign key constraint" in str(exc).lower():
            error_message = "Referenced record does not exist"
        elif "not null constraint" in str(exc).lower():
            error_message = "Required field is missing"
        
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=create_error_response(
                message=error_message,
                status_code=status.HTTP_409_CONFLICT
            )
        )
    
    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_error_handler(
        request: Request,
        exc: SQLAlchemyError
    ) -> JSONResponse:
       
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=create_error_response(
                message="A database error occurred",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        )
    
    # 🎓 GENERIC EXCEPTION HANDLER (last resort)
    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request,
        exc: Exception
    ) -> JSONResponse:

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=create_error_response(
                message="An unexpected error occurred. Please try again later.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        )