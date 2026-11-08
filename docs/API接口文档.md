# API 接口文档

> 版本：v2.0.0　｜　服务地址：`http://127.0.0.1:8000`　｜　在线调试：`/docs`（Swagger）、`/redoc`

本文档覆盖全部 **45 个业务接口**（`/api` 前缀）与 3 个基础接口，以及 AI 流式对话的 SSE 事件协议。字段与代码中的 Pydantic 模型一一对应，可直接用于联调与前端对接。

---

## 目录

1. [通用约定](#1-通用约定)
2. [认证 `/api/auth`](#2-认证-apiauth)
3. [用户 `/api/user`](#3-用户-apiuser)
4. [新闻 `/api/news`](#4-新闻-apinews)
5. [收藏 `/api/favorite`](#5-收藏-apifavorite)
6. [浏览历史 `/api/history`](#6-浏览历史-apihistory)
7. [统计 `/api/stats`](#7-统计-apistats)
8. [AI `/api/ai`](#8-ai-apiai)
9. [文件 `/api/files`](#9-文件-apifiles)
10. [基础接口](#10-基础接口)
11. [权限矩阵](#11-权限矩阵)
12. [错误信息速查](#12-错误信息速查)

---

## 1. 通用约定

### 1.1 请求

| 项 | 说明 |
| --- | --- |
| Base URL | `http://127.0.0.1:8000`，业务接口统一前缀 `/api` |
| 编码 | UTF-8，请求体 `application/json`（文件上传为 `multipart/form-data`） |
| 认证 | `Authorization: Bearer <token>`，token 由登录/注册接口返回 |
| 时间格式 | ISO 8601，如 `2023-08-23T10:50:00`；部分统计字段为字符串 `YYYY-MM-DD HH:MM` |
| 分页 | `page`（≥1，默认 1）、`page_size`（1–100，默认 10） |

### 1.2 统一响应

所有业务接口返回同一个信封：

```json
{
  "code": 200,
  "message": "请求成功",
  "data": {}
}
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `code` | int | 200 表示业务成功，其余为业务错误码 |
| `message` | string | 可直接展示给用户的中文提示 |
| `data` | any | 业务数据，失败时为 `null`（流式接口除外） |

分页数据统一为 `PageData`：

```json
{
  "code": 200,
  "message": "请求成功",
  "data": {
    "list": [],
    "total": 0,
    "page": 1,
    "page_size": 10,
    "has_more": false
  }
}
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `list` | array | 当前页数据 |
| `total` | int | 总条数 |
| `page` | int | 当前页码 |
| `page_size` | int | 每页条数 |
| `has_more` | bool | `page * page_size < total` |

### 1.3 HTTP 状态码与业务 code

⚠️ **两者可能不一致，客户端必须同时判断**：

| 场景 | HTTP 状态 | 响应体 `code` | 示例 |
| --- | --- | --- | --- |
| 正常 | 200 | 200 | 登录成功 |
| `BusinessException`（可预期业务错误） | **200** | 400 / 403 / 404 | 账号或密码错误、无权限、新闻不存在 |
| `HTTPException`（框架抛出） | 401 | 401 | 请先登录 / 登录已失效 |
| 参数校验失败 | 422 | 422 | 请求参数错误：page 应为整数 |
| 唯一约束冲突 | 400 | 400 | 用户名已存在 |
| 数据库异常 | 500 | 500 | 数据库操作失败，请稍后重试 |
| 未捕获异常 | 500 | 500 | 服务器内部错误 |

前端 `src/utils/request.js` 的处理方式是：先看 HTTP 状态，再看 `data.code !== 200` 则 reject 并 toast；`code===401` 或 HTTP 401 统一清空本地凭证并跳转 `/login`（带 `redirect` 参数）。

### 1.4 通用对象

**NewsListItem**（新闻列表项，出现于列表、收藏、历史、相关推荐）：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | int | 新闻 ID |
| `title` | string | 标题 |
| `description` | string\|null | 简介 |
| `image` | string\|null | 封面 URL（`/uploads/xxx` 或外部 URL） |
| `author` | string\|null | 作者 |
| `category_id` | int | 分类 ID |
| `category_name` | string\|null | 分类名称 |
| `views` | int | 浏览量 |
| `publish_time` | datetime\|null | 发布时间 |
| `summary` | string\|null | AI 摘要（Markdown） |
| `highlight` | string\|null | AI 一句话看点 |

**UserResponse**：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | int | 用户 ID |
| `username` | string | 用户名 |
| `nickname` | string\|null | 昵称 |
| `avatar` | string\|null | 头像 URL |
| `gender` | string\|null | `male` / `female` / `unknown` |
| `bio` | string\|null | 简介 |
| `phone` | string\|null | 手机号（唯一） |
| `role` | string | `admin` / `user` |
| `status` | int | `1` 正常 / `0` 禁用 |
| `created_at` | datetime\|null | 创建时间 |

---

## 2. 认证 `/api/auth`

### 2.1 登录

`POST /api/auth/login`　无需认证

| 参数 | 位置 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- | --- |
| `username` | body | string | 是 | 用户名 |
| `password` | body | string | 是 | 密码 |

```json
{ "username": "admin", "password": "123456" }
```

响应 `data`（`LoginResponse`）：

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1, "username": "admin", "nickname": "平台管理员",
    "avatar": null, "gender": "unknown", "bio": "负责新闻与用户管理",
    "phone": null, "role": "admin", "status": 1, "created_at": "2026-11-05T10:00:00"
  }
}
```

失败：`code=400 账号或密码错误`；`code=403 账号已被禁用，请联系管理员`。

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"123456"}'
```

### 2.2 注册

`POST /api/auth/register`　无需认证（注册即为 `user` 角色、`status=1`）

| 参数 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| `username` | string | 是 | 2–50 字符，全局唯一 |
| `password` | string | 是 | 3–72 字符（bcrypt 上限） |
| `nickname` | string\|null | 否 | ≤50 字符，缺省取 `username` |

响应同登录。失败：`code=400 用户名已存在`。

### 2.3 退出登录

`POST /api/auth/logout`　无需认证

响应：`{"code":200,"message":"退出成功","data":null}`

> 服务端**不做 Token 吊销**，JWT 无状态；前端清除 `localStorage` 的 `token` 与 `userInfo` 即完成退出。剩余有效期内旧 Token 仍可用，这是当前设计已知限制。

---

## 3. 用户 `/api/user`

### 3.1 获取当前用户

`GET /api/user/me`　🔒 登录

响应 `data`：`UserResponse`

### 3.2 更新个人资料

`PUT /api/user/me`　🔒 登录

| 参数 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| `nickname` | string\|null | 否 | ≤50 |
| `avatar` | string\|null | 否 | ≤255，通常是 `/uploads/xxx` |
| `gender` | string\|null | 否 | ≤10，建议 `male/female/unknown` |
| `bio` | string\|null | 否 | ≤500 |
| `phone` | string\|null | 否 | ≤20，唯一 |

仅更新传入字段（`exclude_unset + exclude_none`），空字符串会被归一为 `null`。响应 `data`：更新后的 `UserResponse`。

### 3.3 修改密码

`PUT /api/user/password`　🔒 登录

| 参数 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| `old_password` | string | 是 | 原密码 |
| `new_password` | string | 是 | 3–72，且不能与原密码相同 |

失败：`原密码错误`、`新密码不能与原密码相同`。成功后旧 Token 仍有效（无状态）。

### 3.4 用户列表（管理端）

`GET /api/user/list`　🔒 管理员

| 参数 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `page` | int | 1 | ≥1 |
| `page_size` | int | 10 | 1–100 |
| `keywords` | string\|null | — | 模糊匹配 `username` 或 `nickname` |
| `role` | string\|null | — | `admin` / `user`，其他值被忽略 |
| `status` | int\|null | — | `0` / `1`，其他值被忽略 |

响应 `data`：`PageData<UserResponse>`，按 `id` 倒序。

### 3.5 创建用户（管理端）

`POST /api/user`　🔒 管理员

| 参数 | 类型 | 必填 | 默认 | 说明 |
| --- | --- | --- | --- | --- |
| `username` | string | 是 | — | 2–50，唯一 |
| `password` | string | 否 | `123456` | 3–72 |
| `nickname` | string\|null | 否 | 同 username | ≤50 |
| `role` | string | 否 | `user` | 仅 `admin`/`user` |
| `status` | int | 否 | `1` | 非 0/1 时回退为 1 |
| `phone` | string\|null | 否 | — | ≤20，唯一 |
| `avatar` | string\|null | 否 | — | ≤255 |
| `gender` | string\|null | 否 | `unknown` | ≤10 |
| `bio` | string\|null | 否 | — | ≤500 |

失败：`账号已存在`、`手机号已被使用`、`角色只能是 admin 或 user`。成功后会清理 `stats:` 缓存。

### 3.6 更新用户（管理端）

`PUT /api/user/{user_id}`　🔒 管理员

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `nickname` / `avatar` / `gender` / `bio` / `phone` | string\|null | 资料字段，传了才更新 |
| `role` | string\|null | `admin`/`user` |
| `status` | int\|null | `0`/`1` |
| `password` | string\|null | 3–72，传了则重置密码 |

业务保护规则：

- 不能把**当前登录账号**置为禁用（`不能禁用当前登录的账号`）；
- 不能取消**当前登录账号**的管理员身份（`不能取消当前登录账号的管理员身份`）；
- 系统必须保留至少一名管理员（`系统至少需要保留一名管理员`）。

### 3.7 删除用户（管理端）

`DELETE /api/user/{user_id}`　🔒 管理员

- 不能删除自己：`不能删除当前登录的账号`；
- 删除最后一名管理员会被拒绝：`系统至少需要保留一名管理员`；
- 级联删除该用户的 `favorite`、`history`、`ai_chat`、`user_token`（外键 `ON DELETE CASCADE`）。

响应：`{"code":200,"message":"用户已删除","data":null}`

---

## 4. 新闻 `/api/news`

### 4.1 分类列表

`GET /api/news/categories`　公开

响应 `data`：`CategoryResponse[]`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | int | 分类 ID |
| `name` | string | 分类名称 |
| `sort_order` | int | 排序值，越小越前 |
| `news_count` | int | 该分类新闻数 |

> 结果缓存键 `news:categories`，TTL 7200s；新闻增删改后自动失效。

### 4.2 新闻列表

`GET /api/news/list`　公开

| 参数 | 类型 | 默认 | 约束/说明 |
| --- | --- | --- | --- |
| `page` | int | 1 | ≥1 |
| `page_size` | int | 10 | 1–100 |
| `category_id` | int\|null | — | 分类筛选 |
| `keywords` | string\|null | — | 对 `title / description / content` 做 `LIKE %kw%` |
| `author` | string\|null | — | 对 `author` 模糊匹配 |
| `order` | string | `latest` | `latest`（发布时间倒序）/ `hot`（浏览量倒序） |

响应 `data`：`PageData<NewsListItem>`

### 4.3 热榜

`GET /api/news/hot`　公开

| 参数 | 类型 | 默认 | 约束 |
| --- | --- | --- | --- |
| `days` | int | 0 | 0–3650，0 表示不限时间 |
| `limit` | int | 10 | 1–50 |
| `category_id` | int\|null | — | 分类筛选 |

响应 `data`（`HotNewsResponse`）：

```json
{
  "days": 0,
  "total": 10,
  "list": [
    {
      "id": 12, "title": "中国快递业务量突破1000亿件", "description": "...",
      "image": "https://...", "author": "Logistics Analyst",
      "category_id": 8, "category_name": "财经", "views": 17200,
      "publish_time": "2023-08-23T10:50:00",
      "summary": null, "highlight": null,
      "rank": 1, "score": 10356.0, "favorite_count": 3,
      "hot_reason": "阅读 17200 · 收藏 3 · 08-23 发布"
    }
  ]
}
```

热度算法（详见[系统设计 §5.4](系统设计.md#54-热榜算法)）：

```
score = views × 0.6 + favorite_count × 40 + max(0, 30 - age_days) × 3 + (窗口内命中 ? 20 : 0)
```

> 候选集先按 `views` 取 `max(limit*6, 60)` 条，再在内存中综合收藏与时效排序；结果缓存 `news:hot:{days}:{limit}:{category_id}`，TTL 300s。

### 4.4 新闻检索（AI 友好）

`GET /api/news/search`　公开

| 参数 | 类型 | 默认 | 约束 |
| --- | --- | --- | --- |
| `keywords` | string | `""` | ≤50 |
| `category_id` | int\|null | — | 分类 |
| `days` | int | 0 | 0–3650，按发布时间倒推 |
| `limit` | int | 10 | 1–30 |

响应 `data` 为**数组**（非分页）：

```json
[
  {
    "id": 1, "title": "...", "description": "...", "summary": null,
    "category": "科技", "author": "...", "views": 1234,
    "publish_time": "2023-08-20 08:45", "content_excerpt": "正文前 500 字"
  }
]
```

### 4.5 新闻详情

`GET /api/news/{news_id}`　公开（可选携带 Token）

| 参数 | 位置 | 说明 |
| --- | --- | --- |
| `news_id` | path | 新闻 ID |

响应 `data`（`NewsDetailResponse` = `NewsListItem` + 以下字段）：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `content` | string | 正文 |
| `summary_time` | datetime\|null | 摘要生成时间 |
| `favorite_count` | int | 该新闻被收藏总数 |
| `is_favorite` | bool | 当前登录用户是否已收藏（未登录恒 `false`） |
| `related` | NewsListItem[] | 相关推荐，同分类按浏览量取 5 条 |

⚠️ **副作用**：每次调用都会把 `views` 加 1 并提交事务。前端列表页跳详情时请只请求一次，避免重复计数。

### 4.6 读取已有摘要

`GET /api/news/{news_id}/summary`　公开

响应：

```json
{
  "code": 200, "message": "请求成功",
  "data": {
    "news_id": 12,
    "summary": "**核心内容**：...",
    "highlight": "快递业务量创新高",
    "summary_time": "2026-11-06T15:20:00"
  }
}
```

未生成过摘要时 `summary/highlight/summary_time` 均为 `null`；新闻不存在返回 `code=404 新闻不存在`。

### 4.7 生成 AI 摘要

`POST /api/news/{news_id}/summary`　🔒 登录（任意角色）

| 参数 | 位置 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- | --- |
| `news_id` | path | int | — | 新闻 ID |
| `force` | query | bool | `false` | `true` 时忽略已有摘要强制重算 |

响应 `data`（`SummaryResponse`）：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `news_id` | int | 新闻 ID |
| `summary` | string | 摘要（Markdown） |
| `highlight` | string\|null | ≤80 字看点 |
| `summary_time` | datetime\|null | 生成时间 |
| `cached` | bool | `true` 表示命中已有摘要、未调用模型 |

> 未配置 LLM 或调用失败时，自动使用**抽取式摘要**（取前 3 句 + 关键信息列表），不会报错。

### 4.8 批量生成摘要（管理端）

`POST /api/news/summaries/batch`　🔒 管理员

| 参数 | 位置 | 类型 | 默认 | 约束 |
| --- | --- | --- | --- | --- |
| `limit` | query | int | 5 | 1–30 |
| `force` | query | bool | `false` | 为 `false` 时只处理 `summary IS NULL` 的新闻 |

响应：

```json
{
  "requested": 5, "success_count": 4, "failed_count": 1,
  "success": [{ "news_id": 3, "title": "...", "summary": "..." }],
  "failed": [{ "news_id": 9, "title": "...", "error": "timeout" }]
}
```

> 串行调用模型，耗时与 `limit` 成正比；前端超时设为 300s。

### 4.9 创建新闻（管理端）

`POST /api/news`　🔒 管理员

| 参数 | 类型 | 必填 | 约束/默认 |
| --- | --- | --- | --- |
| `title` | string | 是 | 2–255 |
| `content` | string | 是 | ≥2 字符 |
| `description` | string\|null | 否 | ≤500；缺省取正文前 120 字 + `…` |
| `image` | string\|null | 否 | ≤255 |
| `author` | string\|null | 否 | ≤50；缺省 `平台编辑` |
| `category_id` | int | 是 | 必须存在 |
| `publish_time` | datetime\|null | 否 | 缺省当前时间 |
| `views` | int | 否 | 默认 0，负数会被归零 |

响应：`NewsDetailResponse`（不增加浏览量）。分类不存在：`code=400 新闻分类不存在`。

### 4.10 更新新闻（管理端）

`PUT /api/news/{news_id}`　🔒 管理员

请求体为 `NewsUpdateRequest`：所有字段可选（`title/content/description/image/author/category_id/publish_time/views`），只更新传入项。

⚠️ **摘要失效策略**：只要 `title` 或 `content` 发生变化，`summary`、`highlight`、`summary_time` 会被清空，需重新生成。

### 4.11 删除新闻（管理端）

`DELETE /api/news/{news_id}`　🔒 管理员

级联删除该新闻的 `favorite`、`history`、`related_news` 记录（外键 `ON DELETE CASCADE`）。响应 `{"code":200,"message":"新闻已删除","data":null}`

---

## 5. 收藏 `/api/favorite`

> ⚠️ 收藏模块的 **query 参数名为驼峰 `newsId`**（`alias="newsId"`），而请求体字段是下划线 `news_id`。这是历史兼容设计，对接时务必区分。

### 5.1 检查收藏状态

`GET /api/favorite/check?newsId=12`　🔒 登录

响应：`{"code":200,"message":"检查收藏状态成功","data":{"is_favorite":true}}`

### 5.2 添加收藏

`POST /api/favorite/add`　🔒 登录

```json
{ "news_id": 12 }
```

响应 `data`（`FavoriteItem`）：`{favorite_id, favorite_time, news: NewsListItem}`

失败：`新闻不存在`（404）、`已经收藏过该新闻`（400）。

### 5.3 取消收藏

`DELETE /api/favorite/remove?newsId=12`　🔒 登录

成功：`{"code":200,"message":"已取消收藏","data":null}`
不存在：HTTP 200 且 `{"code":404,"message":"收藏记录不存在"}`

### 5.4 收藏列表

`GET /api/favorite/list`　🔒 登录

| 参数 | 默认 | 约束 |
| --- | --- | --- |
| `page` | 1 | ≥1 |
| `page_size` | 10 | 1–100 |

响应 `data`：`PageData<FavoriteItem>`，按收藏时间倒序。

### 5.5 清空收藏

`DELETE /api/favorite/clear`　🔒 登录

响应：`{"code":200,"message":"已清空 3 条收藏","data":null}`

> 收藏增删会失效 `news:hot:` 与 `stats:` 缓存（会影响热度与统计）。

---

## 6. 浏览历史 `/api/history`

### 6.1 记录浏览

`POST /api/history/add`　🔒 登录

```json
{ "news_id": 12 }
```

同一用户对同一新闻只保留一条记录：已存在则刷新 `view_time`。响应 `data`：`{history_id, view_time, news}`。

> 前端调用时带 `silent: true`，失败不弹 toast。

### 6.2 历史列表

`GET /api/history/list`　🔒 登录

分页同通用约定，响应 `data`：`PageData<{history_id, view_time, news}>`，按浏览时间倒序。

### 6.3 删除单条

`DELETE /api/history/delete/{history_id}`　🔒 登录

成功：`删除成功`；不存在：HTTP 200 + `code=404 浏览记录不存在`。

### 6.4 清空历史

`DELETE /api/history/clear`　🔒 登录

响应：`{"code":200,"message":"已清空 12 条浏览记录","data":null}`

---

## 7. 统计 `/api/stats`

> 全部需要 🔒 登录。普通用户与管理员看到的字段不同：用户维度（`total_users/active_users`）仅管理员可见。结果缓存 120s。

### 7.1 数据总览

`GET /api/stats/overview`

响应 `data`（`OverviewResponse`）：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `total_news` | int | 新闻总数 |
| `today_news` | int | 今日发布数 |
| `week_news` | int | 近 7 天（含今日）发布数 |
| `month_news` | int | 近 30 天发布数 |
| `total_views` | int | 累计阅读（`SUM(views)`） |
| `today_views` | int | 今日浏览记录数（`history` 表计数） |
| `total_favorites` | int | 累计收藏数 |
| `total_categories` | int | 分类数 |
| `total_summaries` | int | 已生成摘要的新闻数 |
| `total_users` | int\|null | 注册用户数（仅管理员） |
| `active_users` | int\|null | 状态正常的用户数（仅管理员） |
| `latest_publish_time` | string\|null | 最新发布时间 `YYYY-MM-DD HH:MM` |
| `latest_publish_title` | string\|null | 最新新闻标题 |
| `coverage_start` | string\|null | 最早一篇新闻的时间 |

### 7.2 发布趋势

`GET /api/stats/trend?days=7`

| 参数 | 默认 | 约束 |
| --- | --- | --- |
| `days` | 7 | 1–365 |

响应：

```json
{
  "days": 7,
  "points": [{ "date": "2026-11-02", "news_count": 3, "view_count": 12 }],
  "total_news": 18,
  "total_views": 76
}
```

> 无数据的日期会补 0，保证前端折线图连续。

### 7.3 分类统计

`GET /api/stats/categories`

响应 `data`：`[{id, name, news_count, total_views, favorite_count}]`，按 `sort_order` 排序。

### 7.4 作者统计

`GET /api/stats/authors?limit=10`

| 参数 | 默认 | 约束 |
| --- | --- | --- |
| `limit` | 10 | 1–50 |

响应 `data`：`[{author, news_count, total_views}]`，按发布数、阅读量倒序；作者为空归为 `未知作者`。

### 7.5 按日期区间查询发布量

`GET /api/stats/publish-range?start_date=2026-11-01&end_date=2026-11-08`

| 参数 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `start_date` | date\|null | `end - 6 天` | `YYYY-MM-DD` |
| `end_date` | date\|null | 今天 | `YYYY-MM-DD` |

若 `start > end` 会自动交换。响应：

```json
{
  "start_date": "2026-11-01",
  "end_date": "2026-11-08",
  "count": 12,
  "list": [ /* 最多 20 条 NewsListItem */ ]
}
```

---

## 8. AI `/api/ai`

### 8.1 AI 状态

`GET /api/ai/status`　公开

```json
{
  "code": 200, "message": "请求成功",
  "data": {
    "enabled": true,
    "model": "agnes-2.5-flash",
    "mode": "llm",
    "base_url": "https://api.agnes-ai.cn/v1"
  }
}
```

`enabled=false` 或 `mode="local"` 表示未配置 Key，前端可提示"本地新闻引擎"。

### 8.2 对话（非流式）

`POST /api/ai/chat`　🔒 登录

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `messages` | ChatMessage[] | 是 | `[{role:"user"|"assistant", content:"..."}]`，服务端只取最后 **16 条** |

```json
{
  "messages": [
    { "role": "user", "content": "最近有哪些科技新闻？" }
  ]
}
```

响应 `data`：`{"role":"assistant","content":"## 检索结果（3 条）\n..."}`

失败：`请输入您要对话的内容`（消息全为空）。

> 单轮对话可能触发最多 **6 轮**工具调用，耗时较长，前端超时设为 120s。

### 8.3 对话（SSE 流式）

`POST /api/ai/chat/stream`　🔒 登录

请求体同 8.2。响应 `Content-Type: text/event-stream`，每帧格式：

```
data: {"type":"...","...":"..."}\n\n
```

**事件类型**：

| `type` | 字段 | 说明 |
| --- | --- | --- |
| `status` | `message` | 进度提示：`正在思考…` / `正在整理结果…` / `大模型未配置，使用本地新闻引擎…` |
| `tool_start` | `name`, `label` | 开始调用工具 |
| `tool_end` | `name`, `label`, `preview` | 工具返回，`preview` 为结果前 240 字符 |
| `token` | `content` | 回答文本增量；LLM 模式按模型返回的 `delta` 逐块下发，本地模式按 14 字符切片下发 |
| `done` | — | 回答结束，服务端已持久化对话记录 |
| `error` | `message` | 出错，流结束（如 `登录已失效`、`AI 服务暂时不可用，请稍后重试`） |

**完整示例**：

```
data: {"type":"status","message":"正在思考…"}

data: {"type":"tool_start","name":"search_news","label":"检索新闻数据库"}

data: {"type":"tool_end","name":"search_news","label":"检索新闻数据库","preview":"{\"count\": 3, \"news\": [...]}"}

data: {"type":"token","content":"## 检索"}

data: {"type":"token","content":"结果（3 条）"}

data: {"type":"done"}
```

**客户端要求**：

- 必须用 `fetch + ReadableStream`（`EventSource` 无法携带 `Authorization` Header）；
- 按 `\n\n` 切分帧，取以 `data:` 开头的行；
- 服务端**不发送** `[DONE]` 哨兵，前端已做兼容忽略；
- 非 `text/event-stream` 响应说明出错，应降级解析 JSON 错误体；
- 代理层必须关闭缓冲（Vite 已配置 `x-accel-buffering: no`，Nginx 需 `proxy_buffering off`）。

```bash
curl -N -X POST http://127.0.0.1:8000/api/ai/chat/stream \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"messages":[{"role":"user","content":"最近的热榜"}]}'
```

**两轮工具调用示例（工具调用轮 + 回答轮）**：

```
status(思考) → tool_start(search_news) → tool_end(preview) → status(整理) → token... → done
```

### 8.4 对话历史

`GET /api/ai/history`　🔒 登录

| 参数 | 默认 | 约束 |
| --- | --- | --- |
| `page` | 1 | ≥1 |
| `page_size` | 10 | 1–**50** |

响应 `data`：`PageData<{id, message, response, created_at}>`，按时间倒序。

> 每条记录保存用户消息（截断 6000 字）与完整回答（截断 12000 字）。

### 8.5 清空对话历史

`DELETE /api/ai/history`　🔒 登录

响应：`{"code":200,"message":"已清空 8 条对话记录","data":null}`

### 8.6 新闻简报

`POST /api/ai/digest`　🔒 登录

| 参数 | 类型 | 默认 | 约束 |
| --- | --- | --- | --- |
| `days` | int | 0 | 0–3650 |
| `limit` | int | 8 | 1–20 |

```json
{ "days": 0, "limit": 8 }
```

响应 `data`：`{"content":"## 今日速览\n...","cached":false}`

> 结构固定为 `今日速览 / 重点新闻 / 趋势观察`；`days>0` 且窗口内无新闻时，自动回退到"最近 N 条"并在开头说明。缓存键含日期，TTL 600s。

### 8.7 热榜解读

`POST /api/ai/hot-analysis`　🔒 登录

| 参数 | 类型 | 默认 | 约束 |
| --- | --- | --- | --- |
| `days` | int | 0 | 0–3650 |
| `limit` | int | 10 | 1–20 |

响应 `data`：`{"content":"## 热榜概览\n...","cached":false}`

> 结构：`热榜概览 / 话题聚类 / 值得关注 / 阅读建议`。底层数据来自 4.3 热榜。

### 8.8 生成摘要（AI 入口）

`POST /api/ai/summary`　🔒 登录

```json
{ "news_id": 12, "force": false }
```

响应 `data`：`SummaryResponse`（同 4.7）。

### 8.9 批量摘要（管理端）

`POST /api/ai/batch-summary`　🔒 管理员

| 参数 | 位置 | 默认 | 约束 |
| --- | --- | --- | --- |
| `limit` | query | 5 | 1–30 |
| `force` | query | false | 是否重算已有摘要 |

响应结构同 4.8。

---

## 9. 文件 `/api/files`

### 9.1 上传图片

`POST /api/files/upload`　🔒 登录

`Content-Type: multipart/form-data`，字段名 `file`。

| 校验 | 规则 |
| --- | --- |
| 扩展名 | `.jpg / .jpeg / .png / .gif / .webp / .svg` |
| 大小 | ≤ 10MB |
| 空文件 | 拒绝 |

响应：

```json
{
  "code": 200, "message": "上传成功",
  "data": {
    "url": "/uploads/1794063060189_3ebcacc5.jpeg",
    "filename": "cover.jpg",
    "size": 204800
  }
}
```

失败：`不支持的文件类型`、`上传文件为空`、`文件不能超过 10MB`。

> 落盘文件名为 `时间戳_8位随机串.扩展名`，静态访问路径 `/uploads/<filename>`（`main.py` 已挂载）。该目录**公开可读、无鉴权**，请勿上传敏感内容。

---

## 10. 基础接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/` | 应用信息：`{name, version, docs:"/docs", api:"/api"}` |
| GET | `/health` | 健康检查：`{status:"ok"|"degraded", database:bool, ai:bool}` |
| GET | `/uploads/{filename}` | 上传图片静态访问 |
| GET | `/docs` / `/redoc` | Swagger / ReDoc |
| GET | `/openapi.json` | OpenAPI 规范 |

`/health` 会真实执行 `SELECT 1`；数据库不可用时返回 `status="degraded"`，但 HTTP 仍为 200。

---

## 11. 权限矩阵

| 模块 | 接口 | 公开 | 登录 | 管理员 |
| --- | --- | :-: | :-: | :-: |
| 认证 | `POST /auth/login` `POST /auth/register` `POST /auth/logout` | ✅ | — | — |
| 用户 | `GET/PUT /user/me`、`PUT /user/password` | — | ✅ | ✅ |
| 用户 | `GET /user/list`、`POST /user`、`PUT/DELETE /user/{id}` | — | — | ✅ |
| 新闻 | `GET /news/categories`、`/list`、`/hot`、`/search`、`/{id}`、`/{id}/summary` | ✅ | ✅ | ✅ |
| 新闻 | `POST /news/{id}/summary` | — | ✅ | ✅ |
| 新闻 | `POST /news`、`PUT/DELETE /news/{id}`、`POST /news/summaries/batch` | — | — | ✅ |
| 收藏 | 全部 5 个 | — | ✅ | ✅ |
| 历史 | 全部 4 个 | — | ✅ | ✅ |
| 统计 | 全部 5 个 | — | ✅ | ✅（多用户字段） |
| AI | `GET /ai/status` | ✅ | ✅ | ✅ |
| AI | `chat`、`chat/stream`、`history`、`digest`、`hot-analysis`、`summary` | — | ✅ | ✅ |
| AI | `batch-summary` | — | — | ✅ |
| 文件 | `POST /files/upload` | — | ✅ | ✅ |

> 注：管理员登录后前端只会进入管理页，但后端接口并未禁止管理员调用用户侧接口（如收藏），权限判断以 Token 中的用户身份为准。

---

## 12. 错误信息速查

| code | 典型 message | 来源 |
| --- | --- | --- |
| 400 | 账号或密码错误 | 登录 |
| 400 | 用户名已存在 / 账号已存在 / 手机号已被使用 | 注册、创建用户 |
| 400 | 新闻不存在 / 新闻分类不存在 | 新闻、收藏、历史 |
| 400 | 已经收藏过该新闻 | 收藏 |
| 400 | 原密码错误 / 新密码不能与原密码相同 | 修改密码 |
| 400 | 角色只能是 admin 或 user / 状态只能是 0 或 1 | 用户管理 |
| 400 | 不能禁用当前登录的账号 / 不能取消当前登录账号的管理员身份 | 用户管理 |
| 400 | 系统至少需要保留一名管理员 / 不能删除当前登录的账号 | 用户管理 |
| 400 | 不支持的文件类型 / 上传文件为空 / 文件不能超过 10MB | 上传 |
| 400 | 请输入您要对话的内容 | AI 对话 |
| 403 | 账号已被禁用，请联系管理员 | 登录 |
| 403 | 无权限访问，需要管理员账号 | 管理接口 |
| 404 | 新闻不存在 / 用户不存在 | 详情、管理 |
| 404 | 收藏记录不存在 / 浏览记录不存在 | 取消收藏、删除历史 |
| 401 | 请先登录 / 登录已失效，请重新登录 / 无效的登录凭证 / 用户不存在 / 账号已被禁用 | JWT 依赖 |
| 422 | 请求参数错误：`page` Input should be greater than or equal to 1 | Pydantic 校验 |
| 500 | 数据库操作失败，请稍后重试 / 服务器内部错误 | 全局异常 |

---

> 文档维护：接口调整后请同步更新本文档、`README.md` 的接口入口说明，以及 `frontend/src/api/` 中的请求封装，三者需保持一致。
