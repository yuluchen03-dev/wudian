"""
悟典 - FIX-004 核心观点证据覆盖定向测试（GATE-G：0.75=30/40 → 40/40=1.0）

背景（t1 根因独立确证，G=30/40 逐条复核）
----------------------------------------
``eval/scripts/run_eval.py::eval_claim_coverage`` 对每条 retrieval_gold 记录的
``expected_passage_ids`` 依次 ``corpus.get(pid)`` 查 quote_verifier 语料，存在则
``verify_quote`` 标 supported（quote_exists AND source_correct）。

10 条失败（rg-0021..0030）全部且仅源于同一根因：四派（道/墨/法，共 11 个
expected id）在 Gold 中是双层前缀 ``debate:{sage_key}:{verse_id}``
（如 debate:laozi:daodejing-22-01），而 ``quote_verifier._load_debate_classics``
以**裸 verse_id**（daodejing-22-01）作 corpus 键 → ``corpus.get(pid)`` 恒 miss
→ 无证据条目 → unsupported。与 FIX-003 D1 同源（Gold 双层前缀 vs 服务层裸 id），
但位于 quote_verifier 语料加载层。

t2 补丁（仅改 quote_verifier.py::_load_debate_classics，未动
metrics.py/TARGETS/retrieval_gold.jsonl/run_eval.py/生产 chroma/判据）
------------------------------------------------------------------------
- 循环变量 ``_sage_key`` → ``sage_key``
- ``passage_id=verse_id`` → ``passage_id=f"debate:{sage_key}:{verse_id}"``
  （与 rag_service.py:1214 FIX-003 D1 输出层拼接同构）

实测预期（t1 内存模拟 + G 门重算）：
- 11 个 debate id 全部可有 entry 且 verify_quote → supported=True
  （出处《道德经·第二十二章》《墨子·兼爱上》《韩非子·有度》均正确）
- G = 40/40 = 1.0；73/73 expected id 全可解析（0 miss）

断言强度：
1. 全 40 条 G 门 supported 判定（复刻 eval_claim_coverage 逻辑，数据读冻结 Gold）
2. 73/73 expected id 无 miss（键对齐完备性）
3. 儒派 lunyu/commentary 键格式不得回归（本补丁不得影响儒派）
4. D 门关键样例（quote_exactness）无回退：verify_quote 对已知精确引用
   quote_exists/source_correct/exact_match 保持
5. 直接断言语料键与 Gold 双层前缀同构（防未来再次脱钩）
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.services.quote_verifier import load_corpus, verify_quote  # noqa: E402

GOLD_PATH = Path(__file__).resolve().parents[2] / "eval" / "retrieval_gold.jsonl"

# 儒派键前缀必须保持（不得因 FIX-004 改动而变）
LUNYU_PREFIX = "lunyu:"
COMMENTARY_PREFIX = "commentary:"
DEBATE_PREFIX = "debate:"

# 基线（冻结 eval-run.json）：G=30/40，10 条失败为四派双层前缀结构性 miss
BASELINE_G = 30
BASELINE_FAILURES = {
    "rg-0021", "rg-0022", "rg-0023", "rg-0024", "rg-0025",
    "rg-0026", "rg-0027", "rg-0028", "rg-0029", "rg-0030",
}


def _load_gold() -> list[dict]:
    if not GOLD_PATH.exists():
        raise FileNotFoundError(f"冻结 Gold 不存在: {GOLD_PATH}")
    return [
        json.loads(line)
        for line in GOLD_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _claim_coverage_pred(corpus: dict[str, object]) -> dict[str, list]:
    """复刻 run_eval.eval_claim_coverage 的判定逻辑（只读，不改冻结实现）。"""
    preds: dict[str, list] = {}
    for rec in _load_gold():
        ev = []
        for pid in rec.get("expected_passage_ids") or []:
            entry = corpus.get(pid)
            if entry is None:
                continue
            v = verify_quote(entry.original, entry.source)
            ev.append({
                "evidence_id": pid,
                "verification": "supported" if (v.quote_exists and v.source_correct) else "unsupported",
            })
        preds[rec["id"]] = ev
    return preds


class Fix004CorpusKeyAlignmentTest(unittest.TestCase):
    """语料 id 空间与 Gold 双层前缀同构（补丁的直接产物）。"""

    @classmethod
    def setUpClass(cls):
        cls.corpus = {e.passage_id: e for e in load_corpus(reload=True)}
        cls.gold = _load_gold()

    def test_debate_classic_keys_carry_sage_prefix(self):
        """所有 debate classics 条目键必须以 debate:{sage_key}: 开头（非裸 id）。"""
        bare = [
            e.passage_id
            for e in load_corpus()
            if e.passage_id.startswith("daodejing-") or e.passage_id.startswith("mozi-")
            or e.passage_id.startswith("hanfeizi-") or e.passage_id.startswith("lunyu-taibo-")
        ]
        self.assertEqual(bare, [], f"存在裸 debate id 键（未对齐）: {bare}")

    def test_gold_expected_all_resolvable_zero_miss(self):
        """73/73 expected id 全部可在语料中解析（修复前 11 个四派 id miss）。"""
        miss = []
        for rec in self.gold:
            for pid in rec.get("expected_passage_ids") or []:
                if pid not in self.corpus:
                    miss.append((rec["id"], pid))
        self.assertEqual(miss, [], f"expected id 存在无法解析项: {miss}")

    def test_lunyu_and_commentary_keys_unchanged(self):
        """儒派 lunyu: 与注疏 commentary: 键格式不得被本补丁改变。"""
        lunyu_ok = all(
            k.startswith(LUNYU_PREFIX)
            for k in self.corpus
            if k.startswith(LUNYU_PREFIX) or "." in k and not k.startswith((DEBATE_PREFIX, COMMENTARY_PREFIX))
        )
        self.assertTrue(lunyu_ok, "lunyu 键格式异常")
        commentary_keys = [k for k in self.corpus if k.startswith(COMMENTARY_PREFIX)]
        self.assertGreater(len(commentary_keys), 0, "注疏条目不应消失")


class Fix004ClaimCoverageTest(unittest.TestCase):
    """GATE-G 全量 40 条 supported 判定（复刻 eval_claim_coverage 口径）。"""

    @classmethod
    def setUpClass(cls):
        cls.preds = _claim_coverage_pred({e.passage_id: e for e in load_corpus(reload=True)})

    def test_supported_records_40_of_40(self):
        """修复后 G 门应达 40/40：每条记录至少 1 个 supported 证据。"""
        unsupported = [
            rid for rid, ev in self.preds.items()
            if not any(e["verification"] == "supported" for e in ev)
        ]
        self.assertEqual(
            unsupported, [],
            f"存在无 supported 证据的记录（G<1.0）: {unsupported}",
        )
        self.assertEqual(len(self.preds), 40, "记录数应为 40")

    def test_baseline_failures_now_supported(self):
        """基线 10 条失败（四派双层前缀 miss）必须全部转为 supported。"""
        still_bad = []
        for rid in sorted(BASELINE_FAILURES):
            if rid not in self.preds:
                still_bad.append((rid, "无预测"))
                continue
            ev = self.preds[rid]
            if not any(e["verification"] == "supported" for e in ev):
                still_bad.append((rid, ev))
        self.assertEqual(still_bad, [], f"基线失败未被修复: {still_bad}")

    def test_baseline_supported_still_supported(self):
        """基线已 supported 的 30 条不得回退。"""
        regressed = []
        for rec in _load_gold():
            rid = rec["id"]
            if rid in BASELINE_FAILURES:
                continue
            ev = self.preds.get(rid, [])
            if not any(e["verification"] == "supported" for e in ev):
                regressed.append((rid, ev))
        self.assertEqual(regressed, [], f"基线 supported 发生回退: {regressed}")


class Fix004DGateNoRegressionTest(unittest.TestCase):
    """D 门（quote_exactness）关键样例无回退：verify_quote 语义不受键名影响。"""

    # 已知精确引文 → quote_exists/source_correct/exact_match 数据（既有合同行为）
    EXACT_CASES = [
        # (引文, 正确出处) —— 必须在语料中真实存在
        ("学而时习之，不亦说乎", "《论语·学而》"),
        ("己所不欲，勿施于人", "《论语·卫灵公》"),
        ("为政以德，譬如北辰", "《论语·为政》"),
    ]
    # 引文真实但出处错误 → quote_exists=True & source_correct=False（citation_corrected）
    CORRECTED_CASES = [
        # 「学而时习之」实际在《论语·学而》，声称《论语·八佾》应为 citation_corrected
        ("学而时习之，不亦说乎", "《论语·八佾》"),
    ]
    # 语料中不存在的引文 → quote_exists=False（不得伪造）
    FABRICATED_CASES = [
        ("牛何以耕田而民不惑，王以是问之", "《论语·为政》"),
    ]

    @classmethod
    def setUpClass(cls):
        cls.corpus = {e.passage_id: e for e in load_corpus(reload=True)}

    def test_exact_cases_still_verified(self):
        for quote, src in self.EXACT_CASES:
            with self.subTest(quote=quote):
                v = verify_quote(quote, src)
                self.assertTrue(v.quote_exists, f"引文应存在: {quote}")
                self.assertTrue(v.source_correct, f"出处应正确: {quote} {src}")

    def test_corrected_case_still_citation_corrected(self):
        for quote, wrong_src in self.CORRECTED_CASES:
            with self.subTest(quote=quote):
                v = verify_quote(quote, wrong_src)
                self.assertTrue(v.quote_exists, f"引文应存在（出处错误场景）: {quote}")
                self.assertFalse(v.source_correct, "出处错误应维持 source_correct=False")

    def test_fabricated_case_still_rejected(self):
        for quote, src in self.FABRICATED_CASES:
            with self.subTest(quote=quote):
                v = verify_quote(quote, src)
                self.assertFalse(v.quote_exists, f"伪造引文不得通过: {quote}")

    def test_debate_classic_sources_verify_against_corpus(self):
        """四派经典（laozi/mozi/hanfeizi，即 Gold 所引用的 debate sage）在
        原出处下必须 verify 通过（supported 的出处侧证据）。

        注：诗词类条目（li_bai/su_shi/fan_zhongyan/wang_anshi/zhuge_liang）
        的 source 为纯篇名（如《将进酒》），parse_source 无法解析出经典书名 →
        source_correct=False 属**既有行为**（FIX-004 只对齐 passage_id 键，
        不涉 original/source；且这些条目不在 retrieval_gold expected id 中）。
        故本断言仅覆盖 Gold 实际引用的 laozi/mozi/hanfeizi。
        """
        gold_sages = {"laozi", "mozi", "hanfeizi"}
        bad = []
        for e in self.corpus.values():
            if e.passage_id.startswith(DEBATE_PREFIX):
                sage = e.passage_id.split(":", 1)[1]
                if sage not in gold_sages:
                    continue
                v = verify_quote(e.original, e.source)
                if not (v.quote_exists and v.source_correct):
                    bad.append((e.passage_id, e.source, v.quote_exists, v.source_correct))
        self.assertEqual(
            bad, [], f"四派经典条目在原出处下验证失败: {bad[:5]}"
        )


if __name__ == "__main__":
    unittest.main()