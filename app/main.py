"""
Main Application Module
========================

This is the entry point for the FastAPI application.

**RECURRING PATTERN (You'll see this structure in every FastAPI project):**
- FastAPI app instance creation
- CORS middleware configuration
- Router inclusion (organizing endpoints)
- Database initialization
- Main entry point

**PROJECT-SPECIFIC:**
- The specific routers included
- CORS origins
- API versioning scheme

**ALTERNATIVES:**
- Multiple FastAPI apps (microservices)
- API Gateway pattern (single entry point for multiple services)
- GraphQL instead of REST
- WebSocket support for real-time features
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.api.v1 import inference, auth, users
from app.database import engine, Base

# ===== DATABASE INITIALIZATION =====
# Create all database tables
# **RECURRING:** Database initialization at startup
#
# **How it works:**
# 1. Base.metadata contains all table definitions (User, History, etc.)
# 2. create_all() generates SQL CREATE TABLE statements
# 3. Tables are created if they don't exist (idempotent)
#
# **Note:** This is fine for development, but for production consider:
# - Alembic (database migration tool)
# - SQLAlchemy-migrate
# - Manual SQL scripts
#
# **Why migrations?**
# - Track schema changes over time
# - Rollback capability
# - Data preservation during schema changes
# - Team collaboration (version control for schema)
Base.metadata.create_all(bind=engine)

# ===== SETTINGS =====
# Get application settings (singleton)
settings = get_settings()

# ===== FASTAPI APP INSTANCE =====
# This is the main application object
# **RECURRING:** Every FastAPI project creates an app instance
#
# **Parameters:**
# - title: Shows in OpenAPI docs (Swagger UI)
# - version: API version (shows in docs)
# - openapi_url: Where OpenAPI JSON schema is served
#   Default: /openapi.json
#   Setting to None disables OpenAPI (for security in production?)
#
# **Additional useful parameters:**
# - description: Longer description in docs
# - docs_url: Custom Swagger UI URL (default: /docs)
# - redoc_url: Custom ReDoc URL (default: /redoc)
# - root_path: For reverse proxy deployments
# - dependencies: Global dependencies for all routes
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# ===== CORS MIDDLEWARE =====
# CORS (Cross-Origin Resource Sharing) allows frontend apps to call your API
# **RECURRING:** Almost every web API needs CORS configuration
#
# **What is CORS?**
# Browsers block requests from different domains for security.
# CORS headers tell browsers which domains are allowed.
#
# **Example:**
# Frontend: http://localhost:3000 (React app)
# Backend: http://localhost:8000 (FastAPI)
# Without CORS: Browser blocks requests (same-origin policy)
# With CORS: Backend sends Access-Control-Allow-Origin header → allowed
#
# **Security warning:**
# origins = ["*"] allows ALL domains (fine for dev, dangerous for production!)
#
# **Production setup:**
# origins = [
#     "https://www.yourapp.com",
#     "https://app.yourapp.com",
# ]
origins = [
    "http://localhost",        # Generic localhost
    "http://localhost:3000",   # Common React dev server
    "http://localhost:8000",   # FastAPI dev server (for testing)
    "*",                        # Allow all (DEVELOPMENT ONLY!)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,           # Which domains can access
    allow_credentials=True,          # Allow cookies/authorization headers
    allow_methods=["*"],             # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],             # Allow all headers
    # **Production alternatives:**
    # allow_methods=["GET", "POST", "PUT", "DELETE"]  # Specific methods
    # allow_headers=["Content-Type", "Authorization"]  # Specific headers
)

# ===== ROUTER INCLUSION =====
# Include routers to organize endpoints
# **RECURRING:** Every FastAPI project organizes routes with routers
#
# **How it works:**
# 1. Each module (auth, users, inference) has an APIRouter
# 2. Endpoints are defined on the router: @router.post(...)
# 3. app.include_router() adds all endpoints to the main app
# 4. prefix: URL prefix for all routes in this router
# 5. tags: Groups endpoints in OpenAPI docs
#
# **URL structure:**
# Auth router:
#   /api/v1/token → login endpoint
#
# Users router:
#   /api/v1/users/register → registration
#   /api/v1/users/history → user history
#
# Inference router:
#   /api/v1/predict/image → image inference
#   /api/v1/predict/video → video inference
#
# **Benefits:**
# - Organized codebase (separate files for different features)
# - Easier testing (test routers independently)
# - Reusable (same router in multiple apps)
# - Clear API structure (logical grouping)

# Auth endpoints: /api/v1/token
app.include_router(
    auth.router, 
    prefix=settings.API_V1_STR,  # /api/v1
    tags=["auth"]                # Shows in Swagger UI
)

# User endpoints: /api/v1/users/*
app.include_router(
    users.router, 
    prefix=f"{settings.API_V1_STR}/users",  # /api/v1/users
    tags=["users"]
)

# Inference endpoints: /api/v1/predict/*
app.include_router(
    inference.router, 
    prefix=settings.API_V1_STR,  # /api/v1
    tags=["inference"]
)

# ===== ROOT ENDPOINT =====
# Simple welcome endpoint
# **RECURRING:** Most APIs have a root endpoint for health check/info
@app.get("/")
def read_root():
    """
    Root endpoint - returns welcome message.
    
    **RECURRING:** Health check / info endpoints are common.
    
    **Usage:**
    - Quick API availability check
    - Health monitoring
    - API discovery
    
    **Improvements:**
    - Add version info
    - Add available endpoints
    - Add system status
    - Add uptime
    
    **Example enhanced response:**
    {
        "message": "Welcome to Oloy11 API",
        "version": "1.0.0",
        "status": "healthy",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "auth": "/api/v1/token"
        }
    }
    """
    return {"message": f"Welcome to {settings.PROJECT_NAME} API"}


# ===== APPLICATION RUNNER =====
def main():
    """
    Run the FastAPI application with Uvicorn server.
    
    **RECURRING:** Every FastAPI app needs a ASGI server (Uvicorn, Hypercorn).
    
    **What is Uvicorn?**
    ASGI (Async Server Gateway Interface) server for running FastAPI.
    Like Gunicorn for Flask, or Node.js for Express.
    
    **Parameters:**
    - "app.main:app": Module path to FastAPI app instance
    - host="0.0.0.0": Listen on all network interfaces
      "127.0.0.1" = localhost only
      "0.0.0.0" = accessible from network (needed for Docker, cloud)
    - port=8000: Default HTTP port for FastAPI
    - reload=True: Auto-restart on code changes (DEVELOPMENT ONLY!)
    
    **Production considerations:**
    # Remove reload, add workers
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        workers=4,              # Multiple worker processes
        loop="uvloop",          # Faster event loop
        log_level="warning"     # Less verbose logging
    )
    
    **Alternatives:**
    - Gunicorn + Uvicorn workers (more robust)
    - Hypercorn (HTTP/2 support)
    - Daphne (Django Channels)
    
    **Production deployment:**
    gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
    """
    import uvicorn
    # Run with reload=True for development (auto-restart on changes)
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


# ===== ENTRY POINT =====
# Standard Python entry point
# **RECURRING:** Every executable Python script has this
if __name__ == "__main__":
    main()
