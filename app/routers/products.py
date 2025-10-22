from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import shutil
import os
from pathlib import Path
import mimetypes

from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(
    prefix="/products",
    tags=["products"]
)

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads/products")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

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

@router.post("/upload-image")
async def upload_product_image(
    image: UploadFile = File(...),
    current_shop: models.Shop = Depends(auth.get_current_shop)
):
    """Upload a product image"""
    # Validate file type
    if not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    # Create unique filename using shop ID and original filename
    filename = f"{current_shop.id}_{image.filename}"
    file_path = UPLOAD_DIR / filename
    
    # Save the file
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not upload image: {str(e)}"
        )
    
    # Return the URL path to the image
    return {"image_url": f"/products/images/{filename}"}

@router.get("/images/{filename}")
async def get_product_image(filename: str):
    """Get a product image by filename"""
    file_path = UPLOAD_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    # Determine content type
    content_type, _ = mimetypes.guess_type(filename)
    if not content_type:
        content_type = "application/octet-stream"
    
    return FileResponse(
        path=file_path,
        media_type=content_type,
        filename=filename
    )

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