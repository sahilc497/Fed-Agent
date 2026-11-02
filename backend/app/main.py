import uuid
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.logging import setup_logging, correlation_id_ctx
from app.core.exceptions import MeshBaseException, PermissionDeniedError, AuthenticationError
from app.db.schema import init_db
from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.departments import router as departments_router
from app.api.v1.permissions import router as permissions_router
from app.api.v1.chat import router as chat_router
from app.api.v1.documents import router as documents_router
from app.api.v1.approvals import router as approvals_router
from app.api.v1.audit import router as audit_router
from app.api.v1.agents import router as agents_router
from app.api.v1.federation import router as federation_router

logger = logging.getLogger("federated_mesh.main")

# Initialize structured logging
setup_logging(debug=settings.DEBUG)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Idempotent SQLite schema initialization
    init_db()
    logger.info("Federated Agentic Mesh SQLite database verified.")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Federated Agentic Mesh — Secure Multi-Agent Enterprise AI Backend",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS configuration supporting Localhost, private LAN Wi-Fi IPs, and configured origins
cors_kwargs = {
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
    # Allow any HTTP / HTTPS origin on private LAN, Wi-Fi, or localhost with full credentials
    "allow_origin_regex": r"^https?:\/\/.*$",
    "allow_origins": []
}

app.add_middleware(
    CORSMiddleware,
    **cors_kwargs
)


# Correlation ID Middleware
@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    corr_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    token = correlation_id_ctx.set(corr_id)
    try:
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = corr_id
        return response
    finally:
        correlation_id_ctx.reset(token)


# Exception Handlers
@app.exception_handler(PermissionDeniedError)
async def permission_denied_handler(request: Request, exc: PermissionDeniedError):
    return JSONResponse(
        status_code=403,
        content={"detail": exc.message, "error_type": "PermissionDeniedError"}
    )


@app.exception_handler(AuthenticationError)
async def authentication_error_handler(request: Request, exc: AuthenticationError):
    return JSONResponse(
        status_code=401,
        content={"detail": exc.message, "error_type": "AuthenticationError"}
    )


@app.exception_handler(MeshBaseException)
async def generic_mesh_handler(request: Request, exc: MeshBaseException):
    return JSONResponse(
        status_code=400,
        content={"detail": exc.message, "error_type": exc.__class__.__name__}
    )


# Include Routers
app.include_router(health_router)
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(departments_router, prefix=settings.API_V1_STR)
app.include_router(permissions_router, prefix=settings.API_V1_STR)
app.include_router(chat_router, prefix=settings.API_V1_STR)
app.include_router(documents_router, prefix=settings.API_V1_STR)
app.include_router(approvals_router, prefix=settings.API_V1_STR)
app.include_router(audit_router, prefix=settings.API_V1_STR)
app.include_router(agents_router, prefix=settings.API_V1_STR)
app.include_router(federation_router, prefix=settings.API_V1_STR)



@app.get("/")
async def root():
    return {
        "message": "Welcome to Federated Agentic Mesh Backend API",
        "documentation": "/docs",
        "version": "1.0.0"
    }
