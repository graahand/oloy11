"""
Database Configuration Module
==============================

This module sets up SQLAlchemy ORM (Object-Relational Mapping) for database access.

**RECURRING PATTERN (Almost every FastAPI + Database project):**
- create_engine, declarative_base, sessionmaker setup
- get_db() generator function for dependency injection
- Database session management with try/finally for proper cleanup

**PROJECT-SPECIFIC:**
- The specific DATABASE_URL and database type (SQLite, PostgreSQL, etc.)

**KEY CONCEPTS:**
1. ORM: Maps Python classes to database tables (User class → users table)
2. Session: Manages database transactions and queries
3. Engine: Connects to the database
4. Base: Parent class for all database models

**ALTERNATIVES:**
1. SQLModel - Combines Pydantic + SQLAlchemy (modern, recommended for new projects)
2. Tortoise ORM - Async-native ORM
3. Databases + SQLAlchemy Core - Lower-level, more control
4. Raw SQL with asyncpg/psycopg2 - Most control, most work
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import get_settings

# Get application settings (singleton pattern)
settings = get_settings()

# ===== DATABASE ENGINE =====
# The engine is the connection pool to the database.
# It manages database connections efficiently (opens/closes as needed).
#
# **RECURRING:** Every SQLAlchemy app creates an engine.
#
# **Parameters explained:**
# - settings.DATABASE_URL: Connection string (e.g., "sqlite:///./oloy11.db")
# - connect_args: Database-specific connection arguments
#   {"check_same_thread": False} is ONLY for SQLite!
#   
# **Why check_same_thread=False for SQLite?**
# SQLite by default only allows access from the thread that created it.
# FastAPI uses multiple threads, so we disable this check.
# 
# **Production note:** PostgreSQL/MySQL don't need this, they're thread-safe by default.
engine = create_engine(
    settings.DATABASE_URL, connect_args={"check_same_thread": False}
)

# ===== SESSION FACTORY =====
# SessionLocal is a factory that creates database sessions.
# Think of a session as a "workspace" for database operations.
#
# **RECURRING:** Standard SQLAlchemy pattern.
#
# **Parameters explained:**
# - autocommit=False: You must explicitly call db.commit() to save changes
#   Why? Gives you control over transactions (all-or-nothing operations)
#   Alternative: autocommit=True (auto-saves, but loses transaction control)
#
# - autoflush=False: Changes aren't automatically sent to DB before queries
#   Why? Performance and control over when database operations happen
#   Alternative: autoflush=True (auto-syncs, more intuitive but slower)
#
# - bind=engine: This session factory uses our database engine
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ===== DECLARATIVE BASE =====
# Base is the parent class for all database models (User, History, etc.).
# When you create a model class inheriting from Base:
#   class User(Base): ...
# SQLAlchemy knows it's a database table.
#
# **RECURRING:** Every SQLAlchemy ORM project has this.
#
# **Alternative (newer):**
# from sqlalchemy.orm import DeclarativeBase
# class Base(DeclarativeBase): pass
Base = declarative_base()


def get_db():
    """
    Database session dependency for FastAPI.
    
    **CRITICAL PATTERN - You'll see this in every FastAPI + DB project!**
    
    This is a generator function (note the 'yield' keyword) used for:
    1. Creating a database session for each request
    2. Ensuring the session is properly closed after the request
    3. Dependency injection in FastAPI routes
    
    **How it works:**
    1. Request comes in → get_db() is called
    2. Creates a new session (db = SessionLocal())
    3. 'yield db' provides the session to the route function
    4. Route function uses db to query/modify database
    5. After route finishes, 'finally' block runs → db.close()
    6. Session is closed, connection returned to pool
    
    **Why this pattern?**
    - Automatic cleanup: No risk of leaving connections open
    - Isolation: Each request gets its own session
    - Thread-safe: Sessions don't leak between concurrent requests
    
    **Usage in routes:**
    @router.post("/users")
    def create_user(db: Session = Depends(get_db)):
        # 'db' is automatically injected by FastAPI
        user = User(username="john")
        db.add(user)
        db.commit()
        return user
    
    **RECURRING:** This exact pattern appears in every FastAPI + SQLAlchemy tutorial.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()  # Create new session
    try:
        yield db  # Provide session to the route
    finally:
        db.close()  # Always close the session, even if error occurs
