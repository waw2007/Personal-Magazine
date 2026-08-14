import json
import os

import requests


# =====================
# 项目路径
# =====================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


# =====================
# .env 加载（不覆盖已有环境变量）
# =====================

def load_env_file():
    env_path = os.path.join(BASE_DIR, ".env")
    if not os.path.exists(env_path):
        return

    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if key and key not in os.environ:
                os.environ[key] = value.strip().strip('"').strip("'")


load_env_file()


# =====================
# DeepSeek 配置
# =====================

DEEPSEEK_BASE_URL = os.environ.get(
    "DEEPSEEK_BASE_URL",
    "https://api.deepseek.com"
)

# 模型名可配置：deepseek-chat（默认）/ deepseek-v4-flash / deepseek-v4-pro
DEEPSEEK_MODEL = os.environ.get(
    "DEEPSEEK_MODEL",
    "deepseek-chat"
)


def load_api_key():
    return os.environ.get("DEEPSEEK_API_KEY")


# =====================
# 调用 DeepSeek（OpenAI 兼容接口）
# =====================

def chat(messages, temperature=0.3, max_tokens=600):
    """调用 DeepSeek chat 接口，返回文本内容；失败返回 None。"""
    key = load_api_key()
    if not key:
        print("[DeepSeek] 未配置 DEEPSEEK_API_KEY，跳过 LLM 摘要")
        return None

    try:
        resp = requests.post(
            f"{DEEPSEEK_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json={
                "model": DEEPSEEK_MODEL,
                "messages": messages,
                "response_format": {"type": "json_object"},
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print("[DeepSeek] 调用失败:", e)
        return None


# =====================
# 摘要生成
# =====================

SYSTEM_PROMPT = (
    "你是大学生校园信息助理，擅长把校园通知提炼成简洁摘要与可执行建议。"
    "请严格只输出一个 JSON 对象，不要输出任何多余文字或代码块。"
    'JSON 结构：{"summary": "2-3句摘要（结合标题与正文）", '
    '"deadline": "截止日期，格式严格为 YYYY-MM-DD（如 2026-08-20）。'
    '只提取「截止 / 结束 / 最后」的时间，例如报名截止、提交截止、申请截止、公示截止；'
    '绝不要把「开始 / 启动 / 开通」时间当成截止日期。'
    '若正文只有开始时间而没有明确截止时间，则填 null", '
    '"suggestion": "一句话行动建议"}'
)


def summarize_news(title, keywords, category, source, content=""):
    """基于标题 + 正文，用 LLM 生成摘要；失败返回 None。"""
    user_prompt = (
        f"来源：{source}\n"
        f"分类：{category}\n"
        f"命中关键词：{keywords}\n"
        f"标题：{title}\n"
    )
    if content:
        user_prompt += f"正文：{content}\n"

    content = chat(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
    )

    if not content:
        return None

    # 防御性解析：剥离可能的 markdown 代码块包裹
    content = content.strip()
    if content.startswith("```"):
        content = content.strip("`")
        if content.startswith("json"):
            content = content[4:]

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        print("[DeepSeek] 返回内容无法解析为 JSON:", content[:100])
        return None


# =====================
# 个性化推荐打分
# =====================

RANK_SYSTEM_PROMPT = (
    "你是大学生校园信息助理，负责判断每条校园通知与一位特定学生的相关程度。"
    "请严格只输出一个 JSON 对象，不要输出任何多余文字或代码块。"
    'JSON 结构：{"rankings": [{"id": 数字, "score": 0到10的整数, "reason": "一句话理由"}]}'
    "score 越高代表越相关、越值得优先处理；请结合用户年级/专业/兴趣做语义判断，"
    "不要只看关键词字面匹配（例如本科生不应被「研究生预报名」打高分）。"
)


def rank_news(profile, items):
    """用 LLM 为候选新闻批量打分（0-10），返回 {id: (score, reason)}；失败返回 None。"""
    if not items:
        return {}

    lines = []
    for it in items:
        summary = (it.get("summary") or "")[:60]
        lines.append(
            f"[{it.get('id')}] {it.get('category', '其他')} | "
            f"{it.get('title', '')} | {summary}"
        )

    user_prompt = (
        f"用户画像：{profile.get('grade', '')} / {profile.get('major', '')}，"
        f"兴趣：{', '.join(profile.get('interests', []))}\n"
        "候选通知：\n" + "\n".join(lines)
    )

    content = chat(
        [
            {"role": "system", "content": RANK_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=1000,
    )

    if not content:
        return None

    # 防御性解析：剥离可能的 markdown 代码块包裹
    content = content.strip()
    if content.startswith("```"):
        content = content.strip("`")
        if content.startswith("json"):
            content = content[4:]

    try:
        data = json.loads(content)
    except (json.JSONDecodeError, AttributeError):
        print("[DeepSeek] 推荐打分返回无法解析为 JSON:", content[:100])
        return None

    result = {}
    for r in data.get("rankings", []):
        try:
            result[int(r["id"])] = (int(r.get("score", 0)), r.get("reason", ""))
        except (KeyError, ValueError, TypeError):
            continue
    return result


# =====================
# 今日简报（决策/综合 Agent）
# =====================

DIGEST_SYSTEM_PROMPT = (
    "你是大学生校园信息助理，负责把当天最重要的校园信息整理成一份「今日简报」。"
    "请严格只输出一个 JSON 对象，不要输出任何多余文字或代码块。"
    'JSON 结构：{"overview": "一句话总览今天最值得关注的事", '
    '"items": [{"title": "标题", "why": "为什么与你相关", "action": "建议行动", "deadline": "截止日期(YYYY-MM-DD)或 null"}]}'
    "items 最多 3 条，只挑真正需要用户行动或注意的事项，宁缺毋滥；"
    "已经过期的信息不要纳入。"
)


def generate_digest(profile, items):
    """基于已排名的候选，用 LLM 生成今日简报；失败返回 None。"""
    if not items:
        return None

    lines = []
    for it in items:
        lines.append(
            f"[{it.get('category', '其他')}] {it.get('title', '')} | "
            f"摘要：{(it.get('summary') or '')[:60]} | "
            f"截止：{it.get('deadline') or '无'}"
        )

    user_prompt = (
        f"用户画像：{profile.get('grade', '')} / {profile.get('major', '')}，"
        f"兴趣：{', '.join(profile.get('interests', []))}\n"
        "今日候选（已按相关度排序）：\n" + "\n".join(lines)
    )

    content = chat(
        [
            {"role": "system", "content": DIGEST_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=800,
    )

    if not content:
        return None

    content = content.strip()
    if content.startswith("```"):
        content = content.strip("`")
        if content.startswith("json"):
            content = content[4:]

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        print("[DeepSeek] 简报返回无法解析为 JSON:", content[:100])
        return None
