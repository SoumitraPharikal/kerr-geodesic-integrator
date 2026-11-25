"""FastAPI application for Kerr Geodesics Lab.

Stateless scientific API providing:
- Health and provenance endpoint
- Simulation preset catalogue
- Stateless simulation execution
- Analytical Kerr shadow calculation
- Structured error handling with zero stack-trace leakage
"""

import os
from typing import Any, Dict, List, Optional, Union

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from geodesics.api.schemas import (
    ErrorResponse,
    HealthResponse,
    PresetCatalogueResponse,
    ShadowRequest,
    ShadowResponse,
    SimulationRequest,
    SimulationResponse,
)
from geodesics.api.service import (
    PRESET_METADATA_CATALOGUE,
    run_shadow,
    run_simulation,
)


def _format_validation_response(exc: Union[RequestValidationError, ValidationError]) -> JSONResponse:
    """Helper to classify and format Pydantic and FastAPI validation errors."""
    sanitized_errors = []
    has_physical_value_error = False
    physical_messages = []

    for err in exc.errors():
        loc = err.get("loc", ())
        msg = err.get("msg", "")
        type_ = err.get("type", "")
        clean_msg = msg.replace("Value error, ", "")
        sanitized_errors.append({"loc": list(loc), "message": clean_msg, "type": type_})

        if type_ == "value_error":
            has_physical_value_error = True
            physical_messages.append(clean_msg)

    if has_physical_value_error:
        error_type = "unphysical_configuration"
        message = "; ".join(physical_messages) if physical_messages else "Unphysical configuration parameters."
    else:
        error_type = "invalid_request_parameters"
        message = "Request parameter validation failed."

    error_content = ErrorResponse(
        error_type=error_type,
        message=message,
        details=sanitized_errors,
    ).model_dump()
    return JSONResponse(
        status_code=422,
        content=error_content,
    )


DEFAULT_DEV_ORIGINS: List[str] = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]


def parse_cors_origins(
    raw: Optional[str] = None,
    environment: Optional[str] = None,
) -> List[str]:
    """Parse comma-separated CORS allowed origins from environment.

    Requirements:
    - Trims whitespace and discards empty entries.
    - Strictly rejects wildcard '*' to prevent insecure deployment configuration.
    - In production mode (ENVIRONMENT='production' or APP_ENV='production'):
      requires an explicit, nonempty CORS_ALLOWED_ORIGINS. Fails closed with RuntimeError
      if absent, empty, or whitespace-only.
    - In development mode: falls back to DEFAULT_DEV_ORIGINS when unset or empty.
    """
    if environment is None:
        environment = os.getenv("ENVIRONMENT", os.getenv("APP_ENV", "development"))

    is_production = environment.strip().lower() in ("production", "prod")

    if raw is None:
        raw = os.getenv("CORS_ALLOWED_ORIGINS")

    if raw is None or not raw.strip():
        if is_production:
            raise RuntimeError(
                "In production mode (ENVIRONMENT='production'), CORS_ALLOWED_ORIGINS must be set "
                "to an explicit, non-empty list of origins. Startup aborted to prevent insecure open access."
            )
        return list(DEFAULT_DEV_ORIGINS)

    tokens = [item.strip() for item in raw.split(",") if item.strip()]

    if any(t == "*" for t in tokens):
        raise ValueError(
            "Wildcard CORS origin '*' is strictly prohibited for Kerr Geodesics Lab deployments."
        )

    if not tokens:
        if is_production:
            raise RuntimeError(
                "In production mode (ENVIRONMENT='production'), CORS_ALLOWED_ORIGINS must be set "
                "to an explicit, non-empty list of origins (received empty or whitespace-only value). "
                "Startup aborted to prevent insecure open access."
            )
        return list(DEFAULT_DEV_ORIGINS)

    return tokens


def create_app(
    cors_origins: Optional[List[str]] = None,
    environment: Optional[str] = None,
) -> FastAPI:
    """Factory creating and configuring the Kerr Geodesics Lab FastAPI application."""
    app = FastAPI(
        title="Kerr Geodesics Lab API",
        description="Stateless scientific API adapter for the Kerr Geodesic Integrator v1.0.0 engine.",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Configure CORS origins: fail-closed in production, dev defaults in development
    if cors_origins is not None:
        allowed_origins = cors_origins
    else:
        allowed_origins = parse_cors_origins(environment=environment)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Accept", "Authorization"],
    )

    # -------------------------------------------------------------------------
    # Exception Handlers
    # -------------------------------------------------------------------------

    @app.exception_handler(RequestValidationError)
    def handle_request_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return _format_validation_response(exc)

    @app.exception_handler(ValidationError)
    def handle_pydantic_validation_error(
        request: Request, exc: ValidationError
    ) -> JSONResponse:
        return _format_validation_response(exc)

    @app.exception_handler(KeyError)
    def handle_key_error(request: Request, exc: KeyError) -> JSONResponse:
        clean_msg = str(exc).strip("'\"")
        error_content = ErrorResponse(
            error_type="unsupported_preset",
            message=clean_msg,
        ).model_dump()
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error_content,
        )

    @app.exception_handler(ValueError)
    def handle_value_error(request: Request, exc: ValueError) -> JSONResponse:
        error_content = ErrorResponse(
            error_type="unphysical_configuration",
            message=str(exc),
        ).model_dump()
        return JSONResponse(
            status_code=422,
            content=error_content,
        )

    @app.exception_handler(RuntimeError)
    def handle_runtime_error(request: Request, exc: RuntimeError) -> JSONResponse:
        error_content = ErrorResponse(
            error_type="numerical_integration_failure",
            message=str(exc),
        ).model_dump()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_content,
        )

    @app.exception_handler(Exception)
    def handle_generic_error(request: Request, exc: Exception) -> JSONResponse:
        # Never expose raw stack traces or internal filesystem paths to client
        error_content = ErrorResponse(
            error_type="internal_error",
            message="An unexpected internal server error occurred.",
        ).model_dump()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_content,
        )

    # -------------------------------------------------------------------------
    # Route Handlers (Synchronous def for AnyIO worker pool dispatch)
    # -------------------------------------------------------------------------

    @app.get(
        "/health",
        response_model=HealthResponse,
        summary="Service Health and Engine Version",
        tags=["System"],
    )
    def get_health() -> HealthResponse:
        return HealthResponse()

    @app.get(
        "/api/v1/presets",
        response_model=PresetCatalogueResponse,
        summary="Simulation Preset Catalogue",
        tags=["Presets"],
    )
    def get_presets() -> PresetCatalogueResponse:
        return PresetCatalogueResponse(presets=PRESET_METADATA_CATALOGUE)

    @app.post(
        "/api/v1/simulations",
        response_model=SimulationResponse,
        summary="Execute Stateless Geodesic Simulation",
        tags=["Simulations"],
    )
    def post_simulation(request: SimulationRequest) -> SimulationResponse:
        return run_simulation(request)

    @app.post(
        "/api/v1/shadows",
        response_model=ShadowResponse,
        summary="Construct Analytical Kerr Shadow Boundary",
        tags=["Shadows"],
    )
    def post_shadow(request: ShadowRequest) -> ShadowResponse:
        return run_shadow(request)

    return app


app = create_app()
