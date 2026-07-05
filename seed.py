import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from api.database import SessionLocal
from api.models import User, Organization, Project, Queue, Job
from api.auth_utils import get_password_hash
import uuid

async def seed():
    async with SessionLocal() as db:
        # Clean up existing data to prevent unique constraint errors
        await db.execute(delete(Job))
        await db.execute(delete(Queue))
        await db.execute(delete(Project))
        await db.execute(delete(Organization))
        await db.execute(delete(User))
        await db.commit()

        db_user = User(name="Test Admin", email="admin@test.com", password_hash=get_password_hash("password"))
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)

        org = Organization(name="Test Org", owner_id=db_user.id)
        db.add(org)
        await db.commit()
        await db.refresh(org)

        proj = Project(name="Test Project", organization_id=org.id, api_key="test-api-key-123")
        db.add(proj)
        await db.commit()
        await db.refresh(proj)

        q1 = Queue(name="high_priority", project_id=proj.id, priority=10, concurrency_limit=5)
        q2 = Queue(name="default", project_id=proj.id, priority=5, concurrency_limit=10)
        db.add_all([q1, q2])
        await db.commit()
        await db.refresh(q1)
        await db.refresh(q2)

        j1 = Job(queue_id=q1.id, type="video_transcode", payload={"file": "vid1.mp4"}, status="queued", priority=10)
        j2 = Job(queue_id=q1.id, type="video_transcode", payload={"file": "vid2.mp4"}, status="queued", priority=10)
        j3 = Job(queue_id=q2.id, type="send_email", payload={"to": "user@test.com"}, status="queued", priority=5)
        j4 = Job(queue_id=q1.id, type="video_transcode", payload={"file": "vid3.mp4"}, status="completed", priority=10)
        
        db.add_all([j1, j2, j3, j4])
        await db.commit()
        print("Database seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed())
