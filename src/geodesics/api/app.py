"""FastAPI application for Kerr Geodesics Lab.

Stateless scientific API providing:
- Health and provenance endpoint
- Simulation preset catalogue
- Stateless simulation execution
- Analytical Kerr shadow calculation
- Structured error handling with zero stack-trace leakage
"""

from typing import Any, Dict, Union

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


def create_app() -> FastAPI:
    """Factory creating and configuring the Kerr Geodesics Lab FastAPI application."""
    app = FastAPI(
        title="Kerr Geodesics Lab API",
        description="Stateless scientific API adapter for the Kerr Geodesic Integrator v1.0.0 engine.",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Enable CORS for local Next.js frontend development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3001",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
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
