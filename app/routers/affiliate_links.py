from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import secrets

from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(
    prefix="/affiliate-links",
    tags=["affiliate-links"]
)

def generate_unique_code(db: Session) -> str:
    """Generate a unique code for affiliate links"""
    while True:
        code = secrets.token_urlsafe(8)  # Generate an 8-character unique code
        exists = db.query(models.AffiliateLink).filter(models.AffiliateLink.code == code).first()
        if not exists:
            return code

@router.post("/", response_model=schemas.AffiliateLink)
def create_affiliate_link(
    link: schemas.AffiliateLinkCreate,
    db: Session = Depends(get_db),
    current_shop: models.Shop = Depends(auth.get_current_shop)
):
    """Create a new affiliate link"""
    # Check if product exists and belongs to the current shop
    product = db.query(models.Product)\
        .filter(
            models.Product.id == link.product_id,
            models.Product.shop_id == current_shop.id
        ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or does not belong to your shop"
        )
    
    # Check if blogger exists
    blogger = db.query(models.Blogger).filter(models.Blogger.id == link.blogger_id).first()
    if not blogger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blogger not found"
        )
    
    # Check if affiliate link already exists for this product and blogger
    existing_link = db.query(models.AffiliateLink)\
        .filter(
            models.AffiliateLink.product_id == link.product_id,
            models.AffiliateLink.blogger_id == link.blogger_id
        ).first()
    
    if existing_link:
        return existing_link
    
    # Generate unique code
    code = generate_unique_code(db)
    
    # Create affiliate link
    db_link = models.AffiliateLink(
        code=code,
        product_id=link.product_id,
        blogger_id=link.blogger_id
    )
    db.add(db_link)
    db.commit()
    db.refresh(db_link)
    return db_link

@router.get("/{code}", response_model=schemas.AffiliateLinkDetail)
def get_affiliate_link(code: str, db: Session = Depends(get_db)):
    """Get affiliate link details by code"""
    # Get affiliate link with related product and blogger details
    link = db.query(models.AffiliateLink)\
        .filter(models.AffiliateLink.code == code)\
        .first()
    
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Affiliate link not found"
        )
    
    return link