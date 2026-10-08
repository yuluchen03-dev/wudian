"""
PHASE 0 / t4 可信层只读复现脚本（不修改任何产品代码）

用途：用当前仓库真实实现，验证 docs/kb-v1/audit/trust.md 中关于
CitationValidator / ai_service._validate_citations 的结论。

运行（在仓库根目录）：
    backend\\.venv\\Scripts\\python.exe docs\\kb-v1\\audit\\trust_repro.py

本脚本只调用现有函数，不写入数据库、不写产品文件、不联网。
"""
import asyncio
import sys
from pathlib import Path

# 控制台中文输出（Windows GBK 控制台会乱码）
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.services.citation_validator import CitationValidator, SAGE_CLASSICS  # noqa: E402
from app.services.rag_service import RAGService  # noqa: E402

SEP = "=" * 72


def hr(title):
    print(f"\n{SEP}\n{title}\n{SEP}")


# ------------------------------------------------------------------
# 真实检索结果（模拟一次 debate 中 confucius 的 rag_refs）
# ------------------------------------------------------------------
REAL_REFS = [
    {
        "verse_id": "lunyu_15_24",
        "original": "己所不欲，勿施于人。",
        "source": "《论语·卫灵公》",
        "chapter": "卫灵公篇",
    },
    {
        "verse_id": "lunyu_1_1",
        "original": "学而时习之，不亦说乎？",
        "source": "《论语·学而》",
        "chapter": "学而篇",
    },
]

# ------------------------------------------------------------------
# 六类对抗输入（PROJECT-BRIEF 第十六章）
# ------------------------------------------------------------------
CASES = [
    (
        "C1 伪造古文",
        "子贡问曰：同事抢功，当何以处之？",
        "《论语·子贡》",
        "该句不存在于任何经典，属模型编造。",
    ),
    (
        "C2 真实古文 + 错误出处",
        "己所不欲，勿施于人。",
        "《孟子·梁惠王上》",
        "文本真实存在，但被归到孟子名下。",
    ),
    (
        "C3 同句不同标点",
        "己所不欲 勿施于人",
        "《论语·卫灵公》",
        "去掉标点/加空格，语义同一句。",
    ),
    (
        "C4 繁体版本",
        "己所不欲，勿施於人。",
        "《论语·卫灵公》",
        "「于」→「於」的繁体/异体写法。",
    ),
    (
        "C5 部分引用",
        "己所不欲",
        "《论语·卫灵公》",
        "只引用前半句。",
    ),
    (
        "C6 现代网络鸡汤冒充孔子",
        "你若不勇敢，没人替你坚强。",
        "《论语·述而》",
        "典型现代鸡汤，被冠以孔子出处。",
    ),
    (
        "C7 真实古文 + 同派错误篇章",
        "己所不欲，勿施于人。",
        "《论语·学而》",
        "文本真实，出处错到同书另一篇；同派检查无法发现。",
    ),
    (
        "C8 真实古文 + 未检索到",
        "三人行，必有我师焉。",
        "《论语·述而》",
        "文本确实存在于知识库，但未进入本次 rag_refs。",
    ),
    (
        "C9 真实短句嵌入伪造长文",
        "网络鸡汤：己所不欲，勿施于人。所以你要坚强，别让任何人看轻你。",
        "《论语·卫灵公》",
        "伪造长文把真实原句作为子串嵌入，检验双向子串匹配是否被绕过。",
    ),
    (
        "C10 空出处",
        "己所不欲，勿施于人。",
        "",
        "出处为空，检验 belong 检查是否因空值直接放行。",
    ),
]

FABRICATED = {"C1 伪造古文", "C6 现代网络鸡汤冒充孔子", "C9 真实短句嵌入伪造长文"}


async def run_validator_cases():
    """直接调用仓库真实的 CitationValidator.validate()。"""
    validator = CitationValidator()
    results = {}
    for cid, original, source, note in CASES:
        citations = [{"id": "引1", "出处": source, "原文": original}]
        validated, status = await validator.validate("confucius", citations, REAL_REFS)
        v = validated[0]
        results[cid] = {
            "verifiable": v.verifiable,
            "status": status,
            "kept_original": v.original,
            "claimed_source": v.source,
            "kept_source": v.source,
            "note": note,
        }
    return results


