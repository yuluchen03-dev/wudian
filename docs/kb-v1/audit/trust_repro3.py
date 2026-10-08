"""
PHASE 0 / t4 补充复现脚本 3：离线兜底引用的可验证性与出处准确性（只读）

运行（在 backend 目录）：
    .venv\\Scripts\\python.exe ..\\docs\\kb-v1\\audit\\trust_repro3.py
"""
import asyncio
import importlib
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.services.citation_validator import citation_validator  # noqa: E402
from app.services.rag_service import RAGService  # noqa: E402

de = importlib.import_module("app.services.debate_engine")

SEP = "=" * 72


def hr(t):
    print(f"\n{SEP}\n{t}\n{SEP}")


def main():
    rag = RAGService()

    hr("A. FALLBACK_QUOTES 的真实语料支撑情况")
    print("对每个圣贤：先看本派索引是否有该文本，再看 validate() 结果\n")
    for sage_key, q in de.FALLBACK_QUOTES.items():
        text = q["quote"]
        claimed = q["source"]
        idx = rag._debate_classic_index.get(sage_key, [])
        in_index = any(text.strip("。") in (e.get("original", "").strip("。")) or
                       (e.get("original", "").strip("。")) in text.strip("。")
                       for e in idx)
        index_sources = sorted({e.get("source", "") for e in idx})
        # 用本派真实检索结果作为 rag_refs（与 _retrieve_debate_context 同路径）
        sr = asyncio.run(rag.retrieve_for_debate_sage(sage_key, "我该不该躺平", top_k=5))
        refs = sr.get("verses", []) + sr.get("commentaries", [])
        validated, status = asyncio.run(
            citation_validator.validate(
                sage_key,
                [{"id": "引1", "出处": claimed, "原文": text}],
                refs,
            )
        )
        print(f"[{sage_key}]")
        print(f"    引用原文 : {text}")
        print(f"    声称出处 : {claimed}")
        print(f"    本派索引 : {len(idx)} 条, source 集合={index_sources}")
        print(f"    检索返回 : {len(refs)} 条")
        print(f"    文本在索引中(按原文匹配): {in_index}")
        print(f"    -> verifiable={validated[0].verifiable}  status={status!r}")

    hr("B. 无本派语料的圣贤（如孟子）会得到什么")
    for sage_key in ["mencius", "wang_yangming"]:
        idx = rag._debate_classic_index.get(sage_key)
        sr = asyncio.run(rag.retrieve_for_debate_sage(sage_key, "我该不该躺平", top_k=5))
        print(f"  {sage_key}: 本派索引={'无' if idx is None else len(idx)} 条, "
              f"检索返回 {len(sr.get('verses', []))} 条")

    hr("C. 出处字符串与真实来源是否一致（逐条核对）")
    print("注意：以下为 FALLBACK_QUOTES 中声明的出处 vs 语料里的 source 字段\n")
    for sage_key, q in de.FALLBACK_QUOTES.items():
        idx = rag._debate_classic_index.get(sage_key, [])
        matched = [
            e for e in idx
            if q["quote"].strip("。") in (e.get("original", "").strip("。"))
            or (e.get("original", "").strip("。")) in q["quote"].strip("。")
        ]
        if matched:
            real = matched[0].get("source", "")
            flag = "一致" if q["source"] in real or real in q["source"] else "*** 不一致 ***"
            print(f"  {sage_key}: 声称={q['source']!r} 语料={real!r} -> {flag}")
        else:
            print(f"  {sage_key}: 声称={q['source']!r} 语料中未找到对应条目")

    hr("D. 结论")
    print("  - 离线兜底引用是否可验证取决于该圣贤是否有本派语料")
    print("  - verifiable 只反映「文本出现在本次检索结果中」，不反映出处正确")


if __name__ == "__main__":
    main()
