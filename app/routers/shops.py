from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(
    prefix="/shops",
    tags=["shops"]
)

@router.post("/", response_model=schemas.Shop)
def create_shop(shop: schemas.ShopCreate, db: Session = Depends(get_db)):
    db_shop = db.query(models.Shop).filter(models.Shop.email == shop.email).first()
    if db_shop:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = auth.get_password_hash(shop.password)
    db_shop = models.Shop(
        email=shop.email,
        name=shop.name,
        description=shop.description,
        hashed_password=hashed_password
    )
    db.add(db_shop)
    db.commit()
    db.refresh(db_shop)
    return db_shop

@router.get("/{shop_id}", response_model=schemas.Shop)
def get_shop(
    shop_id: int,
    current_shop: models.Shop = Depends(auth.get_current_shop),
    db: Session = Depends(get_db)
):
    # Check if the user is trying to access their own shop
    if current_shop.id != shop_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this shop"
        )
    return current_shop

@router.get("/me/{shop_id}", response_model=schemas.Shop)
def read_shop_me(
    shop_id: int,
    current_shop: models.Shop = Depends(auth.get_current_shop),
    db: Session = Depends(get_db)
):
    """
    Get shop details by ID.
    The token should be passed in the Authorization header as: Bearer <token>
    """
    # Verify that the requested shop_id matches the authenticated shop
    if current_shop.id != shop_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this shop"
        )
    
    # Get fresh data from database
    db_shop = db.query(models.Shop).filter(models.Shop.id == shop_id).first()
    if not db_shop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shop not found"
        )
    return db_shop

@router.get("/{shop_id}/analytics", response_model=List[schemas.Analytics])
def get_shop_analytics(
    shop_id: int,
    current_shop: models.Shop = Depends(auth.get_current_shop),
    db: Session = Depends(get_db)
):
    """Get all analytics for a shop"""
    # Check if the user is trying to access their own shop
    if current_shop.id != shop_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this shop's analytics"
        )
    
    # Get all products for this shop
    products = db.query(models.Product).filter(models.Product.shop_id == shop_id).all()
    product_ids = [p.id for p in products]
    
    # Get analytics for all products
    analytics = db.query(models.Analytics)\
        .filter(models.Analytics.product_id.in_(product_ids))\
        .all()
    
    return analytics
