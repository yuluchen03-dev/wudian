# FIX-004 实施后最终独立验收报告

- **日期**：2026-10-10
- **审查对象**：FIX-004 工作区补丁（未提交）
- **审查角色**：队长接管 reviewer 任务后的只读独立核验；原 reviewer 因 QUOTA 不可恢复失败。队长未参与 FIX-004 实施，未修改源代码、测试或冻结资产。
- **审查边界说明**：因原 reviewer 的 quota failure，本报告不是原计划中的 fresh-context reviewer 报告；为响应用户“换模型继续完成”，由已切换到 GPT-6 Luna 的队长完成其余只读核验并明确记录此限制。实现者、QA、DevOps、安全成员分别提供的证据均作为成员报告引用，不冒充队长亲自重跑的证据。
- **执行边界**：评测走 `run_eval.py` 默认隔离副本；pytest 走 `conftest.py` 的 per-PID Chroma；未使用生产 Chroma 客户端；未提交、push 或改 Git 索引。

---

## 0. 最终结论

> # **PASS — FIX-004 / GATE-G**

FIX-004 修复了核心观点证据覆盖的 corpus-id 对齐缺陷。独立隔离评测得 **GATE-G = 40/40 = 1.000**，冻结目标为 ≥0.95；原 30/40=0.75 基线中的 10 条（rg-0021..rg-0030）均恢复为 supported，分母仍为 40。改动不修改冻结公式、TARGETS、Gold 或判据。

此 PASS **仅表示 FIX-004 及其 GATE-G 验收通过**，不代表整个 KB-V1 达到全部 Gate，也不关闭其他阻塞：E=11/12=0.9167（FIX-002）、F=0.55（FIX-003）仍低于目标；Q5、EVAL-FIDELITY-001 等开放事项继续保持 OPEN。

---

## 1. 实现范围与 diff 审查

`t2` 报告及队长只读 `git diff` 核对一致：

- 唯一 FIX-004 tracked 源码改动：`backend/app/services/quote_verifier.py` 的 `_load_debate_classics`；循环键变量用于输出 id，`passage_id` 从裸 `verse_id` 变成 `debate:{sage_key}:{verse_id}`。
- 新增定向测试：`backend/tests/test_fix004_claim_coverage.py`。
- 与 Gold 双层 ID 同构，并与 FIX-003 D1 的 `debate:{sage_key}:{verse_id}` 形式一致。
- `verify_quote` 的文本/出处判断逻辑没有因 id 变更而修改；`passage_id` 用于语料索引，评测按 Gold id 查 corpus 后再走既有 quote/source 验证。
- 未改 `metrics.py`、TARGETS、`retrieval_gold.jsonl`、`run_eval.py`、contract、生产 Chroma 或 `eval/eval-run.json`。HEAD 记录为 `899519b`，未提交。

补丁范围符合 t1 设计，无发现缩小 denominator、弱化断言或以诊断指标代替 Gate 的迹象。定向测试覆盖 Gold ID 可解析性、40 条覆盖、基线失败转 supported、旧 30 条无回退、儒派/注疏键格式、D 门关键样例、错误出处和伪造引文拒绝，以及 Gold 引用的四派经典出处。

---

## 2. 独立冻结评测结果

队长使用 `backend/.venv/Scripts/python.exe eval/scripts/run_eval.py --out %TEMP%\\wudian_fix004_review_eval.json` 独立执行；运行器默认复制 Chroma 到临时隔离目录，报告标记 `used_production=false`。结果：

| Gate | 本轮隔离实测 | 目标 | 结果/解释 |
|---|---:|---:|---|
| D quote_exactness | 18/18 = 1.000 | ≥0.99 | PASS，无回退 |
| E unsupported_correct_refusal | 11/12 = 0.9167 | ≥0.95 | 未达；FIX-002 已记录阻塞 uq-0009 |
| F Recall@5 | 22/40 = 0.55 | ≥0.90 | 未达；FIX-003 已记录语义检索阻塞 |
| G core_claim_evidence_coverage | **40/40 = 1.000** | **≥0.95** | **PASS；分母保持 40** |
| H source_attribution | 18/18 = 1.000 | ≥0.98 | PASS，无回退 |
| I fabricated_classical_quote | 0 | 0 | PASS（冻结口径） |
| J school_leakage | 0/19 = 0.000 | <0.01 | PASS，分母保持 19 |

