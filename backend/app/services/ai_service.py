import json

from openai import AsyncOpenAI

from app.config import settings

client = AsyncOpenAI(api_key=settings.DEEPSEEK_API_KEY, base_url=settings.DEEPSEEK_BASE_URL)

PROMPT_TEMPLATE = """你是一个专业的题库出题专家，请根据以下要求生成选择题。

知识领域：{topic}
难度级别：{difficulty}（easy=基础概念，medium=理解应用，hard=综合分析）
生成数量：{count} 道
{extra_context}

严格按照以下 JSON 格式输出，不要有任何其他文字：
{{
  "questions": [
    {{
      "content": "题干内容",
      "option_a": "选项A内容",
      "option_b": "选项B内容",
      "option_c": "选项C内容",
      "option_d": "选项D内容",
      "correct_answer": "A",
      "explanation": "解析：正确答案是A，因为..."
    }}
  ]
}}

质量要求：
1. 题干清晰无歧义，长度20-100字
2. 四个选项长度相近，干扰项有真实迷惑性
3. 不使用"以上都是"/"以上都不是"类选项
4. 解析先说结论再解释原理，不超过150字
5. 同批题目知识点均匀覆盖，不重复出题"""


def _build_prompt(topic: str, difficulty: str, count: int, extra_context: str) -> str:
    ctx = f"\n参考资料（请基于以下内容出题）：\n{extra_context}\n" if extra_context else ""
    return PROMPT_TEMPLATE.format(
        topic=topic, difficulty=difficulty, count=count, extra_context=ctx
    )


def _parse(raw: str) -> list[dict]:
    """Extract the questions list from a model response, tolerating ```json fences."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    data = json.loads(text)
    questions = data.get("questions", data if isinstance(data, list) else [])
    if not isinstance(questions, list) or not questions:
        raise ValueError("response contained no questions")
    return questions


async def generate_questions(
    topic: str, difficulty: str, count: int, extra_context: str = ""
) -> list[dict]:
    """Call DeepSeek and return a list of question dicts. Retries the parse once."""
    prompt = _build_prompt(topic, difficulty, count, extra_context)

    last_err: Exception | None = None
    for _ in range(2):  # ponytail: one retry is enough; LLM JSON failures are usually transient
        resp = await client.chat.completions.create(
            model=settings.DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        try:
            return _parse(resp.choices[0].message.content or "")
        except (json.JSONDecodeError, ValueError) as e:
            last_err = e
    raise RuntimeError(f"AI 返回内容解析失败: {last_err}")


SUGGEST_PROMPT = """你是一个专业的题库设计专家。
用户正在为"{bank_title}"创建题库，请推荐 6 个适合出选择题的核心知识点或考点主题。

要求：
1. 每个主题 6-16 个字，简洁具体，适合直接作为出题范围
2. 覆盖该领域的不同方向，不要全部集中在同一子领域
3. 仅输出 JSON，格式如下，不要有任何其他文字：
{{"topics": ["主题1", "主题2", "主题3", "主题4", "主题5", "主题6"]}}"""


async def suggest_topics(bank_title: str) -> list[str]:
    """根据题库标题，让 AI 推荐适合出题的知识点主题列表。"""
    prompt = SUGGEST_PROMPT.format(bank_title=bank_title)
    last_err: Exception | None = None
    for _ in range(2):
        resp = await client.chat.completions.create(
            model=settings.DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.8,
        )
        try:
            data = json.loads(resp.choices[0].message.content or "")
            topics = data.get("topics", [])
            if isinstance(topics, list) and topics:
                return [str(t) for t in topics]
        except (json.JSONDecodeError, ValueError) as e:
            last_err = e
    raise RuntimeError(f"AI 推荐知识点失败: {last_err}")
