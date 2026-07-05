from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text
import uuid
from datetime import datetime

from ..database import get_db
from ..models import User, Queue, Job, Worker, ScheduledJob
from .deps import get_current_user
from pydantic import BaseModel
from typing import Any, Dict, Optional, List

router = APIRouter(prefix="/api/v1", tags=["jobs"])

class JobCreate(BaseModel):
    type: str
    payload: Dict[str, Any]
    priority: Optional[int] = None
    run_at: Optional[datetime] = None

class ClaimJobsRequest(BaseModel):
    worker_id: uuid.UUID
    count: int = 1

class RecurringJobCreate(BaseModel):
    cron_expression: str
    job_template: Dict[str, Any]

@router.post("/queues/{queue_id}/jobs", status_code=status.HTTP_201_CREATED)
async def submit_job(queue_id: uuid.UUID, job_data: JobCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    queue = await db.get(Queue, queue_id)
    if not queue:
        raise HTTPException(status_code=404, detail="Queue not found")
        
    db_job = Job(
        queue_id=queue_id,
        type=job_data.type,
        payload=job_data.payload,
        priority=job_data.priority if job_data.priority is not None else queue.priority,
        run_at=job_data.run_at or datetime.utcnow(),
        status="queued" if not job_data.run_at or job_data.run_at <= datetime.utcnow() else "scheduled"
    )
    db.add(db_job)
    await db.commit()
    await db.refresh(db_job)
    return db_job

@router.post("/queues/{queue_id}/jobs/recurring", status_code=status.HTTP_201_CREATED)
async def create_recurring_job(queue_id: uuid.UUID, recurring_data: RecurringJobCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        from croniter import croniter
        if not croniter.is_valid(recurring_data.cron_expression):
            raise ValueError("Invalid cron expression")
        next_run = croniter(recurring_data.cron_expression, datetime.utcnow()).get_next(datetime)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid cron expression: {e}")
        
    db_scheduled = ScheduledJob(
        queue_id=queue_id,
        cron_expression=recurring_data.cron_expression,
        job_template=recurring_data.job_template,
        next_run_at=next_run
    )
    db.add(db_scheduled)
    await db.commit()
    await db.refresh(db_scheduled)
    return db_scheduled

@router.post("/queues/{queue_id}/jobs/claim")
async def claim_jobs(queue_id: uuid.UUID, request: ClaimJobsRequest, db: AsyncSession = Depends(get_db)):
    # Atomic claim logic using PostgreSQL FOR UPDATE SKIP LOCKED
    claim_query = text("""
        UPDATE jobs 
        SET status='claimed', 
            claimed_by=:worker_id, 
            claimed_at=NOW() 
        WHERE id IN (
            SELECT id FROM jobs 
            WHERE queue_id = :queue_id 
              AND status = 'queued' 
              AND run_at <= NOW() 
              AND EXISTS (SELECT 1 FROM queues WHERE queues.id = jobs.queue_id AND queues.is_paused = FALSE)
            ORDER BY priority DESC, run_at ASC 
            LIMIT :limit 
            FOR UPDATE SKIP LOCKED
        ) 
        RETURNING *
    """)
    
    result = await db.execute(claim_query, {
        "worker_id": request.worker_id,
        "queue_id": queue_id,
        "limit": request.count
    })
    claimed_jobs = result.mappings().all()
    await db.commit()
    return claimed_jobs

@router.get("/queues/{queue_id}/jobs/{job_id}")
async def get_job(queue_id: uuid.UUID, job_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = await db.get(Job, job_id)
    if not job or job.queue_id != queue_id:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
