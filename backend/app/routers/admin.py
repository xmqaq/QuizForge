import json

import redis as redis_lib
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.config import settings
from app.dependencies import require_roles
from app.models.user import User, UserRole

router = APIRouter()

_redis = redis_lib.Redis.from_url(settings.REDIS_URL, decode_responses=True)
CONFIG_KEY = "quizforge:system_config"

CONFIG_DEFAULTS = {
    "deepseek_api_key": "",
    "deepseek_base_url": "https://api.deepseek.com",
    "deepseek_model": "deepseek-chat",
    "site_name": "QuizForge",
    "allow_register": True,
}


def get_config() -> dict:
    raw = _redis.get(CONFIG_KEY)
    cfg = json.loads(raw) if raw else {}
    return {**CONFIG_DEFAULTS, **cfg}


class ConfigUpdate(BaseModel):
    deepseek_api_key: str | None = None
    deepseek_base_url: str | None = None
    deepseek_model: str | None = None
    site_name: str | None = None
    allow_register: bool | None = None


@router.get("/public-config", summary="站点公开配置（无需登录）")
async def get_public_config():
    """登录/注册页用：只暴露站点名与是否开放注册，不含任何敏感信息。"""
    cfg = get_config()
    return {"site_name": cfg["site_name"], "allow_register": cfg["allow_register"]}


@router.get("/config", summary="获取系统配置（管理员）")
async def get_system_config(
    _: User = Depends(require_roles(UserRole.admin)),
):
    cfg = get_config()
    # 隐藏 key 的完整内容，只显示末4位
    key = cfg.get("deepseek_api_key", "")
    cfg["deepseek_api_key_masked"] = (
        "*" * (len(key) - 4) + key[-4:] if len(key) > 4 else "*" * len(key)
    )
    cfg["deepseek_api_key"] = ""  # 不返回原始 key
    return cfg


@router.put("/config", summary="更新系统配置（管理员）")
async def update_system_config(
    data: ConfigUpdate,
    _: User = Depends(require_roles(UserRole.admin)),
):
    cfg = get_config()
    updates = data.model_dump(exclude_unset=True, exclude_none=True)
    cfg.update(updates)
    _redis.set(CONFIG_KEY, json.dumps(cfg))
    # 同步更新 ai_service 使用的 client（重新初始化）
    if {"deepseek_api_key", "deepseek_base_url", "deepseek_model"} & updates.keys():
        from app.services import ai_service

        ai_service.reload_client(
            api_key=cfg.get("deepseek_api_key") or settings.DEEPSEEK_API_KEY,
            base_url=cfg.get("deepseek_base_url") or settings.DEEPSEEK_BASE_URL,
            model=cfg.get("deepseek_model") or settings.DEEPSEEK_MODEL,
        )
    return {"detail": "配置已更新"}
