"""端到端验证脚本：注册 → 登录 → 建题库 → AI 出题 → 轮询 → 查题目。

用法：
    确保后端(8000)、postgres、redis、celery 均已启动，且配置了 DEEPSEEK_API_KEY，然后：
    python test_api.py
"""
import sys
import time
import uuid

import httpx

BASE = "http://localhost:8000/api/v1"


def show(step: str, resp: httpx.Response) -> dict:
    body = ""
    try:
        body = resp.json()
    except Exception:
        body = resp.text[:200]
    summary = str(body)
    print(f"[{step}] {resp.status_code} -> {summary[:300]}")
    return body if isinstance(body, dict) else {}


def main() -> int:
    suffix = uuid.uuid4().hex[:8]
    email = f"tester_{suffix}@example.com"
    username = f"tester_{suffix}"
    password = "secret123"

    with httpx.Client(timeout=30) as c:
        # 1. register
        r = c.post(f"{BASE}/auth/register", json={
            "email": email, "username": username, "password": password,
        })
        show("register", r)
        r.raise_for_status()

        # 2. login (OAuth2 form: username 字段填邮箱)
        r = c.post(f"{BASE}/auth/login", data={"username": email, "password": password})
        login = show("login", r)
        r.raise_for_status()
        token = login["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. me
        r = c.get(f"{BASE}/auth/me", headers=headers)
        show("me", r)
        r.raise_for_status()

        # 4. create bank
        r = c.post(f"{BASE}/banks", headers=headers, json={
            "title": "网络安全", "description": "Web 安全题库", "status": "published",
        })
        bank = show("create_bank", r)
        r.raise_for_status()
        bank_id = bank["id"]

        # 5. submit AI generation
        r = c.post(f"{BASE}/ai/generate", headers=headers, json={
            "bank_id": bank_id, "topic": "SQL注入", "difficulty": "medium",
            "count": 3, "auto_approve": True,
        })
        task = show("ai_generate", r)
        r.raise_for_status()
        task_id = task["task_id"]

        # 6. poll task up to 60s
        status = None
        for _ in range(30):
            r = c.get(f"{BASE}/ai/task/{task_id}", headers=headers)
            state = show("task_poll", r)
            status = state.get("status")
            if status in ("done", "failed"):
                break
            time.sleep(2)

        if status != "done":
            print(f"!! 任务未完成 (status={status})，请检查 celery / DEEPSEEK_API_KEY")
            return 1

        # 7. list generated questions
        r = c.get(f"{BASE}/questions", headers=headers, params={"bank_id": bank_id})
        data = show("list_questions", r)
        r.raise_for_status()
        print(f"== 成功：题库 {bank_id} 共生成 {data.get('total')} 道题")
        return 0


if __name__ == "__main__":
    sys.exit(main())
