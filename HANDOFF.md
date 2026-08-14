# Personal Magazine · 项目接手文档

> 目的：让任何新接手的人（包括未来的自己）看完这份文档，就能理解这个项目「为什么存在、现在长什么样、接下来怎么继续做」，无需翻代码考古。

---

## 1. 一句话介绍

**Personal Magazine** 是一个面向大学生个人的「校园信息 AI 助手」：自动抓取学校通知 → 用大模型理解并摘要 → 按重要性排序推荐 → 主动推送提醒。

核心理念只有一句：**让信息找人，而不是人找信息。**

---

## 2. 需求来源

### 2.1 出发点：校园信息环境的痛点

大学生每天面对的信息源超过 10 个（学校官网、教务处、学院网站、班级群、微信群、公众号、邮件……），但信息分散、价值密度低、关键时间被淹没：

| 痛点 | 表现 |
| --- | --- |
| 信息过载 | 重要通知淹没在闲聊、广告、重复转发中 |
| 来源分散 | 数十个平台，每天在多个 App 间切换寻找 |
| 价值密度低 | 大量与自己无关、描述复杂、关键时间被隐藏 |
| 事件易遗忘 | 四六级、竞赛报名、奖学金申请等长周期事件容易错过 |

### 2.2 原始创想

需求源自 4 份 `.docx` 文档（保存在项目根目录，**不公开、不进入 git**）：

- `Personal Magazine.docx` — 原始创想
- `我理解你的创想.docx` — 概念深化
- `Personal Magazine 需求分析与技术评估.docx` — 需求 + 技术评估
- `Personal Magazine 综合需求分析与技术评估.docx` — 综合版 v1.0（最完整）

### 2.3 目标用户

- 首要用户：作者本人（大连理工大学软件学院，智能无人系统技术专业）
- 可扩展：其他高校学生（通过改 `config/websites.json` 适配）

### 2.4 终局愿景

> 大学生版的 **Notion + Perplexity + 日历 + AI Agent** —— 校园场景下的信息中枢与行动外脑。

完整闭环：`发现信息 → 理解信息 → 判断价值 → 制定行动 → 提醒执行`

---

## 3. 预设框架（架构设计）

### 3.1 技术栈

| 层 | 技术 |
| --- | --- |
| 后端 | Python 3.11 + FastAPI + Uvicorn |
| 爬虫 | requests + BeautifulSoup + lxml + chardet |
| AI 摘要 | DeepSeek API（OpenAI 兼容接口） |
| 前端 | React 19 + Vite |
| 存储 | 本地 JSON 文件（MVP 阶段，无数据库） |
| 通知 | 浏览器 Notification API |

### 3.2 核心数据流（Pipeline）

```
爬虫 crawl
   │  抓取 config/websites.json 里配置的网站，提取并去重
   │  extract_date() 从标题前缀正则提取发布时间（如 2025-1017 → 2025-10-17）
   ▼
筛选 filter
   │  基于关键词打分（scorer.py），保留 score ≥ 3 的信息
   ▼
分类 classifier
   │  按标题关键词分为：教务 / 奖助学金 / 竞赛 / 就业 / 科研 / 其他
   ▼
抓正文 fetch_content
   │  对需摘要的条目抓取详情页正文（含失效检测：HTTP 非 200 / 失效信号）
   ▼
摘要 summarizer
   │  调用 DeepSeek 结合「标题 + 正文」生成结构化条目（summary / suggestion / deadline）
   │  deadline 统一为 YYYY-MM-DD，无法确定则 null
   ▼
推荐 recommender
      LLM 语义打分（结合 user_profile.json 的年级/专业/兴趣），关键词匹配兜底
      × 时间衰减因子 _time_factor(date)（7d=1.0 / 14d=0.9 / 30d=0.8 / >30d=0.5）
```

> 发布时间回填链路：标题前缀日期 → `changes.py` 的 `first_seen`（首次抓取日）→ 今天。
> 旧通知因时间衰减自动降权，避免「过期的公示」一直霸占推荐位。
> 失效/过期：死链（HTTP 非 200 或正文含「已删除」等信号）标记 `invalid`，截止日期已过标记 `expired`，两者均不再进入推荐。

