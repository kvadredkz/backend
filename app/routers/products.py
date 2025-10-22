from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(
    prefix="/products",
    tags=["products"]
)

@router.get("/", response_model=List[schemas.Product])
def get_products(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_shop: models.Shop = Depends(auth.get_current_shop)
):
    """Get all products for the current shop"""
    products = db.query(models.Product)\
        .filter(models.Product.shop_id == current_shop.id)\
        .offset(skip)\
        .limit(limit)\
        .all()
    return products

@router.get("/{product_id}", response_model=schemas.Product)
def get_product(
    product_id: int,
    blogger_id: int | None = None,
    db: Session = Depends(get_db)
):
    """
    Get a single product by ID.
    If blogger_id is provided, it will record the visit in analytics.
    """
    product = db.query(models.Product)\
        .filter(models.Product.id == product_id)\
        .first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # Record visit in analytics if blogger_id is provided
    if blogger_id:
        analytics = db.query(models.Analytics)\
            .filter(
                models.Analytics.product_id == product_id,
                models.Analytics.blogger_id == blogger_id
            ).first()
        
        if analytics:
            analytics.visit_count += 1
        else:
            analytics = models.Analytics(
                product_id=product_id,
                blogger_id=blogger_id,
                visit_count=1
            )
            db.add(analytics)
        
        db.commit()

    return product

@router.get("/{product_id}/analytics", response_model=List[schemas.Analytics])
def get_product_analytics(
    product_id: int,
    db: Session = Depends(get_db),
    current_shop: models.Shop = Depends(auth.get_current_shop)
):
    """Get analytics for a product with blogger details"""
    # Check if the product belongs to the current shop
    product = db.query(models.Product)\
        .filter(
            models.Product.id == product_id,
            models.Product.shop_id == current_shop.id
        ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Query analytics with joined blogger details
    analytics = db.query(models.Analytics)\
        .join(models.Blogger)\
        .filter(models.Analytics.product_id == product_id)\
        .all()
    
    return analytics

@router.post("/", response_model=schemas.Product)
def create_product(
    product: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_shop: models.Shop = Depends(auth.get_current_shop)
):
    """Create a new product"""
    if product.shop_id != current_shop.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create product for this shop"
        )
    
    db_product = models.Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product