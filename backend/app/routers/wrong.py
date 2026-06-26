import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.question import Question
from app.models.user import User
from app.models.wrong_question import WrongQuestion
from app.schemas.question import QuestionResponse
from app.utils.time import naive_utcnow

router = APIRouter()


async def _get_record(db: AsyncSession, user: User, question_id: uuid.UUID) -> WrongQuestion:
    rec = await db.scalar(
        select(WrongQuestion).where(
            WrongQuestion.user_id == user.id, WrongQuestion.question_id == question_id
        )
    )
    if rec is None:
        raise HTTPException(status_code=404, detail="错题记录不存在")
    return rec


@router.get("", summary="我的错题本")
async def list_wrong(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    bank_id: uuid.UUID | None = None,
    is_mastered: bool | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """返回当前用户的错题，附带题目详情。可按题库和掌握状态过滤。"""
    stmt = (
        select(WrongQuestion, Question)
        .join(Question, Question.id == WrongQuestion.question_id)
        .where(WrongQuestion.user_id == current_user.id)
    )
    if bank_id is not None:
        stmt = stmt.where(Question.bank_id == bank_id)
    if is_mastered is not None:
        stmt = stmt.where(WrongQuestion.is_mastered.is_(is_mastered))

    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = await db.execute(
        stmt.order_by(WrongQuestion.last_wrong_at.desc()).offset((page - 1) * size).limit(size)
    )
    items = [
        {
            "question_id": str(w.question_id),
            "wrong_count": w.wrong_count,
            "last_wrong_at": w.last_wrong_at,
            "is_mastered": w.is_mastered,
            "mastered_at": w.mastered_at,
            "question": QuestionResponse.model_validate(q),
        }
        for w, q in rows.all()
    ]
    return {"items": items, "total": total, "page": page, "size": size}


@router.post("/{question_id}/master", summary="标记错题为已掌握")
async def master(
    question_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rec = await _get_record(db, current_user, question_id)
    rec.is_mastered = True
    rec.mastered_at = naive_utcnow()
    await db.commit()
    return {"detail": "已标记为掌握"}


@router.delete("/{question_id}", summary="从错题本移除")
async def remove(
    question_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rec = await _get_record(db, current_user, question_id)
    await db.delete(rec)
    await db.commit()
    return {"detail": "已移除"}
