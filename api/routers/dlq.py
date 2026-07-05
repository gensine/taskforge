from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid
from datetime import datetime

from ..database import get_db
from ..models import User, Job, DeadLetterQueue
from .deps import get_current_user

router = APIRouter(prefix="/api/v1", tags=["dlq"])

@router.post("/dead-letter/{dlq_id}/requeue")
async def requeue_dlq(dlq_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(DeadLetterQueue).where(DeadLetterQueue.id == dlq_id))
    dlq_entry = result.scalars().first()
    if not dlq_entry:
        raise HTTPException(status_code=404, detail="DLQ entry not found")
        
    # Requeue the job
    job = await db.get(Job, dlq_entry.job_id)
    if job:
        job.status = "queued"
        job.attempt_count = 0
        job.claimed_by = None
        job.run_at = datetime.utcnow()
        
    # Remove from DLQ
    await db.delete(dlq_entry)
    await db.commit()
    return {"status": "requeued", "job_id": job.id if job else None}
