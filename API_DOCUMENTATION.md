# API Documentation

This document outlines the REST APIs exposed by TaskForge - Distributed Job Scheduler.

The API is built using FastAPI, and an interactive OpenAPI (Swagger) UI is automatically generated and accessible at `http://localhost:8000/docs`.

## Authentication
Most endpoints are protected by OAuth2 with Password (and hashing), using Bearer JWT tokens.
- **Endpoint:** `POST /api/v1/auth/token`
- **Payload:** `username` (email) and `password`
- **Response:** `{"access_token": "<token>", "token_type": "bearer"}`

## Core Resources

### 1. Queues
Manage job queues which act as isolated pipelines for jobs.
- **`GET /api/v1/queues/`**: List all queues.
- **`POST /api/v1/queues/`**: Create a new queue. Requires `project_id`, `name`, `priority`, and `concurrency_limit`.
- **`PATCH /api/v1/queues/{queue_id}`**: Pause/Resume a queue by updating `is_paused`.

### 2. Jobs
Submit and manage background jobs.
- **`POST /api/v1/queues/{queue_id}/jobs/`**: Submit a new job to a queue.
  - **Payload**: `{"type": "video_transcode", "payload": {"file": "vid1.mp4"}, "priority": 10}`
- **`POST /api/v1/queues/{queue_id}/jobs/batch`**: Submit multiple jobs atomically.
- **`POST /api/v1/queues/{queue_id}/jobs/recurring`**: Schedule a recurring job using a `cron_expression`.
- **`GET /api/v1/queues/{queue_id}/jobs/{job_id}`**: Check the status of a specific job.
- **`DELETE /api/v1/queues/{queue_id}/jobs/{job_id}`**: Cancel a pending job.

### 3. Dead Letter Queue (DLQ)
Review and replay failed jobs.
- **`GET /api/v1/queues/{queue_id}/dlq/`**: Fetch jobs that have permanently failed and been moved to the DLQ.
- **`POST /api/v1/queues/{queue_id}/dlq/{job_id}/replay`**: Retry a failed job in the DLQ by moving it back to the active queue.

### 4. Metrics & Observability
Endpoints utilized by the React Dashboard for real-time monitoring.
- **`GET /api/v1/metrics/system-health`**: Returns total active workers and total configured queues.
- **`GET /api/v1/metrics/recent-jobs`**: Returns a list of the most recent jobs across all queues with their status.
- **`GET /api/v1/workers/`**: List all active background workers and their last heartbeat timestamp.

### 5. Admin & Dashboard Operations
These endpoints are used directly by the React dashboard for administrative control and observability. **They require JWT Authentication.**
- **`GET /api/v1/metrics/queues`**: List all queues with their active/paused status.
- **`PATCH /api/v1/metrics/queues/{queue_id}/pause`**: Instantly pause a queue, instructing workers to skip its jobs.
- **`PATCH /api/v1/metrics/queues/{queue_id}/resume`**: Resume a paused queue.
- **`DELETE /api/v1/metrics/queues/{queue_id}`**: Delete a queue permanently.
