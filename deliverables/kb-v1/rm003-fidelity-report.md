# RM-003 / EVAL-FIDELITY-001 — Acceptance Report

## TASK ID

`RM-003` / `EVAL-FIDELITY-001` — 把冻结的 `fabricated_classical_quote` 指标接到**生产**
`citation_guard.guard_citations` 裁决（thin adapter），消除 run_eval 合成 `verifiable` 的保真缺口。

## STATUS

- **实施（本轮）**：已完成（thin adapter + 聚焦测试 + 基线 + 报告落盘）。
- **独立复现（本轮）**：由 Codex 在 fresh-context 独立复现（见 §Tests / §Eval）。
- **报告结论**：`READY_FOR_CODEX_REVIEW`。**不**宣称项目或任务整体 PASS —— 存在多个
  仍未关闭的 Gate 失败与显式限制（见 §Limitations）。
- 项目级接口没变：`metrics.py` / `TARGETS` / Gold / 冻结 JSONL / 冻结公式，**字节不变**。

## Model & Routing 证据 / 404

- 本任务在 deepseek-harness provider 上执行。
- 先前对模型 **`xiaobai/deepseek-v4.1-flash`** 的请求反复收到 **404**（模型 / 路由不可用）。
- 经授权，路由回退到本会话**已配置**的 deepseek-harness 模型
  **`shushen/deepseek-v4-flash-0731`**（同一 provider，**未切换 provider**）。
- 本会话确认无权限修复、也未修改工作区 ACL；`pwsh` 执行通道因工作区根目录
  `grantWrite` 供给失败（`SetNamedSecurityInfoW failed (Win32 5): grantWrite(D:\systemDir\Desktop\悟典)`）
  而不可用 —— 这解释了为何部分命令（py_compile）需由 Codex 侧独立执行。

## Baseline vs 本轮复现（必须区分）

- **baseline**：`deliverables/kb-v1/rm003-fidelity-baseline.json`（本轮由实施者写入）。
  该文件对 `eval/adversarial_quotes.jsonl` 全部 20 条逐条记录
  `case_id / quote / claimed_source / expected / harness_verdict / production_verdict /
  difference / root_cause`，并识别：
  - 现有合成 verifiable：`eval/scripts/run_eval.py:129`（`_quote_prediction` 内
    `verifiable = quote_exists and source_correct and match_type != 'partial'`）。
  - 应替换成的生产裁决函数：`citation_guard.guard_citations(...) -> GuardedCitation.verifiable`
    （背后是 `trust_state.decide_trust_state` + `trust_state.is_verifiable`）。
  - **baseline 的 verdict 为静态推导**（runtime 在实施会话不可执行），**非实测**；
    已在文件内 `"measurement_status": "runtime NOT executed"` 明确标注，并给出用于实测的命令。
- **本轮复现**：下列 §Tests / §Eval 的结果由 Codex 在 fresh-context **独立运行得到**，
  属于「本轮独立复现」，不是 baseline 的静态推导值。
- **区分结论**：baseline 先于源码/测试改动写入；本轮独立复现结果证实了改后的行为。

## Files Changed

仅在 RM-003 允许范围内改动 / 新增：

1. **`backend/app/services/citation_guard.py`**（改）
   - `GuardedCitation` 增加 `exact_match: bool = False` 与 `match_type: str = "none"` 两个字段
     （由 `guard_citations` 内部已算出的谓词回填），便于 adapter 字段映射。
   - 新增纯函数 `metric_prediction_from_guarded(g) -> {quote_exists, exact_match,
     normalized_match, source_correct, correct_source, trust_state, match_type,
     similarity, verifiable, verdict_basis}`，**仅做字段映射**，不重复任何匹配/出处/完整性门/
     L1/trust-state 逻辑。
   - `__all__` 加入 `metric_prediction_from_guarded`。
2. **`eval/scripts/run_eval.py`**（改）
   - 新增 `_production_refs()`：从 `quote_verifier.load_corpus()` 构造 feed 给
     `guard_citations` 的 refs（`original` + `source`；**刻意省略 `text_type`** 以镜像生产
     `RAGReference` 形态，不伪造元数据）。
   - 新增 `_production_adversarial_prediction(rec, refs)`：调 `guard_citations` → 经
     `metric_prediction_from_guarded` 映射为冻结指标预测形状。
   - `eval_adversarial()`：adversarial 预测改走**生产裁决**路径（不再用 `_quote_prediction`
     的合成 `verifiable`），并在结果里追加 `diagnostic_verdict_path`（说明来源），
     保留原有 `diagnostic_fragment_displayed_as_classic` 诊断。
