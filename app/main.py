"""FastAPI application factory wiring and centralized HTTP error handling."""
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import logging
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.db import initialize_database
from app.errors import DomainError
from app.feedback import feedback_router, initialize_feedback_storage
from app.routers import reports, tickets

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    initialize_feedback_storage()
    logger.info("database and feedback schemas initialized")
    yield


app = FastAPI(title="Ticket Service", version="1.0.0", lifespan=lifespan)
app.include_router(tickets.router)
app.include_router(reports.router)
app.include_router(feedback_router)


@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID") or request.headers.get("X-Request-ID") or str(uuid4())
    request.state.correlation_id = correlation_id
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


def _error_response(request: Request, status_code: int, code: str, message: str) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", str(uuid4()))
    return JSONResponse(status_code=status_code, content={"error": {
        "code": code, "message": message, "timestamp": datetime.now(timezone.utc).isoformat(),
        "correlation_id": correlation_id,
    }})


@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, error: DomainError) -> JSONResponse:
    logger.warning("domain failure correlation_id=%s detail=%s", getattr(request.state, "correlation_id", "unknown"), str(error))
    return _error_response(request, error.status_code, error.code, error.client_message)


@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, error: HTTPException) -> JSONResponse:
    message = error.detail if isinstance(error.detail, str) else "The request could not be completed."
    code = "ticket_not_found" if error.status_code == 404 else "http_error"
    return _error_response(request, error.status_code, code, message)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, _: RequestValidationError) -> JSONResponse:
    return _error_response(request, 422, "validation_error", "Request validation failed.")


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, error: Exception) -> JSONResponse:
    logger.exception("unhandled failure correlation_id=%s", getattr(request.state, "correlation_id", "unknown"), exc_info=error)
    return _error_response(request, 500, "internal_error", "An unexpected error occurred.")


@app.get("/health", tags=["operational"])
def health() -> dict[str, str]:
    return {"status": "ok"}
