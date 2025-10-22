from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import models, schemas
from ..database import get_db

router = APIRouter(
    prefix="/bloggers",
    tags=["bloggers"]
)

@router.post("/", response_model=schemas.Blogger)
def create_blogger(
    blogger: schemas.BloggerCreate,
    db: Session = Depends(get_db)
):
    """Create a new blogger"""
    # Check if blogger with this email already exists
    db_blogger = db.query(models.Blogger).filter(models.Blogger.email == blogger.email).first()
    if db_blogger:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new blogger
    db_blogger = models.Blogger(**blogger.dict())
    db.add(db_blogger)
    db.commit()
    db.refresh(db_blogger)
    return db_blogger

@router.get("/", response_model=List[schemas.Blogger])
def get_bloggers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all bloggers"""
    bloggers = db.query(models.Blogger).offset(skip).limit(limit).all()
    return bloggers
