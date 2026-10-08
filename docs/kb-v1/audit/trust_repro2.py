"""
PHASE 0 / t4 补充复现脚本：逐句证据绑定与状态语义（只读）

运行（在 backend 目录）：
    .venv\\Scripts\\python.exe ..\\docs\\kb-v1\\audit\\trust_repro2.py
"""
import asyncio
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.services.citation_validator import CitationValidator  # noqa: E402
from app.services.rag_service import RAGService  # noqa: E402

# 注意：app.services.__init__ 会把 debate_engine 这个名字绑定为 DebateEngine 实例，
# 因此这里必须用 importlib 取真实模块对象。
import importlib  # noqa: E402

de = importlib.import_module("app.services.debate_engine")

SEP = "=" * 72


def hr(t):
    print(f"\n{SEP}\n{t}\n{SEP}")


def main():
    hr("A. 逐句证据绑定：无关语句是否也会被判为 verifiable=True")
    print("调用真实 debate_engine._bind_sentence_evidence（使用真实 RAG 索引）")
    print("注意：该函数不把「句子」与「检索到的原文」做任何文本比对。\n")

    sentences = [
        "己所不欲，勿施于人。",          # 论语真实原文
        "今天天气不错，我打算去打球。",   # 与论语完全无关
        "股价暴跌让我很焦虑。",          # 现代焦虑话题
    ]
    for s in sentences:
        ev = asyncio.run(de._bind_sentence_evidence("confucius", s))
        for e in ev:
            print(f"  句子: {e.sentence!r}")
            print(f"    -> verifiable={e.verifiable}  similarity={e.similarity:.4f}")
            print(f"       source={e.source!r}")
            print(f"       original={e.original[:40]!r}")

    hr("B. 无引用时 CitationValidator 的 status 语义")
    v = CitationValidator()
    validated, status = asyncio.run(v.validate("confucius", [], []))
    print(f"  输入 citations=[] rag_refs=[]")
    print(f"  -> validated={validated} status={status!r}")
    print("  结论：空引用被报告为 all_verified（因为 all_verified 初值为 True）")

    hr("C. 出处为空时同派检查是否放行")
    validated, status = asyncio.run(
        v.validate(
            "confucius",
            [{"id": "引1", "出处": "", "原文": "人皆有不忍人之心"}],
            [{"source": "《孟子》", "original": "人皆有不忍人之心"}],
        )
    )
    print(f"  孟子原文 + 空出处，sage=confucius（应为跨派）")
    print(f"  -> verifiable={validated[0].verifiable} status={status!r}")
    print("  结论：source 为空时 _check_classic_belonging 直接返回 True，跨派检查失效")

    hr("D. 白名单：LLM 可否引用 rag_refs 之外的 source")
    print("  _match_citation 只比对 原文 与 rag_refs[].original；")
    print("  source(出处) 字段从不参与匹配，仅做同派字符串包含检查。")
    validated, status = asyncio.run(
        v.validate(
            "confucius",
            [{"id": "引1", "出处": "《论语·卫灵公》", "原文": "己所不欲，勿施于人。"}],
            [{"source": "《论语·卫灵公》", "original": "己所不欲，勿施于人。"}],
        )
    )
    print(f"  正常命中 -> verifiable={validated[0].verifiable} status={status!r}")

    hr("E. 真实 RAG 检索是否总能返回结果（无关 query）")
    rag = RAGService()
    for q in ["今天天气不错", "股价暴跌让我很焦虑", "完全无关的现代话题xyz"]:
        res = asyncio.run(rag.retrieve_for_debate_sage("confucius", q, top_k=3))
        verses = res.get("verses", [])
        print(f"  query={q!r} -> 返回 {len(verses)} 条")
        for x in verses[:2]:
            print(f"      sim={x['similarity']:.4f} {x['source']} | {x['original'][:30]!r}")
    print("\n  说明：_debate_keyword_search 对 score==0 的条目强制赋 0.25，")
    print("  因此本派索引非空时几乎不会返回空结果 → 逐句证据 verifiable 恒为 True。")

    hr("F. 结论")
    print("  1) sentence_evidence.verifiable 不校验句子与原文的文本一致性（高误报）")
    print("  2) 空引用 → status=all_verified（假阳性状态）")
    print("  3) 空 source → 跨派检查失效")
    print("  4) source/出处 从不参与文本匹配，出处正确性无校验路径")


if __name__ == "__main__":
    main()
