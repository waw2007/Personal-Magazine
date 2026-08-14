# Personal Magazine · 个人校园信息智能助理

> **让信息找人，而不是人找信息。**

> 🔧 **开发者 / 接手者**：请先阅读 [HANDOFF.md](./HANDOFF.md)，看完即可上手开发。

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

| 模块 | 说明 | 状态 |
| --- | --- | --- |
| 校园信息雷达 | 8 个站点（7 个 DUT 子站 + 四六级）自动抓取，正文全文喂给 LLM 摘要，主动推送 | ✅ |
| 个性化推荐 | LLM 语义打分（年级/专业/兴趣）+ 时间衰减 + 反馈修正 + 关键词兜底 | ✅ |
| 反馈学习 | 已读/归档行为反向调整推荐权重，越用越懂你 | ✅ |
| 今日简报 | 决策 Agent 把当天信息综合成「总览 + 最多 3 件行动项」 | ✅ |
| 失效/过期检测 | 死链与已过截止日期打标记，推荐自动排除 | ✅ |
| 提醒 Agent | 统一待办清单：聚合「临近截止通知 + 到期倒数日」，主动弹汇总通知 | ✅ |
| 关键词订阅 | 自定义关注主题，命中即高亮 + 主动推送（/watch） | ✅ |
| 截止日期提醒 | deadline 标准化 YYYY-MM-DD，3 天内截止弹系统通知 | ✅ |
| 个人事件管理 | 四六级 / 竞赛等倒数日 + 到期提醒 | ✅ |
| 聊天信息智能助手 | 监控微信 / QQ 群消息 | ⚠️ 规划中（合规风险） |
| 多 Agent 协作 | 抓取 / 理解 / 决策 / 提醒分工 | 🚧 进行中（已有简报 Agent + 提醒 Agent） |

## 4. 目录结构

```
Personal Magazine/
├── README.md                     # 本文档（面向使用者）
├── HANDOFF.md                    # 开发者接手文档
├── start.bat                     # Windows 一键启动
├── *.docx                        # 产品需求 / 技术评估文档
└── CampusAI/
    ├── backend/
    │   ├── main.py               # FastAPI 入口（REST API + 定时抓取）
    │   ├── pipeline.py           # 数据流水线 run_pipeline(sites=None)
    │   ├── scheduler.py          # 各网站抓取频率调度
    │   ├── digest.py             # 今日简报（决策 Agent）
    │   ├── reminders.py          # 提醒 Agent（统一待办清单）
    │   ├── subscriptions.py      # 关键词订阅（关注主题）
    │   ├── feedback.py           # 反馈学习（已读/归档 → 推荐权重）
    │   ├── events.py             # 倒数日事件
    │   ├── changes.py            # 变更检测 + 首次发现日期
    │   ├── requirements.txt
    │   ├── .env                  # DeepSeek key（不提交）
    │   ├── .env.example          # 配置模板
    │   ├── config/websites.json  # 监控网站配置（含 frequency_hours）
    │   ├── data/                 # 爬取结果 JSON（不提交）
    │   ├── crawler/              # 网页爬虫 + 正文抓取
    │   ├── filter/               # 关键词筛选 + 打分
    │   ├── classifier/           # 新闻分类
    │   ├── summarizer/           # DeepSeek 摘要 / 打分 / 简报
    │   ├── recommender/          # 个性化推荐（时间衰减）
    │   └── profile/              # 用户画像
    └── frontend/                 # React + Vite 前端
```

## 5. 技术栈

- **Python 3.11** + **FastAPI** + **Uvicorn**
- **requests** + **BeautifulSoup** + **lxml**（爬虫与解析）
- **chardet**（网页编码自动检测）
- **DeepSeek API**（OpenAI 兼容接口：摘要 / 打分 / 简报）
- **React 19 + Vite**（前端信息流 + 浏览器通知）

## 6. 快速开始

### 6.1 环境准备

```bash
# 后端
cd CampusAI/backend
python -m venv venv
venv/Scripts/activate          # Windows（macOS/Linux 用 source venv/bin/activate）
pip install -r requirements.txt

# 配置 DeepSeek key（必填，否则摘要降级为占位文案）
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY

# 前端
cd ../frontend
npm install
```

### 6.2 一键启动（推荐，Windows）

双击项目根目录的 `start.bat`，自动开两个窗口分别启动后端和前端。

- 前端：http://127.0.0.1:5173
- 接口文档：http://127.0.0.1:8000/docs