最终产物写入 `data/processed_news.json`，由前端通过 REST API 展示。

### 3.3 目录结构

```
Personal Magazine/
├── README.md               # 面向使用者的说明
├── HANDOFF.md              # 本文档（面向接手开发者）
├── LICENSE                 # MIT
├── start.bat               # Windows 一键启动（后端 + 前端）
├── *.docx                  # 原始需求文档（不公开）
└── CampusAI/
    ├── backend/
    │   ├── main.py             # FastAPI 入口：所有路由 + 定时抓取
    │   ├── pipeline.py         # 数据流水线编排 run_pipeline(sites=None)
    │   ├── scheduler.py        # per-site 抓取频率调度（due_sites/mark_crawled）
    │   ├── digest.py           # 今日简报（决策 Agent）
    │   ├── reminders.py        # 提醒 Agent（统一待办清单）
    │   ├── subscriptions.py    # 关键词订阅（关注主题）
    │   ├── feedback.py         # 反馈学习（已读/归档 → 推荐权重）
    │   ├── events.py           # 倒数日事件数据层
    │   ├── requirements.txt
    │   ├── .env                # DeepSeek key（不提交）
    │   ├── .env.example        # 配置模板
    │   ├── config/websites.json # 监控网站列表（含 frequency_hours）
    │   ├── data/               # 数据产物（*.json 均不提交）
    │   ├── crawler/            # 网页爬虫
    │   ├── filter/             # 关键词筛选 + 打分
    │   ├── classifier/         # 新闻分类
    │   ├── summarizer/         # DeepSeek 摘要
    │   ├── recommender/        # 个性化推荐
    │   └── profile/            # 用户画像
    └── frontend/
        ├── package.json
        ├── vite.config.js
        └── src/
            ├── App.jsx                  # 主组件：视图切换 + 轮询通知
            ├── main.jsx
            ├── App.css / index.css
            └── components/
                ├── NewsCard.jsx         # 新闻卡片
                ├── DigestPanel.jsx      # 今日简报面板
                ├── ReminderPanel.jsx    # 提醒面板
                ├── WatchPanel.jsx       # 关注（关键词订阅）面板
                └── EventPanel.jsx       # 倒数日面板
```

### 3.4 数据文件（`backend/data/`）

| 文件 | 内容 | 是否提交 git |
| --- | --- | --- |
| `news.json` | 爬虫原始输出（约 208 条） | ❌ |
| `important_news.json` | 筛选后的重要信息（约 49 条） | ❌ |
| `processed_news.json` | 最终含摘要的数据（前端展示用） | ❌ |
| `events.json` | 倒数日事件（个人数据） | ❌ |
| `subscriptions.json` | 关注词列表（个人数据） | ❌ |
| `feedback.json` | 反馈学习权重（已读/归档计数） | ❌ |
| `user_profile.json` | 用户画像（年级/专业/兴趣） | ❌ |
| `seen.json` | 已推送 URL 基线（变更检测用） | ❌ |
| `site_state.json` | 各网站上次抓取时间（调度用） | ❌ |

> 所有 `data/*.json` 都不提交，跑 `python pipeline.py` 可重新生成；`events.json` / `user_profile.json` / `subscriptions.json` / `feedback.json` 由用户行为自动生成或手动维护。

---

## 4. 目前完成了什么

### 4.1 功能完成度

