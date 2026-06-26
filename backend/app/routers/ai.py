import json
import os
import uuid

import redis.asyncio as aioredis
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.file_task import FileTask, FileType
from app.models.user import User
from app.schemas.ai import GenerateFromFileResponse, GenerateRequest, GenerateResponse
from app.tasks.ai_tasks import generate_from_file_task, generate_questions_task

router = APIRouter()
_redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

# upload extension -> stored FileType
_EXT_MAP = {".pdf": FileType.pdf, ".docx": FileType.word, ".txt": FileType.txt, ".md": FileType.markdown}


@router.post("/generate", response_model=GenerateResponse, summary="AI 出题（按主题）")
async def generate(req: GenerateRequest, current_user: User = Depends(get_current_user)):
    """提交一个异步 AI 出题任务，立即返回 task_id，用 /ai/task/{task_id} 查询进度。"""
    task_id = str(uuid.uuid4())
    generate_questions_task.delay(
        task_id,
        str(req.bank_id),
        req.topic,
        req.difficulty.value,
        req.count,
        req.auto_approve,
        str(current_user.id),
    )
    return GenerateResponse(task_id=task_id)


@router.post(
    "/generate-from-file",
    response_model=GenerateFromFileResponse,
    summary="AI 出题（按上传文件）",
)
async def generate_from_file(
    bank_id: uuid.UUID = Form(...),
    difficulty: str = Form("medium"),
    count: int = Form(10),
    auto_approve: bool = Form(False),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """上传 pdf/docx/txt/md 文件，解析内容后由 AI 据此出题。"""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in _EXT_MAP:
        raise HTTPException(status_code=400, detail="仅支持 pdf/docx/txt/md 文件")

    data = await file.read()
    if len(data) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"文件超过 {settings.MAX_UPLOAD_SIZE_MB}MB 限制")

    os.makedirs(settings.FILE_UPLOAD_DIR, exist_ok=True)
    stored_name = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(settings.FILE_UPLOAD_DIR, stored_name)
    with open(file_path, "wb") as f:
        f.write(data)

    file_task = FileTask(
        user_id=current_user.id,
        original_filename=file.filename or stored_name,
        file_path=file_path,
        file_type=_EXT_MAP[ext],
    )
    db.add(file_task)
    await db.commit()
    await db.refresh(file_task)

    task_id = str(uuid.uuid4())
    generate_from_file_task.delay(
        task_id,
        str(bank_id),
        str(file_task.id),
        difficulty,
        count,
        auto_approve,
        str(current_user.id),
    )
    return GenerateFromFileResponse(task_id=task_id, file_task_id=str(file_task.id))


@router.get("/task/{task_id}", summary="查询出题任务状态")
async def task_status(task_id: str, current_user: User = Depends(get_current_user)):
    """返回 Redis 中存储的任务状态（status / progress / generated / questions）。"""
    raw = await _redis.get(f"task:{task_id}")
    if raw is None:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")
    return json.loads(raw)