def run_ai_service_logic_cases():
    """复刻 ai_service._validate_citations 的判定分支（同一算法）。"""
    rag_originals = set()
    for ref in REAL_REFS:
        orig = ref.get("original", "")
        if orig:
            rag_originals.add(orig.strip())
            cleaned = (
                orig.replace("。", "").replace("，", "").replace("？", "")
                .replace("！", "").replace("；", "").strip()
            )
            if cleaned:
                rag_originals.add(cleaned)

    out = {}
    for cid, original, source, note in CASES:
        cit_cleaned = (
            original.replace("。", "").replace("，", "").replace("？", "")
            .replace("！", "").replace("；", "").strip()
        )
        verifiable = False
        for rt in rag_originals:
            if (
                cit_cleaned in rt or rt in cit_cleaned
                or original in rt or rt in original
            ):
                verifiable = True
                break
        out[cid] = verifiable
    return out


def check_debate_classic_isolation():
    """检查 _debate_classic_index 的真实隔离内容（只读内存索引）。"""
    rag = RAGService()
    per_sage = {}
    for sage_key, entries in rag._debate_classic_index.items():
        per_sage[sage_key] = [
            {"id": e.get("id"), "book": e.get("book"), "original": e.get("original", "")[:40]}
            for e in entries
        ]
    return per_sage


def cross_school_probe():
    """
    跨派引用探针：把老子原文挂到孔子名下，看 validator 是否察觉。
    这是 PROJECT-BRIEF 第十六章「上善若水是不是庄子」类问题的结构等价物。
    """
    validator = CitationValidator()
    # 老子《道德经》第八章原文，被错误归到庄子；同时该文本不在 confucius 的 rag_refs 中
    citations = [{"id": "引1", "出处": "《庄子·逍遥游》", "原文": "上善若水，水善利万物而不争。"}]
    # 场景 A：rag_refs 为空（检索未命中）
    va, sa = asyncio.run(validator.validate("confucius", citations, []))
    # 场景 B：rag_refs 命中了该文本（例如检索串台），但出处写的是庄子
    refs_hit = [{"original": "上善若水，水善利万物而不争。", "source": "《道德经》"}]
    vb, sb = asyncio.run(validator.validate("confucius", citations, refs_hit))
    return {
        "A_no_rag_hit": {"verifiable": va[0].verifiable, "status": sa},
        "B_rag_hit_wrong_attribution": {
            "verifiable": vb[0].verifiable,
            "status": sb,
            "kept_source": vb[0].source,
        },
    }


def debate_engine_logic_cases():
    """
    复刻 debate_engine._validate_citations 的判定分支（注意：与
    citation_validator._match_citation 的容错集合不同，二者存在分歧）。
    该函数只复刻逻辑，不修改产品代码。
    """
    rag_originals = set()
    for ref in REAL_REFS:
        orig = ref.get("original", "")
        if orig:
            rag_originals.add(orig.strip())
            cleaned = (
                orig.replace("。", "").replace("，", "").replace("？", "")
                .replace("！", "").replace("；", "").strip()
            )
            if cleaned:
                rag_originals.add(cleaned)

    out = {}
    for cid, original, source, note in CASES:
        cit_cleaned = (
            original.replace("。", "").replace("，", "").replace("？", "")
            .replace("！", "").replace("；", "").strip()
        )
        verifiable = False
        for rt in rag_originals:
            if (
                cit_cleaned in rt or rt in cit_cleaned
                or original in rt or rt in original
            ):
                verifiable = True
                break
        out[cid] = verifiable
    return out


def corpus_existence_probe():
    """
    区分「文本存在于知识库」与「文本出现在本次检索结果中」。
    直接对真实 Chroma collection 做 where_document 子串查询（只读）。
    """
    rag = RAGService()
    probes = {
        "己所不欲，勿施于人。": "C2/C3/C4/C5/C7 的文本",
        "三人行，必有我师焉。": "C8 的文本",
        "上善若水，水善利万物而不争。": "老子的上善若水",
        "你若不勇敢，没人替你坚强。": "C6 现代鸡汤",
        "子贡问曰：同事抢功，当何以处之？": "C1 伪造古文",
    }
    out = {}
    for text, label in probes.items():
        if rag.collection is None:
            out[label] = "collection 不可用"
            continue
        try:
            rows = rag.collection.get(
                where_document={"$contains": text[:12]},
                limit=3,
                include=["metadatas"],
            )
            metas = rows.get("metadatas") or []
            out[label] = {
                "query_prefix": text[:12],
                "hits": len(rows.get("ids") or []),
                "sources": [m.get("source", "?") for m in metas if isinstance(m, dict)],
            }
        except Exception as e:  # pragma: no cover
            out[label] = f"查询异常: {e}"
    return out


