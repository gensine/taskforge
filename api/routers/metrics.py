from fastapi import APIRouter, Depends
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from ..database import get_db

router = APIRouter(prefix="/api/v1/metrics", tags=["metrics"])

@router.get("/system-health")
async def system_health(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT count(*) FROM workers WHERE status = 'active'"))
    active_workers = result.scalar()
    result = await db.execute(text("SELECT count(*) FROM queues"))
    total_queues = result.scalar()
    return {"active_workers": active_workers, "total_queues": total_queues}

@router.get("/recent-jobs")
async def recent_jobs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text("SELECT id, type, status, priority FROM jobs ORDER BY created_at DESC LIMIT 10")
    )
    jobs = result.mappings().all()
    return jobs

@router.get("/queues")
async def all_queues(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text("SELECT id, name, priority, concurrency_limit, is_paused FROM queues ORDER BY created_at DESC")
    )
    return result.mappings().all()

@router.patch("/queues/{queue_id}/pause")
async def pause_queue(queue_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    await db.execute(text("UPDATE queues SET is_paused = true WHERE id = :qid"), {"qid": str(queue_id)})
    await db.commit()
    return {"status": "paused"}

@router.patch("/queues/{queue_id}/resume")
async def resume_queue(queue_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    await db.execute(text("UPDATE queues SET is_paused = false WHERE id = :qid"), {"qid": str(queue_id)})
    await db.commit()
    return {"status": "resumed"}

@router.delete("/queues/{queue_id}")
async def delete_queue(queue_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    await db.execute(text("DELETE FROM queues WHERE id = :qid"), {"qid": str(queue_id)})
    await db.commit()
    return {"status": "deleted"}
