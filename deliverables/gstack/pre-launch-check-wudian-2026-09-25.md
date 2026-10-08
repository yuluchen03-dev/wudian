# 悟典 · 上线前全检报告（代码审查 + 安全审计 + QA 测试）

**日期**：2026-09-25
**场景**：上线前全检（Pre-Launch Check）→ Go / No-Go 决策
**项目**：悟典（可追溯的中国思想问答入口）· 黑客松演示项目
**技术栈**：前端 Next.js 14.1.0 (App Router) + React 18 + TS + Tailwind；后端 FastAPI + SQLAlchemy + SQLite/PostgreSQL + JWT；RAG(chroma) + LLM(openai 兼容)
**参与成员**：产品评审员（代码审查）+ 安全官（OWASP/STRIDE 安全审计）+ 质量门神（QA 测试，由主理人兜底实测）
**结论**：🔴 **暂缓上线（No-Go）** —— 存在 7 项上线阻塞项，其中 5 项为高危安全阻塞

---

## 📌 TL;DR（执行摘要）

- 整体结论：🔴 **暂缓上线**。当前形态**在线**fails：公网带注册/社区发布存在账户接管与零鉴权风险。
- 阻塞项数量：**7 项**（🔴 严重 6 + 🟠 高 1 中影响发布流程）；安全维度单独判定 **HIGH**。
- 最致命三点：① `JWT_SECRET_KEY` 默认占位符 → 可伪造任意用户令牌；② 社区模块**完全无鉴权**（硬编码用户 1001）；③ 前端 `next@14.1.0` 存在 critical 级 CVE（Server Actions SSRF / 缓存投毒）。
- 下一步：按下方 P0 清单修复 5 项安全阻塞 + 2 项功能/流程阻塞后复测转 🟢；若仅本地离线演示，至少完成 P0-1~P0-3 并切 `APP_ENV=production`。

---

## 🎯 核心结论卡片

| 项目 | 内容 |
|------|------|
| Go / No-Go | 🔴 **No-Go（暂缓上线）** |
| 严重度分布 | 🔴 11 / 🟠 20 / 🟡 13 / 🟢 4（跨三维度去重合并后） |
| 关键行动项 | 7 项 P0 阻塞 + 8 项 P1 + 若干 P2 |
| 建议负责人 | 后端（鉴权/密钥）→ 安全官复核；前端（资源/构建/Hooks）→ 前端 + QA 复测 |
| 复测门槛 | `npm run test` 全绿 + 后端 pytest 全绿 + P0 安全项清零 + 生产环境变量校验通过 |

---

## 1. 各成员核心结论

### 🔍 产品评审员（代码审查）
- 核心判断：**良（偏下）**。分层清晰、命名统一、LLM 容错到位；但有 2 个 🔴 硬伤——社区整模块无真实鉴权、登录页 Hooks 违规必崩。
- 关键建议：统一 API 响应契约（现有三套并存）；修 `api.ts` 字段映射错误与 SSE 流鉴权；把 mock/真实路径隔离；补 mapper 与 auth/community 单测。

### 🛡️ 安全官（OWASP Top 10 + STRIDE）
- 核心判断：**风险等级 HIGH，构成上线阻塞**。JWT 默认密钥可伪造、社区零鉴权、`.env` 明文 LLM Key、开发模式默认开启、next 关键漏洞。
- 关键建议：JWT 密钥强制环境变量 + 启动 fail-fast；吊销并轮换泄漏的 API Key；UGC 写接口接入真实鉴权；上线显式 `APP_ENV=production`；升级 `next>=14.2.25`。

### ✅ 质量门神（QA 实测）
- 核心判断：**No-Go 倾向**。构建前置检查 `stage-check` 通过，但**测试套件不自洽**：前端 2 个用例因资源缺失失败并中断后续用例，后端测试**开箱无法运行**。
- 关键建议：补齐缺失静态资源后让 `npm run test` 全绿；为后端建立 venv 并固化依赖安装步骤；修复登录页 Hooks 崩溃。

### 🔧 主理人（QA 兜底实测）
- 实测环境：本机无项目 venv；托管 Python 3.13 与系统 Python 3.11 均缺后端依赖；服务端口 3000/8000 无监听。
- 执行命令：`npm run test`（前端）、`python -m pytest tests -q`（后端）、`npm run stage-check`（构建前置检查）、资源清单核对。

