import json

from openai import AsyncOpenAI

from app.config import settings

client = AsyncOpenAI(api_key=settings.DEEPSEEK_API_KEY, base_url=settings.DEEPSEEK_BASE_URL)
_active_model = settings.DEEPSEEK_MODEL


def reload_client(api_key: str, base_url: str, model: str = ""):
    """运行时切换 AI 凭证 / 模型（管理员在系统设置里改了配置后调用）。"""
    global client, _active_model
    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    if model:
        _active_model = model

PROMPT_TEMPLATE = """你是一个专业的题库出题专家，请根据以下要求生成选择题。

核心知识点（必须覆盖，可自然延伸）：{topic}
难度级别：{difficulty}（easy=基础概念，medium=理解应用，hard=综合分析）
生成数量：{count} 道
{extra_context}

出题策略：
- 以上述知识点为主干方向，结合实际考试题型自然延伸相关考点
- 不要机械地按知识点平均分配题目数量，以整体覆盖面和质量为准
- 不同知识点之间可以有交叉融合，体现综合考察

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


# ponytail: 保守估算，汉字~2token，英文~1token
_MAX_CONTEXT_CHARS = 6000

_JSON_FORMAT_ERRORS = ("response_format", "json_object", "not support", "unsupported", "invalid", "unknown field")


def _build_prompt(topic: str, difficulty: str, count: int, extra_context: str) -> str:
    if extra_context:
        if len(extra_context) > _MAX_CONTEXT_CHARS:
            head = extra_context[:4500]
            tail = extra_context[-1500:]
            extra_context = head + "\n\n…（中间内容已省略）…\n\n" + tail
        ctx = f"\n参考资料（请基于以下内容出题）：\n{extra_context}\n"
    else:
        ctx = ""
    return PROMPT_TEMPLATE.format(
        topic=topic, difficulty=difficulty, count=count, extra_context=ctx
    )


def _parse(raw: str) -> list[dict]:
    """从模型响应中提取题目列表，兼容 ```json 包裹和裸 JSON 两种格式。"""
    text = raw.strip()

    # 去除 markdown 代码块
    if "```" in text:
        for part in text.split("```"):
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            try:
                data = json.loads(part)
                if isinstance(data, dict) and "questions" in data:
                    questions = data["questions"]
                    if isinstance(questions, list) and questions:
                        return questions
            except (json.JSONDecodeError, ValueError):
                continue

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(text[start:end])
        else:
            raise ValueError(f"无法从响应中提取 JSON：{text[:200]}")

    questions = data.get("questions", data if isinstance(data, list) else [])
    if not isinstance(questions, list) or not questions:
        raise ValueError("response contained no questions")
    return questions


async def generate_questions(
    topic: str, difficulty: str, count: int, extra_context: str = ""
) -> list[dict]:
    """调用 LLM 生成选择题列表。兼容不支持 response_format 的模型。"""
    prompt = _build_prompt(topic, difficulty, count, extra_context)
    last_err: Exception | None = None

    for use_json_format in (True, False):
        kwargs: dict = {
            "model": _active_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
        }
        if use_json_format:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            resp = await client.chat.completions.create(**kwargs)
            return _parse(resp.choices[0].message.content or "")
        except Exception as e:
            err_str = str(e).lower()
            if use_json_format and any(kw in err_str for kw in _JSON_FORMAT_ERRORS):
                continue
            if isinstance(e, (json.JSONDecodeError, ValueError)):
                last_err = e
                continue
            raise

    raise RuntimeError(f"AI 返回内容解析失败: {last_err}")


SUGGEST_PROMPT = """你是一个专业的题库设计专家。
用户正在为"{bank_title}"创建题库，请推荐 6 个适合出选择题的核心知识点或考点主题。

要求：
1. 每个主题 6-16 个字，简洁具体，适合直接作为出题范围
2. 覆盖该领域的不同方向，不要全部集中在同一子领域
3. 仅输出 JSON，格式如下，不要有任何其他文字：
{{"topics": ["主题1", "主题2", "主题3", "主题4", "主题5", "主题6"]}}"""


async def suggest_topics(bank_title: str) -> list[str]:
    """根据题库标题推荐知识点主题列表。兼容不支持 response_format 的模型。"""
    prompt = SUGGEST_PROMPT.format(bank_title=bank_title)
    last_err: Exception | None = None

    for use_json_format in (True, False):
        kwargs: dict = {
            "model": _active_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.8,
        }
        if use_json_format:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            resp = await client.chat.completions.create(**kwargs)
            data = json.loads(resp.choices[0].message.content or "")
            topics = data.get("topics", [])
            if isinstance(topics, list) and topics:
                return [str(t) for t in topics]
            raise ValueError("response contained no topics")
        except Exception as e:
            err_str = str(e).lower()
            if use_json_format and any(kw in err_str for kw in _JSON_FORMAT_ERRORS):
                continue
            if isinstance(e, (json.JSONDecodeError, ValueError)):
                last_err = e
                continue
            raise

    raise RuntimeError(f"AI 推荐知识点失败: {last_err}")
