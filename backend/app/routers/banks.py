import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.question_bank import BankStatus, QuestionBank
from app.models.user import User, UserRole
from app.schemas.question_bank import (
    QuestionBankCreate,
    QuestionBankResponse,
    QuestionBankUpdate,
)

router = APIRouter()


async def _get_bank_or_404(db: AsyncSession, bank_id: uuid.UUID) -> QuestionBank:
    bank = await db.get(QuestionBank, bank_id)
    if bank is None:
        raise HTTPException(status_code=404, detail="题库不存在")
    return bank


def _owner_or_admin(bank: QuestionBank, user: User) -> None:
    if bank.created_by != user.id and user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="无权操作此题库")


@router.get("", summary="题库列表")
async def list_banks(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    category_id: int | None = None,
    status: BankStatus | None = None,
):
    stmt = select(QuestionBank)
    if category_id is not None:
        stmt = stmt.where(QuestionBank.category_id == category_id)
    if status is not None:
        stmt = stmt.where(QuestionBank.status == status)

    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = await db.scalars(
        stmt.order_by(QuestionBank.created_at.desc()).offset((page - 1) * size).limit(size)
    )
    items = [QuestionBankResponse.model_validate(r) for r in rows]
    return {"items": items, "total": total, "page": page, "size": size}


@router.post("", response_model=QuestionBankResponse, summary="创建题库")
async def create_bank(
    data: QuestionBankCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bank = QuestionBank(**data.model_dump(), created_by=current_user.id)
    db.add(bank)
    await db.commit()
    await db.refresh(bank)
    return bank


@router.get("/{bank_id}", response_model=QuestionBankResponse, summary="题库详情")
async def get_bank(bank_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await _get_bank_or_404(db, bank_id)


@router.put("/{bank_id}", response_model=QuestionBankResponse, summary="更新题库")
async def update_bank(
    bank_id: uuid.UUID,
    data: QuestionBankUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bank = await _get_bank_or_404(db, bank_id)
    _owner_or_admin(bank, current_user)
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(bank, k, v)
    await db.commit()
    await db.refresh(bank)
    return bank


@router.delete("/{bank_id}", summary="删除题库")
async def delete_bank(
    bank_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bank = await _get_bank_or_404(db, bank_id)
    _owner_or_admin(bank, current_user)
    await db.delete(bank)
    await db.commit()
    return {"detail": "已删除"}
