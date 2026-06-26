"""纯逻辑单测：不依赖数据库/Redis/网络。覆盖历史上出过 bug 的关键路径。"""
import pytest

from app.services.ai_service import _parse
from app.services.file_service import _truncate, HEAD, TAIL, MAX_TEXT
from app.utils.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.utils.time import naive_utcnow


# ---- AI 返回解析 ----
def test_parse_plain_json():
    raw = '{"questions": [{"content": "q", "correct_answer": "A"}]}'
    qs = _parse(raw)
    assert len(qs) == 1 and qs[0]["correct_answer"] == "A"


def test_parse_strips_code_fence():
    raw = '```json\n{"questions": [{"content": "q"}]}\n```'
    assert len(_parse(raw)) == 1


def test_parse_rejects_garbage():
    with pytest.raises((ValueError, Exception)):
        _parse("not json at all")


def test_parse_rejects_empty_questions():
    with pytest.raises(ValueError):
        _parse('{"questions": []}')


# ---- 文件截断 ----
def test_truncate_short_unchanged():
    assert _truncate("hello") == "hello"


def test_truncate_long_keeps_head_and_tail():
    text = "H" * 7000 + "T" * 3000
    out = _truncate(text)
    assert len(out) < MAX_TEXT + 10
    assert out.startswith("H" * HEAD)
    assert out.endswith("T" * TAIL)
    assert "..." in out


# ---- 密码 & JWT ----
def test_password_roundtrip():
    h = hash_password("secret123")
    assert verify_password("secret123", h)
    assert not verify_password("wrong", h)


def test_jwt_carries_sub_and_role():
    tok = create_access_token("uid-7", "editor")
    payload = decode_access_token(tok)
    assert payload["sub"] == "uid-7" and payload["role"] == "editor"


# ---- 时间：必须是 naive（匹配 DB 列）----
def test_naive_utcnow_is_tz_naive():
    assert naive_utcnow().tzinfo is None