想开机自启，把 `start.bat` 的快捷方式丢进 `Win+R` → `shell:startup` 即可。

### 6.3 手动分开跑

```bash
# 终端 1：后端
cd CampusAI/backend
venv/Scripts/python.exe -m uvicorn main:app --port 8000

# 终端 2：前端
cd CampusAI/frontend
npm run dev
```

### 6.4 重新抓数据

```bash
cd CampusAI/backend
venv/Scripts/python.exe pipeline.py
```

或 `POST /pipeline/run`。后端启动后会按各网站 `frequency_hours` 自动增量抓取，无需手动执行。

## 7. API 端点

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/` | 服务状态 |
| GET | `/status` | 系统状态 + 新闻数量 + 新增列表 |
| GET | `/news` | 全部新闻 |
| GET | `/important` | 重要新闻（importance ≥ 8） |
| GET | `/search?q=` | 按关键词搜索 |
| GET | `/latest` | 最新 5 条 |
| GET | `/recommend` | 个性化推荐（含 engine / reason / feedback_factor） |
| POST | `/feedback` | 上报已读/归档反馈（学习个性化） |
| GET | `/feedback` | 查看当前反馈权重 |
| GET | `/digest` | 今日简报（LLM 综合） |
| GET | `/reminders` | 提醒清单（临近截止 + 到期事件，统一待办） |
| GET | `/watch` | 命中关注词的信息（含 matched 命中词） |
| GET | `/subscriptions` | 关注词列表 |
| POST | `/subscriptions` | 添加关注词 |
| DELETE | `/subscriptions/{id}` | 删除关注词 |
| GET | `/category/{category}` | 按分类查看 |
| GET | `/events` | 倒数日列表（含剩余天数） |
| POST | `/events` | 添加倒数日事件 |
| DELETE | `/events/{id}` | 删除倒数日事件 |
| POST | `/pipeline/run` | 手动触发抓取（全量） |
| GET | `/pipeline/status` | 抓取状态 + 各网站下次抓取时间 |

## 8. 数据处理流程

```
爬虫 crawl
   │  抓取配置的站点，提取链接 + 标题日期（支持 content_selector 定位正文容器）
   ▼
筛选 filter
   │  关键词打分（scorer.py），保留 score ≥ 3
   ▼
分类 classifier
   │  教务 / 奖助学金 / 竞赛 / 就业 / 科研 / 其他
   ▼
抓正文 fetch_content
   │  抓详情页正文（含失效检测）
   ▼
摘要 summarizer
   │  DeepSeek 结合「标题 + 正文」生成 summary / deadline / suggestion
   ▼
推荐 recommender
      LLM 语义打分 × 时间衰减，关键词兜底
   ▼
简报 digest
      决策 Agent 综合成「总览 + 行动项」
   ▼
提醒 reminders
      提醒 Agent 聚合「临近截止 + 到期事件」为统一待办，主动弹汇总通知
```

## 9. 配置

- **`config/websites.json`** — 监控网站列表，每项含 `name` / `url` / `type` / `frequency_hours`（抓取频率，小时）/ `keywords` / 可选 `content_selector`（CSS 选择器，只在对应容器内找链接，用于避开页脚噪声，如四六级的 `#Content1`）。
- **`data/user_profile.json`** — 用户画像（年级 / 专业 / 兴趣标签），用于个性化推荐。
- **`data/subscriptions.json`** — 关注词列表（用户在前端「关注」面板增删，用于命中高亮 + 推送）。
- **`data/feedback.json`** — 反馈学习权重（已读/归档的累计计数，自动生成，用于推荐修正）。
- **`backend/.env`** — DeepSeek 配置：`DEEPSEEK_API_KEY`（必填）、`DEEPSEEK_MODEL`（可选，默认 `deepseek-chat`）、`DEEPSEEK_BASE_URL`（可选）。

## 10. 已知问题与待办

- [ ] 聊天群消息监控（微信 / QQ），需评估合规风险
- [ ] 上云部署（当前本地常驻，关机即停）
- [ ] 多 Agent 协作进一步完善（抓取 / 理解 / 决策 / 提醒分工）

## 11. 相关文档

- `Personal Magazine.docx` — 原始创想
- `我理解你的创想.docx` — 概念深化
- `Personal Magazine 需求分析与技术评估.docx` — 需求 + 技术评估
- `Personal Magazine 综合需求分析与技术评估.docx` — 综合版 v1.0（最完整）
