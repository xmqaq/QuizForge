import uuid
from collections import Counter
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.question import Difficulty, Question, QuestionStatus
from app.models.question_bank import QuestionBank
from app.models.user import User, UserRole
from app.schemas.question import QuestionCreate, QuestionResponse, QuestionUpdate

router = APIRouter()


async def _get_question_or_404(db: AsyncSession, question_id: uuid.UUID) -> Question:
    q = await db.get(Question, question_id)
    if q is None:
        raise HTTPException(status_code=404, detail="题目不存在")
    return q


@router.get("", summary="题目列表")
async def list_questions(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=1000),
    bank_id: uuid.UUID | None = None,
    status: QuestionStatus | None = None,
    difficulty: Difficulty | None = None,
):
    stmt = select(Question)
    if bank_id is not None:
        stmt = stmt.where(Question.bank_id == bank_id)
    if status is not None:
        stmt = stmt.where(Question.status == status)
    if difficulty is not None:
        stmt = stmt.where(Question.difficulty == difficulty)

    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = await db.scalars(
        stmt.order_by(Question.created_at.desc()).offset((page - 1) * size).limit(size)
    )
    items = [QuestionResponse.model_validate(r) for r in rows]
    return {"items": items, "total": total, "page": page, "size": size}


@router.post("", response_model=QuestionResponse, summary="手动创建题目")
async def create_question(
    data: QuestionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bank = await db.get(QuestionBank, data.bank_id)
    if bank is None:
        raise HTTPException(status_code=404, detail="题库不存在")

    q = Question(**data.model_dump(), created_by=current_user.id)
    db.add(q)
    bank.question_count += 1
    await db.commit()
    await db.refresh(q)
    return q


@router.get("/{question_id}", response_model=QuestionResponse, summary="题目详情")
async def get_question(question_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await _get_question_or_404(db, question_id)


@router.put("/{question_id}", response_model=QuestionResponse, summary="更新题目")
async def update_question(
    question_id: uuid.UUID,
    data: QuestionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = await _get_question_or_404(db, question_id)
    if q.created_by != current_user.id and current_user.role not in (
        UserRole.admin,
        UserRole.editor,
    ):
        raise HTTPException(status_code=403, detail="无权操作此题目")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(q, k, v)
    await db.commit()
    await db.refresh(q)
    return q


@router.delete("/{question_id}", summary="删除题目")
async def delete_question(
    question_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = await _get_question_or_404(db, question_id)
    if q.created_by != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="无权操作此题目")
    bank = await db.get(QuestionBank, q.bank_id)
    await db.delete(q)
    if bank and bank.question_count > 0:
        bank.question_count -= 1
    await db.commit()
    return {"detail": "已删除"}


@router.post("/{question_id}/approve", response_model=QuestionResponse, summary="审核通过")
async def approve_question(
    question_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin, UserRole.editor)),
):
    q = await _get_question_or_404(db, question_id)
    q.status = QuestionStatus.approved
    await db.commit()
    await db.refresh(q)
    return q


@router.post("/{question_id}/reject", response_model=QuestionResponse, summary="审核拒绝")
async def reject_question(
    question_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin, UserRole.editor)),
):
    q = await _get_question_or_404(db, question_id)
    q.status = QuestionStatus.rejected
    await db.commit()
    await db.refresh(q)
    return q


class BulkActionRequest(BaseModel):
    question_ids: list[uuid.UUID]
    action: Literal["approve", "reject", "delete"]


@router.post("/bulk", summary="批量操作题目")
async def bulk_action(
    data: BulkActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not data.question_ids:
        raise HTTPException(status_code=400, detail="请选择至少一道题目")
    if len(data.question_ids) > 200:
        raise HTTPException(status_code=400, detail="单次批量操作不能超过 200 道")

    ids = data.question_ids

    if data.action in ("approve", "reject"):
        if current_user.role not in (UserRole.admin, UserRole.editor):
            raise HTTPException(status_code=403, detail="无权进行审核操作")
        new_status = QuestionStatus.approved if data.action == "approve" else QuestionStatus.rejected
        await db.execute(
            sa_update(Question)
            .where(Question.id.in_(ids))
            .values(status=new_status)
        )
        await db.commit()
        return {"detail": f"已{'通过' if data.action == 'approve' else '拒绝'} {len(ids)} 道题目"}

    if data.action == "delete":
        if current_user.role != UserRole.admin:
            raise HTTPException(status_code=403, detail="批量删除需要管理员权限")
        rows = await db.scalars(select(Question).where(Question.id.in_(ids)))
        questions = list(rows)
        if not questions:
            raise HTTPException(status_code=404, detail="未找到指定题目")

        bank_counts = Counter(str(q.bank_id) for q in questions)
        for q in questions:
            await db.delete(q)

        for bank_id_str, count in bank_counts.items():
            bank = await db.get(QuestionBank, uuid.UUID(bank_id_str))
            if bank:
                bank.question_count = max(0, bank.question_count - count)

        await db.commit()
        return {"detail": f"已删除 {len(questions)} 道题目"}

    raise HTTPException(status_code=400, detail="未知操作")
