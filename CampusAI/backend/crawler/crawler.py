import requests
from bs4 import BeautifulSoup
import json
import os
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
                    "url": full_url
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
