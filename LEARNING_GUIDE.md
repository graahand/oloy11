# FastAPI Learning Guide
## Understanding What Recurs vs What's Project-Specific

This document helps you understand which patterns you'll see in **EVERY** FastAPI project vs what's specific to this YOLO inference API.

---

##  RECURRING PATTERNS (You'll see these EVERYWHERE)

### 1. **Configuration Management** (`app/config.py`)
**Will recur:**
- Settings class with environment variables
- `@lru_cache()` for singleton settings
- `get_settings()` dependency injection pattern

**May vary:**
- Specific settings names and values
- Whether using pydantic.BaseSettings or plain class

---

### 2. **Database Setup** (`app/database.py`)
**Will recur:**
- `create_engine`, `declarative_base`, `sessionmaker`
- `get_db()` generator function for dependency injection
- Try/finally pattern for session cleanup

**May vary:**
- Database type (SQLite, PostgreSQL, MySQL)
- Connection arguments (check_same_thread is SQLite-specific)
- Whether using async SQLAlchemy

---

### 3. **Security & Authentication** (`app/security.py`)
**Will recur:**
- Password hashing with passlib or similar
- JWT token creation and validation
- `get_current_user` dependency for protected routes
- OAuth2PasswordBearer for token extraction

**May vary:**
- Hash algorithm (bcrypt, argon2, scrypt)
- Token expiration times
- Whether using refresh tokens
- OAuth2 vs API keys vs sessions

---

### 4. **Database Models** (`app/models/user.py`, `app/models/history.py`)
**Will recur:**
- SQLAlchemy ORM models inheriting from Base
- Primary keys, foreign keys, indexes
- User model with username/email/password
- Timestamp columns for tracking

**May vary:**
- Specific fields and relationships
- History/audit table structure (project-specific)
- Whether using Alembic migrations

---

### 5. **Pydantic Schemas** (`app/models/schemas.py`)
**Will recur:**
- Separate schemas for create vs read operations
- BaseModel with validators
- `Config` class with `from_attributes=True`
- Token schema for authentication

**May vary:**
- Specific fields and validation rules
- Response model structures

---

### 6. **Authentication Routes** (`app/api/v1/auth.py`)
**Will recur:**
- `/token` endpoint for login
- `OAuth2PasswordRequestForm` for username/password
- Returning JWT token in standard format
- 401 errors for invalid credentials

**May vary:**
- Additional auth methods (2FA, OAuth providers)
- Password reset endpoints
- Email verification

---

### 7. **User Management Routes** (`app/api/v1/users.py`)
**Will recur:**
- User registration endpoint
- Protected endpoints using `Depends(get_current_user)`
- Checking if username exists before registration
- Password hashing before storage

**May vary:**
- Additional user endpoints (profile, update, delete)
- Email verification flow
- Admin-specific endpoints

---

### 8. **Main Application** (`app/main.py`)
**Will recur:**
- FastAPI app instance creation
- CORS middleware configuration
- Router inclusion with prefixes and tags
- Database table creation at startup
- Root endpoint for health check

**May vary:**
- Specific routers and routes
- Middleware configuration
- Additional startup/shutdown events

---

### 9. **API Organization**
**Will recur:**
- Separating routes into modules (auth, users, etc.)
- Using APIRouter for grouping
- Dependency injection pattern
- Response models and error handling

**May vary:**
- Number and names of route modules
- API versioning strategy

---

##  PROJECT-SPECIFIC PATTERNS (Specific to this ML API)

### 1. **Model Management** (`app/utils.py`)
**Specific to ML projects:**
- Singleton pattern for model loading
- YOLO-specific inference code
- Image preprocessing pipeline

**Similar in other ML APIs:**
- Model loading at startup (singleton)
- Preprocessing functions
- Prediction wrapper functions

---

### 2. **Inference Endpoints** (`app/api/v1/inference.py`)
**Specific to this project:**
- YOLO parameters (conf, iou, max_det)
- Image and video processing
- Frame-by-frame video inference
- Result format specific to YOLO

**Similar in other ML APIs:**
- File upload handling
- URL-based input
- Optional authentication
- Result logging

---

### 3. **History Tracking** (`app/models/history.py`)
**Specific to this project:**
- Tracking inference actions
- Storing YOLO results in JSON

**Similar concepts elsewhere:**
- Audit tables
- Action logging
- User activity tracking

---

## Key Concepts to Master

### Dependency Injection
```python
# This pattern is EVERYWHERE in FastAPI
def endpoint(
    db: Session = Depends(get_db),           # Database session
    current_user: User = Depends(get_current_user),  # Authentication
    settings: Settings = Depends(get_settings)       # Configuration
):
    pass
```

### Async vs Sync
- FastAPI supports both
- Use `async def` for I/O-bound operations (API calls, file I/O)
- Use `def` for CPU-bound operations (computation, ML inference)
- Database operations can be either (depends on driver)

### Error Handling
```python
# Standard pattern
raise HTTPException(
    status_code=400,
    detail="Error message",
    headers={"optional": "header"}
)
```

### Response Models
```python
# Validates output and generates docs
@router.post("/endpoint", response_model=UserOut)
def endpoint():
    return user  # FastAPI validates against UserOut
```

---

##  What You Should Practice

1. **Setting up new FastAPI projects** - Configuration, database, auth
2. **Creating CRUD endpoints** - Create, Read, Update, Delete
3. **Implementing authentication** - JWT, OAuth2, protected routes
4. **Working with databases** - SQLAlchemy models, queries, migrations
5. **File uploads** - Handling images, videos, documents
6. **Background tasks** - For long-running operations
7. **Testing** - pytest, TestClient, mocking
8. **Deployment** - Docker, environment variables, production setup

---

## Recommended Next Steps

1. **Modify this project:**
   - Add password reset functionality
   - Add email verification
   - Add user profile updates
   - Add pagination to history endpoint
   - Add filtering and sorting

2. **Build similar projects:**
   - Blog API (posts, comments, likes)
   - E-commerce API (products, cart, orders)
   - Task management API (projects, tasks, assignments)
   - Chat API (rooms, messages, users)

3. **Learn advanced topics:**
   - Alembic database migrations
   - Background tasks with Celery
   - WebSocket for real-time features
   - GraphQL with Strawberry
   - Testing with pytest
   - Docker deployment

---

##  Resources

- **Official FastAPI Docs:** https://fastapi.tiangolo.com/
- **SQLAlchemy Docs:** https://docs.sqlalchemy.org/
- **Pydantic Docs:** https://docs.pydantic.dev/
- **JWT.io:** https://jwt.io/ (understand JWTs)
- **OAuth2 Spec:** https://oauth.net/2/

---

**Remember:** The patterns in config.py, database.py, security.py, and main.py will appear in almost EVERY FastAPI project you work on. Master these, and you can quickly understand and build any FastAPI application!
