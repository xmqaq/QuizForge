from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.schemas.user import UserCreate
from app.utils.security import create_access_token, hash_password, verify_password


async def register_user(db: AsyncSession, data: UserCreate) -> User:
    existing = await db.scalar(
        select(User).where(or_(User.email == data.email, User.username == data.username))
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱或用户名已被注册"
        )

    user_count = await db.scalar(select(func.count()).select_from(User))
    first_user = user_count == 0

    # 管理员可在系统设置里关闭注册；首个用户（初始管理员）始终放行
    if not first_user:
        from app.routers.admin import get_site_config

        try:
            allow_register = get_site_config().get("allow_register", True)
        except Exception:
            allow_register = True  # redis 不可用时放行，避免把注册彻底锁死
        if not allow_register:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="管理员已关闭新用户注册"
            )

    user = User(
        email=data.email,
        username=data.username,
        hashed_password=hash_password(data.password),
        role=UserRole.admin if first_user else UserRole.user,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate(db: AsyncSession, email: str, password: str) -> User:
    user = await db.scalar(select(User).where(User.email == email))
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="邮箱或密码错误"
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被禁用")
    return user


def issue_token(user: User) -> str:
    return create_access_token(str(user.id), user.role.value)
