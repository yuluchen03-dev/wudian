# FIX-005 / Q5 — REAL PROVIDER E2E 报告

- **日期**：2026-10-11
- **执行环境**：DSH Agent Teams（Harness Desktop 0.2.0-rc.2 + @nanmicoder/dsh-agent-teams 0.1.22）
- **上游冻结件**：FIX-005A commit `34afd1d`（TERMINAL PASS，streaming citation bypass remediation）
- **本报告性质**：受控、低成本、隔离的真实 Provider E2E 验证

---

## 0. FINAL VERDICT

```
Q5_REAL_PROVIDER_E2E = FAIL
```

**独立 reviewer 终审 verdict = FAIL（不批准 PASS）**，见 §13。

### 0.1 本报告初稿的 PASS 结论已被推翻（决定性反例 F-1）

初稿声称 `model = agnes-3.0-flash` 并据此判定 PASS。独立复核证明该 model 身份**不成立**：

- 持久作用域（User/Machine）**不存在** `LLM_PROVIDER` / `AGNES_MODEL` / `AGNES_BASE_URL`（实测 User=False, Machine=False）；这些值来自 git-ignored `backend/.env`。
- 干净进程按应用自身持久配置解析得 model = **`agnes-2.0-flash`**（`backend/app/core/config.py:59` 默认值），而非初稿声称的 `agnes-3.0-flash`。
- 端点实测：`agnes-2.0-flash` → **503 model_not_found**；`agnes-3.0-flash` → 200。
- 用应用自身持久配置实跑生产路径：3 次 RateLimit 重试后失败 → 回落缓存兜底、`confidence=low`、`honest_note`=「AI 服务暂时不可用，已返回预设回答。」

即：初稿的 PASS **仅在实施者进程内临时注入 `AGNES_MODEL=agnes-3.0-flash` 的条件下成立**；在应用持久配置下，应用**无法**调用该 provider。这与 `AGENTS.md:113`「不要因 ZCode 能调用模型，就宣布应用 Q5 已解除」直接冲突。

**实施者方法错误（如实记录）**：初稿执行时以 `$env:` 在进程内自设 `LLM_PROVIDER`/`AGNES_MODEL`/`AGNES_BASE_URL`，并把自设值误当作环境既有配置读取，因而未发现持久配置与端点不匹配。

因此本报告**不得**作为 Q5 通过的依据。已复现为真的技术事实见 §5（合同层）与 §6（中断行为），但它们不足以支撑 Q5 PASS。

---

## 1. Provider / Model / Endpoint（secret-free）

| 项 | 值 |
|---|---|
| provider | `agnes`（悟典应用 `config.py:200` 既有分支，运行时 `LLM_PROVIDER=agnes`） |
| model | `agnes-3.0-flash` |
| endpoint scheme | `https` |
| endpoint host | `apihub.agnes-ai.com` |
| endpoint path | `/v1` |
| API 协议 | OpenAI-compatible `POST /v1/chat/completions`（实测可用） |

**endpoint 来源**：运行时环境变量 override（`AGNES_BASE_URL`）。**未修改任何 tracked provider 配置**——`git diff -- backend/app/core/config.py backend/app/services/llm_client.py` 为空。

### 关于 provider 命名的说明（如实记录）

DSH 桌面端 `llm-pi-ai` 中该 provider 的 id 为 `agens`（拼写为 gens），其 `apiKeyEnv` 为 `AGENS_API_KEY`；而悟典应用源码 `config.py:202` 读取的是 `AGNES_API_KEY`（gnes）。两者拼写不同、互不通用。**本次 Q5 走的是悟典应用路径**，因此使用 `AGNES_API_KEY`。本报告不修改任何一方的拼写。

---

## 2. Credential 注入方式与存在性

| 项 | 结果 |
|---|---|
| credential env name | `AGNES_API_KEY` |
| `credential_present` | **true**（仅记录布尔值与长度，值从未打印/落盘） |
| 注入方式 | 用户级环境变量（User scope）已存在；本次执行在**同一进程内**读取该变量并注入子进程环境后立即运行测试，凭证仅存在于该进程内存 |
| 是否写入源码/fixture/日志/报告/Git | **否** |
| 是否读取 `.env` / shell history / 凭证文件 | **否** |

执行期内只对具体变量做存在性检查，未使用会整体输出环境的 `env` / `Get-ChildItem Env:` 之类命令。

---

## 3. Preflight（联网前）

```
provider             = agnes
model                = agnes-3.0-flash
endpoint_resolved    = true (scheme=https host=apihub.agnes-ai.com path=/v1)
credential_env_name  = AGNES_API_KEY
credential_present   = true
production_db        = false
production_chroma    = false
streaming_citation_guard = PASS  (FIX-005A, 34afd1d)
mock_e2e             = PASS
max_calls = 20 | concurrency = 1 | max_retry = 1 | cost_ceiling <= USD 1 equivalent
```

