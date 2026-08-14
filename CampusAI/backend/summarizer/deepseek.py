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
    'JSON 结构：{"summary": "2-3句摘要", "deadline": "截止日期，无则填 null", '
    '"suggestion": "一句话行动建议"}'
)


def summarize_news(title, keywords, category, source):
    """基于标题等元信息，用 LLM 生成摘要；失败返回 None。"""
    user_prompt = (
        f"来源：{source}\n"
        f"分类：{category}\n"
        f"命中关键词：{keywords}\n"
        f"标题/内容：{title}\n"
    )

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
