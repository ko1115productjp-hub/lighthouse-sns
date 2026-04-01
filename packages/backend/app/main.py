"""
Lighthouse Backend API
Main FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, Base


async def run_migrations():
    """Run pending database migrations on startup."""
    from sqlalchemy import text

    async with engine.begin() as conn:
        # Add tags column if it doesn't exist
        await conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'outputs' AND column_name = 'tags'
                ) THEN
                    ALTER TABLE outputs ADD COLUMN tags VARCHAR(30)[] NOT NULL DEFAULT '{}';
                END IF;
            END $$;
        """))
        print("✅ Database migrations checked")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 Starting Lighthouse Backend API...")
    print(f"📊 Database URL: {settings.DATABASE_URL}")

    # Run pending migrations
    try:
        await run_migrations()
    except Exception as e:
        print(f"⚠️ Migration error (non-fatal): {e}")

    yield

    # Shutdown
    print("👋 Shutting down Lighthouse Backend API...")


app = FastAPI(
    title="Lighthouse API",
    description="Knowledge Archive for Humanity - Academic citation-based platform",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
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


@app.get("/api/v1/health")
async def api_v1_health_check():
    """API v1 health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected",  # TODO: Add actual DB health check
        "redis": "connected",  # TODO: Add actual Redis health check
    }


# Include routers
from app.routers import auth, users, outputs, citations, agreements, follow, outputs_verify, search, notifications, places

app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(outputs.router, prefix="/api/v1")
app.include_router(outputs_verify.router, prefix="/api/v1")
app.include_router(citations.router, prefix="/api/v1")
app.include_router(agreements.router, prefix="/api/v1")
app.include_router(follow.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(places.router, prefix="/api/v1")
