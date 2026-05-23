from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.responses import error_response
from backend.api.routes import auth, rankings, reports, stocks, strategies, tasks, watchlist


def create_app() -> FastAPI:
    app = FastAPI(
        title="MM2 AI Quant Stock Selection API",
        version="0.1.0",
        description="First-stage local FastAPI backend with mock data.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health_check() -> dict:
        return {
            "status": "ok",
            "service": "mm2-backend",
            "mock": True,
        }

    @app.exception_handler(HTTPException)
    async def handle_http_exception(_, exc: HTTPException) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, dict) else {}
        code = detail.get("code", "COMMON_BAD_REQUEST")
        message = detail.get("message", str(exc.detail))
        details = detail.get("details", {})
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(code=code, message=message, details=details),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_exception(_, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content=error_response(
                code="COMMON_BAD_REQUEST",
                message="请求参数不合法",
                details={"errors": exc.errors()},
            ),
        )

    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(strategies.router, prefix="/api", tags=["strategies"])
    app.include_router(rankings.router, prefix="/api", tags=["rankings"])
    app.include_router(stocks.router, prefix="/api", tags=["stocks"])
    app.include_router(watchlist.router, prefix="/api", tags=["watchlist"])
    app.include_router(reports.router, prefix="/api", tags=["reports"])
    app.include_router(tasks.router, prefix="/api", tags=["tasks"])

    return app


app = create_app()
