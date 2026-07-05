from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid
from typing import List

from ..database import get_db
from ..models import User, Project, Organization, Queue, RetryPolicy
from ..schemas import QueueCreate, QueueUpdate, QueueResponse, RetryPolicyResponse
from .deps import get_current_user

router = APIRouter(prefix="/api/v1", tags=["queues"])

async def verify_project_access(project_id: uuid.UUID, db: AsyncSession, current_user: User):
    result = await db.execute(
        select(Project).join(Organization).where(Project.id == project_id, Organization.owner_id == current_user.id)
    )
    if not result.scalars().first():
        raise HTTPException(status_code=403, detail="Not authorized for this project")

@router.post("/projects/{project_id}/queues", response_model=QueueResponse, status_code=status.HTTP_201_CREATED)
async def create_queue(project_id: uuid.UUID, queue: QueueCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    await verify_project_access(project_id, db, current_user)
    
    # check unique name per project
    result = await db.execute(select(Queue).where(Queue.project_id == project_id, Queue.name == queue.name))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Queue name already exists in this project")
    
    db_queue = Queue(
        project_id=project_id,
        name=queue.name,
        priority=queue.priority,
        concurrency_limit=queue.concurrency_limit,
        is_paused=queue.is_paused
    )
    db.add(db_queue)
    await db.commit()
    await db.refresh(db_queue)
    
    if queue.default_retry_policy:
        rp = queue.default_retry_policy
        db_rp = RetryPolicy(
            queue_id=db_queue.id,
            strategy=rp.strategy,
            base_delay_ms=rp.base_delay_ms,
            max_retries=rp.max_retries,
            max_delay_ms=rp.max_delay_ms
        )
        db.add(db_rp)
        await db.commit()
        await db.refresh(db_rp)
        db_queue.default_retry_policy_id = db_rp.id
        await db.commit()
        await db.refresh(db_queue)
        
    return db_queue

@router.get("/projects/{project_id}/queues", response_model=List[QueueResponse])
async def list_queues(project_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    await verify_project_access(project_id, db, current_user)
    result = await db.execute(select(Queue).where(Queue.project_id == project_id))
    return result.scalars().all()

@router.patch("/queues/{queue_id}", response_model=QueueResponse)
async def update_queue(queue_id: uuid.UUID, update_data: QueueUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Queue).where(Queue.id == queue_id))
    queue = result.scalars().first()
    if not queue:
        raise HTTPException(status_code=404, detail="Queue not found")
    await verify_project_access(queue.project_id, db, current_user)
    
    if update_data.priority is not None:
        queue.priority = update_data.priority
    if update_data.concurrency_limit is not None:
        queue.concurrency_limit = update_data.concurrency_limit
    if update_data.is_paused is not None:
        queue.is_paused = update_data.is_paused
        
    await db.commit()
    await db.refresh(queue)
    return queue
