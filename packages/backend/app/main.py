"""
SNS Platform Backend API
Main FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 Starting SNS Backend API...")
    print(f"📊 Database URL: {settings.DATABASE_URL}")

    # Create tables (for development only, use Alembic in production)
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)

    yield

    # Shutdown
    print("👋 Shutting down SNS Backend API...")


app = FastAPI(
    title="SNS Platform API",
    description="Academic citation-based social network platform",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "SNS Platform API is running",
        "version": "0.1.0",
    }


@app.get("/api")
async def api_root():
    """API root endpoint for frontend health check"""
    return {
        "status": "ok",
        "message": "SNS Platform API is running",
        "version": "0.1.0",
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",  # TODO: Add actual DB health check
        "redis": "connected",  # TODO: Add actual Redis health check
    }


# Include routers
from app.routers import auth, users, outputs, citations, agreements, follow, outputs_verify, search, notifications

app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(outputs.router, prefix="/api/v1")
app.include_router(outputs_verify.router, prefix="/api/v1")
app.include_router(citations.router, prefix="/api/v1")
app.include_router(agreements.router, prefix="/api/v1")
app.include_router(follow.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
