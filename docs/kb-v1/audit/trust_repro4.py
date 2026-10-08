"""
PHASE 0 / t4 补充复现脚本 4：前端硬编码 verified:true 的引用是否真的在语料中（只读）

运行（在仓库根目录）：
    backend\\.venv\\Scripts\\python.exe docs\\kb-v1\\audit\\trust_repro4.py
"""
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

REPO_ROOT = Path(__file__).resolve().parents[3]
CASES_TS = REPO_ROOT / "frontend" / "lib" / "thoughtCourtCases.ts"
LUNYU = REPO_ROOT / "data" / "processed" / "lunyu.json"
DEBATE = REPO_ROOT / "data" / "processed" / "debate_classics.json"

SEP = "=" * 72


def hr(t):
    print(f"\n{SEP}\n{t}\n{SEP}")


def norm(s: str) -> str:
    return re.sub(r"[\s。，、！？；：（）()《》「」『』\"'·]", "", s or "")


def load_corpus_texts():
    texts = []
    data = json.loads(LUNYU.read_text(encoding="utf-8"))
    book = data.get("book", "论语")
    for ch in data.get("chapters", []):
        for v in ch.get("verses", []):
            if v.get("original"):
                texts.append((book, ch.get("chapter_title", ""), v["original"]))
    dc = json.loads(DEBATE.read_text(encoding="utf-8"))
    for sage, classic in dc.get("classics", {}).items():
        b = classic.get("book", "")
        for v in classic.get("verses", []):
            if v.get("original"):
                texts.append((b, v.get("chapter", ""), v["original"]))
    # 注疏
    comm = REPO_ROOT / "backend" / "data" / "commentaries" / "lunyu_zhuxi.json"
    if comm.exists():
        cd = json.loads(comm.read_text(encoding="utf-8"))
        for item in cd.get("commentaries", []):
            if item.get("original"):
                texts.append(("朱熹《论语集注》", item.get("chapter", ""), item["original"]))
    return texts


def main():
    hr("从 thoughtCourtCases.ts 提取所有硬编码引用")
    src = CASES_TS.read_text(encoding="utf-8")
    pattern = re.compile(
        r'original:\s*"([^"]+)"\s*,\s*source:\s*"([^"]+)"[^}]*?verified:\s*(true|false)'
    )
    items = pattern.findall(src)
    print(f"共提取 {len(items)} 条")

    corpus = load_corpus_texts()
    corpus_norm = [norm(t[2]) for t in corpus]

    hr("逐条核对：该引用是否真实存在于当前语料库")
    not_found = []
    for original, source, verified in items:
        n = norm(original)
        # 全等或包含（双向）
        hit = any(n and (n == cn or n in cn or cn in n) for cn in corpus_norm)
        status = "在语料中" if hit else "*** 语料中未找到 ***"
        print(f"  [{verified}] {source} | {original}")
        print(f"        -> {status}")
        if not hit:
            not_found.append((original, source, verified))

    hr("汇总")
    print(f"  硬编码引用总数: {len(items)}")
    print(f"  其中标记 verified=true 的: {sum(1 for i in items if i[2] == 'true')}")
    print(f"  语料中未找到的: {len(not_found)}")
    for o, s, v in not_found:
        print(f"      [{v}] {s} | {o}")
    print("\n  说明：前端这些条目是静态硬编码数据，其 verified 字段为字面量，")
    print("  并非由后端 QuoteVerifier 或 CitationValidator 计算得出。")

    hr("语料规模参照")
    print(f"  当前可核对文本条数（论语 + 百家 + 注疏）: {len(corpus)}")


if __name__ == "__main__":
    main()