G 门失败明细为空。F 门当前失败、E 门 uq-0009 失败均如实保留；运行器还报告 diagnostic `diagnostic_fragment_displayed_as_classic=1`（aq-0011），它不是冻结 Gate I，不能据此声称 I 失败或把它并入 I。

QA 成员 `t3` 另外以 run_eval 隔离副本和冻结公式直接重算双通道复现 G=40/40，确认 8/8 冻结资产 SHA 与 handoff snapshot 匹配、denominator 未缩小。其证据输出位于临时目录 `%TEMP%\\wudian_fix004_t3\\eval-run.json`；此处作为成员报告引用。

---

## 3. 回归测试

队长独立复跑：

- `backend/.venv/Scripts/python.exe -m pytest tests/test_fix004_claim_coverage.py tests/test_quote_verifier.py tests/test_quote_contract.py tests/test_claim_evidence.py tests/test_citation_guard.py -q`（backend 工作目录）：**190 passed，5 subtests passed**。
- `backend/.venv/Scripts/python.exe -m pytest tests -q`（backend 工作目录）：**496 passed，1 failed，297 subtests passed**；唯一失败 `test_ai_provider.py::TestProviderSwitching::test_default_provider_is_openai`，实际值 `agnes` 而断言期望 `openai`。该失败涉及 gitignored `backend/.env` 的环境配置，不在 FIX-004 diff 中；DevOps 报告此前同测试从不加载 backend/.env 的仓库根目录对照通过（classification A）。它仍是全套测试的真实失败结果，故不写成“全量全绿”。
- 队长独立复跑前端：`npx tsc --noEmit` + `npm test`：exit 0；Vitest **23 files / 41 tests passed**。`runtimeAssets` 因无本地 :3000 服务而 SKIP（非运行时资产验证通过）。DevOps 也报告同样前端通过，FIX-004 未触碰 frontend。

因此没有发现 FIX-004 引入的新失败；现有 agnes 配置失败和 runtimeAssets 环境跳过仍须显式保留。

---

## 4. 冻结资产及 Chroma 数据安全

- 队长逐一校验 handoff snapshot 列出的 8 个冻结文件（7 个 eval JSONL + `eval/scripts/metrics.py`）：字节数和 SHA-256 **8/8 全匹配**。
- 生产 Chroma 只读文件指纹：snapshot 中 5 个 HNSW/索引文件的字节数和 SHA-256 **5/5 匹配**；未打开生产数据库客户端。成员 security 的隔离副本内容指纹为 `doc_count=143`、`id_md5=58795f71e427304cbe02a3e85f49498d`，与 handoff / 前轮记录一致。
- `chroma.sqlite3` 大小仍为 4,120,576 bytes；队长此次观察 SHA-256 为 `e15965864ff3572cecbbfaf3730cd9cad358f89b878f1b8c890543254c23ee94`，不同于 handoff SHA。此前各 FIX 活动期间也出现不同 sqlite SHA。按仓库 `_chroma_fingerprint.py` 文档，Chromadb 打开会写 catalog 元数据，sqlite SHA 不作为内容完整性判据。成员 security 亦如实提示 FIX-004 活动期 mtime 不能排除并行探针曾短暂打开生产目录；故本报告不把 sqlite SHA 变化解释成 FIX-004 数据变更，也不声称仅凭 SHA 证明内容未变。HNSW 字节与隔离副本内容指纹支持“索引内容未见变化”；任何并行探针窗口限制继续披露。

---

## 5. 保持 OPEN 的事项与限制

以下事项未由 FIX-004 关闭：RFC-1/2/3、EVAL-FIDELITY-001、citation_guard/RAGReference `text_type` L1 缺口、Q3 底本授权、Q5 真实 LLM 凭证与端到端验证、FIX-002 的 uq-0009↔sc-0003 张力、FIX-003 的语义硬底 rg-0003/0021/0035/0036。FIX-004 只修复 G 门 Gold/corpus id 对齐。

原 reviewer 任务因 QUOTA 失败，由用户明确要求换模型后队长接管。本报告透明保留这一审查上下文限制，不伪称原 reviewer 已完成 fresh-context 工作；队长未参与实现，并独立读取 diff、执行隔离冻结评测、hash 核验与相关测试，补足了 t6 所需证据。
