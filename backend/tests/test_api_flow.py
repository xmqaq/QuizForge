"""API 集成测试（SQLite）：认证、权限、答题判分、错题入库、随机取题一致性。"""
from tests.conftest import auth_headers, make_admin


async def test_register_login_me(client):
    h, user = await auth_headers(client)
    me = await client.get("/auth/me", headers=h)
    assert me.status_code == 200
    assert me.json()["email"] == user["email"]


async def test_duplicate_register_rejected(client):
    h, user = await auth_headers(client)
    dup = await client.post(
        "/auth/register",
        json={"email": user["email"], "username": "other", "password": "secret123"},
    )
    assert dup.status_code == 400


async def test_approve_requires_privilege(client):
    h, user = await auth_headers(client)
    bank = (await client.post("/banks", headers=h, json={"title": "B"})).json()
    q = (
        await client.post(
            "/questions",
            headers=h,
            json={
                "bank_id": bank["id"], "content": "c", "option_a": "a", "option_b": "b",
                "option_c": "c", "option_d": "d", "correct_answer": "A",
            },
        )
    ).json()
    # 普通用户不能审核
    resp = await client.post(f"/questions/{q['id']}/approve", headers=h)
    assert resp.status_code == 403


async def _seed_bank_with_questions(client, h, n=4, answer="B"):
    bank = (await client.post("/banks", headers=h, json={"title": "Quiz"})).json()
    ids = []
    for i in range(n):
        q = (
            await client.post(
                "/questions",
                headers=h,
                json={
                    "bank_id": bank["id"], "content": f"Q{i}", "option_a": "a", "option_b": "b",
                    "option_c": "c", "option_d": "d", "correct_answer": answer,
                },
            )
        ).json()
        await client.post(f"/questions/{q['id']}/approve", headers=h)
        ids.append(q["id"])
    return bank, ids


async def test_quiz_grading_and_wrong_book(client):
    h, user = await auth_headers(client)
    await make_admin(user["id"])
    bank, _ = await _seed_bank_with_questions(client, h, n=3, answer="B")

    s = (await client.post("/quiz/sessions", headers=h,
                           json={"bank_id": bank["id"], "mode": "sequential"})).json()
    qs = (await client.get(f"/quiz/sessions/{s['id']}/questions", headers=h)).json()
    assert len(qs) == 3

    # 第一题答错(A)，其余答对(B)
    for i, q in enumerate(qs):
        ans = "A" if i == 0 else "B"
        r = (await client.post(f"/quiz/sessions/{s['id']}/answer", headers=h,
                               json={"question_id": q["id"], "user_answer": ans})).json()
        assert r["correct_answer"] == "B"
        assert r["is_correct"] == (ans == "B")

    fin = (await client.post(f"/quiz/sessions/{s['id']}/finish", headers=h)).json()
    assert fin["answered_count"] == 3 and fin["correct_count"] == 2
    assert fin["status"] == "finished"

    # 错题本应有那道答错的题
    wrong = (await client.get("/wrong", headers=h)).json()
    assert wrong["total"] == 1
    assert wrong["items"][0]["question_id"] == qs[0]["id"]


async def test_random_quiz_set_is_stable(client):
    """修复点：随机模式下，会话题目在开始时固定，多次获取一致。"""
    h, user = await auth_headers(client)
    await make_admin(user["id"])
    bank, _ = await _seed_bank_with_questions(client, h, n=6, answer="C")

    s = (await client.post("/quiz/sessions", headers=h,
                           json={"bank_id": bank["id"], "mode": "random", "total_questions": 3})).json()
    a = [q["id"] for q in (await client.get(f"/quiz/sessions/{s['id']}/questions", headers=h)).json()]
    b = [q["id"] for q in (await client.get(f"/quiz/sessions/{s['id']}/questions", headers=h)).json()]
    assert len(a) == 3 and a == b


async def test_answer_rejects_foreign_question(client):
    h, user = await auth_headers(client)
    await make_admin(user["id"])
    bank, _ = await _seed_bank_with_questions(client, h, n=2, answer="A")
    # 另一个题库的题
    other, other_ids = await _seed_bank_with_questions(client, h, n=1, answer="A")

    s = (await client.post("/quiz/sessions", headers=h,
                           json={"bank_id": bank["id"], "mode": "sequential"})).json()
    r = await client.post(f"/quiz/sessions/{s['id']}/answer", headers=h,
                          json={"question_id": other_ids[0], "user_answer": "A"})
    assert r.status_code == 400
