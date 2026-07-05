from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..database import get_db
from ..models import Worker

router = APIRouter(prefix="/api/v1/workers", tags=["workers"])

@router.get("/")
async def list_workers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Worker))
    workers = result.scalars().all()
    return workers