3. **`backend/tests/test_eval_fidelity.py`**（新增）
   - 聚焦测试（11 条），覆盖 SPEC 要求的逐类用例，全部使用隔离 fixture（本地 refs），
     **不写生产 Chroma**。
4. **`deliverables/kb-v1/rm003-fidelity-baseline.json`**（新增）
   - 基线（见上）。先于源码/测试改动写入。
5. **`deliverables/kb-v1/rm003-fidelity-report.md`**（新增，本文件）。

**未改动**：`eval/scripts/metrics.py`、`TARGETS`、`eval/adversarial_quotes.jsonl` 等冻结 JSONL、
`backend/data`（Gold/语料）、`backend/chroma_db`（生产索引）、前端、以及任何 FIX-002/003/004/005A
无关代码；`git` 历史未变。

## Adapter Path（thin，不重复逻辑）

```
run_eval.eval_adversarial
  -> _production_refs()                     # corpus -> [{original, source}], 无 text_type
  -> _production_adversarial_prediction(rec, refs)
       -> citation_guard.guard_citations([{id, source, original}], rag_refs=refs)
            # 内部: decide_trust_state + is_verifiable + 长度/白名单/出处/片段/L1
       -> metric_prediction_from_guarded(guarded[0])   # 仅映射字段
  -> compute_fabricated_classical_quote(records, preds)  # 冻结实现，未改
```

## Tests

- 命令：`backend\.venv\Scripts\python.exe -m pytest tests/test_eval_fidelity.py -q`（backend 工作目录）
- 结果：**11 passed**
- 覆盖用例（与 DSH-RM003-SPEC §Mandatory Tests 对齐）：
  absent/fake quote、exact correct quote、wrong source、short fragment、commentary/L2 quote、
  cross-sentence fusion、traditional/simplified punctuation variant、real corpus quote、
  以及「冻结指标消费生产裁决 / 无合成 verifiable 可覆盖」的断言。
- `py_compile`：**PASS**（源码语法检查通过）。

## Regression

- Backend full suite：**522 passed, 1 failed, 297 subtests passed**。
  唯一失败为 `tests/test_ai_provider.py::TestProviderSwitching::test_default_provider_is_openai`：
  当前 `backend/.env` 使 `Settings().LLM_PROVIDER` 为 `agnes`，而该测试期望 `openai`。
  这是已知的基线环境冲突，未涉及 RM-003 文件或路径。
- Frontend `npm test`：**41 passed**（23 Vitest files plus existing wiring checks）；
  runtime asset check按脚本约定因未启动 localhost 服务而跳过。

## Canonical Isolated Eval（本轮独立复现）

运行方式：从 `backend` 目录运行、临时输出路径、临时 `JWT_SECRET_KEY`、
默认复制 Chroma 到隔离目录（`used_production=false`）；**未传 `--use-production-chroma`**。
runner 返回码 `0`（详见 §Runner 返回码限制）。

| Gate | 指标 | 值 | 分母 | 冻结阈值 | 判定 |
|---|---|---|---|---|---|
| D | quote_exactness | **18/18 = 1.000** | 18 | >= 0.99 | PASS |
| H | source_attribution | **18/18 = 1.000** | 18 | >= 0.98 | PASS |
| I | fabricated_classical_quote | **0** | 20 | == 0 | PASS |
| E | unsupported_correct_refusal | **11/12 = 0.9166666667** | 12 | >= 0.95 | **FAIL**（failure `uq-0009`）|
| F | Recall@5 | **0.55** | 40 | >= 0.90 | **FAIL** |
| G | core_claim_evidence_coverage | **40/40 = 1.000** | 40 | >= 0.95 | PASS |
| J | school_leakage | **0/19 = 0.0** | 19 | < 0.01 | PASS |

- 诊断（**非**冻结指标）：`diagnostic_fragment_displayed_as_classic = 1`（case `aq-0011`）。
- **完整阈值映射**：D=0.99、E=0.95、F=0.90、G=0.95、H=0.98、I=0（绝对计数）、J<0.01。
- **分母均未变**：D/H 分子分母、绝缘 fabricated=20、E=12、F=40、G=40、J=19，均与冻结口径一致。
- 这些是「本轮独立复现」的新鲜测量值；历史 `eval/eval-run.json` 的旧值（如 E=0/12）不代表本轮。

### Runner 返回码限制

`run_eval.main()` 在写好结果后总是返回 `0`，仅在「显式启用生产 Chroma 且内容指纹变化」时返回 `2`。
故 **Gate FAIL 时 runner 仍返回 0** —— 回归判定必须以指标数值为准，不能只看进程退出码。
本轮 `rc=0` 与 `unsupported_correct_refusal`/`Recall@5` 两处 FAIL 并存，符合该限制。

