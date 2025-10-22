# DeltaHub Backend

A FastAPI application for managing shops, products, orders, and affiliate marketing analytics.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a PostgreSQL database named 'deltahub'

4. Create a .env file with the following content:
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/deltahub
SECRET_KEY=your-secret-key-here-please-change-in-production
```

5. Run the application:
```bash
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

## API Documentation

Once the application is running, you can access:
- Interactive API documentation: http://localhost:8000/docs
- Alternative API documentation: http://localhost:8000/redoc

## Main Features

1. Shop Management
   - Shop registration and authentication
   - Product management

2. Product Management
   - Create and list products
   - View product orders and analytics

3. Order Management
   - Create orders through affiliate links
   - Update order statuses
   - Track order analytics

4. Analytics
   - Track product visits through affiliate links
   - Monitor order conversions
   - Calculate earnings per blogger

## Authentication

The API uses JWT tokens for authentication. To authenticate:

1. Register a shop using POST /shops/
2. Get a token using POST /token with your email and password
3. Use the token in the Authorization header for protected endpoints