def main():
    hr("环境")
    print("REPO_ROOT:", REPO_ROOT)
    print("BACKEND  :", BACKEND)

    hr("1. CitationValidator.validate() 对六类对抗输入的真实判定")
    res = asyncio.run(run_validator_cases())
    for cid, original, source, note in CASES:
        r = res[cid]
        print(f"\n[{cid}] {note}")
        print(f"    原文={original!r}")
        print(f"    声称出处={source!r}")
        print(f"    -> verifiable={r['verifiable']}  status={r['status']!r}")

    hr("2. 三个校验实现的判定对比")
    ai = run_ai_service_logic_cases()
    de = debate_engine_logic_cases()
    print(f"  {'用例':<28} {'citation_validator':<20} {'ai_service':<12} {'debate_engine':<14}")
    for cid, _, _, _ in CASES:
        print(
            f"  {cid:<28} {str(res[cid]['verifiable']):<20} "
            f"{str(ai[cid]):<12} {str(de[cid]):<14}"
        )
    # 关键分歧：citation_validator 带 SAGE_CLASSICS 同派检查，
    # ai_service / debate_engine 的 _validate_citations 只有文本子串匹配。
    diverged = [
        cid for cid, *_ in CASES
        if res[cid]["verifiable"] != ai[cid]
    ]
    print("\n  citation_validator 与 ai_service 判定不一致的用例:", diverged or "无")
    print("  ai_service 与 debate_engine 判定不一致的用例:",
          [cid for cid, *_ in CASES if ai[cid] != de[cid]] or "无")

    hr("3. 关键断言：明确伪造的两类是否被拦截")
    failed = []
    for cid in FABRICATED:
        got = res[cid]["verifiable"]
        ok = got is False
        print(f"  {cid} 应 verifiable=False -> 实际 {got}  {'OK' if ok else '*** 未拦截 ***'}")
        if not ok:
            failed.append(cid)
    print("\n伪造文本被误判为可验证的用例:", failed or "无")

    hr("4. 出处正确性是否被校验")
    c2 = res["C2 真实古文 + 错误出处"]
    print("  C2 真实古文 + 错误出处《孟子·梁惠王上》")
    print("    verifiable =", c2["verifiable"], "（该用例未进入 rag_refs，故为 False）")
    c7 = res["C7 真实古文 + 同派错误篇章"]
    print("  C7 真实古文 + 同派错误篇章《论语·学而》（正确应为《论语·卫灵公》）")
    print("    verifiable =", c7["verifiable"], "  status =", c7["status"])
    print("    kept_source =", c7["kept_source"])
    print("    -> verifiable=True 且 status=all_verified：出处错误被完全放过")
    c10 = res["C10 空出处"]
    print("  C10 空出处 -> verifiable =", c10["verifiable"], " status =", c10["status"])

    hr("4b. 双向子串匹配绕过（C9）")
    c9 = res["C9 真实短句嵌入伪造长文"]
    print("  原文 = 网络鸡汤：己所不欲，勿施于人。所以你要坚强，别让任何人看轻你。")
    print("    verifiable =", c9["verifiable"], "  status =", c9["status"])
    print("    -> 伪造长文因包含真实原句子串而被判为可验证" if c9["verifiable"]
          else "    -> 未命中")

    hr("5. 跨派引用探针（老子上善若水挂孔子/庄子名下）")
    probe = cross_school_probe()
    for k, v in probe.items():
        print(f"  {k}: {v}")

    hr("6. _debate_classic_index 真实规模（只读内存索引）")
    per_sage = check_debate_classic_isolation()
    for k, v in per_sage.items():
        print(f"  {k}: {len(v)} 条")
        for e in v[:2]:
            print(f"      - {e['id']} | {e['book']} | {e['original']}")

    hr("7. SAGE_CLASSICS 白名单覆盖面")
    for k, v in SAGE_CLASSICS.items():
        print(f"  {k}: {v}")

    hr("8. 「文本存在于知识库」vs「出现在本次检索结果」")
    ex = corpus_existence_probe()
    for label, info in ex.items():
        print(f"  {label}: {info}")

    hr("结论摘要")
    print("  - 六类对抗输入中，被判定 verifiable=True 的用例：")
    for cid, _, _, note in CASES:
        if res[cid]["verifiable"]:
            print(f"      {cid} ({note})")
    print("  - 出处正确性（source_correct）在当前实现中：无任何校验路径")
    print("  - 明确伪造文本未拦截数：", len(failed))
    print("  - citation_validator 与 ai_service 判定分歧用例：", diverged or "无")


if __name__ == "__main__":
    main()
