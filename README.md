# TaskForge - Distributed Job Scheduler

A highly scalable, robust, and asynchronous Distributed Job Scheduler (TaskForge) built from scratch. This system is designed to reliably execute asynchronous background jobs across multiple workers, handling concurrency, exponential backoffs, and dead letter queues seamlessly.

## Core Features

- **Atomic Job Claiming:** Workers utilize PostgreSQL's `FOR UPDATE SKIP LOCKED` to atomically claim jobs. This guarantees that no single job is ever picked up by more than one worker, enabling infinite horizontal worker scaling.
- **Priority Queues:** Queues and individual jobs can be assigned priority levels, ensuring critical workloads are processed first.
- **Advanced Retry Policies:** Native support for fixed, linear, and exponential backoff retry strategies when jobs fail.
- **Dead Letter Queue (DLQ):** Jobs that permanently fail after exhausting their retry limits are moved to a quarantine DLQ for later inspection and manual replay.
- **Recurring & Scheduled Jobs:** Schedule delayed jobs to run in the future, or use cron syntax to emit recurring jobs.
- **Real-Time Observability:** A premium dark-mode React dashboard provides real-time insights into system health, active workers, queue throughput, and recent job statuses, along with administrative controls to pause, resume, or delete queues on the fly.

## Architecture & Stack

- **Backend**: FastAPI (Python 3.11+), SQLAlchemy (Async), asyncpg
- **Database**: PostgreSQL (Primary data store for Jobs and Queues)
- **Cache/Metrics**: Redis (Used for real-time statistical caching)
- **Frontend**: React, Vite, TailwindCSS
- **Containerization**: Fully containerized with Docker and orchestrated via Docker Compose.

*(For detailed architectural diagrams and trade-offs, please refer to [ARCHITECTURE.md](./ARCHITECTURE.md) and [DESIGN_DECISIONS.md](./DESIGN_DECISIONS.md)).*

## Quick Start (Docker)

This project is fully containerized. You do not need to install Python or Node locally to run the entire stack.

1. Ensure you have [Docker Desktop](https://www.docker.com/products/docker-desktop) installed and running.
2. Clone this repository:
   ```bash
   git clone https://github.com/gensine/taskforge.git
   cd taskforge
   ```
3. Spin up the entire infrastructure (Database, Cache, API, Background Worker, and Frontend UI):
   ```bash
   docker-compose up -d --build
   ```

Once the containers are running, the following services will be available:
- **Frontend Dashboard:** [http://localhost:5173](http://localhost:5173)
- **API Documentation (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Backend API Base URL:** `http://localhost:8000`

## Local Development Setup (Native)

If you prefer to run the system natively without Docker, follow these steps:

### 1. Database Setup
1. Install and start [PostgreSQL](https://www.postgresql.org/download/).
2. Create a new database for the project (e.g., `job_scheduler`).

### 2. Backend & Worker Setup
1. Ensure you have Python 3.11+ installed.
2. Open a terminal in the root directory and create a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   # source venv/bin/activate  # On Mac/Linux
   ```
3. Install the dependencies for both the API and the Worker:
   ```bash
   pip install -r api/requirements.txt
   pip install -r worker/requirements.txt
   ```
4. Set your `DATABASE_URL` environment variable if your database credentials differ from the default (`postgresql+asyncpg://postgres:password@localhost/job_scheduler`).
5. Start the FastAPI backend server:
   ```bash
   uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
   ```
6. Open a new terminal, activate the virtual environment, and start a background worker:
   ```bash
   python worker/main.py
   ```

### 3. Frontend Dashboard Setup
1. Ensure you have [Node.js](https://nodejs.org/) installed.
2. Open a new terminal in the `frontend` directory:
   ```bash
   cd frontend
   ```
3. Install the frontend dependencies:
   ```bash
   npm install
   ```
4. (Optional) If your API is running on a different URL/port, create a `.env` file by copying `.env.example` and updating `VITE_API_BASE_URL`.
5. Start the React development server:
   ```bash
   npm run dev
   ```

The dashboard will now be accessible at `http://localhost:5173`.

> **Default Dashboard Credentials:** If you ran `seed.py`, log in with email: `admin@test.com` and password: `password`.

## Running Automated Tests

I have included a suite of automated end-to-end integration tests using `pytest` and `httpx` to verify the core APIs and atomic job processing logic.

To run the tests locally:
```bash
# 1. Setup a virtual environment
python -m venv venv
venv\Scripts\activate  # On Windows

# 2. Install testing dependencies
pip install pytest pytest-asyncio httpx

# 3. Run the end-to-end Python test script against the live containerized API
python e2e_test.py
```

## Documentation

For a deeper dive into the APIs and the design choices made while building this scheduler, please refer to the following documents:
- **[API Documentation](./API_DOCUMENTATION.md)**: Detailed endpoints, payloads, and authentication flows.
- **[Architecture](./ARCHITECTURE.md)**: System and ER diagrams.
- **[Design Decisions](./DESIGN_DECISIONS.md)**: An overview of why specific technologies and patterns were chosen (e.g., Pull vs. Push workers).

## Author

Built as a robust, production-inspired distributed systems project by Vaishnavi Mishra.
