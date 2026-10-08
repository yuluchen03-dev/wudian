# 悟典项目 · 全面工程审查报告（技术债评估 + 事故响应演练）

**日期**：2026-09-25
**工作流**：工作流 5（技术债评估）+ 工作流 3（事故响应演练）
**参与成员**：Cody / Archi / Rex / Tessa / Docu（Docu 未交付，由主理人基于已读文档补全）

---

## 📌 TL;DR（执行摘要）

- **整体结论**：悟典项目代码架构清晰（分层规范、AI 降级链路完整、SQL 注入零发现），但**游戏化经济完整性存在可被利用的漏洞**，SQLite 未开 WAL、无备份机制是最大事故风险，前端测试全部为「伪测试」（源码正则断言，行为覆盖≈0%），文档与实际代码存在明显漂移。
- **严重度分布**：🔴严重 2 项 / 🟠高 13 项 / 🟡中 16 项 / 🟢低 7 项（合并去重后共 38 项）
- **阻塞项**：游戏化 EXP 可被无限刷分（P0 阻塞上线）；SSE 流式回复前端错误被吞 + 未带 token（P0 阻塞演示）
- **阻塞 / 非阻塞**：2 项阻塞上线/演示，其余为可排期技术债

---

## 🎯 核心结论卡片

| 项目 | 内容 |
|------|------|
| 整体评级 | 🟡 有条件通过（需修复 TOP 3 后方可上线） |
| 阻塞项数量 | 2 |
| 关键行动项 | 8 条（分三阶段，总投入约 6.5 个工作日） |
| 建议下一步 | 立即修复 EXP 刷分漏洞 + SSE 链路缺陷（1 天内），本周完成 WAL + 备份脚本（Rex A1-A3），本月补 CI + auth 测试 |

---

## 第一部分：技术债评估（工作流 5）

### 债务清单（按 Priority = (Impact + Risk) × (6 - Effort) 排序）