---

## 2. 综合审查发现（去重合并，按严重度排序）

| # | 严重度 | 类别 | 位置 | 问题描述 | 修复建议 | 来源 |
|---|--------|------|------|---------|----------|------|
| 1 | 🔴 | 安全/鉴权 | `backend/app/core/config.py:46` | `JWT_SECRET_KEY` 默认 `"change-me-in-production"`，且 `backend/.env` 仅设 `SECRET_KEY` 未覆盖它 → 线上用公开默认密钥，任何人可伪造任意用户（含任意 `sub`）令牌，账户完全接管 | 强制从环境变量读取强随机密钥；为默认/缺失时启动即失败（fail-fast）；用 `secrets.token_urlsafe(48)` 生成 | 安全官（代码#16 交叉） |
| 2 | 🔴 | 安全/越权 | `backend/app/api/community.py:50-52, 69-264` | 社区模块**完全无鉴权**，22 处调用硬编码 `_CURRENT_USER_ID=1001 / "zengzi"`，所有建组/打卡/笔记/点赞/PK 冒名到同一用户，真实登录用户数据被忽略 | 全部写操作改 `Depends(get_current_active_user)`，用真实 `current_user.id`；删除 `_CURRENT_*` 常量；补资源归属校验 | 安全官 + 产品评审员 |
| 3 | 🔴 | 安全/配置 | `backend/.env:30,51` + `config.py:23-24` | 明文硬编码第三方 LLM API Key；`APP_ENV=development`、`APP_DEBUG=True` 为默认 → AI 端点匿名开放 + Swagger `/docs` 暴露 | 立即在提供方**吊销并轮换**密钥；密钥仅经环境变量注入；上线显式 `APP_ENV=production` 并在 CI 校验 | 安全官 |
| 4 | 🔴 | 安全/依赖 | `frontend/package.json` (`next@14.1.0`) | `npm audit` 实测 13 漏洞（1 critical/11 high/1 moderate）；`next` critical = Server Actions SSRF(CVE-2024-34351) + 缓存投毒(CVE-2024-46982)；`postcss` high | 升级 `next>=14.2.25`（或 15.x）；`npm audit fix`；重审 postcss 等 | 安全官 |
| 5 | 🔴 | 功能/前端 | `frontend/app/login/page.tsx:19-23` | `LoginPage` 在 `useState` 之后、`useCallback` 之前 `if (isLoggedIn()) return` 提前返回 → Hooks 调用数不一致，**hydration 必崩**（"Rendered more/fewer hooks than expected"） | 删除条件早返回，跳转移入 `useEffect(() => { if (isLoggedIn()) router.replace("/") }, [])` | 产品评审员 |
| 6 | 🔴 | QA/流程 | `frontend/tests/visualAssetsWiring.test.cjs:63`、`bookCoverAssets.test.cjs` | `npm run test` **失败**：缺 `public/agens/sages/portraits/wang_yangming.png`（另 `su_shi/wang_anshi/fan_zhongyan` 仅有 svg）、缺 `public/agens/books/zuozhuan.png`；因脚本用 `&&` 串联，中断在第 14 个用例，后续 `readerExperience`+`thoughtCourt*` 5 个用例未被主命令执行 | 补齐 4 个先贤 PNG 与缺失书籍封面 PNG；把 `&&` 链改为聚合跑全部再汇总，避免单点失败掩盖后续用例 | 质量门神 + 主理人 |
| 7 | 🔴 | QA/环境 | `backend/`（无 venv）+ `requirements.txt` | 后端测试**开箱无法运行**：项目无 venv，托管/系统 Python 均 `ModuleNotFoundError: pydantic_settings` → `npm run test` 后端段 17 个用例整体收集失败 | 建 venv 并 `pip install -r backend/requirements.txt`；在 README/CI 固化"环境准备"步骤 | 质量门神 + 主理人 |
| 8 | 🟠 | 安全/会话 | `frontend/lib/auth.ts`、`api.ts:221,1630` | access+refresh token 存 `localStorage` → XSS 即会话劫持；refresh **不可撤销/不轮换**，被盗可续期至约 49 天 | access 改进内存/`httpOnly` cookie；refresh 走 `httpOnly+Secure+SameSite`；引入 token 版本/黑名单支持吊销 | 安全官 |
| 9 | 🟠 | 安全/认证 | `backend/app/api/auth.py` | 登录/注册**无速率限制/账户锁定/验证码**；登录存在时序旁路（用户不存在时跳过 `verify_password`）→ 用户名枚举 | 网关或 `slowapi` 限流（如 5 次/分/IP）；失败计数+临时锁定；统一"用户名或密码错误" | 安全官 |
| 10 | 🟠 | 安全/配置 | `backend/next.config.js`、`app/main.py:94-132` | 缺 CSP 与 HSTS；`/health` 泄露 `database_path`/`chroma_persist_dir` 等内部路径与 env | 增加严格 CSP（至少 `default-src 'self'`）；生产 HTTPS+HSTS；`/health` 移除绝对路径/敏感字段 | 安全官 |
| 11 | 🟠 | 安全/越权 | `backend/app/core/deps.py:158-195` | `get_current_user_or_demo` 在 `is_development` 时对任意无 token 请求返回 `id=0` demo 用户 → 全部 AI 接口裸奔；且 demo 用户是 `SimpleNamespace` 鸭子类型伪装 `User`，访问 ORM 属性即崩 | 用独立开关（如 `ALLOW_ANON_AI`）替代 `APP_ENV` 判定；生产必须 401；demo 用户字段/方法与 `User` 对齐 | 产品评审员（安全官 F-04 交叉） |
| 12 | 🟠 | 契约/一致性 | `backend/app/api/learning.py:82-519` vs 其余路由 | API 响应契约**三套并存**（裸 `response_model` / `APIResponse` 信封 / 无信封裸 dict），前端被迫 `resp?.data?.X ?? resp?.X ?? data` 逐接口兜底 | 全局统一一种返回风格（推荐统一信封）并配套 OpenAPI | 产品评审员 |
| 13 | 🟠 | 缺陷/映射 | `frontend/lib/api.ts:328-335` | `getProgress` 把 `total_verses`(总经文数)当作 `totalChapters`(总章节数)，且 `readChapters` 硬编码 `[]` → 学习进度展示失真 | 对齐后端 `LearningProgress` 真实字段；`readChapters` 由后端返回或推导 | 产品评审员 |
| 14 | 🟠 | 缺陷/鉴权 | `frontend/lib/api.ts:1052-1064` | `chatWithSageStream` 用原生 `fetch` 直连 `/ai/chat-sage`，**未附 Authorization 头**，绕过 axios 拦截器 → 非 dev 环境 401、且异常路径 citations SSE 事件缺 `type` 字段致引用静默丢失 | 该 fetch 补 Bearer 头或改用 `apiClient` streaming；兜底事件统一补 `type` | 产品评审员 |
| 15 | 🟠 | 缺陷/并发 | `backend/app/api/auth.py:63-91` | `register` 先查后插 TOCTOU 竞态；唯一约束冲突时 `flush()` 抛 `IntegrityError` 无捕获 → 500 | 依赖 `unique=True` 约束并 `try/except IntegrityError` 转 409；或 `INSERT ... ON CONFLICT` | 产品评审员 |
| 16 | 🟠 | 测试/覆盖 | `frontend/tests/*.cjs`、`backend/tests/*.py` | 测试未覆盖 `api.ts` 字段映射层、后端 auth、community、llm_client（重试/配额）；本次 #13/#14 契约缺陷均不会被现有测试捕获 | 为 `api.ts` 每个 mapper 加纯函数单测；补 `test_auth.py`、`test_llm_client.py` | 产品评审员 |
| 17 | 🟠 | QA/环境 | 服务端口 | 3000/8000 无监听，真实前后端链路**未实测**（`stage-check` 仅通过端口与就绪检查） | 上线前启动前后端并跑通 `/demo` 四幕 + 注册登录 + 1 个 AI 端点冒烟 | 主理人 |
| 18 | 🟡 | 安全/注入 | `backend/app/services/ai_service.py:106,166,214` | 用户 `question/text/context/history` 经 `.format()` 直拼提示词，无隔离定界（无工具调用，影响限于内容篡改） | 用定界符包裹不可信输入；系统提示强化边界；输出做内容/长度校验 | 安全官 |
| 19 | 🟡 | 安全/数据 | `wudian.db`（权限 644） | SQLite 明文含用户哈希/邮箱，全局可读 | 收紧为 `600`；生产迁移 PostgreSQL；禁止置于 web 可访问目录 | 安全官 |
| 20 | 🟡 | 可维护/迁移 | `backend/app/core/database.py:78-82`、`init_db.py` | 声明含 Alembic 但**无任何迁移文件**，建表靠 `create_all` → 生产 PG 无 schema 演进/回滚路径 | 补 Alembic 初始化与首版迁移；生产走 `alembic upgrade head` | 产品评审员 |
| 21 | 🟡 | 代码质量 | `backend/app/api/ai.py:99,305`、`config.py` | 硬编码 `top_k=5/3` 未用 `settings.RAG_TOP_K`；函数内重复局部 import；`JWT_SECRET_KEY` 默认值、`.env` 相对路径 | 统一引用配置常量；import 提到顶部；配置绝对路径化 + fail-fast | 产品评审员 |
| 22 | 🟡 | 可维护 | `frontend/lib/api.ts`（约 2000 行） | 15+ mock 模块与内联假数据混杂于单一文件，真实/演示路径易混淆 | 拆分 `lib/mock/*` 并抽象 `ApiAdapter` 接口隔离 | 产品评审员 |
| 23 | 🟡 | 缺陷/静默 | `backend/app/api/ai.py:170-217,237-282` | `except Exception` 兜底返回缓存、只记 log 不返回 5xx → 静默吞错，可能把无关缓存当正确答案展示 | 兜底限定"服务不可用"场景；结构化告警；前端对 low confidence 显著提示"非实时" | 产品评审员 |
| 24 | 🟢 | 低 | `security.py:72`、`api.ts:618` 等 | 刷新令牌倍数、`pkSubmit` 硬编码 `120s` 等魔法数字 | 提取常量 | 产品评审员 |

