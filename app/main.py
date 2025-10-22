from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List
from . import models, schemas, auth
from .database import engine, get_db
from sqlalchemy import and_, func
from .routers import shops, products, affiliate_links, bloggers

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="DeltaHub API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://deltahub-frontend.onrender.com",
        "http://localhost:3000",  # For local development
        "http://localhost:5173"   # For local Vite development
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Access-Control-Allow-Headers",
        "Access-Control-Allow-Origin",
        "Access-Control-Allow-Methods"
    ],
    expose_headers=["*"],
    max_age=3600  # Cache preflight requests for 1 hour
)


# Include routers
app.include_router(shops.router)
app.include_router(products.router)
app.include_router(affiliate_links.router)
app.include_router(bloggers.router)

# Authentication endpoints
@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    shop = auth.authenticate_shop(db, form_data.username, form_data.password)
    if not shop:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": shop.email, "shop_id": shop.id},
        expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "shop_id": shop.id,
        "email": shop.email,
        "name": shop.name
    }

# Product endpoints
@app.post("/products/", response_model=schemas.Product)
def create_product(
    product: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_shop: models.Shop = Depends(auth.get_current_shop)
):
    if product.shop_id != current_shop.id:
        raise HTTPException(status_code=403, detail="Not authorized to create product for this shop")
    db_product = models.Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.get("/products/", response_model=List[schemas.Product])
def get_products(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_shop: models.Shop = Depends(auth.get_current_shop)
):
    products = db.query(models.Product)\
        .filter(models.Product.shop_id == current_shop.id)\
        .offset(skip)\
        .limit(limit)\
        .all()
    return products

# Order endpoints
@app.post("/orders/", response_model=schemas.Order)
def create_order(order: schemas.OrderCreate, db: Session = Depends(get_db)):
    db_order = models.Order(**order.dict())
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

@app.get("/products/{product_id}/orders/", response_model=List[schemas.Order])
def get_product_orders(
    product_id: int,
    db: Session = Depends(get_db),
    current_shop: models.Shop = Depends(auth.get_current_shop)
):
    product = db.query(models.Product)\
        .filter(and_(models.Product.id == product_id, models.Product.shop_id == current_shop.id))\
        .first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return db.query(models.Order).filter(models.Order.product_id == product_id).all()

@app.put("/orders/{order_id}/status")
def update_order_status(
    order_id: int,
    status: models.OrderStatus,
    db: Session = Depends(get_db),
    current_shop: models.Shop = Depends(auth.get_current_shop)
):
    order = db.query(models.Order)\
        .join(models.Product)\
        .filter(
            and_(
                models.Order.id == order_id,
                models.Product.shop_id == current_shop.id
            )
        ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order.status = status
    
    if status == models.OrderStatus.PROCESSED:
        # Update analytics
        analytics = db.query(models.Analytics)\
            .filter(
                and_(
                    models.Analytics.product_id == order.product_id,
                    models.Analytics.blogger_id == order.blogger_id
                )
            ).first()
        
        if analytics:
            analytics.order_count += 1
            analytics.items_sold += order.quantity
            analytics.money_earned += (order.quantity * order.price_per_item)
    
    db.commit()
    return {"status": "success"}

# Analytics endpoints
@app.post("/analytics/visit")
def record_visit(
    product_id: int,
    blogger_id: int,
    db: Session = Depends(get_db)
):
    analytics = db.query(models.Analytics)\
        .filter(
            and_(
                models.Analytics.product_id == product_id,
                models.Analytics.blogger_id == blogger_id
            )
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
    return {"status": "success"}

@app.get("/products/{product_id}/analytics", response_model=List[schemas.Analytics])
def get_product_analytics(
    product_id: int,
    db: Session = Depends(get_db),
    current_shop: models.Shop = Depends(auth.get_current_shop)
):
    product = db.query(models.Product)\
        .filter(and_(models.Product.id == product_id, models.Product.shop_id == current_shop.id))\
        .first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return db.query(models.Analytics)\
        .filter(models.Analytics.product_id == product_id)\
        .all()
