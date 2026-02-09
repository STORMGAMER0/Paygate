from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import text
from datetime import datetime, timezone
from pathlib import Path
from app.database import engine, Base, SessionLocal
from app.schemas import HealthCheck
from app.auth.routes import router as auth_router
from app.payments.routes import router as payments_router
from app.admin.routes import router as admin_router

# Get frontend directory path
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="PayGate API",
    description="A production-ready payment gateway API with Paystack integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(payments_router)
app.include_router(admin_router)


# Mount static files for frontend
if FRONTEND_DIR.exists():
    app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
    app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")


@app.get("/", tags=["Frontend"])
def serve_frontend():
    """Serve the frontend application."""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Welcome to PayGate API", "docs": "/docs"}


@app.get("/dashboard.html", tags=["Frontend"])
def serve_dashboard():
    """Serve the dashboard page."""
    return FileResponse(FRONTEND_DIR / "dashboard.html")


@app.get("/admin.html", tags=["Frontend"])
def serve_admin():
    """Serve the admin page."""
    return FileResponse(FRONTEND_DIR / "admin.html")


@app.get("/index.html", tags=["Frontend"])
def serve_index():
    """Serve the index page."""
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health", response_model=HealthCheck, tags=["Health"])
def health_check():
    """Health check endpoint."""
    db_status = "connected"
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception:
        db_status = "disconnected"

    return HealthCheck(
        status="healthy" if db_status == "connected" else "unhealthy",
        database=db_status,
        timestamp=datetime.now(timezone.utc)
    )
