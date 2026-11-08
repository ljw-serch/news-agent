# AI 新闻资讯平台（news-agent）

一个前后端分离的新闻资讯与 AI Agent 平台：用户可以浏览、搜索、收藏新闻，查看 AI 摘要与热榜；管理员可以发布新闻、管理用户、查看运营数据；内置的新闻智能助手可以**直接调用数据库工具**回答问题，而不是凭空生成内容。

- 后端：FastAPI + SQLAlchemy 2.0（全异步）+ MySQL + Redis + OpenAI 兼容大模型
- 前端：Vue 3 + Vite + Pinia + Vue Router + Vant
- 文档索引：[接口文档](API接口文档.md) ｜ [数据库设计](数据库设计.md) ｜ [系统设计](系统设计.md)

---

## 1. 项目简介

传统新闻站点的 AI 功能大多停留在"把正文丢给模型做摘要"，容易出现答非所问、编造数据的问题。本项目把 AI 做成一个**有工具、有边界**的 Agent：

1. 模型只能通过 9 个受控工具（检索、热榜、详情、摘要、统计、趋势、分类、分类统计、简报）读取数据库；
2. System Prompt 明确禁止使用模型自身知识编造新闻，查不到就如实说"数据库中没有找到相关新闻"；
3. 未配置大模型或调用失败时，自动降级为**本地规则引擎**，仍能查库、出热榜、出统计，页面不会白屏；
4. 前端以 SSE 流式接收"思考中 → 调用工具 → 生成回答"的全过程。

### 1.1 功能一览

| 端 | 功能 |
| --- | --- |
| 用户端 | 新闻列表（分类/关键词/作者筛选、最新/最热排序）、新闻详情、相关推荐、热榜、AI 摘要、每日简报、热榜解读、AI 对话（流式）、收藏、浏览历史、个人资料、修改密码、主题切换、中英文切换 |
| 管理端 | 数据总览（新闻量/阅读量/收藏/用户数/发布趋势）、新闻管理（增删改、封面上传、批量生成摘要）、用户管理（增删改、禁用、角色调整） |
| AI 能力 | 新闻摘要（100–180 字 + 40 字看点）、每日/区间简报、热榜解读、Agent 多轮工具调用、SSE 流式输出、无 Key 本地降级 |

### 1.2 角色与权限

| 角色 | 说明 | 可见范围 |
| --- | --- | --- |
| 游客 | 未登录 | 仅登录/注册页（前端强制跳转） |
| 普通用户 `user` | 默认注册角色 | 新闻、详情、热榜、AI 助手、收藏、历史、设置、个人资料 |
| 管理员 `admin` | 由种子数据或管理员创建 | 仅数据总览、新闻管理、用户管理三个页面 |

> 前后端双重校验：前端路由守卫按 `meta.requiresAdmin / requiresUser` 拦截；后端用 `get_current_admin` 依赖校验角色，普通用户即使直接调接口也会被拒（`code=403`）。

---

## 2. 技术栈

### 2.1 后端

| 类别 | 选型 | 说明 |
| --- | --- | --- |
| Web 框架 | FastAPI ≥0.115 | 原生支持异步、自动生成 OpenAPI 文档 |
| ASGI | Uvicorn ≥0.30 | 开发用 `--reload`，生产建议多 worker + Nginx |
| ORM | SQLAlchemy 2.0（async） | `Mapped[]` 声明式模型，`AsyncSession` |
| 驱动 | asyncmy ≥0.2.10 | MySQL 异步驱动，配合 greenlet |
| 校验 | Pydantic v2 + pydantic-settings | 请求/响应模型与环境变量 |
| 认证 | PyJWT（HS256） + passlib[bcrypt] | 无状态 JWT，密码 bcrypt 哈希 |
| 缓存 | redis ≥5（redis.asyncio） | 可选，连接失败自动降级 |
| 大模型 | openai ≥1.50（AsyncOpenAI） | OpenAI 兼容协议，可换任意兼容服务商 |
| 文件 | python-multipart | 图片上传（白名单 + 10MB 限制） |

### 2.2 前端

