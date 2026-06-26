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