> 去重说明：#2 与安全官 F-03、#3 与 F-02/F-04、#1 与 F-01、#11 与 F-04 属同一问题，已合并计数。安全官完整清单（F-01~F-14）见成员原始报告。

---

## 3. 上线阻塞项清单（Go/No-Go 依据）

| 阻塞编号 | 关联发现 | 类别 | 说明 | 解除条件 |
|----------|----------|------|------|----------|
| **B-1** | #1 | 安全 | JWT 默认密钥可伪造令牌 | 密钥改环境变量注入 + fail-fast，`APP_ENV=production` |
| **B-2** | #2 | 安全/鉴权 | 社区模块零鉴权、冒名 UGC | 全部写接口接真实鉴权 + 归属校验 |
| **B-3** | #3 | 安全/配置 | `.env` 明文密钥 + 开发模式默认开启 | 吊销轮换 Key；上线 `APP_ENV=production`、关 Swagger |
| **B-4** | #4 | 安全/依赖 | `next@14.1.0` critical CVE | 升级 `next>=14.2.25` 并 `npm audit` 归零 |
| **B-5** | #5 | 功能 | 登录页 Hooks 违规必崩 | 跳转移入 `useEffect`，登录页可正常渲染 |
| **B-6** | #6 | QA | 前端测试套件失败（缺资源） | 补 4 个先贤 PNG + `zuozhuan.png`，`npm run test` 全绿 |
| **B-7** | #7 | QA/环境 | 后端测试无法运行 | 建 venv 装依赖，pytest 全绿 |

