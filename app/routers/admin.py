from fastapi import APIRouter, HTTPException, status
from alembic import command
from alembic.config import Config
from pathlib import Path
import os

router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)

@router.post("/migrate")
async def run_migrations():
    """Run all pending database migrations"""
    try:
        # Get the absolute path to alembic.ini
        alembic_ini_path = str(Path(__file__).parent.parent.parent / "alembic.ini")
        
        # Create Alembic configuration
        alembic_cfg = Config(alembic_ini_path)
        
        # Run the migration
        command.upgrade(alembic_cfg, "head")
        
        return {"message": "Migrations completed successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Migration failed: {str(e)}"
        )