## Regression

- backend full pytest：522 passed, 1 failed, 297 subtests passed。唯一失败为 tests/test_ai_provider.py::TestProviderSwitching::test_default_provider_is_openai：当前 backend/.env 将 LLM_PROVIDER 解析为 agnes，而测试期望 openai；这是环境/配置阻塞，不能计为 PASS。
- frontend npm test：23 个文件、41 个测试通过。
- frontend npx tsc --noEmit：exit 0。
- runtime-assets：因未启动前端服务而跳过。

## Production Chroma Safety

- **未打开生产索引客户端**；未传 `--use-production-chroma`；未 `build_index(force=True)`。
- 评测使用**隔离临时副本** + 临时环境变量（`CHROMA_PERSIST_DIR` 指向隔离目录），
  仅在必要时复制生产文件到临时目录（只读复制）。
- **指纹（只读，before == after，未变）**：
  - `chroma.sqlite3`：4,120,576 bytes；SHA-256 `4C97B5D03991E436457206D7D26682C71C634D2C09F93F639E769172479EDA31`
  - `data_level0.bin`：167,600 bytes；SHA-256 `2A3617E926A15F4587921C9B8245D4838B0C3EA7B7474AED135629228AD657F0`
  - 上述所列生产索引文件全部 unchanged（before == after）。
- 指纹仅证明“对应文件字节未变”，**不**作为语义完整性证明（AGENTS.md 纪律）。

## Limitations（如实保留，不关闭）

1. **`RAGReference` 缺 `text_type`**：生产 ref 无 `text_type`，`rag_service` 未传播；
   `citation_guard` 对缺失 `text_type` 的 ref 按既有兼容性回退视为 L1。Adapter 亦**省略**
   `text_type` 以镜像生产形态、不伪造元数据。因此 **RC4（L2 注疏不得判 verified）在
   citation_guard 这条路径上尚未统一强制**，仅由权威实现 `quote_verifier.verify_quote`
   强制；缺失元数据本身是该限制的原因。
   - 已验证：ref 显式带 `text_type="commentary"` 时 `guard_citations` 得到 `quote_relaxed`
     （非 verified、不可展示）；`verifiable` 仍为 True（quote_relaxed 属 verifiable 态，
     这是生产语义，不是“可作经典原文展示”）。
2. **`citation_guard` 无 §3.3 跨句界规则**：`guard_citations` 的 `exact_match`
   （`quote_exists ∧ source_correct ∧ 非片段`）不执行契约 §3.3 句界规则 ——
   该规则只在 `verify_quote`（权威实现）落实。因此把冻结 fabricated 指标接到生产裁决后，
   跨句拼接串若在语料中是连续子串仍会被判 `quote_exists=True`；当前冻结对抗语料
   不含此类拼接，故 fabricated 计数不受影响，但该缺口单独记录（跨句/句界规则未完全合同化到 guard）。
3. **`aq-0011` 冻结标签/RFC-2 诊断**：`diagnostic_fragment_displayed_as_classic=1`（aq-0011，
   `士不可以不弘毅` 被判 verified/verifiable=True），与冻结标签
   （expected.verifiable=False / quote_relaxed）冲突 —— 属 RFC-2 式“真实完整短句 vs 摘句”
   口径问题，非 EVAL-FIDELITY-001 引入；保持 open。
4. **EVAL-FIDELITY-001 本身**：本适配让冻结指标消费生产裁决，提升了**测量保真**，
   但未改变任何冻结分数；不消除 §1/§2 中的 guard 缺口。
5. **`RFC-1 / RFC-2 / RFC-3`**：仍 open（数据集/公式/句界完整性/归一化表统一），不因本次关闭。
6. **Q3（语料授权/底本）**、**Q5（真实应用 LLM 凭证 / 端到端 E2E）**：仍 open。
   - retrieval 指标（Recall@5 等）：当前环境的 ChromaDB 包可用，隔离评测使用生产索引的
     临时副本；但配置使用确定性的本地 hash embedding 而非语义 embedding，故 F 值不代表
     生产语义召回。
   - 未做真实 LLM 端到端验证（无凭证，Agnes 环境失败为已知基线问题，与本次改动无关）。

## Commit

- **未提交**（无 commit SHA）。按治理要求仅精确暂存经授权文件，本会话未创建 commit。

---

## 结论

实施完成 + Codex 独立复现通过（tests 11 passed；canonical eval 见上；py_compile PASS；
生产 Chroma 指纹 before==after 未变）。E 与 F 两处 Gate 仍 **FAIL**，且存在
§Limitations 所列缺口。**不**宣称项目或任务整体 PASS。

**`READY_FOR_CODEX_REVIEW`**
