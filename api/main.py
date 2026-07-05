from fastapi import FastAPI
from .routers import auth, projects, queues, jobs, dlq, metrics, workers
from .database import engine, Base
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="TaskForge - Distributed Job Scheduler")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(queues.router)
app.include_router(jobs.router)
app.include_router(dlq.router)
app.include_router(metrics.router)
app.include_router(workers.router)

@app.on_event("startup")
async def startup():
    # Generate tables for dev without alembic
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/health")
def health_check():
    return {"status": "ok"}
