import asyncio
import json
import uuid

import redis
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models.file_task import FileTask, FileTaskStatus
from app.models.question import Difficulty, Question, QuestionSource, QuestionStatus
from app.models.question_bank import QuestionBank
from app.services import ai_service, file_service
from celery_worker import celery

_redis = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
TASK_TTL = 86400


def _set_state(task_id: str, **fields) -> None:
    key = f"task:{task_id}"
    current = _redis.get(key)
    state = json.loads(current) if current else {}
    state.update(fields)
    _redis.set(key, json.dumps(state, ensure_ascii=False), ex=TASK_TTL)


def _session_maker():
    # ponytail: fresh NullPool engine per task run — avoids asyncpg "attached to a
    # different loop" errors when reusing the app engine across Celery asyncio.run loops.
    from sqlalchemy.pool import NullPool

    engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    return engine, async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def _persist_questions(
    bank_id: str, items: list[dict], difficulty: str, auto_approve: bool, user_id: str, task_id: str
) -> list[dict]:
    engine, Session = _session_maker()
    status = QuestionStatus.approved if auto_approve else QuestionStatus.pending_review
    saved: list[dict] = []
    try:
        async with Session() as db:
            for i, item in enumerate(items, start=1):
                q = Question(
                    bank_id=uuid.UUID(bank_id),
                    content=item["content"],
                    option_a=item["option_a"],
                    option_b=item["option_b"],
                    option_c=item["option_c"],
                    option_d=item["option_d"],
                    correct_answer=item["correct_answer"],
                    explanation=item.get("explanation"),
                    difficulty=Difficulty(difficulty),
                    source=QuestionSource.ai_generated,
                    status=status,
                    ai_model=settings.DEEPSEEK_MODEL,
                    created_by=uuid.UUID(user_id) if user_id else None,
                )
                db.add(q)
                await db.flush()
                saved.append({"id": str(q.id), **item})
                _set_state(task_id, generated=i, questions=saved)

            await db.execute(
                update(QuestionBank)
                .where(QuestionBank.id == uuid.UUID(bank_id))
                .values(question_count=QuestionBank.question_count + len(saved))
            )
            await db.commit()
        return saved
    finally:
        await engine.dispose()


async def _run_generate(task_id, bank_id, topic, difficulty, count, auto_approve, user_id):
    _set_state(
        task_id,
        status="processing",
        progress=0,
        generated=0,
        total=count,
        questions=[],
    )
    items = await ai_service.generate_questions(topic, difficulty, count)
    saved = await _persist_questions(bank_id, items, difficulty, auto_approve, user_id, task_id)
    _set_state(task_id, status="done", progress=100, generated=len(saved), questions=saved)


@celery.task(name="generate_questions_task")
def generate_questions_task(task_id, bank_id, topic, difficulty, count, auto_approve, user_id):
    try:
        asyncio.run(
            _run_generate(task_id, bank_id, topic, difficulty, count, auto_approve, user_id)
        )
    except Exception as e:  # noqa: BLE001 - report any failure back to the client via Redis
        _set_state(task_id, status="failed", error_message=str(e))


async def _load_file_task(file_task_id: str):
    engine, Session = _session_maker()
    try:
        async with Session() as db:
            ft = await db.get(FileTask, uuid.UUID(file_task_id))
            if ft is None:
                raise ValueError("FileTask 不存在")
            return ft.file_path, ft.file_type.value
    finally:
        await engine.dispose()


async def _update_file_task(file_task_id: str, **fields):
    engine, Session = _session_maker()
    try:
        async with Session() as db:
            await db.execute(
                update(FileTask).where(FileTask.id == uuid.UUID(file_task_id)).values(**fields)
            )
            await db.commit()
    finally:
        await engine.dispose()


async def _run_from_file(
    task_id, bank_id, file_task_id, difficulty, count, auto_approve, user_id
):
    _set_state(task_id, status="processing", progress=0, generated=0, total=count, questions=[])

    file_path, file_type = await _load_file_task(file_task_id)
    text = file_service.parse_file(file_path, file_type)
    await _update_file_task(
        file_task_id, status=FileTaskStatus.processing, parsed_content=text
    )

    topic = "基于上传文档的知识点"
    items = await ai_service.generate_questions(topic, difficulty, count, extra_context=text)
    saved = await _persist_questions(bank_id, items, difficulty, auto_approve, user_id, task_id)

    await _update_file_task(
        file_task_id, status=FileTaskStatus.done, questions_generated=len(saved)
    )
    _set_state(task_id, status="done", progress=100, generated=len(saved), questions=saved)


@celery.task(name="generate_from_file_task")
def generate_from_file_task(
    task_id, bank_id, file_task_id, difficulty, count, auto_approve, user_id
):
    try:
        asyncio.run(
            _run_from_file(
                task_id, bank_id, file_task_id, difficulty, count, auto_approve, user_id
            )
        )
    except Exception as e:  # noqa: BLE001
        _set_state(task_id, status="failed", error_message=str(e))
        try:
            asyncio.run(
                _update_file_task(
                    file_task_id, status=FileTaskStatus.failed, error_message=str(e)
                )
            )
        except Exception:
            pass