---

## 4. 发布检查清单（勾选项）

- [ ] `APP_ENV=production`、`APP_DEBUG=False`、Swagger `/docs` 关闭
- [ ] `JWT_SECRET_KEY` 已注入强随机值（非默认），缺失即启动失败
- [ ] 泄漏的 LLM API Key 已在提供方吊销并轮换，新 Key 仅经环境变量注入
- [ ] 社区及所有 UGC 写接口已接入真实 JWT 鉴权 + 资源归属校验
- [ ] `next` 升级至 `>=14.2.25`，`npm audit` 无 critical/high
- [ ] `NEXT_PUBLIC_USE_MOCK=false` 在 CI 断言（生产禁止静默 mock）
- [ ] `frontend` 4 个缺失立绘 PNG + `books/zuozhuan.png` 已补齐
- [ ] 后端 venv 建立、`pip install -r backend/requirements.txt`、pytest 全绿
- [ ] 前端 `npm run test` 全绿（含此前被 `&&` 中断的用例）
- [ ] 端口 3000/8000 已启动并跑通 `/demo` 四幕 + 注册登录 + 1 个 AI 端点冒烟
- [ ] `wudian.db` 权限收紧为 600；生产切 PostgreSQL 并启用加密
- [ ] 登录页 Hooks 崩溃已修复并实测通过