| 类别 | 选型 | 说明 |
| --- | --- | --- |
| 框架 | Vue 3.5（`<script setup>`） | 组合式 API |
| 构建 | Vite 7 | 开发代理 `/api`、`/uploads`，SSE 关闭缓冲 |
| 状态 | Pinia 3 | 用户、主题、语言三个 store |
| 路由 | Vue Router 4 | 角色守卫 + 旧路径兼容重定向 |
| UI | Vant 4 | 移动端优先组件库 |
| 请求 | Axios 1.12 | 统一拦截器：注入 Token、解包 envelope、401 跳登录 |
| 流式 | fetch + ReadableStream | 手动解析 SSE，不依赖 EventSource（需自定义 Header） |
| Markdown | marked + DOMPurify | AI 回答渲染前做 XSS 清洗 |
| 国际化 | vue-i18n 9 | zh-CN / en-US |

### 2.3 数据与外部服务

| 组件 | 用途 | 是否必需 |
| --- | --- | --- |
| MySQL 8.x（实际连接 `news_app_v2`，utf8mb4） | 业务主库 | 必需 |
| Redis | 分类/热榜/统计/简报缓存 | 可选，缺失自动降级 |
| OpenAI 兼容 LLM | 摘要、简报、热榜解读、Agent | 可选，缺失走本地引擎 |
| 本地磁盘 `backend/uploads/` | 图片存储 | 必需（可替换为对象存储） |

---

## 3. 系统架构

```mermaid
flowchart LR
    subgraph Client["浏览器"]
        V["Vue 3 页面<br/>用户端 / 管理端"]
    end

    subgraph API["FastAPI 应用"]
        R["路由层 app/api<br/>8 个 Router / 45 个接口"]
        D["依赖层<br/>JWT 解析 · 角色守卫"]
        S["业务层 app/services<br/>新闻 · 用户 · 统计 · AI Agent"]
        M["模型层 app/models<br/>SQLAlchemy 2.0"]
        E["统一响应 / 全局异常"]
    end

    subgraph Infra["基础设施"]
        DB[("MySQL 8<br/>news_app_v2")]
        RD[("Redis<br/>缓存（可选）")]
        LLM["LLM 服务<br/>OpenAI 兼容"]
        FS["uploads<br/>本地图片"]
    end

    V -->|"HTTP / SSE"| R
    R --> D --> S --> M --> DB
    S -->|"cache_get / set"| RD
    S -->|"chat.completions"| LLM
    R --> FS
```

分层职责：路由层只做参数接收与响应包装；业务层承载全部规则；模型层只描述表结构；公共层统一 `{code, message, data}` 与异常映射。

### 3.1 目录结构

```
news- agent/
├── backend/
│   ├── app/
│   │   ├── api/            # 路由：auth user news favorite history stats ai files
│   │   ├── services/       # 业务：auth user news favorite history stats
│   │   │                   #       ai summary hotspot chat agent agent_tools
│   │   ├── models/         # ORM：user/news/interaction
│   │   ├── schemas/        # Pydantic 请求响应模型
│   │   ├── dependencies/   # get_current_user / get_current_admin / get_optional_user
│   │   ├── common/         # Response / PageData / BusinessException / 异常处理器
│   │   ├── utils/          # jwt / password / cache
│   │   ├── config.py       # Settings（环境变量）
│   │   ├── database.py     # 引擎、Session、建表、轻量迁移、种子数据
│   │   └── main.py         # 应用入口、CORS、静态目录、生命周期
│   ├── uploads/            # 上传图片（.gitkeep 占位）
│   ├── requirements.txt
│   └── .env                # 本地配置（已被 .gitignore 忽略）
├── frontend/
│   ├── src/
│   │   ├── api/            # 与后端一一对应的请求封装
│   │   ├── views/          # 用户页面 + views/admin 管理页面
│   │   ├── components/     # NewsCard / TrendChart / StatCard / NavList / EmptyState
│   │   ├── layouts/        # Layout.vue（导航 + 主题 + 语言）
│   │   ├── router/         # 路由表 + 角色守卫
│   │   ├── store/          # user / theme / language
│   │   ├── utils/          # request / auth / user / format
│   │   ├── i18n/           # zh-CN / en-US
│   │   └── assets/css/     # global.css（CSS 变量主题）
│   ├── dist/               # 已构建产物
│   ├── vite.config.js
│   └── package.json
├── 数据库sql文件/
│   ├── database.sql        # 建库建表（2026-11 自实库反向导出，不含业务数据）
│   └── migration_v2.sql    # 旧库升级脚本（role/status/summary 等字段）
└── docs/
    ├── README.md             # 本文件（项目说明）
    ├── API接口文档.md
    ├── 数据库设计.md
    └── 系统设计.md
```