| # | 严重度 | 类别 | 优先级分 | 问题描述 | 证据位置 | 建议修复 | 来源 |
|---|--------|------|---------|---------|---------|---------|------|
| 1 | 🔴 | 安全/经济完整性 | 18 | 打卡/复习经验值由客户端上报且无上限，可被无限刷分 | `backend/app/api/learning.py:181-193, 291-322` | 服务端计算 EXP，schema 加 `le=100` 上限，提交前校验到期+去重 | Cody |
| 2 | 🔴 | 正确性/SRE 高优 | 16 | 配置校验器 `validate_app_debug` 递归调用 Settings()，APP_DEBUG=true 时服务启动失败 | `backend/app/core/config.py:146-154` | 改用 `model_validator(mode="after")` 完成跨字段检查 | Cody |
| 3 | 🟠 | 性能/阻塞 | 15 | RAG 检索（async 端点内调用同步 chroma query）阻塞事件循环 | `backend/app/services/rag_service.py:906-912` | 包 `asyncio.to_thread` 或换 chroma async client | Archi |
| 4 | 🟠 | 性能/阻塞 | 15 | 辩论存储同步文件 IO（235 个 JSON 逐个加载）阻塞事件循环 | `backend/app/services/debate_storage.py:23-77` | 迁移到 SQLite（见 ADR-1） | Archi + Cody |
| 5 | 🟠 | 安全/前端 | 14 | SSE chat-sage 错误事件被 catch{} 吞掉 + fetch 未带 Authorization token | `frontend/lib/api.ts:1052-1113` | 手动加 Authorization 头，throw 移出 try | Cody |
| 6 | 🟠 | 架构/数据 | 13 | 数据陈旧副本分叉：根目录 wudian.db（6 月）与 backend/wudian.db（9 月）并存 | 根目录 `wudian.db`(380KB) vs `backend/wudian.db`(438KB) | 删除根目录副本，清理根目录 stale data/debates + chroma_db | Archi |
| 7 | 🟠 | 架构/安全 | 13 | 无 schema 迁移管理：`backend/migrations/` 为空，`init_db()` 仅在开发环境执行 | `backend/migrations/`（空目录） | 引入 Alembic，`create_all` 仅保留测试用途 | Archi |
| 8 | 🟠 | 配置/安全 | 12 | `.env` 含真实 API_KEY（DEEPSEEK/QWEN），密钥命名 `SECRET_KEY` 与配置要求 `JWT_SECRET_KEY` 不符 | `backend/.env` 第 9 行；`config.py:49` | 统一密钥名，提供 .env.example 校验脚本 | Archi |
| 9 | 🟠 | 测试 | 12 | 认证链路零测试：JWT 签发/校验、过期 token、密码处理无覆盖 | 无 `test_auth*.py` | 补 8 个用例集成测试（1 天内） | Tessa |
| 10 | 🟠 | 测试 | 11 | 前端 23 个测试全部为源码正则断言的「接线测试」，行为覆盖≈0% | `frontend/tests/*.test.cjs` | 渐进替换为 Vitest + Testing Library | Tessa |
| 11 | 🟠 | 架构 | 11 | AI Provider 切换/降级路径零测试，openai 未安装时降级分支从未被测 | `backend/app/services/llm_client.py:23-31` | 补 mock openai SDK 单测（0.5 天） | Tessa |
| 12 | 🟠 | 安全/信息泄露 | 10 | `/health` 端点公开返回服务器绝对文件系统路径 | `backend/app/main.py:121-132` | 生产环境收敛为仅返回 status 与布尔健康位 | Cody |
| 13 | 🟠 | 测试 | 10 | 无 CI，测试靠手动，依赖 PowerShell，新环境无法一键复现 | 全项目无 .github/workflows | 加 GitHub Actions：pytest + 前端 test + tsc --noEmit | Tessa |
| 14 | 🟡 | 性能 | 9 | N+1 查询：`get_due_reviews` 对每条 SRS 记录单独发 Verse 查询（最多 201 次） | `backend/app/api/learning.py:267-283` | 一次 `select(SrsRecord, Verse).join()` 批量取回 | Cody |
| 15 | 🟡 | 架构 | 9 | 辩论一局内多位先贤串行生成（无 asyncio.gather） | `backend/app/services/debate_engine.py:462-468` | 互不依赖的立论轮并行化 | Archi |
| 16 | 🟡 | 架构 | 9 | backend 反向依赖仓库根目录（classics_service 4 层 parent 回溯） | `backend/app/services/classics_service.py:23` | 数据路径收敛进 settings，解锁 backend 独立部署 | Archi |
| 17 | 🟡 | 性能 | 8 | 无缓存层：Redis 配置齐全但全仓库零引用，热门内容每请求重查 | `config.py:40-44`（redis_url 无人调用） | 先用进程内 TTL 缓存，Redis 推迟到多实例需求时 | Archi |
| 18 | 🟡 | 安全 | 8 | access/refresh token 存 localStorage，7 天 refresh 有效期且无 jti/吊销 | `frontend/lib/auth.ts:11-60`；`config.py:71-74` | 短期：缩短有效期 + jti 黑名单；中期改 httpOnly Secure Cookie | Cody |
| 19 | 🟡 | 安全 | 8 | quiz 接口（GET /api/learning/quiz/{verse_id}）未认证，题库可被匿名爬取 | `backend/app/api/learning.py:340-349` | 补 current_user 依赖 | Cody |
| 20 | 🟡 | 正确性 | 8 | PK 会话内存泄漏：`_pk_sessions` 全局字典清理代码被注释 | `backend/app/services/community_service.py:1066` | 恢复 del 或加 TTL | Cody |
| 21 | 🟡 | 性能 | 7 | SQLite 未开 WAL/busy_timeout，多并发写可能锁死 | `backend/app/core/database.py:27-34` | connect 后执行 WAL pragma + event listener | Cody + Archi + Rex |
| 22 | 🟡 | 可维护性 | 7 | 三个服务类超长（community_service 1207 行、rag_service 1149 行、debate_engine 887 行） | `backend/app/services/*.py` | 按领域拆分子模块 | Cody |
| 23 | 🟡 | 可维护性 | 7 | chat_with_sage 单函数 200+ 行，流式/非流式两条降级路径内联重复 | `backend/app/api/ai.py:80-282` | 抽出 `_build_citations()` 与 `_fallback_reply()` | Cody |
| 24 | 🟡 | 安全 | 7 | SSE 错误事件把内部异常 `str(e)` 原样发给前端，可能泄露路径/类名 | `backend/app/api/debate.py:150-152, 196-198` | 对外返回通用文案，详细错误仅入日志 | Cody |
| 25 | 🟡 | 配置 | 6 | pytest 未列入 requirements.txt，新环境无法运行测试 | `backend/requirements.txt`（grep 无 pytest） | 加 requirements-dev.txt | Tessa |
| 26 | 🟡 | 配置 | 6 | conftest.py 用 `del sys.modules` 强制重载配置，导入顺序脆弱 | `backend/tests/conftest.py:26-30` | 改用 pytest 环境变量注入或 Settings 显式构造 | Tessa |
| 27 | 🟢 | 架构 | 5 | 死代码：`debate_orchestrator.py` 全仓库无任何引用 | `backend/app/services/debate_orchestrator.py` | 删除或标注 experimental | Archi |
| 28 | 🟢 | 架构 | 5 | 同一份数据多副本：classics_catalog.json 在 frontend/lib/ 与 data/processed/ md5 一致 | md5 `497d8318...` 两处一致 | 前端运行时从 API 拉取，删除内置副本 | Archi |
| 29 | 🟢 | 依赖 | 5 | python-jose[cryptography] 已停更，存在 CVE-2024-33663/33664 | `backend/requirements.txt:18` | 迁移到 pyjwt | Cody |
| 30 | 🟢 | 依赖 | 5 | python-multipart 下限允许带 ReDoS 漏洞的旧版（CVE-2024-24762） | `backend/requirements.txt:20` | 提升下限至 >=0.0.18 | Cody |
| 31 | 🟢 | 依赖 | 5 | passlib[bcrypt] 声明但零引用，与新版 bcrypt 有兼容冲突 | `backend/requirements.txt:19` | 移除 passlib | Cody |
| 32 | 🟢 | 依赖 | 4 | 全部后端依赖 `>=` 无上界，无锁文件（pip-tools/uv lock） | `backend/requirements.txt` 全文 | pip-compile 或 uv lock 生成锁文件 | Cody |
| 33 | 🟢 | 依赖 | 4 | tailwindcss 在 frontend/package.json dependencies（应 devDependencies） | `frontend/package.json` | 移到 devDependencies | Cody |
| 34 | 🟢 | 仓库卫生 | 4 | 25+ 个 .log 文件散落目录；根目录 `nul` 是 Windows 保留名文件 | 根目录、frontend/、backend/ | 归档到统一目录并删除；`nul` 用 `\\?\` 前缀删除 | Cody |
| 35 | 🟢 | 架构 | 3 | 双构建产物并存：根 `dist/`（Next 导出 17M）与 `frontend/.next/` 并存 | 根目录 `dist/`、`scripts/build-site.mjs` | 明确唯一构建入口 | Archi |
| 36 | 🟢 | 文档 | 3 | database_schema.md 声称 PostgreSQL 15 + pgvector + 16 表，实际 SQLite 无 pgvector | `database_schema.md` 头部 vs 实际 | 修订文档，标注「目标架构 vs 现状」 | Archi + 主理人 |
| 37 | 🟢 | 文档 | 3 | README 未覆盖环境变量配置（.env 必要性、JWT_SECRET_KEY 生成方式） | `README.md` 无 .env 章节 | 补充环境变量配置章节 | 主理人 |
| 38 | 🟢 | 文档 | 2 | 无 API 接口文档、无 Runbook、无环境变量清单 | docs/ 无 API 相关文档 | 见文档债 TOP 3 | 主理人 |

### 依赖债清单（合并去重）

| 依赖 | 位置 | 问题 | 建议 | 来源 |
|------|------|------|------|------|
| python-jose[cryptography] | requirements.txt:18 | 已停更，CVE-2024-33663/33664 | 迁移到 pyjwt | Cody |
| python-multipart | requirements.txt:20 | 下限允许带 ReDoS 旧版（CVE-2024-24762） | 提升下限至 >=0.0.18 | Cody |
| passlib[bcrypt] | requirements.txt:19 | 声明但零引用，与新 bcrypt 有冲突 | 移除 passlib | Cody |
| 全后端依赖无锁文件 | requirements.txt 全文 | 不同环境版本不可复现 | pip-compile 或 uv lock | Cody |
| tailwindcss | frontend/package.json | 构建期依赖挂在 dependencies | 移到 devDependencies | Cody |
| pptxgenjs | 根 package.json | 一次性脚本依赖挂在生产依赖 | 移到 devDependencies 或 tools/ | Cody |
| React 18 + Next 15.5 | frontend/package.json | Next 15 官方推荐 React 19（升级债） | 列入后续计划 | Cody |

### 测试债专项（Tessa 原始产出）

- 后端 17 个真实 pytest（覆盖率约 15-25%），核心模块（auth、learning、community）零测试
- 前端 23 个 `.cjs` 测试全为源码正则断言的「接线测试」，行为覆盖≈0%
- 无 CI（无 .github/workflows），pytest 未在 requirements.txt
- TOP 5 优先补测：①认证链路（1 天）②AI Provider 切换/降级（0.5 天）③SRS 学习进度（0.5 天）④DB 初始化幂等性（0.5 天）⑤前端关键旅程冒烟（1-1.5 天）
- 三阶段计划总投入约 5.5-6 个工作日

### 架构债专项（Archi 原始产出 + ADR）

**ADR-1**：辩论会话从文件系统迁移到 SQLite
- 决策：新增 debate_sessions 表，debate_storage 改为读写 SQLite
- 理由：消除 3 个问题——async 端点阻塞 IO、用户数据无备份、list_sessions 线性劣化
- 代价：约 1-2 天开发 + 数据迁移脚本

**ADR-2**：建立数据单一事实源 + 清理陈旧副本
- 决策：删除根目录三组陈旧副本（wudian.db/data/debates/chroma_db），数据路径收敛进 settings
- 理由：数据分叉是最危险的债，解锁 backend 独立部署与容器化
- 代价：约 1 天清理 + 回归测试

**ADR-3**：引入 Alembic + 环境启动自检
- 决策：初始化 Alembic（config 已预留 sync_database_url），lifespan 校验关键配置
- 理由：当前"development 才建表 + SECRET_KEY 命名漂移"意味着换机器必起不来
- 代价：约 0.5-1 天

---

## 第二部分：事故响应流程演练（工作流 3）

### 事故时间线（基于真实日志 E1-E10）

| 时间 | 事件 | 日志证据 |
|------|------|---------|
| 启动 | LLM API_KEY 未配置 → AI 降级 | server_stderr.log / codex-backend-8000.stderr.log |
| 启动 | chromadb 未安装 → RAG 降级为关键词检索 | server_stderr.log |
| 运行 | OPTIONS /api/analyze 400 Bad Request ×8 | codex-8000.stderr.log |
| 运行 | GET /api/health 404 | codex-8000.stderr.log |
| 运行 | ConnectionResetError [WinError 10054]（SSE 断连） | server_stderr.log 反复出现 |
| 运行 | 422 Unprocessable Entity（register/debate/start） | server_stdout.log |
| 运行 | RAG 索引数 122 条 vs 143 条经文不一致 | codex-8000.stderr.log vs server_stdout.log |
| 运行 | uvicorn --reload 反复重启 60+ 次（WatchFiles 检测到 tests/*.py 变化） | codex-backend-8001.stderr.log（496 行） |
| 发现 | 两份 wudian.db 分裂（根目录 380KB vs backend/ 438KB） | ls -la 对比 |
| 发现 | 两份 chroma_db 分裂（根目录 184K vs backend/ 4.1M） | ls -la 对比 |

### SEV 评级（五场景映射）

| 场景 | 定级 | 依据 |
|------|------|------|
| S1. SQLite 数据库锁死/损坏 + 双库分裂 | **SEV2**（演示当天升级 SEV1） | 无 WAL/busy_timeout；无备份；双库已实际分裂 |
| S2. LLM API 不可用/超时/Key 失效 | SEV3 | E1/E2 已真实发生；有降级模式兜底 |
| S3. RAG/Chroma 索引不可用或数据不一致 | SEV3 | E3+E8；有关键词检索降级 |
| S4. 后端启动失败（JWT_SECRET_KEY 缺失） | SEV1（演示前 1h）/SEV2 | config.py 必填项未配置即启动失败 |
| S5. CORS/路由不匹配导致前端整体不可用 | SEV3 | E5 已真实发生 |

### 主演练场景：S1（SQLite 锁死/损坏 + 双库分裂）七阶段摘要

| 阶段 | 具体步骤（本项目） | 就绪度 |
|------|----------------|--------|
| 检测 | 查 `/health`；看前端白屏；tail `backend/*.log` | ⚠️ 部分（无自动监控） |
| 分级 | 本演练定义 SEV1-4 标准表（详见原始报告） | ❌ 缺失（本文档交付后即就绪） |
| 隔离 | 停后端 → 复制 db 到 backup/时间戳目录 → 移根目录陈旧副本到 quarantine/ | ❌ 缺失（无备份/停写预案） |
| 根因（5 Why） | 无 WAL + 无 busy_timeout + 无备份 + 旧副本不清理 → 小锁升级为数据事故 | ❌ 缺失（无复盘文化） |
| 修复 | R1 开 WAL+busy_timeout（10min）；R2 db 修复（若已损坏）；R3 清理分裂（5min） | ⚠️ 部分（git 回滚能力存在，修复脚本不存在） |
| 恢复 | `/health` 验证 + PRAGMA integrity_check + 冒烟路径（注册→阅读→Sage→辩论） | ⚠️ 部分（健康端点现成，无自动化校验） |
| 复盘 | 时间线 + 行动项表 A1-A8（详见原始报告） | ❌ 缺失 |

### 一页纸事故速查卡（简化版）

| 当 X 发生 | 查 Y | 执行 Z |
|---|---|---|
| 页面 500 / `database is locked` | `GET /health`；`ls -la backend/wudian.db` | ①停后端 ②复制 db 到 backup/时间戳 ③开 WAL ④冒烟验证 |
| `disk image is malformed` | `PRAGMA integrity_check` | 停写→备份坏库→`.recover` 重建→换回；失败则回滚 backup/ |
| AI 回复全是"（降级模式）" | `/health` 的 `llm_available`；`.env` 的 LLM_PROVIDER/API_KEY | 补 Key→重启→health 确认 true |
| 服务起不来（演示前！） | 启动日志第一行报错；`JWT_SECRET_KEY` 是否设置 | 缺 Key→按 config.py 生成并写入 .env；端口占用→`netstat -ano \| findstr 8000` 杀旧进程 |
| 日志无限增长 / 服务反复重启 | stderr 中 WatchFiles reload 循环 | 加 `--reload-exclude`；日志轮转（A5） |

---

## 第三部分：文档债（主理人补全，基于已读文档）

### 文档资产盘点

| 文档 | 位置 | 状态 | 备注 |
|------|------|------|------|
| README.md | 根目录 | ⚠️ 部分过时 | 启动命令与实际 package.json scripts 基本一致；缺环境变量配置章节 |
| database_schema.md | 根目录 | ❌ 严重漂移 | 声称 PostgreSQL 15 + pgvector + 16 表，实际 SQLite 无 pgvector；ER 图引用不存在的 HNSW 索引 |
| HACKATHON_OPTIMIZATIONS.md | 根目录 | ✅ 可用 | 历史优化记录 |
| 不做清单.md | 根目录 | ✅ 可用 | 项目约束记录 |
| Pitch讲稿_3分钟.md | 根目录 | ✅ 可用 | 路演口径 |
| docs/hackathon/data-trust-statement.md | docs/hackathon/ | ✅ 可用 | 数据可信声明 |
| docs/hackathon/final-delivery-checklist.md | docs/hackathon/ | ✅ 可用 | 交付检查清单 |
| docs/hackathon/investor-qa.md | docs/hackathon/ | ✅ 可用 | 投资人问答 |
| docs/hackathon/scoring-map.md | docs/hackathon/ | ✅ 可用 | 评分映射 |
| docs/hackathon/trae-execution-log.md | docs/hackathon/ | ✅ 可用 | Trae 执行日志 |
| docs/superpowers/plans/ | docs/superpowers/ | 待抽查 | 规划文档子目录 |
| docs/superpowers/specs/ | docs/superpowers/ | 待抽查 | 规格文档子目录 |
| deliverables/gstack.md | deliverables/ | ✅ 可用 | 交付物清单 |

### 文档债清单

| # | 严重度 | 问题 | 证据 | 影响 | 建议 |
|---|--------|------|------|------|------|
| 1 | 🟠 | database_schema.md 严重漂移：声称 PostgreSQL 15 + pgvector，实际 SQLite | schema 头部 vs backend/app/core/database.py 实际使用 | 新人/评委按文档理解得出错误架构图 | 修订为「目标架构（PostgreSQL）vs 现状（SQLite）」双版本 |
| 2 | 🟡 | README 缺环境变量配置章节 | README.md 无 .env 说明，无 JWT_SECRET_KEY 生成指引 | 新环境部署直接启动失败 | 新增「环境变量」章节，列出所有必填/选填项 |
| 3 | 🟡 | 无 API 接口文档 | 全项目无 OpenAPI/Swagger 之外的 API 文档 | 新人接入成本高；评委追问时无法快速查证 | 用 FastAPI 内置 /docs 即可，补充 README 链接 |
| 4 | 🟡 | 无部署/运行手册（Runbook） | 无独立部署文档 | 事故响应只能靠临场发挥（见 Rex 演练结论） | 新增 docs/DEPLOYMENT.md |
| 5 | 🟢 | docs/superpowers/plans/ 和 specs/ 内容待抽查 | 目录存在但未读取 | 可能过期或重复 | 由 Docu 后续补充 |
| 6 | 🟢 | README 未说明 AI 降级模式与 Provider 配置 | README 无 LLM_PROVIDER/API_KEY 说明 | 演示时 AI 不可用无法快速定位 | 在「最快体验」章节后补充「AI 配置」小节 |

### TOP 3 应补文档

1. **环境变量清单**（`docs/ENVIRONMENT.md`）：列出所有必填/选填 .env 变量，说明用途、默认值、生成方式
2. **部署 Runbook**（`docs/DEPLOYMENT.md`）：一键启动命令、健康检查、冒烟测试、事故速查卡（整合 Rex 的速查卡）
3. **架构现状 vs 目标架构**（`docs/ARCHITECTURE.md`）：澄清 SQLite vs PostgreSQL、Next.js 15 vs Vite 等关键差异

---

## ✅ 行动清单（按优先级排序）

| # | 行动 | 负责角色 | 紧急度 | 预期完成 | 来源 |
|---|------|---------|--------|---------|------|
| 1 | 修复打卡/复习经验值刷分漏洞（服务端计算 EXP，schema 加 le=100，提交前校验到期+去重） | Cody 指定开发 | P0 | 1 天内 | Cody + Tessa #2/#3 |
| 2 | 修复 SSE chat-sage 双重缺陷（fetch 加 Authorization 头，catch 中 rethrow error） | Cody 指定开发 | P0 | 1 天内 | Cody #4/#5 |
| 3 | 修复 config.py validate_app_debug 递归（改用 model_validator mode="after"） | Cody 指定开发 | P0 | 当天 | Cody #1 |
| 4 | SQLite 开 WAL + busy_timeout + timeout=30（database.py connect_args） | Rex A1 | P0 | 当天 | Rex + Cody #9 + Archi #6 |
| 5 | 写 `scripts/backup_db.py`（复制 wudian.db + chroma_db 到 backup/带时间戳，保留最近 7 份） | Rex A2 | P0 | 当天 | Rex |
| 6 | 清理根目录陈旧副本（wudian.db + chroma_db + data/debates/）并隔离到 quarantine/ | Rex A3 | P0 | 当天 | Archi #6 |
| 7 | 加 requirements-dev.txt（pytest + pytest-asyncio）+ 建 .github/workflows/ci.yml | Tessa 第一阶段 | P1 | 本周 | Tessa |
| 8 | 补 auth 链路集成测试（TOP5 #1，约 8 用例） | Tessa 第一阶段 | P1 | 本周 | Tessa |
| 9 | RAG 检索包 asyncio.to_thread（或换 chroma async client） | Archi 指定开发 | P1 | 本周 | Archi |
| 10 | 辩论会话从文件系统迁移到 SQLite（ADR-1） | Archi 指定开发 | P1 | 2 周内 | Archi |
| 11 | 引入 Alembic 迁移 + 环境启动自检（ADR-3） | Archi 指定开发 | P1 | 2 周内 | Archi |
| 12 | 写 docs/ENVIRONMENT.md + docs/DEPLOYMENT.md + 修订 database_schema.md | 主理人协调 | P2 | 本月 | 主理人 + Rex A5 |

---

## ⚠️ 待完善 / 已知局限

- 多库（Docu）的文档债评估未完成，本文档债部分由主理人基于已读文档（README.md、database_schema.md、docs/ 目录结构）补全，抽样深度有限（仅 10 个文件）
- 未实际运行 `PRAGMA integrity_check` 验证 wudian.db 实际表结构与 database_schema.md 的差异程度
- 前端代码（126 个 TS/TSX 文件）仅抽样读取 api.ts 和 auth.ts，未做全量审查
- 优先级公式中 Effort 为主观估算，需工程负责人复核

---

## 📚 数据来源 & 成员产出索引

- **Cody（代码审查师）** 原始产出：22 项代码问题 + 10 项依赖债，重点发现 EXP 刷分漏洞、SSE 链路缺陷、config 递归隐患
- **Archi（架构师）** 原始产出：10 项架构债 + 8 项性能风险 + 3 条 ADR，重点发现数据副本分叉、RAG 阻塞事件循环、无迁移管理
- **Rex（SRE 工程师）** 原始产出：七阶段事故响应演练 + 5 场景 SEV 评级 + 一页纸速查卡 + 8 条行动项（A1-A8），基于 8 个真实日志文件做健康体检
- **Tessa（测试专家）** 原始产出：测试现状盘点（后端 17 真测试/前端 23 伪测试/无 CI）+ TOP 5 补测清单 + 三阶段测试计划（总投入约 6 工作日）
- **Docu（技术文档师）**：未交付（多次催促无响应），文档债部分由主理人基于已读文档补全

---

> 本报告由工程保障团队 AI 协作生成，关键决策请由人类工程负责人复核。
