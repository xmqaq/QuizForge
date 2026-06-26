from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401 - ensures all tables are registered on Base.metadata
from app.database import Base, async_engine
from app.routers import (
    admin,
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
    # 用 redis 里持久化的系统配置覆盖默认 DeepSeek 客户端（管理员在系统设置改过则生效）
    # redis 不可用时不阻塞启动，退回 .env 默认值即可
    try:
        from app.config import settings
        from app.services import ai_service

        cfg = admin.get_config()
        ai_service.reload_client(
            api_key=cfg.get("deepseek_api_key") or settings.DEEPSEEK_API_KEY,
            base_url=cfg.get("deepseek_base_url") or settings.DEEPSEEK_BASE_URL,
            model=cfg.get("deepseek_model") or settings.DEEPSEEK_MODEL,
        )
    except Exception:  # ponytail: redis 抖动不该拖垮整个 API 启动
        pass
    yield


app = FastAPI(title="QuizForge API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # 用 Bearer Token 鉴权，不依赖 cookie；credentials=False 才能与 origins="*" 合法共存
    allow_credentials=False,
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
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])


@app.get("/", tags=["root"])
async def root():
    return {"name": "QuizForge API", "status": "ok"}