应用侧解析确认：`settings.llm_config` → provider/base_url/model 一致；`LLMClient` 初始化成功并绑定 `agnes-3.0-flash`。

---

## 4. 真实调用计数与用量

| 阶段 | 用例 | 真实调用 |
|---|---|---|
| Smoke | 端点连通与模型可用 | 1 |
| Phase A | Q5-RP-01、Q5-RP-06、Q5-RP-07、Q5-RP-08 | 4 |
| Phase B | Q5-RP-09、Q5-RP-10 | 2 |
| 合同层（无 provider 调用） | Q5-RP-02/03/04/05 | 0 |
| Phase C | Q5-RP-C1（受控 4xx） | 1（不计入 chat 用例） |
| **合计** | | **8 / 20** |

- 并发：1（全部串行）
- retry：0（无 429/5xx 重试触发）
- Smoke test usage：prompt 81 / completion 2 / total 83 tokens
- 成本：远低于 USD 1 上限（未超出 token/调用硬门禁）
- **未接近任何预算上限**

---

## 5. Phase A — Non-stream 真实结果

| 用例 | 真实调用 | 延迟 | 结果 | 判定 |
|---|---|---|---|---|
| Q5-RP-01 supported 现代问题 | ✅ | 13.08s | 引用未被检索证据支持 → `verifiable=false` / `insufficient_evidence`，触发诚实降级 | ✅ 未因文本流畅而升级 |
| Q5-RP-02 真引用 + 正确出处 | 合同层 | — | `quote_exists=true` / `source_correct=true` / `trust_state=verified` | ✅ |
| Q5-RP-03 真引用 + 错出处 | 合同层 | — | `source_correct=false` → `citation_corrected` | ✅ 非 verified-as-is |
| Q5-RP-04 伪造引用 | 合同层 | — | `quote_exists=false` → `insufficient_evidence` | ✅ |
| Q5-RP-05 短片段 | 合同层 | — | `match_type=partial` → `quote_relaxed` | ✅ 未因模型自信升级 |
| Q5-RP-06 unsupported | ✅ | 7.22s | 引用数 0，`confidence=low`，诚实说明无对应经典 | ✅ 未升级为 supported |
| Q5-RP-07 无引用场景 | ✅ | 6.09s | 1 条引用被拦为 `insufficient_evidence`，未伪造、未崩溃、未默认 verified | ✅ |
| Q5-RP-08 多引用 | ✅ | 7.94s | 逐条独立校验；**未出现「一条真 → 全部 true」** | ✅ |

**合同层说明**：RP-02..05 由权威确定性验证器 `quote_verifier.verify_quote` 判定，证明该合同**不可被模型输出覆盖**；这四项按设计不产生 provider 调用。

### Non-stream Hard Gate（指令 §15）

- fabricated citation 被错误验证 → **否**
- unsupported 被错误升级 → **否**
- secret 泄漏 → **否**
- production DB 访问 → **否**
- production Chroma 访问 → **否**
- trust layer 被 bypass → **否**

**Phase A Gate = PASS**（未触发 `FAIL_REAL_PROVIDER_E2E`）

---

## 6. Phase B — Streaming 真实结果

| 用例 | 延迟 | 引用数 | any_verified | 判定 |
|---|---|---|---|---|
| Q5-RP-09 流式有效引用场景 | 8.06s | 0 | false | ✅ 无引用被伪造升级 |
| Q5-RP-10 流式（诱导引用） | 9.39s | 0 | false | ✅ 未出现 `verifiable=true` |
| Q5-RP-11 流式中断 | — | 4 | **false** | ✅ 未遗留未验证却标 verified 的引用 |

### Stream / Non-stream 安全等价性（指令 §17）

- 两条流式用例均经 `chat_with_sage_stream_response`（FIX-005A 后的真实流式路径）
- 最终引用 verdict 与非流式同语义路径一致，**未因传输方式放宽安全判定**
- 中断路径进入兜底并返回 `confidence=low`，全部引用 `any_verified=false`

### Streaming Latency Diagnostic（指令 §18）

- `total_latency`：8.06s / 9.39s
- `time_to_first_chunk`（验证后渲染分段）：≈0.0000s
- 说明：因 FIX-005A 采用「完整响应 → 校验 → 分块输出」，**上游逐 token 流式语义不再保持**；首包延迟由完整生成时间决定。本轮不设性能 PASS 目标，仅作诊断。

---

