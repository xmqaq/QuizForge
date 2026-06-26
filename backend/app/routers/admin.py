import asyncio
import json

import redis as redis_lib
from fastapi import APIRouter, Depends, HTTPException
from openai import AsyncOpenAI
from pydantic import BaseModel

from app.config import settings
from app.dependencies import require_roles
from app.models.user import User, UserRole

router = APIRouter()

_redis = redis_lib.Redis.from_url(settings.REDIS_URL, decode_responses=True)
CONFIG_KEY = "quizforge:system_config"
MODELS_KEY = "quizforge:ai_providers"

# 内置预设模型商
PRESET_PROVIDERS = [
    {"id": "deepseek",  "name": "DeepSeek",     "base_url": "https://api.deepseek.com/v1",                          "default_model": "deepseek-chat"},
    {"id": "qwen",      "name": "通义千问 Qwen", "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",    "default_model": "qwen-turbo"},
    {"id": "minimax",   "name": "MiniMax",       "base_url": "https://api.minimax.chat/v1",                          "default_model": "abab6.5s-chat"},
    {"id": "zhipu",     "name": "智谱 GLM",      "base_url": "https://open.bigmodel.cn/api/paas/v4",                 "default_model": "glm-4-flash"},
    {"id": "kimi",      "name": "月之暗面 Kimi", "base_url": "https://api.moonshot.cn/v1",                           "default_model": "moonshot-v1-8k"},
    {"id": "baichuan",  "name": "百川 AI",       "base_url": "https://api.baichuan-ai.com/v1",                       "default_model": "Baichuan4"},
    {"id": "lingyiwanwu", "name": "零一万物 Yi",  "base_url": "https://api.lingyiwanwu.com/v1",                       "default_model": "yi-lightning"},
    {"id": "groq",      "name": "Groq",          "base_url": "https://api.groq.com/openai/v1",                       "default_model": "llama-3.3-70b-versatile"},
    {"id": "custom",    "name": "自定义（OpenAI 兼容）", "base_url": "",                                             "default_model": ""},
]

SITE_DEFAULTS = {"site_name": "QuizForge", "allow_register": True, "active_provider": "deepseek"}


def get_site_config() -> dict:
    raw = _redis.get(CONFIG_KEY)
    cfg = json.loads(raw) if raw else {}
    return {**SITE_DEFAULTS, **cfg}


def get_providers() -> list[dict]:
    """返回所有模型商配置（含预设+自定义扩展），api_key 已存储。"""
    raw = _redis.get(MODELS_KEY)
    stored: dict = json.loads(raw) if raw else {}
    result = []
    for p in PRESET_PROVIDERS:
        saved = stored.get(p["id"], {})
        result.append({
            **p,
            "api_key": saved.get("api_key", ""),
            "model": saved.get("model", p["default_model"]),
            "base_url": saved.get("base_url", p["base_url"]),
            "enabled": saved.get("enabled", False),
            "is_preset": True,
        })
    # 用户自行添加的自定义服务商（id 以 custom_ 开头）
    for pid, pdata in stored.items():
        if pid.startswith("custom_"):
            result.append({**pdata, "id": pid, "is_preset": False})
    return result


def get_active_provider() -> dict | None:
    """返回当前激活的模型商配置（含 api_key）。"""
    cfg = get_site_config()
    active_id = cfg.get("active_provider", "deepseek")
    providers = get_providers()
    for p in providers:
        if p["id"] == active_id and p.get("api_key"):
            return p
    # 兜底：找第一个有 key 且 enabled 的
    for p in providers:
        if p.get("api_key") and p.get("enabled"):
            return p
    return None


# ── 公开接口 ──────────────────────────────────────────────
@router.get("/public-config", summary="站点公开配置（无需登录）")
async def get_public_config():
    cfg = get_site_config()
    return {"site_name": cfg["site_name"], "allow_register": cfg["allow_register"]}


# ── 管理员接口 ────────────────────────────────────────────
@router.get("/site-config", summary="站点配置（管理员）")
async def get_site_config_api(_: User = Depends(require_roles(UserRole.admin))):
    return get_site_config()


class SiteConfigUpdate(BaseModel):
    site_name: str | None = None
    allow_register: bool | None = None
    active_provider: str | None = None


@router.put("/site-config", summary="更新站点配置（管理员）")
async def update_site_config(data: SiteConfigUpdate, _: User = Depends(require_roles(UserRole.admin))):
    cfg = get_site_config()
    updates = data.model_dump(exclude_unset=True, exclude_none=True)
    cfg.update(updates)
    _redis.set(CONFIG_KEY, json.dumps(cfg))
    # 切换激活模型时，重载 ai_service client
    if "active_provider" in updates:
        _reload_ai_client()
    return {"detail": "站点配置已更新"}


@router.get("/providers", summary="获取所有 AI 模型商配置（管理员）")
async def list_providers(_: User = Depends(require_roles(UserRole.admin))):
    providers = get_providers()
    # 隐藏 api_key，只显示末4位
    for p in providers:
        key = p.get("api_key", "")
        p["api_key_masked"] = ("*" * max(0, len(key) - 4) + key[-4:]) if len(key) > 4 else ("*" * len(key))
        p["api_key"] = ""
        p["has_key"] = bool(key)
    return providers


