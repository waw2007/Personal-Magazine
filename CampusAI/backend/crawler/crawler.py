import requests
from bs4 import BeautifulSoup
import json
import os
import re
from urllib.parse import urljoin, urlparse
import chardet


# =====================
# 项目路径
# =====================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


# =====================
# 网站配置
# =====================

def load_websites():
    path = os.path.join(
        BASE_DIR,
        "config",
        "websites.json"
    )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# =====================
# 编码检测
# =====================

def decode_html(response):
    content = response.content

    result = chardet.detect(content)
    encoding = result["encoding"]
    confidence = result["confidence"]

    print("检测编码:", encoding, "可信度:", confidence)

    # 优先尝试
    encodings = ["utf-8", encoding, "gb18030", "gbk"]

    for enc in encodings:
        if not enc:
            continue
        try:
            return content.decode(enc)
        except Exception:
            pass

    return content.decode("utf-8", errors="ignore")


# =====================
# 链接清洗规则
# =====================

# 常见导航 / 装饰性标题，不是新闻，直接丢弃
NAV_TITLES = {
    "首页", "首页>>", "English", "EN", "中文",
    "学生", "教工", "校友", "考生与访客",
    "学校简介", "现任领导", "历任领导", "历史沿革",
    "组织机构", "大学文化", "学校地图", "校史云展馆",
    "校园风光", "联系方式",
    "更多", "查看更多", "更多>>", "Read More", "Read More >",
    "上一页", "下一页", "上页", "下页", "尾页", "首 页",
    "A", "A-", "A+",
    "通知公告",  # 栏目名而非具体通知
}

# 导航栏目名通常 ≤ 6 字（如"院情总览""师资队伍"），新闻标题再短也 ≥ 8 字
MIN_TITLE_LEN = 8


def normalize_href(href, base_url):
    """规范化链接：过滤 javascript/mailto/tel/锚点等，仅保留 http(s)。"""
    href = (href or "").strip()
    if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
        return None

    full = urljoin(base_url, href)

    if urlparse(full).scheme not in ("http", "https"):
        return None

    return full


def clean_title(title):
    """折叠连续空白（含换行），去掉首尾空白。"""
    return " ".join((title or "").split())


def is_navigation(title):
    """判断标题是否为导航 / 装饰 / 分页等无效条目。"""
    if not title:
        return True
    if title in NAV_TITLES:
        return True
    if title.isdigit():          # 分页页码，如 "2" "3"
        return True
    if len(title) < MIN_TITLE_LEN:  # 过短：导航栏目 / 装饰性文本
        return True
    return False


# =====================
# 发布日期提取
# =====================

DATE_PATTERN = re.compile(r"^(\d{4})\D{0,2}(\d{1,2})\D{0,2}(\d{1,2})")


def extract_date(title):
    """从标题前缀提取发布日期。

    兼容「2025-1017 / 2026-08 07 / 2026-0807 / 2026年8月7日」等格式；
    提取不到或值非法（如学年范围 2026-2027）返回 None。
    """
    m = DATE_PATTERN.match((title or "").strip())
    if not m:
        return None
    year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not (2000 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31):
        return None
    return f"{year:04d}-{month:02d}-{day:02d}"


# =====================
# 详情页正文抓取 + 失效检测
# =====================

# 常见正文容器选择器（按优先级尝试）
CONTENT_SELECTORS = [
    ".TRS_Editor", ".v_news_content", "#vsb_content", "#vsb_content_2",
    ".article-content", ".article", "article", ".news_content",
    ".content", "#content", ".main-content", ".detail",
]

# 判定「内容已失效/被删除」的文本信号（保守集合，避免误伤）
INVALID_SIGNALS = [
    "已失效", "已删除", "已撤下", "已被删除",
    "页面不存在", "内容不存在", "该文章已删除",
]

# 喂给 LLM 的正文最大长度（控制 token 与成本）
MAX_CONTENT_CHARS = 1500


def extract_content(html):
    """从详情页 HTML 提取正文纯文本，优先命中常见容器，否则退回 body 全文。"""
    soup = BeautifulSoup(html, "lxml")
    for sel in CONTENT_SELECTORS:
        node = soup.select_one(sel)
        if node:
            text = node.get_text(" ", strip=True)
            text = re.sub(r"\s+", " ", text)
            if len(text) >= 50:
                return text
    # 兜底：去掉脚本/样式后取 body 全文
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text(" ", strip=True)
    return re.sub(r"\s+", " ", text)


def fetch_content(url):
    """抓取详情页正文，返回 (content, status_code)。

    - content：正文纯文本（失败为 None），截断到 MAX_CONTENT_CHARS
    - status_code：HTTP 状态码（异常为 None），供失效检测用
    """
    try:
        resp = requests.get(
            url,
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        status = resp.status_code
        if status != 200:
            return None, status
        html = decode_html(resp)
        content = extract_content(html)
        if not content:
            return None, status
        return content[:MAX_CONTENT_CHARS], status
    except Exception as e:
        print("抓取正文失败:", url, e)
        return None, None


def is_invalid_link(content, status):
    """判定链接是否已失效：HTTP 非 200，或正文含失效信号。"""
    if status is not None and status != 200:
        return True
    if not content:
        return False  # 无正文时无法判定，按未失效处理
    return any(sig in content for sig in INVALID_SIGNALS)


# =====================
# 单页面爬取
# =====================

def crawl_page(url):
    print("访问:", url)

    try:
        response = requests.get(
            url,
            timeout=20,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        html = decode_html(response)
        soup = BeautifulSoup(html, "lxml")

        results = []
        seen = set()

        for a in soup.find_all("a"):
            title = clean_title(a.get_text())
            full_url = normalize_href(a.get("href"), url)

            if full_url is None or is_navigation(title):
                continue
            if full_url in seen:
                continue

            seen.add(full_url)
            results.append(
                {
                    "title": title,
                    "url": full_url,
                    "date": extract_date(title)
                }
            )

        return results

    except Exception as e:
        print("访问失败:", e)
        return []


# =====================
# Pipeline 入口
# =====================

def crawl_sites(sites):
    """抓取给定的一组网站，跨站点按 URL 去重。"""
    all_news = []
    seen = set()

    for site in sites:
        print("\n======", site["name"], "======")

        news = crawl_page(site["url"])

        for item in news:
            # 跨站点去重：同一 URL 只保留首次出现
            if item["url"] in seen:
                continue
            seen.add(item["url"])
            item["source"] = site["name"]
            all_news.append(item)

    print("\n获取新闻:", len(all_news), "条")

    return all_news


def crawl():
    """抓取全部网站（全量抓取）。"""
    return crawl_sites(load_websites())


if __name__ == "__main__":
    crawl()
