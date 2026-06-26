from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401 - ensures all tables are registered on Base.metadata
from app.database import Base, async_engine
from app.routers import (
    ai,
    auth,
    banks,
    files,
    questions,
    quiz,
    stats,
    study_plan,
    users,
    wrong,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="QuizForge API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(questions.router, prefix="/api/v1/questions", tags=["questions"])
app.include_router(banks.router, prefix="/api/v1/banks", tags=["banks"])
app.include_router(quiz.router, prefix="/api/v1/quiz", tags=["quiz"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["ai"])
app.include_router(files.router, prefix="/api/v1/files", tags=["files"])
app.include_router(stats.router, prefix="/api/v1/stats", tags=["stats"])
app.include_router(wrong.router, prefix="/api/v1/wrong", tags=["wrong"])
app.include_router(study_plan.router, prefix="/api/v1/study-plans", tags=["study-plans"])


@app.get("/", tags=["root"])
async def root():
    return {"name": "QuizForge API", "status": "ok"}
