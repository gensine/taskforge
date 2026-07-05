import asyncio
import logging
import os
import signal
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine
from croniter import croniter
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost/job_scheduler")
engine = create_async_engine(DATABASE_URL)

WORKER_ID = str(uuid.uuid4())
QUEUE_ID = os.getenv("QUEUE_ID", None) # In a real scenario, worker might poll multiple queues

shutdown_event = asyncio.Event()

async def heartbeat_loop():
    while not shutdown_event.is_set():
        try:
            async with engine.begin() as conn:
                # Upsert worker heartbeat
                await conn.execute(
                    text("""
                        INSERT INTO workers (id, hostname, status, started_at, last_heartbeat_at, concurrency)
                        VALUES (:id, :hostname, 'active', NOW(), NOW(), 10)
                        ON CONFLICT (id) DO UPDATE SET last_heartbeat_at = NOW()
                    """),
                    {"id": WORKER_ID, "hostname": os.uname().nodename if hasattr(os, 'uname') else 'windows-worker'}
                )
        except Exception as e:
            logger.error(f"Heartbeat failed: {e}")
        await asyncio.sleep(5)

import json

async def process_job(job):
    logger.info(f"Processing job {job.id} of type {job.type}")
    try:
        # simulate work, replace with real handler logic
        await asyncio.sleep(1)
        if job.payload and job.payload.get("fail"):
            raise Exception("Simulated failure from payload")
            
        async with engine.begin() as conn:
            await conn.execute(
                text("UPDATE jobs SET status='completed', completed_at=NOW() WHERE id=:id"),
                {"id": job.id}
            )
        logger.info(f"Job {job.id} completed")
    except Exception as e:
        logger.error(f"Job {job.id} failed: {e}")
        async with engine.begin() as conn:
            # Fetch policy
            policy_result = await conn.execute(
                text("SELECT * FROM retry_policies WHERE queue_id = :qid LIMIT 1"),
                {"qid": job.queue_id}
            )
            policy = policy_result.mappings().first()
            
            new_attempt = job.attempt_count + 1
            if new_attempt >= job.max_attempts:
                # DLQ transition
                await conn.execute(
                    text("UPDATE jobs SET status='dead_letter', attempt_count=:attempts WHERE id=:id"),
                    {"attempts": new_attempt, "id": job.id}
                )
                await conn.execute(
                    text("""
                        INSERT INTO dead_letter_queue (id, job_id, queue_id, final_error, attempt_history, moved_at)
                        VALUES (:dlq_id, :job_id, :queue_id, :error, :history, NOW())
                    """),
                    {
                        "dlq_id": str(uuid.uuid4()), "job_id": job.id, "queue_id": job.queue_id, 
                        "error": str(e), "history": json.dumps([{"attempt": new_attempt, "error": str(e)}])
                    }
                )
                logger.warning(f"Job {job.id} moved to DLQ")
            else:
                # Retry math
                delay_ms = 1000
                if policy:
                    if policy.strategy == "fixed":
                        delay_ms = policy.base_delay_ms
                    elif policy.strategy == "linear":
                        delay_ms = policy.base_delay_ms * new_attempt
                    elif policy.strategy == "exponential":
                        delay_ms = min(policy.base_delay_ms * (2 ** (new_attempt - 1)), policy.max_delay_ms)
                
                await conn.execute(
                    text("""
                        UPDATE jobs 
                        SET status='queued', 
                            attempt_count=:attempts, 
                            run_at = NOW() + interval '1 millisecond' * :delay,
                            claimed_by = NULL
                        WHERE id=:id
                    """),
                    {"attempts": new_attempt, "delay": delay_ms, "id": job.id}
                )
                logger.info(f"Job {job.id} scheduled for retry {new_attempt}")

async def polling_loop():
    if not QUEUE_ID:
        logger.warning("QUEUE_ID not set, polling will skip unless updated.")
        
    while not shutdown_event.is_set():
        if not QUEUE_ID:
            await asyncio.sleep(5)
            continue
            
        try:
            async with engine.begin() as conn:
                # Atomic claim
                result = await conn.execute(
                    text("""
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
                            LIMIT 1 
                            FOR UPDATE SKIP LOCKED
                        ) 
                        RETURNING *
                    """),
                    {"worker_id": WORKER_ID, "queue_id": QUEUE_ID}
                )
                jobs = result.mappings().all()
                
            for job in jobs:
                # Fire and forget processing to allow concurrent execution up to limit
                asyncio.create_task(process_job(job))
                
        except Exception as e:
            logger.error(f"Polling failed: {e}")
            
        await asyncio.sleep(2) # polling interval

async def cron_loop():
    while not shutdown_event.is_set():
        try:
            async with engine.begin() as conn:
                # Find due scheduled jobs using SKIP LOCKED
                result = await conn.execute(
                    text("""
                        SELECT * FROM scheduled_jobs 
                        WHERE is_active = TRUE AND next_run_at <= NOW() 
                        FOR UPDATE SKIP LOCKED
                    """)
                )
                due_jobs = result.mappings().all()
                for sj in due_jobs:
                    # Instantiate job
                    template = sj.job_template
                    await conn.execute(
                        text("""
                            INSERT INTO jobs (id, queue_id, type, payload, status, priority, run_at, cron_expression)
                            VALUES (:id, :qid, :type, :payload, 'queued', :priority, NOW(), :cron)
                        """),
                        {
                            "id": str(uuid.uuid4()), "qid": sj.queue_id, "type": template.get("type", "default"),
                            "payload": json.dumps(template.get("payload", {})), "priority": template.get("priority", 0),
                            "cron": sj.cron_expression
                        }
                    )
                    # Update next_run_at
                    next_run = croniter(sj.cron_expression, datetime.utcnow()).get_next(datetime)
                    await conn.execute(
                        text("UPDATE scheduled_jobs SET last_triggered_at = NOW(), next_run_at = :next WHERE id = :id"),
                        {"next": next_run, "id": sj.id}
                    )
        except Exception as e:
            logger.error(f"Cron loop failed: {e}")
        await asyncio.sleep(60)

async def main():
    logger.info(f"Worker {WORKER_ID} starting")
    
    loop = asyncio.get_running_loop()
    # Windows doesn't support add_signal_handler for all signals, so we handle it gracefully where possible
    try:
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, shutdown_event.set)
    except NotImplementedError:
        pass # Windows environment fallback
        
    asyncio.create_task(heartbeat_loop())
    asyncio.create_task(cron_loop())
    await polling_loop()
    
    logger.info("Worker shutting down gracefully...")
    # In a full implementation, wait for active process_job tasks to finish here

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        shutdown_event.set()
