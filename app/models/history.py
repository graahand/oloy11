"""
History Model
=============

Database model for tracking user actions (inference history).

**PROJECT-SPECIFIC (You won't see this exact model in other projects):**
- This is specific to ML inference tracking
- Fields are tailored to YOLO object detection

**RECURRING CONCEPTS:**
- Audit/history tables for tracking user actions
- Foreign keys to link to user table
- Timestamps for when actions occurred
- JSON columns for flexible data storage

**ALTERNATIVES:**
- Separate tables for different action types
- NoSQL database for more flexible schema (MongoDB)
- Event sourcing pattern (store all events, derive state)
- External logging service (ELK stack, CloudWatch)
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class History(Base):
    """
    History database model for tracking user inference actions.
    
    **PROJECT-SPECIFIC:** This model is specific to ML inference tracking.
    
    **RECURRING CONCEPTS:**
    - Audit tables are common for compliance/debugging
    - Foreign keys link records to users
    - Timestamps track when events occurred
    
    **This creates a table like:**
    CREATE TABLE history (
        id INTEGER PRIMARY KEY,
        user_id INTEGER REFERENCES users(id),
        action_type VARCHAR,
        resource_path VARCHAR,
        timestamp DATETIME,
        result_summary JSON
    );
    
    **Usage:**
    # Log inference
    history = History(
        user_id=user.id,
        action_type="image_inference",
        resource_path="/uploads/image.jpg",
        result_summary={"detections": 5}
    )
    db.add(history)
    db.commit()
    
    # Query history
    history = db.query(History).filter(History.user_id == user.id).all()
    
    **Related files:**
    - app/api/v1/users.py: read_history() - queries this table
    - app/api/v1/inference.py: predict_image(), predict_video() - creates records
    """
    
    # Table name in the database
    __tablename__ = "history"
    
    # ===== COLUMNS =====
    
    # Primary key: Unique identifier for each history record
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key: Links to the User who performed the action
    # ForeignKey("users.id"): References the id column in users table
    # **RECURRING:** Foreign keys are used everywhere to link tables
    # 
    # **How it works:**
    # - Ensures referential integrity (can't reference non-existent user)
    # - Allows joins: SELECT * FROM history JOIN users ON history.user_id = users.id
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Action type: What kind of action was performed
    # Examples: "image_inference", "video_inference"
    # **PROJECT-SPECIFIC:** These values depend on your application
    # 
    # **Alternative:** Use enum for validation
    # from enum import Enum
    # class ActionType(str, Enum):
    #     IMAGE = "image_inference"
    #     VIDEO = "video_inference"
    action_type = Column(String)
    
    # Resource path: Where the uploaded file is stored
    # Example: "/uploads/abc123.jpg"
    # **PROJECT-SPECIFIC:** For file upload tracking
    # 
    # **Note:** In production, consider:
    # - Storing relative paths only (more portable)
    # - Using cloud storage URLs (S3, Azure Blob)
    # - Implementing file cleanup (delete old files)
    resource_path = Column(String)
    
    # Timestamp: When the action occurred
    # default=datetime.now: Automatically set to current time when record created
    # **RECURRING:** Timestamps are common in audit tables
    # 
    # **Note:** For timezone awareness, use:
    # from datetime import datetime, timezone
    # default=lambda: datetime.now(timezone.utc)
    timestamp = Column(DateTime, default=datetime.now)
    
    # Result summary: JSON data with inference results
    # **FLEXIBLE:** JSON columns store arbitrary structured data
    # Example: {"detections": 5, "confidence": 0.95}
    # 
    # **RECURRING:** JSON columns are increasingly common for flexible schemas
    # 
    # **Pros:**
    # - Flexible schema (add fields without migrations)
    # - Store complex nested data
    # 
    # **Cons:**
    # - Can't efficiently query nested data
    # - No schema validation at database level
    # - Takes more space than normalized tables
    # 
    # **Alternatives:**
    # - Separate tables for structured data
    # - PostgreSQL JSONB (queryable JSON)
    # - NoSQL database (MongoDB, DynamoDB)
    result_summary = Column(JSON)
    
    # ===== RELATIONSHIPS =====
    # SQLAlchemy relationship: Allows easy access to related User object
    # **RECURRING:** Relationships make ORM queries more intuitive
    # 
    # **Usage:**
    # history_record = db.query(History).first()
    # username = history_record.user.username  # Automatically loads User
    # 
    # **How it works:**
    # - SQLAlchemy automatically performs JOIN when accessing .user
    # - Can configure lazy loading vs eager loading
    # 
    # **Alternatives:**
    # - back_populates: Two-way relationship (add to User model too)
    #   user = relationship("User", back_populates="history")
    # - lazy loading options: lazy="joined", lazy="subquery", etc.
    user = relationship("User")
