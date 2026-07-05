from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Integer
from sqlalchemy import JSON, Uuid as UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Organization(Base):
    __tablename__ = "organizations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

class Project(Base):
    __tablename__ = "projects"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"))
    name = Column(String, nullable=False)
    api_key = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class RetryPolicy(Base):
    __tablename__ = "retry_policies"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    queue_id = Column(UUID(as_uuid=True), ForeignKey("queues.id"), nullable=True)
    strategy = Column(String, nullable=False) # fixed, linear, exponential
    base_delay_ms = Column(Integer, default=1000)
    max_retries = Column(Integer, default=3)
    max_delay_ms = Column(Integer, default=60000)

class Queue(Base):
    __tablename__ = "queues"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))
    name = Column(String, nullable=False)
    priority = Column(Integer, default=0, index=True)
    concurrency_limit = Column(Integer, default=10)
    is_paused = Column(Boolean, default=False)
    default_retry_policy_id = Column(UUID(as_uuid=True), ForeignKey("retry_policies.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Worker(Base):
    __tablename__ = 'workers'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hostname = Column(String)
    status = Column(String, default='active')
    started_at = Column(DateTime, default=datetime.utcnow)
    last_heartbeat_at = Column(DateTime, default=datetime.utcnow, index=True)
    concurrency = Column(Integer, default=10)

class Job(Base):
    __tablename__ = 'jobs'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    queue_id = Column(UUID(as_uuid=True), ForeignKey('queues.id', ondelete='CASCADE'))
    type = Column(String, nullable=False)
    payload = Column(JSON)
    status = Column(String, default='queued', index=True)
    priority = Column(Integer, default=0)
    run_at = Column(DateTime, default=datetime.utcnow, index=True)
    cron_expression = Column(String, nullable=True)
    parent_batch_id = Column(UUID(as_uuid=True), ForeignKey('jobs.id'), nullable=True)
    attempt_count = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    idempotency_key = Column(String, nullable=True)
    claimed_by = Column(UUID(as_uuid=True), ForeignKey('workers.id', ondelete='SET NULL'), nullable=True)
    claimed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class DeadLetterQueue(Base):
    __tablename__ = 'dead_letter_queue'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey('jobs.id', ondelete='CASCADE'))
    queue_id = Column(UUID(as_uuid=True), ForeignKey('queues.id'))
    final_error = Column(String)
    attempt_history = Column(JSON)
    moved_at = Column(DateTime, default=datetime.utcnow)


class ScheduledJob(Base):
    __tablename__ = 'scheduled_jobs'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    queue_id = Column(UUID(as_uuid=True), ForeignKey('queues.id', ondelete='CASCADE'))
    cron_expression = Column(String, nullable=False)
    job_template = Column(JSON, nullable=False)
    next_run_at = Column(DateTime, index=True)
    is_active = Column(Boolean, default=True)
    last_triggered_at = Column(DateTime, nullable=True)

