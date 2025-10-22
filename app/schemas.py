from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from .models import OrderStatus

class ShopBase(BaseModel):
    name: str
    description: Optional[str] = None
    email: EmailStr

class ShopCreate(ShopBase):
    password: str

class Shop(ShopBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    image_url: Optional[str] = None

class ProductCreate(ProductBase):
    shop_id: int

class Product(ProductBase):
    id: int
    shop_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class BloggerBase(BaseModel):
    name: str
    email: EmailStr
    bio: Optional[str] = None

class BloggerCreate(BloggerBase):
    pass

class Blogger(BloggerBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class OrderBase(BaseModel):
    product_id: int
    blogger_id: int
    quantity: int
    price_per_item: float
    client_phone: str

class OrderCreate(OrderBase):
    pass

class Order(OrderBase):
    id: int
    status: OrderStatus
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class AnalyticsBase(BaseModel):
    product_id: int
    blogger_id: int
    visit_count: int = 0
    order_count: int = 0
    items_sold: int = 0
    money_earned: float = 0.0

class Analytics(AnalyticsBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    blogger: Optional[Blogger] = None  # Include blogger details

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    shop_id: int
    email: str
    name: str

class TokenData(BaseModel):
    email: Optional[str] = None

class AffiliateLinkBase(BaseModel):
    product_id: int
    blogger_id: int

class AffiliateLinkCreate(AffiliateLinkBase):
    pass

class AffiliateLink(AffiliateLinkBase):
    id: int
    code: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class AffiliateLinkDetail(AffiliateLink):
    product: Product
    blogger: Blogger

    class Config:
        from_attributes = True