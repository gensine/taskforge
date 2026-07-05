from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..database import get_db
from ..models import Worker, User
from .deps import get_current_user

router = APIRouter(prefix="/api/v1/workers", tags=["workers"])

@router.get("/")
async def list_workers(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Worker))
    workers = result.scalars().all()
    return workers