class ProviderUpdate(BaseModel):
    api_key: str | None = None
    model: str | None = None
    base_url: str | None = None
    enabled: bool | None = None
    name: str | None = None  # 仅自定义服务商可改名


@router.put("/providers/{provider_id}", summary="更新模型商配置（管理员）")
async def update_provider(
    provider_id: str,
    data: ProviderUpdate,
    _: User = Depends(require_roles(UserRole.admin)),
):
    raw = _redis.get(MODELS_KEY)
    stored: dict = json.loads(raw) if raw else {}
    if provider_id not in stored:
        stored[provider_id] = {}
    updates = data.model_dump(exclude_unset=True, exclude_none=True)
    # api_key 留空时不覆盖（前端留空=不修改）
    if "api_key" in updates and updates["api_key"] == "":
        del updates["api_key"]
    stored[provider_id].update(updates)
    _redis.set(MODELS_KEY, json.dumps(stored))
    # 如果修改的是当前激活服务商，重载 client
    cfg = get_site_config()
    if cfg.get("active_provider") == provider_id:
        _reload_ai_client()
    return {"detail": "已更新"}


class CustomProviderCreate(BaseModel):
    name: str
    base_url: str
    api_key: str
    model: str


@router.post("/providers/custom", summary="新增自定义模型商")
async def add_custom_provider(data: CustomProviderCreate, _: User = Depends(require_roles(UserRole.admin))):
    import uuid as _uuid

    pid = "custom_" + str(_uuid.uuid4())[:8]
    raw = _redis.get(MODELS_KEY)
    stored: dict = json.loads(raw) if raw else {}
    stored[pid] = {
        "name": data.name, "base_url": data.base_url,
        "api_key": data.api_key, "model": data.model,
        "enabled": True, "default_model": data.model,
    }
    _redis.set(MODELS_KEY, json.dumps(stored))
    return {"detail": "已添加", "id": pid}


@router.delete("/providers/{provider_id}", summary="删除自定义模型商")
async def delete_custom_provider(provider_id: str, _: User = Depends(require_roles(UserRole.admin))):
    if not provider_id.startswith("custom_"):
        raise HTTPException(400, "只能删除自定义模型商")
    raw = _redis.get(MODELS_KEY)
    stored: dict = json.loads(raw) if raw else {}
    stored.pop(provider_id, None)
    _redis.set(MODELS_KEY, json.dumps(stored))
    return {"detail": "已删除"}


@router.post("/providers/{provider_id}/fetch-models", summary="获取模型列表")
async def fetch_models(provider_id: str, _: User = Depends(require_roles(UserRole.admin))):
    """调用对应服务商的 /models 接口，返回可用模型列表。"""
    raw = _redis.get(MODELS_KEY)
    stored: dict = json.loads(raw) if raw else {}
    pdata = stored.get(provider_id, {})
    # 找到预设 base_url
    preset = next((p for p in PRESET_PROVIDERS if p["id"] == provider_id), None)
    base_url = pdata.get("base_url") or (preset["base_url"] if preset else "")
    api_key = pdata.get("api_key", "")
    if not api_key:
        raise HTTPException(400, "请先配置该服务商的 API Key")
    if not base_url:
        raise HTTPException(400, "请先配置 Base URL")
    try:
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        models_resp = await asyncio.wait_for(client.models.list(), timeout=10)
        model_ids = sorted([m.id for m in models_resp.data])
        return {"models": model_ids}
    except Exception as e:
        raise HTTPException(500, f"获取模型列表失败：{str(e)}")


@router.post("/providers/{provider_id}/verify", summary="验证 API Key 有效性")
async def verify_provider(provider_id: str, _: User = Depends(require_roles(UserRole.admin))):
    """发送一个最小 token 请求，验证 key 是否有效。"""
    raw = _redis.get(MODELS_KEY)
    stored: dict = json.loads(raw) if raw else {}
    pdata = stored.get(provider_id, {})
    preset = next((p for p in PRESET_PROVIDERS if p["id"] == provider_id), None)
    base_url = pdata.get("base_url") or (preset["base_url"] if preset else "")
    api_key = pdata.get("api_key", "")
    model = pdata.get("model") or (preset["default_model"] if preset else "")
    if not api_key:
        raise HTTPException(400, "请先配置 API Key")
    try:
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        await asyncio.wait_for(
            client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=1,
            ),
            timeout=15,
        )
        return {"valid": True, "detail": f"验证通过，模型：{model}"}
    except Exception as e:
        return {"valid": False, "detail": str(e)}


def _reload_ai_client():
    """重载 ai_service 的 client，切换到当前激活服务商。"""
    provider = get_active_provider()
    if provider:
        from app.services import ai_service

        ai_service.reload_client(
            api_key=provider["api_key"],
            base_url=provider.get("base_url", ""),
            model=provider.get("model", ""),
        )
