from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class History(Base):
    __tablename__ = "history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action_type = Column(String)
    resource_path = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    result_summary = Column(JSON)
    
    user = relationship("User")