---

## 4. 快速开始

### 4.1 环境要求

| 依赖 | 版本 |
| --- | --- |
| Python | 3.11+（当前虚拟环境为 3.13） |
| Node.js | 18+ |
| MySQL | 8.x（当前连接 `news_app_v2`，字符集 `utf8mb4`） |
| Redis | 5+（可选） |

### 4.2 初始化数据库

方式一：SQL 全量导入（推荐全新环境）

```bash
mysql -u root -p < "数据库sql文件/database.sql"
```

> 📌 **说明**：脚本建的是 `news_app_v2`，与 `backend/.env` 的 `DATABASE_URL` 一致；内容为表结构（自实际库反向导出），不含业务数据。8 个分类与 `admin`/`user` 两个账号由后端启动时自动写入，导入后直接启动即可。脚本含 `DROP TABLE IF EXISTS`，**不要在有数据的库上执行**。

方式二：由后端自动建表（不导入 SQL 也能跑）

```bash
cd backend
source .venv/bin/activate
python -m app.database
```

> 启动时也会自动执行 `init_db()`：建表 → 补齐旧库缺失字段（`user.role/status`、`news.summary/summary_time/highlight`）→ 写入 8 个分类与 `admin`/`user` 两个演示账号，已有的新闻数据不会被覆盖。

### 4.3 启动后端

