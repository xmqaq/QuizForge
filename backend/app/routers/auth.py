from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserResponse
from app.services import auth_service

router = APIRouter()


@router.post("/register", response_model=UserResponse, summary="注册新用户")
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """创建一个新用户。邮箱与用户名必须唯一，密码使用 bcrypt 哈希存储。"""
    return await auth_service.register_user(db, data)


@router.post("/login", response_model=Token, summary="登录获取 Token")
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """使用邮箱(username 字段填邮箱)与密码登录，返回 JWT access_token。"""
    user = await auth_service.authenticate(db, form.username, form.password)
    token = auth_service.issue_token(user)
    return Token(access_token=token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse, summary="获取当前用户")
async def me(current_user: User = Depends(get_current_user)):
    """返回当前 Bearer Token 对应的登录用户信息。"""
    return current_user
