# Personal Magazine · 个人校园信息智能助理

> **让信息找人，而不是人找信息。**

一个面向大学生个人的「信息雷达 + 提醒中枢」，用 AI 自动完成校园信息的**收集、理解、筛选、关联、提醒**，把学生的注意力从"搜索信息"里释放出来，投入到"利用信息做出行动"上。

> 项目别名：Campus AI Agent · Student OS · UniRadar · My Academic Assistant

---

## 1. 背景与痛点

大学校园信息环境高度碎片化，学生每天面对的信息源超过 10 个——学校官网、教务处、学院网站、书院通知、班级群、QQ 群、微信群、邮件、公众号……信息存在，但学生**无法及时发现**。典型痛点：

| 痛点 | 表现 |
| --- | --- |
| 信息过载 | 重要通知淹没在闲聊、广告、重复转发中 |
| 来源分散 | 数十个平台，每天在多个 App 间切换寻找 |
| 价值密度低 | 大量与自己无关、描述复杂、关键时间被隐藏 |
| 事件易遗忘 | 四六级、竞赛报名、奖学金申请等长周期、多阶段事件容易错过 |

## 2. 产品定位

终局愿景：**大学生版的 Notion + Perplexity + 日历 + AI Agent**——学生校园场景下的信息中枢与行动外脑。

完整的认知-行动闭环：

```
发现信息 → 理解信息 → 判断价值 → 制定行动 → 提醒执行
```

## 3. 功能模块

| 模块 | 目标 | 状态 |
| --- | --- | --- |
| 校园信息雷达 | 监控网站，按关键词筛选，AI 摘要，主动推送 | ✅ React 前端 + AI 摘要 + 通知弹窗 |
| 聊天信息智能助手 | 监控微信 / QQ 群消息，筛选关注的人与关键词 | 📋 规划中（含合规风险） |
| 个人事件管理 | 四六级 / 竞赛 / 奖学金等倒数日提醒 + 到期提醒 | ✅ 倒数日卡片 + 浏览器提醒 |
| 信息智能评分与用户画像 | 按兴趣与重要度排序推荐 | ✅ 简单实现（关键词匹配） |
| 多 Agent 协作 | 多智能体分工协作 | 📋 规划中 |

## 4. 目录结构

```
Personal Magazine/
├── README.md
├── *.docx                        # 产品需求 / 技术评估文档
└── CampusAI/
    └── backend/
        ├── main.py               # FastAPI 入口（REST API）
        ├── pipeline.py           # 数据处理流水线
        ├── requirements.txt      # 依赖清单
        ├── api/news.py           # 额外路由（未接入 main.py）
        ├── config/websites.json  # 监控网站配置
        ├── data/                 # 爬取结果 JSON
        ├── crawler/              # 网页爬虫
        ├── filter/               # 关键词筛选 + 打分
        ├── classifier/           # 新闻分类
        ├── summarizer/           # 摘要生成（DeepSeek）
        ├── recommender/          # 个性化推荐
        ├── profile/              # 用户画像
        └── services/             # 数据服务层
    └── frontend/                 # React + Vite 前端
```

## 5. 技术栈

- **Python 3.11** + **FastAPI**（REST API）+ **Uvicorn**
- **requests** + **BeautifulSoup** + **lxml**（爬虫与解析）
- **chardet**（网页编码自动检测）
- **DeepSeek API**（OpenAI 兼容接口，生成新闻摘要与行动建议）
- **React 19 + Vite**（前端，通知卡片信息流 + 浏览器通知弹窗）

## 6. 快速开始

### 6.1 创建环境并安装依赖

```bash
cd CampusAI/backend
python -m venv venv
venv/Scripts/activate          # Windows（macOS/Linux 用 source venv/bin/activate）
pip install -r requirements.txt
```

### 6.2 运行数据处理流水线

```bash
python pipeline.py
```

