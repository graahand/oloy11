"""
User Model
==========

Database model for user accounts.

**RECURRING PATTERN (You'll see this in every app with users):**
- User table with id, username, email, password
- Unique constraints on username/email
- Indexed columns for fast lookups

**PROJECT-SPECIFIC:**
- Specific fields (could add: full_name, is_active, created_at, etc.)

**ALTERNATIVES:**
- Add role-based access control: role = Column(String, default="user")
- Add account status: is_active = Column(Boolean, default=True)
- Add timestamps: created_at = Column(DateTime, default=datetime.now)
- Add profile fields: avatar_url, bio, etc.
"""

from sqlalchemy import Column, Integer, String
from app.database import Base

class User(Base):
    """
    User database model.
    
    **RECURRING:** User models are in almost every web application.
    
    **SQLAlchemy ORM Basics:**
    - Inherits from Base (makes it a database table)
    - __tablename__ defines the actual table name in the database
    - Each Column represents a field in the table
    - Column types (Integer, String) map to database types
    
    **This creates a table like:**
    CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        username VARCHAR UNIQUE NOT NULL,
        email VARCHAR UNIQUE NOT NULL,
        hashed_password VARCHAR NOT NULL
    );
    
    **Usage:**
    # Create user
    user = User(username="john", email="john@example.com", hashed_password="$2b$...")
    db.add(user)
    db.commit()
    
    # Query user
    user = db.query(User).filter(User.username == "john").first()
    
    **Related files:**
    - app/api/v1/auth.py: Queries User for login
    - app/api/v1/users.py: Creates User for registration
    - app/security.py: Queries User for authentication
    """
    
    # Table name in the database
    # **RECURRING:** Every SQLAlchemy model has __tablename__
    __tablename__ = "users"
    
    # ===== COLUMNS =====
    
    # Primary key: Unique identifier for each user
    # primary_key=True: Makes this the primary key
    # index=True: Creates database index for faster lookups
    # **RECURRING:** Every table needs a primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Username: Unique, used for login
    # unique=True: No two users can have same username
    # index=True: Fast lookups when querying by username
    # **RECURRING:** Most user models have username
    username = Column(String, unique=True, index=True)
    
    # Email: Unique, for communication
    # unique=True: No two users can have same email
    # index=True: Fast lookups when querying by email
    # **RECURRING:** Most user models have email
    email = Column(String, unique=True, index=True)
    
    # Password: Stored as bcrypt hash, NEVER plain text!
    # **SECURITY CRITICAL:** Always store hashed passwords
    # **RECURRING:** Every auth system stores password hashes
    # 
    # Example hash: $2b$12$KIXxnJLvBEZaGQVPZqYTx.h9jZ8u9LjVQP3vK5xF7YwKHhEq5E8xW
    hashed_password = Column(String)