| 模块 | 状态 | 说明 |
| --- | --- | --- |
| 校园信息爬虫 | ✅ | 8 个站点（7 个 DUT 子站 + 四六级）抓取 + 链接过滤 + 去重，支持 `content_selector` 定位正文容器 |
| 关键词筛选 | ✅ | 基于关键词打分（scorer.py，含推免/复试/大赛/补缓考等新来源词） |
| 新闻分类 | ✅ | 6 类：教务/奖助学金/竞赛/就业/科研/其他 |
| AI 摘要 | ✅ | DeepSeek 生成 summary/suggestion/deadline |
| 个性化推荐 | ✅ | LLM 语义打分（DeepSeek）+ 关键词兜底 |
| 前端信息流 | ✅ | 卡片流 + 分类/搜索 + 浏览器通知弹窗 |
| 已读标记 / 归档 | ✅ | localStorage 持久化：已读置灰、归档移入「已归档」视图 |
| 移动端适配 | ✅ | 600px 断点：搜索占满整行、卡片/操作按钮换行 |
| 倒数日 | ✅ | 事件增删 + 剩余天数 + 到期提醒（3 天内弹通知） |
| 定时抓取 | ✅ | 按网站各自频率自动抓取（per-site）+ 手动全量触发 |
| 网页变更检测 | ✅ | URL 指纹去重，只推送真正新增的通知 |
| 抓取频率配置化 | ✅ | websites.json 配 `frequency_hours`，2h/6h/12h 分频调度 |
| 发布时间提取 | ✅ | 标题前缀正则 + first_seen 回填，卡片展示 📅 日期 |
| 时间衰减推荐 | ✅ | 推荐分 × `_time_factor(date)`，旧通知自动降权 |
| 截止日期提醒 | ✅ | deadline 标准化 YYYY-MM-DD，3 天内截止弹系统通知（去重） |
| 正文全文摘要 | ✅ | 抓取详情页正文喂给 DeepSeek，deadline/摘要质量显著提升 |
| 失效/过期检测 | ✅ | 死链（HTTP 非 200/失效信号）+ 已过截止日期打标记，推荐排除 |
| 今日简报 | ✅ | 决策 Agent 把当天信息综合成「总览 + 最多 3 件行动项」（/digest） |
| 提醒 Agent | ✅ | 统一待办清单：聚合「临近截止 + 到期事件」，主动弹汇总通知（/reminders） |
| 关键词订阅 | ✅ | 自定义关注主题，命中即高亮 + 主动推送（/watch + /subscriptions） |
| 反馈学习 | ✅ | 已读/归档行为反向调整推荐权重，越用越懂你（/feedback） |
| 部署 | ⚠️ | 本地常驻（start.bat）+ GitHub 公开仓库 |

### 4.2 已完成的后端 API

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/` | 服务状态 |
| GET | `/status` | 系统状态 + 新闻数量 |
| GET | `/news` | 全部新闻 |
| GET | `/important` | 重要新闻（importance ≥ 8） |
| GET | `/search?q=` | 关键词搜索 |
| GET | `/latest` | 最新 5 条 |
| GET | `/recommend` | 个性化推荐（含 feedback_factor） |
| POST | `/feedback` | 上报已读/归档反馈 |
| GET | `/feedback` | 查看反馈权重 |
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
| POST | `/pipeline/run` | 手动触发抓取 |
| GET | `/pipeline/status` | 抓取任务状态 + 各网站下次抓取时间 |

### 4.3 尚未完成 / 遗留问题

- [ ] 聊天群消息监控（微信/QQ）—— 见下方「未来方向」，需评估合规

---

## 5. 未来方向（Roadmap）

按优先级排序（「近期」已全部完成）：

### 中期（需要设计）
1. **聊天群消息监控** — 监控微信/QQ 群的关键词，⚠️ 涉及隐私与平台合规，需先评估法律风险
2. **多 Agent 协作** — 抓取、理解、决策、提醒等多个 Agent 分工
3. **信息智能评分模型** — 从规则打分升级为可学习的评分

### 远期
4. **上云部署** — 公网访问 + 24 小时在线（当前是本地常驻，关机即停）
5. **多用户 / 多学校** — 从个人工具走向可配置的通用产品

---

## 6. 如何接手（开发指南）

### 6.1 环境准备

```bash
# 后端（Python 3.11）
cd CampusAI/backend
python -m venv venv
venv/Scripts/activate          # Windows（macOS/Linux: source venv/bin/activate）
pip install -r requirements.txt

# 配置 DeepSeek key（必填，否则摘要降级为占位文案）
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY

