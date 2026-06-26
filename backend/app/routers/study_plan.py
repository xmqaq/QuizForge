import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.question_bank import QuestionBank
from app.models.study_plan import StudyPlan
from app.models.user import User
from app.schemas.study_plan import StudyPlanCreate, StudyPlanResponse, StudyPlanUpdate

router = APIRouter()


async def _get_plan(db: AsyncSession, plan_id: uuid.UUID, user: User) -> StudyPlan:
    plan = await db.get(StudyPlan, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="学习计划不存在")
    if plan.user_id != user.id:
        raise HTTPException(status_code=403, detail="无权访问该计划")
    return plan


@router.post("", response_model=StudyPlanResponse, summary="创建学习计划")
async def create_plan(
    data: StudyPlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if await db.get(QuestionBank, data.bank_id) is None:
        raise HTTPException(status_code=404, detail="题库不存在")
    plan = StudyPlan(**data.model_dump(), user_id=current_user.id)
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan


@router.get("", summary="我的学习计划")
async def list_plans(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    base = select(StudyPlan).where(StudyPlan.user_id == current_user.id)
    total = await db.scalar(select(func.count()).select_from(base.subquery()))
    rows = await db.scalars(
        base.order_by(StudyPlan.created_at.desc()).offset((page - 1) * size).limit(size)
    )
    return {"items": [StudyPlanResponse.model_validate(r) for r in rows], "total": total, "page": page, "size": size}


@router.get("/{plan_id}", response_model=StudyPlanResponse, summary="学习计划详情")
async def get_plan(
    plan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _get_plan(db, plan_id, current_user)


@router.put("/{plan_id}", response_model=StudyPlanResponse, summary="更新学习计划")
async def update_plan(
    plan_id: uuid.UUID,
    data: StudyPlanUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plan = await _get_plan(db, plan_id, current_user)
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(plan, k, v)
    await db.commit()
    await db.refresh(plan)
    return plan


@router.delete("/{plan_id}", summary="删除学习计划")
async def delete_plan(
    plan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plan = await _get_plan(db, plan_id, current_user)
    await db.delete(plan)
    await db.commit()
    return {"detail": "已删除"}