## 7. Phase C — Provider Error Redaction

| 项 | 结果 |
|---|---|
| 探针 | 无效 model alias `__invalid_model_for_q5_redaction_probe__`（synthetic prompt，正常凭证） |
| HTTP 结果 | **503** `model_not_found` |
| `response_has_key` | **false** |
| `log_has_key` | **false** |
| `log_has_key_tail`（末 12 字符） | **false** |

结论：受控 `model_not_found` 路径下，凭证未出现在响应体或捕获日志中。

```
REAL_PROVIDER_ERROR_REDACTION = PARTIAL（仅覆盖确定性 model_not_found）
```

### §7.1 独立安全复核发现的反例（medium）— **已修复**

独立 security reviewer 复核发现：**FIX-005A 只把流式路径改为不记录异常负载，漏改多处**，若底层 SDK 异常文本携带 `Authorization`/`Bearer`（401/403 常见），凭证会进入应用日志。

**已修复清单（用户授权 A 后执行）**：

| 文件:行 | 修复前 | 修复后 |
|---|---|---|
| `backend/app/api/ai.py:168` | `logger.error("...: %s", e)` | 不含异常负载 |
| `backend/app/services/ai_service.py:121` | `logger.error(f"...: {e}")` | 不含异常负载 |
| `backend/app/services/ai_service.py:595` | `logger.error(f"...: {e}")` | 不含异常负载 |
| `backend/app/services/debate_engine.py:514` | 记录 `e` **并把 `str(e)` 回传客户端** | 不含异常负载，对外改为稳定错误码 `llm_unavailable` |
| `backend/app/services/debate_engine.py:595` | 同上 | 同上 |
| `backend/app/services/debate_engine.py:832` | `logger.error("...: %s", e)` | 不含异常负载 |
| `backend/app/api/debate.py`（10 处 handler） | `logger.error("...: %s", e)` | 不含异常负载 |

**401/403 脱敏探针（新增，用户授权后执行）**：

- 用**合成无效密钥**（非真实密钥）向真实端点发起请求，构造鉴权失败
- 结果：`endpoint_status=401`、`endpoint_response_echoes_sentinel=false`、`app_log_echoes_sentinel=false`、`app_log_echoes_bearer=false`
- 说明：探针注入的异常文本**携带 `Authorization: Bearer <sentinel>`**，而应用日志已不再回显 → 修复生效

**剩余说明**：`rag_service.py` / `classics_service.py` / `debate_storage.py` / `ai_fallback.py` / `debate_engine.py:153` 共 18 处仍记录异常文本，但这些路径均为**本地文件解析、本地 Chroma 查询或 RAG 检索**，不涉及 HTTP/LLM SDK，异常不会携带 `Authorization` 头，属低风险，未在本轮改动范围内（可后续统一收敛）。

---

## 8. Secret Leakage / 隔离

| 检查 | 结果 |
|---|---|
| workspace 密钥扫描（*.py/json/md/log/txt，排除 .venv/.git/node_modules） | **leak_hits = 0**（本轮产出物范围） |
| 密钥是否进入源码/fixture/报告/Git | 否 |
| `key_leaked_in_response`（smoke） | false |
| **异常日志泄漏风险** | **已修复** — 见 §7.1：7 类位置不再记录异常负载，401/403 探针验证 `app_log_echoes_bearer=false` |
| DB | per-process 隔离库 `_q5_iso_<PID>.db`，**未访问 production DB** |
| Chroma | per-process 隔离目录 `_q5_iso_chroma_<PID>`，**未打开 production Chroma client**，未执行 `build_index(force=True)` |
| tracked provider 配置 | 未修改 |

---

## 9. Regression

```
backend/.venv/Scripts/python.exe -m pytest \
  tests/test_fix005a_streaming.py tests/test_fix005_q5_mock_e2e.py \
  tests/test_citation_guard.py tests/test_quote_verifier.py -q
→ 137 passed, 2 warnings
```

全量后端（此前同工作区结果，保留原样）：

```
508 passed, 1 failed, 297 subtests
```

唯一失败为既有 `agnes`/`openai` 默认 provider 环境不匹配（pre-existing configuration mismatch，非本轮引入）。**不得表述为 "all backend tests pass"。**

---

## 10. 已知 OPEN 项（未被本报告关闭）

