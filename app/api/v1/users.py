from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.history import History
from app.models.schemas import UserCreate, UserOut
from app.security import get_password_hash, get_current_user
from typing import List

router = APIRouter()

@router.post("/register", response_model=UserOut)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/history")
def read_history(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    history = db.query(History).filter(History.user_id == current_user.id).offset(skip).limit(limit).all()
    return history