依次执行：**抓取 → 筛选 → 分类 → 摘要**，结果写入 `data/` 目录。

### 6.3 启动 API 服务

```bash
uvicorn main:app --reload
```

访问 http://127.0.0.1:8000/docs 查看交互式接口文档。

### 6.4 启动前端

```bash
cd CampusAI/frontend
npm install
npm run dev
```

访问 http://127.0.0.1:5173 查看通知信息流（需先启动后端）。

### 6.5 一键启动（Windows）

双击项目根目录的 `start.bat`，会自动开两个窗口分别启动后端和前端。想开机自启的话，把它的快捷方式丢进 `Win+R` → `shell:startup` 文件夹即可。

## 7. API 端点

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/` | 服务状态 |
| GET | `/status` | 系统状态 + 新闻数量 |
| GET | `/news` | 全部新闻 |
| GET | `/important` | 重要新闻（importance ≥ 8） |
| GET | `/search?q=` | 按关键词搜索 |
| GET | `/latest` | 最新 5 条 |
| GET | `/recommend` | 个性化推荐（结合用户画像） |
| GET | `/category/{category}` | 按分类查看 |
| GET | `/events` | 倒数日事件列表（含剩余天数 / 是否临近） |
| POST | `/events` | 添加倒数日事件 |
| DELETE | `/events/{id}` | 删除倒数日事件 |
| POST | `/pipeline/run` | 手动触发数据抓取 |
| GET | `/pipeline/status` | 抓取任务状态 |

## 8. 数据处理流程

```
爬虫 crawl
   │  抓取 config/websites.json 中配置的网站，提取所有链接
   ▼
筛选 filter
   │  基于关键词打分（scorer.py），保留 score ≥ 3 的信息
   ▼
分类 classifier
   │  按标题关键词分为：教务 / 奖助学金 / 竞赛 / 就业 / 科研 / 其他
   ▼
摘要 summarizer
   │  调用 DeepSeek 生成结构化条目（summary / suggestion / deadline）
   ▼
推荐 recommender
      结合 user_profile.json 的兴趣标签打分排序
```

### 8.1 定时抓取

后端启动后会**每天 08:00 自动跑一遍**流水线（无需手动执行 `pipeline.py`）；也可随时 `POST /pipeline/run` 手动触发，`GET /pipeline/status` 查看最近一次运行结果。定时任务只在后端进程运行时生效。
```

## 9. 配置

- **`config/websites.json`** — 监控网站列表，每项含 `name` / `url` / `type` / `keywords`。
- **`data/user_profile.json`** — 用户画像（年级 / 专业 / 兴趣标签），用于个性化推荐。
- **`backend/.env`** — DeepSeek 配置（复制 `.env.example` 填写）：`DEEPSEEK_API_KEY`（必填）、`DEEPSEEK_MODEL`（可选，默认 `deepseek-chat`）。未配置时摘要自动降级为占位文案。

## 10. 已知问题与待办

- [x] 爬虫精确选择器 + 去重（已重写 `crawler.py`，导航垃圾 1700+ → 79 条）
- [x] LLM 摘要接入 DeepSeek（已用真实 key 端到端验证，`summary`/`suggestion`/`deadline` 均为 AI 生成）
- [ ] `api/news.py` 路由未挂载到 `main.py`（`include_router` 缺失）
- [x] React 前端信息流 + 浏览器通知弹窗（`frontend/`）
- [x] 事件倒数日模块（四六级 / 竞赛等，含到期提醒）
- [ ] 聊天群消息监控（微信 / QQ）待实现，需评估合规风险
- [ ] 缺少配置化抓取频率、网页变更检测、失效检测

## 11. 相关文档

- `Personal Magazine.docx` — 原始创想
- `我理解你的创想.docx` — 概念深化
- `Personal Magazine 需求分析与技术评估.docx` — 需求 + 技术评估
- `Personal Magazine 综合需求分析与技术评估.docx` — 综合版 v1.0（最完整）