# 前端（Node.js）
cd ../frontend
npm install
```

### 6.2 启动

**方式一：一键启动** — 双击项目根目录 `start.bat`（自动开两个窗口）。

**方式二：手动分开跑**
```bash
# 终端 1：后端
cd CampusAI/backend
venv/Scripts/python.exe -m uvicorn main:app --port 8000

# 终端 2：前端
cd CampusAI/frontend
npm run dev
```

访问 http://127.0.0.1:5173（前端），接口文档 http://127.0.0.1:8000/docs。

### 6.3 关键文件地图（改哪里）

| 想做的事 | 改哪个文件 |
| --- | --- |
| 新增监控网站 | `config/websites.json`（噪声多的站点加 `content_selector` 定位容器） |
| 改筛选规则 / 打分 | `filter/scorer.py`、`filter/news_filter.py` |
| 改分类规则 | `classifier/classifier.py` |
| 改摘要逻辑 / 提示词 | `summarizer/summary.py`、`summarizer/deepseek.py` |
| 改推荐逻辑 / 时间衰减 | `recommender/recommend.py`（`_time_factor`、`CANDIDATE_LIMIT` 预筛） |
| 改今日简报 | `digest.py` + `summarizer/deepseek.py`（`generate_digest`） |
| 改提醒逻辑 | `reminders.py`（`build_reminders`）+ 前端 `App.jsx` 的提醒 effect |
| 改关键词订阅 | `subscriptions.py`（`matching_news`）+ 前端 `WatchPanel.jsx` |
| 改反馈学习 | `feedback.py`（`feedback_factor`）+ `recommender/recommend.py` + 前端 `App.jsx` 的 toggleRead/toggleArchive |
| 改正文抓取 / 失效判定 | `crawler/crawler.py`（`fetch_content` / `is_invalid_link`） |
| 改发布时间提取 | `crawler/crawler.py`（`extract_date`）+ `changes.py`（`first_seen`） |
| 改用户画像字段 | `profile/user_profile.py` + `data/user_profile.json` |
| 改倒数日逻辑 | `events.py` |
| 改抓取频率 / 调度 | `scheduler.py` + `config/websites.json` 的 `frequency_hours` |
| 加新 API 路由 | `main.py` |
| 改前端页面 | `frontend/src/App.jsx` 及相关组件 |
| 改前端样式 | `frontend/src/App.css` |

### 6.4 常见开发任务

- **重新抓数据**：`python pipeline.py` 或 `POST /pipeline/run`
- **看数据长啥样**：打开 `data/processed_news.json`（每条含 title/summary/deadline/suggestion/category/keywords/importance 等字段）
- **调试前端**：改 `App.jsx` 后 Vite 热更新自动生效；后端改完需重启 uvicorn（或用 `--reload`）

### 6.5 已知坑与注意事项（重要）

1. **`.env` 千万别提交** — 里面是真实 DeepSeek key，`.gitignore` 已排除，但每次提交前留个心眼。
2. **`.docx` 需求文档不公开** — 已在 `.gitignore` 用 `*.docx` 排除，本地保留即可。
3. **访问 GitHub 需要代理** — 国内直连会超时，需开 Clash（`127.0.0.1:7890`），git 已配全局代理。代理关了 git push/pull 会失败。
4. **Windows 控制台中文乱码** — GBK vs UTF-8 问题。调试时若 print 中文乱码，改把结果写 UTF-8 文件再读。
5. **DeepSeek key 缺失时** — `summarize_news()` 会回退到占位文案，pipeline 不会崩，但摘要质量差。
6. **定时抓取只在后端运行时生效** — 关机即停，这是本地部署的固有限制。

---

## 7. 一句话给接手者的建议

> 从 `pipeline.py` 的 `run_pipeline()` 开始读，顺着 `crawl → filter → classify → summarize → recommend` 五个函数走一遍，就能摸清整个后端脉络；前端只有 `App.jsx` + 两个组件，半天能看完。想加功能，优先从「近期方向」里挑，改动小、见效快。