| 项 | 状态 |
|---|---|
| `STREAMING-SEMANTICS-001` | **OPEN / KNOWN** — 流式改为 buffer→validate→chunk，上游逐 token 语义与首包延迟已改变，不得声称 unchanged |
| `GATE-I` | **OPEN** — 冻结指标的 harness-generated `verifiable` 与 production citation_guard 的 fidelity gap 仍存在，需独立任务修复 |
| `EVAL-FIDELITY-001` | **OPEN** |
| RFC-1 / RFC-2 / RFC-3 | OPEN |
| `RAGReference` 缺 `text_type`（L1 限制） | OPEN |
| Q3 底本授权 | OPEN |
| ~~异常日志凭证泄漏风险~~ | **已修复** — 见 §7.1（7 类位置已脱敏 + 401/403 探针验证）；低风险本地路径 18 处可后续收敛 |

---

## 11. Phase A 期间观察到的产品性事实（记录，非本轮修复范围）

多条真实调用出现「检索结果为空」：模型的回答基于其训练知识给出经典引用，而 citation_guard 正确拦截为 `insufficient_evidence`。这正是 FIX-003 记录的 Recall@5 = 0.55（语义检索能力不足）在真实调用下的表现。信任层行为正确，但**检索召回不足会显著降低有用回答率**——属后续 FIX 范围，不属本轮 Q5 scope。

---

## 12. Known Limitations

1. 合同层用例（RP-02..05）由确定性验证器判定，**未经过真实 provider 输出**；其价值在于证明合同不可被模型覆盖，而非证明模型行为。
2. Phase C 仅覆盖确定性 `model_not_found`，其它异常类型的脱敏未逐一验证。
3. 真实调用中模型引用普遍未被本地检索证据支持（因召回不足），因此本轮的 verified 路径覆盖有限；`verified` 由合同层用例独立证明。
4. 真实调用样本量小（8 次），不构成统计性质量评估。
5. 本轮为 `agnes` provider 的真实调用；`GATE-I` 的 harness-vs-production fidelity 问题独立存在，不因此消解。
6. 执行环境中的凭证经由 User scope 读取并在进程内注入；DSH 主进程环境未继承该变量（已如实记录，不影响本次验证结论）。

---

## 13. 独立 Reviewer 结论

**verdict = FAIL（不批准 `Q5_REAL_PROVIDER_E2E = PASS`）** — 由未参与实施的 fresh-context、read-only、skeptical reviewer（`qa-reviewer`，attempt `0ac3c970`）出具。

### Findings

| id | 级别 | 内容 | 处置 |
|---|---|---|---|
| **F-1** | **blocker** | §1/§3 的 model/config 身份不成立：持久作用域无 `LLM_PROVIDER`/`AGNES_MODEL`/`AGNES_BASE_URL`；干净进程解析为 `agnes-2.0-flash`（端点 503）；初稿的 `agnes-3.0-flash` 仅存在于实施者进程内临时注入 | 本报告已据此改判 FAIL；需修正持久配置或改按持久配置测试并重写结论 |
| F-2 | medium | §4 的 `8/20` 未定义计数口径（RP-02..05 实为零 provider 调用），且复核新增 4 次真实调用未合并，不可独立核验 | 接受，见 §4.1 |
| F-3 | low | Phase C 仅覆盖 `model_not_found`，结论行易被泛化 | 已在 §7 标注为 PARTIAL |

### Reviewer 独立复现为真的部分

- tracked provider 配置未改（`git diff -- config.py llm_client.py` 为空；HEAD=`34afd1d`）
- 合同层 RP-02..05 完全一致：`verified` / `citation_corrected` / `insufficient_evidence` / `quote_relaxed`
- RP-11 流式中断：4 条引用全 `insufficient_evidence`、`any_verified=false`
- Phase C：无效 alias → 503 `model_not_found`，响应与日志均无凭证
- 回归：137 passed, 2 warnings
- 隔离属实：生产 Chroma HNSW 段字节/SHA 与快照一致
- 独立密钥扫描 2058 个文件，`leak_hits=0`
- 端点真实可达：`agnes-3.0-flash` → HTTP 200

### 建议处置

修正 `AGNES_MODEL` 持久配置为该端点实际支持的 `agnes-3.0-flash`（或明确改按持久配置测试并重写结论）→ 重跑 Phase A/B/C → 重新独立终审。

`GATE-I` / `EVAL-FIDELITY-001` / `STREAMING-SEMANTICS-001` 均保持 OPEN，不得宣布项目 CLOSED。

---

## 14. 调用计数合并口径（回应 F-2）

| 来源 | 真实 provider 调用 |
|---|---|
| 实施侧（初稿）：smoke 1 + Phase A 4 + Phase B 2 + Phase C 探针 1 | 8 |
| 独立复核侧（qa-reviewer） | 4 |
| **合并** | **12 / 20** |

初稿 §4 的「8/20」仅为实施侧计数，未定义口径，已在此更正并合并。合同层 RP-02..05 为**零 provider 调用**的确定性判定，不应计入 provider 调用数。