```bash
cd backend
source .venv/bin/activate          # 首次部署：python3 -m venv .venv
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- 接口根地址：<http://127.0.0.1:8000/api>
- Swagger：<http://127.0.0.1:8000/docs> ｜ ReDoc：<http://127.0.0.1:8000/redoc>
- 健康检查：<http://127.0.0.1:8000/health> → `{"status":"ok","database":true,"ai":true|false}`

### 4.4 启动前端

```bash
cd frontend
npm install
npm run dev        # http://127.0.0.1:5173
npm run build      # 产物在 frontend/dist
npm run preview    # 预览构建产物 http://127.0.0.1:4173
```

Vite 已配置开发代理：`/api` 与 `/uploads` 转发到 `127.0.0.1:8000`，并对 `text/event-stream` 关闭 `cache-control` 与 `x-accel-buffering`，保证 SSE 不被缓冲。

### 4.5 演示账号

| 用户名 | 密码 | 角色 |
| --- | --- | --- |
| `admin` | `123456` | 管理员 |
| `user` | `123456` | 普通用户 |

> 两个账号的密码哈希在 `database.sql` 与 `init_db()` 中一致，均为 `123456`。生产环境请立即修改，并更换 `JWT_SECRET_KEY`。

---

## 5. 配置说明

配置来源优先级：环境变量 > `backend/.env` > `app/config.py` 默认值（`pydantic-settings`，大小写不敏感）。

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `DATABASE_URL` | `mysql+asyncmy://root:***@127.0.0.1:3306/news_app_v2?charset=utf8mb4` | 异步 MySQL 连接串，务必使用 `mysql+asyncmy` |
| `REDIS_URL` | `redis://127.0.0.1:6379/0` | 缓存地址 |
| `REDIS_ENABLED` | `true` | 置 `false` 可强制关闭缓存 |
| `JWT_SECRET_KEY` | `change-me-in-env` | **必须修改**，泄露等同登录凭证泄露 |
| `JWT_ALGORITHM` | `HS256` | 签名算法 |
| `JWT_EXPIRE_HOURS` | `72` | Token 有效期（小时） |
| `LLM_API_KEY` | 空 | 为空则全站走本地降级引擎 |
| `LLM_BASE_URL` | `https://api.agnes-ai.cn/v1` | OpenAI 兼容地址 |
| `LLM_MODEL` | `agnes-2.5-flash` | 模型名 |
| `LLM_TIMEOUT` | `90` | 单次调用超时（秒） |
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173,...` | 逗号分隔的允许来源 |
| `DEBUG` | `true` | 调试开关 |

代码内常量（`config.py`）：

| 常量 | 值 | 作用 |
| --- | --- | --- |
| `MAX_FILE_SIZE` | 10MB | 上传大小上限 |
| `ALLOWED_EXTENSIONS` | jpg/jpeg/png/gif/webp/svg | 上传类型白名单 |
| `MAX_PAGE_SIZE` | 100 | 列表分页上限 |
| `CACHE_TTL_CATEGORY` | 7200s | 分类缓存 |
| `CACHE_TTL_HOT` | 300s | 热榜缓存 |
| `CACHE_TTL_STATS` | 120s | 统计缓存 |
| `CACHE_TTL_DIGEST` | 600s | 简报/热榜解读缓存 |

### 5.1 AI 两种运行模式

| 模式 | 触发条件 | 行为 |
| --- | --- | --- |
| LLM 模式 | `LLM_API_KEY` 非空 | Agent 通过 function calling 调 9 个工具；摘要/简报/热榜解读由模型生成 |
| 本地模式 | 未配置 Key，或调用抛 `AIUnavailable / AIError` | 规则引擎解析意图：ID 摘要 / 热榜 / 统计 / 简报 / 分类 / 关键词检索；摘要退化为抽取式 |

无论哪种模式，`/api/ai/status` 都会返回 `{"enabled":bool,"mode":"llm|local",...}`，前端据此提示。

---

## 6. 页面与路由

| 路径 | 页面 | 权限 |
| --- | --- | --- |
| `/login`、`/register` | 登录、注册 | 公开（已登录会跳回落地页） |
| `/manager/news` | 新闻资讯列表 | 登录 |
| `/manager/news/:id` | 新闻详情 | 登录 |
| `/manager/hot` | 热榜 | 登录 |
| `/manager/ai-chat` | AI 智能助手（流式） | 登录 |
| `/manager/favorite` | 我的收藏 | 登录 |
| `/manager/history` | 浏览历史 | 登录 |
| `/manager/settings` | 偏好设置（主题/语言） | 登录 |
| `/manager/profile` | 个人资料 | 登录 |
| `/manager/password` | 修改密码 | 登录 |
| `/manager/admin/home` | 数据总览 | 管理员 |
| `/manager/admin/news` | 新闻管理 | 管理员 |
| `/manager/admin/users` | 用户管理 | 管理员 |

`/home`、`/aichat`、`/news/detail/:id` 等旧路径已做 301 式重定向，登录后按角色落到 `/manager/news` 或 `/manager/admin/news`。

---

## 7. 常见问题

**Q1：前端提示"网络异常，请确认后端服务已启动"？**
后端未起或端口不是 8000。前端代理写死在 `vite.config.js` 的 `target`，改端口需同步修改。

**Q2：页面能打开但新闻列表为空？**
数据库里没有数据。执行 `database.sql` 导入，或由管理员在"新闻管理"新增；`init_db()` 只补分类和账号，不补新闻。

**Q3：`/docs` 能打开但接口返回 401？**
除 `/api/auth/*`、`/api/news/*` 的读接口、`/api/ai/status` 外均需登录。在 Swagger 右上角 `Authorize` 填入登录拿到的 `token`（`Bearer` 前缀由 Swagger 自动补）。

**Q4：AI 回答总是"数据库中没有找到相关新闻"？**
说明确实没检索到。检查关键词、分类 ID 与 `days` 时间窗；数据库演示数据的发布时间集中在 2023 年，用"最近 7 天"会查不到，建议 `days=0`。

**Q5：AI 速度慢或超时？**
单条摘要/简报走 LLM 可能 10–60s，前端对应请求超时设为 90–300s。批量摘要为串行调用，`limit` 越大越慢。

**Q6：Redis 没装会报错吗？**
不会。`utils/cache.py` 首次连接失败即标记 `_disabled`，后续直接跳过缓存，接口照常返回。

**Q7：上传图片 404？**
确认 `backend/uploads/` 存在且有写权限，且通过 `/uploads/<filename>` 访问（后端已挂载静态目录）。

---

## 8. 文档索引

| 文档 | 内容 |
| --- | --- |
| [API接口文档.md](API接口文档.md) | 45 个业务接口 + 3 个基础接口、统一响应、错误码、SSE 事件协议、权限矩阵 |
| [数据库设计.md](数据库设计.md) | 8 张表字段字典、ER 图、索引与约束、冗余字段取舍、迁移说明 |
| [系统设计.md](系统设计.md) | 分层架构、认证/浏览/Agent/摘要/热榜流程、缓存与降级、安全、性能、扩展点 |

## 9. 许可

本项目为学习与课程实践用途，未附带开源许可证。使用第三方依赖请遵循其各自许可（FastAPI、SQLAlchemy、Vue、Vant 等）。
