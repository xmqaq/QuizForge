import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.user import User, UserRole
from app.schemas.user import UserResponse, UserUpdate
from app.utils.security import hash_password

router = APIRouter()


@router.get("", response_model=list[UserResponse], summary="用户列表（管理员）")
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
):
    rows = await db.scalars(select(User).order_by(User.created_at.desc()))
    return list(rows)


@router.get("/{user_id}", response_model=UserResponse, summary="用户详情")
async def get_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if user_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="只能查看自己的信息")
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.put("/{user_id}", response_model=UserResponse, summary="更新用户")
async def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """本人可改用户名/邮箱/密码；角色和启用状态仅管理员可改。"""
    is_admin = current_user.role == UserRole.admin
    if user_id != current_user.id and not is_admin:
        raise HTTPException(status_code=403, detail="无权修改其他用户")

    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    fields = data.model_dump(exclude_unset=True)
    if not is_admin and ("role" in fields or "is_active" in fields):
        raise HTTPException(status_code=403, detail="只有管理员可修改角色或启用状态")

    if "password" in fields:
        user.hashed_password = hash_password(fields.pop("password"))
    for k, v in fields.items():
        setattr(user, k, v)
    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/{user_id}", summary="停用用户（管理员）")
async def deactivate_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
):
    """软删除：置为停用，保留答题/题库等历史数据。"""
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.is_active = False
    await db.commit()
    return {"detail": "用户已停用"}
