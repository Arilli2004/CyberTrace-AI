"""
CyberTrace AI — FastAPI Backend Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn

from app.core.config import settings
from app.core.logging import setup_logging
from app.database.connection import init_db
from app.api import auth, users, cases, evidence, parser, normalization, graph, csp, timeline, reports, ai, ucs, astar, forward_chaining

# ─── Logging ─────────────────────────────────────────────────────────────────
setup_logging()


# ─── Lifespan ────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    await init_db()
    yield


# ─── App Instance ─────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered digital forensics and evidence reconstruction platform.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)


# ─── Middleware ───────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Static Files ────────────────────────────────────────────────────────────
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# ─── Routers ─────────────────────────────────────────────────────────────────
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(cases.router, prefix="/api/cases", tags=["Cases"])
app.include_router(evidence.router, prefix="/api/evidence", tags=["Evidence"])
app.include_router(parser.router, prefix="/api/parser", tags=["Parser"])
app.include_router(normalization.router, prefix="/api", tags=["Normalization"])
app.include_router(graph.router, prefix="/api", tags=["Knowledge Graph"])
app.include_router(csp.router, prefix="/api", tags=["CSP Reasoning Engine"])
app.include_router(timeline.router, prefix="/api/timeline", tags=["Timeline"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(ai.router, prefix="/api/ai", tags=["AI"])
app.include_router(ucs.router, prefix="/api/v1/ai/ucs", tags=["Uniform Cost Search"])
app.include_router(ucs.router, prefix="/api/ai/ucs", tags=["Uniform Cost Search"])
app.include_router(astar.router, prefix="/api/v1/ai/astar", tags=["A* Search"])
app.include_router(astar.router, prefix="/api/ai/astar", tags=["A* Search"])
app.include_router(forward_chaining.router, prefix="/api/v1/ai/forward-chaining", tags=["Forward Chaining"])
app.include_router(forward_chaining.router, prefix="/api/ai/forward-chaining", tags=["Forward Chaining"])


# ─── Health Check ────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": "1.0.0",
    }


@app.get("/", tags=["Root"])
async def root():
    return {"message": f"Welcome to {settings.APP_NAME} API", "docs": "/api/docs"}


# ─── Entry Point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