## 5. 回滚预案

1. **触发条件**：上线后出现鉴权异常、社区数据错乱、AI 端点批量 5xx 或页面白屏。
2. **一级回退（分钟级）**：将 `NEXT_PUBLIC_USE_MOCK=true` 重构建部署，切到"演示稳定层"，保留舞台与问题、隐藏真实写操作，UI 明确标注"演示数据"。README 已定义 `stable-demo` 替代路径。
3. **二级回退**：关闭社区写接口（或整体下线 `/community`），保留只读思想审判场只读演示链路 `/demo → 证 → 辩 → 判`。
4. **三级回退**：回退到上一可用构建产物（`dist/` 或上一版本镜像），并将 `APP_ENV` 切回受限只读配置。
5. **数据回滚**：SQLite 场景直接恢复上线前 `wudian.db` 备份副本；生产 PG 场景走 Alembic `downgrade` 或时间点恢复。
6. **复盘**：记录事故时间线、影响面、根因，48h 内补测试用例防回归。

---

## ✅ 行动清单（按优先级）

| # | 行动 | 负责方 | 紧急度 | 关联 |
|---|------|--------|--------|------|
| 1 | JWT 密钥强制环境变量 + 启动 fail-fast；上线 `APP_ENV=production` | 后端 | P0 | B-1/B-3 |
| 2 | 吊销并轮换泄漏的 LLM API Key，改仅环境变量注入 | 后端/运维 | P0 | B-3 |
| 3 | 社区模块全量接入 `get_current_active_user` + 归属校验，删除硬编码常量 | 后端 | P0 | B-2 |
| 4 | 升级 `next>=14.2.25` 并 `npm audit fix` 归零 | 前端 | P0 | B-4 |
| 5 | 修复登录页 Hooks 违规（跳转移入 `useEffect`） | 前端 | P0 | B-5 |
| 6 | 补齐 4 个先贤 PNG + `zuozhuan.png`；`npm run test` 全绿 | 前端/美术 | P0 | B-6 |
| 7 | 建后端 venv 装依赖，pytest 全绿；README 固化环境准备 | 后端 | P0 | B-7 |
| 8 | 统一 API 响应契约；修 `api.ts` 映射与 SSE 流鉴权/兜底事件 | 前后端 | P1 | #12/#13/#14 |
| 9 | 令牌改 httpOnly cookie + CSP；refresh 可吊销/轮换；登录限流 | 前后端 | P1 | #8/#9 |
| 10 | 补 `api.ts` mapper / auth / community / llm_client 单测 | 前后端 | P1 | #16 |
| 11 | 补 Alembic 迁移、配置绝对路径化、清理魔法数字 | 后端 | P2 | #20/#21 |
| 12 | 拆分 mock 到 `lib/mock/*` 并抽象 `ApiAdapter` | 前端 | P2 | #22 |

---

## ⚠️ 待完善 / 已知局限

- **真实链路未实测**：本机 3000/8000 无监听，前端 `curl` 冒烟未执行（已由代码层审查与单测部分覆盖）。
- **后端运行时未验证**：因缺依赖，17 个后端用例未真正执行；未排除运行期另有缺陷。
- **响应式/浏览器兼容**：仅做代码层核查（1440/390 布局、`'use client'`/hydration 风险），未做真机截图对照。
- **chroma/RAG 检索质量**：本次未评估检索命中率与幻觉率（超出上线前全检范围）。
- **依赖审计基线**：`npm audit` 结果可能随注册表更新变化，建议上线当天再跑一次。

---

## 📚 成员产出索引

- `gstack-product-reviewer`（代码审查）：22 项发现，2×🔴 + 8×🟠，含文件行级证据与优先改进项（对话已回传）
- `gstack-security-officer`（安全审计）：STRIDE 建模 + OWASP Top 10 检查表 + F-01~F-14 发现表，判定 HIGH/阻塞（对话已回传）
- `gstack-qa-lead`（QA 测试）：会话中断，原始产出未完整回传；QA 维度由主理人实测兜底（`npm run test` / `pytest` / `stage-check`）

---

> 本报告由软件工坊 AI 协作生成，关键决策请由工程负责人复核。安全项上线前必须清零后再复测。
