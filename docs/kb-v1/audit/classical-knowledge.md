# PHASE 0 审计报告 — 原典与注疏数据、来源与分层现状

- 任务：t2 / attempt 1 / attempt_id `fe4975b1-1813-46e7-b1f1-f7f70b6baba8`
- 执行者：classical-knowledge（古籍知识工程师）
- 仓库：`D:\systemDir\Desktop\悟典`，branch `codex/overall-optimization`，HEAD `64c8618`
- 审计日期：2026-07（本机系统日期）
- 审计性质：**只读**。未修改任何数据、脚本或产品代码；未补写或"修正"任何原典文本。
- 可复现脚本（本报告全部数字的来源，已置于 `docs/kb-v1/audit/`）：
  - `classical_audit_1_integrity.py` — 引文/典故交叉引用完整性
  - `classical_audit_2_scale.py` — 文件规模、语料计数、V1 书目覆盖、Schema 字段存在性
  - `classical_audit_3_layers.py` — L1–L5 分层盘点、内部出处冲突扫描
  - `classical_audit_4_provenance.py` — 生成器可复现性、文本缺陷明细
  - `classical_audit_5_source_semantics.py` — `source` 字段语义、授权字段核查

---

## 0. 结论摘要（先读这一段）

1. **V1 目标书目 12 部中，实际有原典语料的只有 3 部，且其中 2 部各只有 4 条摘句。** 论语 107 章 + 道德经 4 条 + 墨子 4 条 + 韩非子 4 条。孟子/荀子/大学/中庸/庄子/商君书/传习录/孙子兵法 **完全无数据**。
2. **PROJECT-BRIEF 第六章 Passage Schema 的 29 个字段中，只有 6 个以结构化形式存在**（`chapter_id`、`chapter_title`、`original`、`author`、`dynasty`、`created_at`/`updated_at`），其余 23 个缺失，包括全部来源字段、全部授权字段、全部复核字段、全部分层字段（`text_type`）。
3. **没有任何一条 passage 能追溯到具体底本。** 语料里出现的 `source` 是「引用标签」（如 `《论语·泰伯》`），不是数据提供方；`classics_catalog.json` 的 3 个 URL 只挂在目录层，123 部书**没有任何一部**带 `source_url`/`source_edition`/`license`。
4. **没有找到任何人工复核或校对记录。** 对 5 个语料文件全文检索 `校对`/`复核`/`人工`/`审定`/`proofread`/`verified`/`reviewed`，**零命中**。因此当前全部语料**只能定为 C 级或 D 级，不能定为 A 级**。
5. **发现 1 处原文缺陷、1 处内部出处冲突、2 处引文悬空引用、16 条典故悬空引用、9 条 quote_cards 无法在语料中逐字定位。** 详见第 4、6 节。
6. **`build_lunyu.py` 是纯内置字典脚本，无任何网络导入，输出与磁盘 JSON 逐字节一致** —— 说明语料是**人工/LLM 辅助编写后固化的静态数据**，而非从权威库抓取。这是"无法追溯底本"的根本原因，也是 PHASE 1 Source Registry 必须解决的第一问题。
7. **外部核验受限**：本机对 `ctext.org`、`zh.wikisource.org` 的访问被拒（`non-public IP address`），web_search 因缺少 `DEEPSEEK_API_KEY` 不可用。因此**本报告不对任何一条文本作"与通行本一致"的最终断言**，只报告可本地证实的内部一致性事实与可疑点，并逐条标注不确定度。见第 4.4 与第 8 节。

---

## 1. 语料规模真实统计表

### 1.1 命令

```powershell
$env:PYTHONIOENCODING="utf-8"; [Console]::OutputEncoding=[System.Text.Encoding]::UTF8
python docs/kb-v1/audit/classical_audit_2_scale.py
```

### 1.2 原始输出（节选 A 段）

```
=== A. file-level scale ===
lunyu.json                  92746 bytes  top=dict
lunyu_quotes.json           10965 bytes  top=dict
debate_classics.json         8860 bytes  top=dict
classics_catalog.json       27793 bytes  top=dict
knowledge_graph.json        16228 bytes  top=dict
quote_cards.json            18490 bytes  top=22
timeline.json               12017 bytes  top=dict
idioms.json                 19272 bytes  top=dict
comics.json                  7838 bytes  top=1
theater_scripts.json        24478 bytes  top=6
```

### 1.3 汇总表

| 文件 | 大小(B) | 书籍 / 学派 | 章节数 | 条目数 | 结构化字段清单 | 是否 L1 原典 |
|---|---|---|---|---|---|---|
| `data/processed/lunyu.json` | 92746 | 论语 / 儒家 | 20 | **107 verse** | `verse_id, title, original, translation, annotations[{char,pinyin,meaning}], keywords`；容器级 `book, author, dynasty, description, total_chapters, chapters[{chapter_id, chapter_title, summary, verses}]` | **是（L1）** |
| `data/processed/lunyu_quotes.json` | 10965 | 论语 / 儒家 | — | 36 | `id, original, source, translation, scene, level` | 部分（摘句，非完整章） |
| `data/processed/debate_classics.json` | 8860 | 论语/道德经/墨子/韩非子/李白/苏轼/范仲淹/王安石/诸葛亮 | 每派 1–4 | **21 verse** | `id, chapter, original, translation, source, keywords`；容器级 `book` | **是（L1，但极稀疏）** |
| `data/processed/classics_catalog.json` | 27793 | 123 部书目（经史子集…） | 目录 `totalChapters` | 123 book | `id, title, category, author, dynasty, description, coverColor, totalChapters`；`sources[{name,url,note}]` | 否（仅书目元数据，无正文） |
| `data/processed/knowledge_graph.json` | 16228 | 儒家传承 | — | 21 node / 24 edge | node: `id,label,type,subtype,courtesy_name,birth_year,death_year,era,description,core_thought,tags,real_name`；edge: `source,target,relation,label,description`；`meta` | 否（L3） |
| `data/processed/quote_cards.json` | 18490 | 论语为主 | — | 22 | `id,quote,source,vernacular,modern_interpretation,style,image_keyword,background_color,accent_color,tags,like_count,share_count,created_at` | 否（含 D 级 AI 解释） |
| `data/processed/timeline.json` | 12017 | 春秋战国 | — | 30 event | `id,year,year_label,title,category,description,tags`；`meta` | 否（L5 背景） |
| `data/processed/idioms.json` | 19272 | 论语 | — | **39**（`meta.total` 写 35，**不一致**） | `idiom,original_text,source,chapter,chapter_num,verse_num,meaning,modern_usage,tags`；`meta` | 部分（摘句） |
| `data/processed/comics.json` | 7838 | 论语 | — | 1 | `id,title,summary,classical_source,cover_keyword,panel_count,panels,style_guide,characters,tags,...` | 否（D 级 AI 脚本） |
| `data/processed/theater_scripts.json` | 24478 | 论语 | — | 6 | `id,title,summary,classical_source,modern_setting,moral,roles,scenes,tags,...` | 否（D 级 AI 脚本） |

> 说明：`data/raw/` **完全为空**（`Get-ChildItem data/raw -Recurse -Force | Measure-Object → Count 0`），且 `git ls-files data/raw` 为 0 —— 即**没有任何原始底本留档**。这与 `data/README.md` 中「raw/ 原始数据（预留）」的描述一致，但对可追溯性而言是硬缺口。

---

## 2. 字段对照 PROJECT-BRIEF 第六章 Passage Schema

### 2.1 命令

```powershell
python docs/kb-v1/audit/classical_audit_2_scale.py   # F 段
```

### 2.2 原始输出（F 段）

```
=== F. schema field presence (structured, not prose) ===
  passage_id             ABSENT
  book_id                ABSENT
  book_title             ABSENT
  chapter_id             PRESENT
  chapter_title          PRESENT
  section                ABSENT
  line_no                ABSENT
  original               PRESENT
  original_traditional   ABSENT
  original_simplified    ABSENT
  source_provider        ABSENT
  source_url             ABSENT
  source_edition         ABSENT
  author                 PRESENT
  dynasty                PRESENT
  text_type              ABSENT
  commentator            ABSENT
  commentary_dynasty     ABSENT
  school                 ABSENT
  concepts               ABSENT
  modern_topics          ABSENT
  modern_scenarios       ABSENT
  stance                 ABSENT
  verification_level     ABSENT
  proofread_status       ABSENT
  license                ABSENT
  embedding_version      ABSENT
  created_at             PRESENT
  updated_at             PRESENT
```

### 2.3 判定表

| PROJECT-BRIEF 字段 | 状态 | 说明 |
|---|---|---|
| `passage_id` | **缺失** | 无统一 ID；现有 `verse_id`（如 `1.1`）只覆盖论语，`debate_classics` 用 `daodejing-08-01` 等另一套 ID 空间，`lunyu_zhuxi` 用 `verse_id`，三套不统一 |
| `book_id` | **缺失** | 只有 `book` 中文名（`"论语"`），无稳定 slug；`classics_catalog.json` 有 `id`（`"lunyu"`）但**未与语料关联** |
| `book_title` | **部分有** | 等价于 `book`，存在但非规范字段名 |
| `chapter_id` | **已有** | `lunyu.json` 为整数；`debate_classics` 无独立 id，只有 `chapter` 中文名 |
| `chapter_title` | **已有** | 同上 |
| `section` | **缺失** | 无 |
| `line_no` | **缺失** | 无；`idioms.json` 的 `verse_num` 是最接近的字段，但只覆盖典故 |
| `original` | **已有** | 所有 L1 条目均有 |
| `original_traditional` | **缺失** | 无繁体字段 |
| `original_simplified` | **缺失** | 无显式简体字段（现有文本实为简体） |
| `source_provider` | **缺失** | **无来源提供方字段** |
| `source_url` | **缺失** | **无来源链接**（仅 `classics_catalog.json` 目录层有 3 个 URL） |
| `source_edition` | **缺失** | **无底本/版本字段** |
| `author` | **已有** | 仅 `lunyu.json` 容器级；`debate_classics` 各派**无** author |
| `dynasty` | **已有** | 仅 `lunyu.json` 容器级；`debate_classics` 各派**无** dynasty |
| `text_type` | **缺失** | **最严重的分层缺口**——见 2.4 |
| `commentator` | **缺失** | 注疏者只以字符串形式出现在 `source` 里（`朱熹《论语集注》`），无独立字段 |
| `commentary_dynasty` | **缺失** | 只在文件级 `dynasty: 南宋` |
| `school` | **缺失** | `debate_classics` 各派容器**无** `school` 字段（实测 `v.get("school") → None` × 9） |
| `concepts` | **缺失** | 只有自由文本 `keywords` / `tags`，非受控词表 |
| `modern_topics` | **缺失** | 无 |
| `modern_scenarios` | **缺失** | 有 `scene`（36 条）/ `modern_usage`（39 条）/ `modern_setting`（6 条），但**非结构化枚举、无本体** |
| `stance` | **缺失** | 无 |
| `verification_level` | **缺失** | **无质量等级字段** |
| `proofread_status` | **缺失** | **无复核状态字段** |
| `license` | **缺失** | **无授权字段**；仅 `lunyu_zhuxi.json` 的 `description` 散文提到「公版已过版权期」 |
| `embedding_version` | **缺失** | 无 |
| `created_at` / `updated_at` | **部分有** | 仅出现在 `quote_cards`/`comics`/`theater_scripts` 条目与 `meta.updated_at`（`timeline`/`idioms`/`knowledge_graph`，值均为 `2025-01-01`）；**L1 语料本身没有** |

### 2.4 原文、译文、注释是否混在同一 chunk —— **是，且是当前 RAG 的直接输入**

这不是推测，而是代码事实：

- `backend/app/services/rag_service.py:314` 构造检索文档：
  ```python
  full_text = f"【篇章】{ch_title} 【原文】{original} 【译文】{translation}"
  if ann_text:
      full_text += f" 【注释】{ann_text}"
  ```
- 注疏同样混入：`rag_service.py:352`
  ```python
  full_text = f"【篇章】{chapter} 【原文】{original} 【注疏】{commentary}"
  ```
- 各派经典同样：`rag_service.py:389-394` 拼 `【经典】【篇章】【原文】【译文】【关键词】`

即：**一个 verse 的 原典原文 + 现代白话译文 + 生僻字注释 + 关键词 被拼成一个字符串后向量化**；注疏条目则把 原文 + 朱熹注疏 拼成一个字符串。PROJECT-BRIEF 第五章「禁止把这些层混成普通 chunk」与第六章「原典和注疏必须分开储存」在当前实现中**均不满足**。

注：`lunyu_zhuxi.json` 与 `lunyu.json` 是**两个独立文件**（物理分离），但：
- 注疏条目**内嵌了原文副本**（`commentary[i].original`），与 `lunyu.json` 重复存储；
- 检索时两者被写入**同一个 Chroma collection**（`settings.CHROMA_COLLECTION`，`rag_service.py:245-249`），仅靠 `metadata.doc_type` 区分；
- 文件回退模式（`_file_keyword_search`）更是把 `_file_index` 与 `_commentary_index` 的分数**直接混在一个列表里排序**（`rag_service.py:429-461`）。

**结论：物理文件分离 ≠ 逻辑分层。当前没有 `text_type` 字段，分层只靠 `doc_type` 字符串约定，且原典与注疏进入同一检索空间。**

---

## 3. 来源与授权审计

### 3.1 命令

```powershell
python docs/kb-v1/audit/classical_audit_5_source_semantics.py
```

### 3.2 原始输出

```
=== semantics of existing 'source' fields ===
lunyu_quotes.json source samples: ['学而第一·1', '学而第一·1', '学而第一·1', '学而第一·4', '学而第一·3']
  -> citation label (chapter), NOT a data provider

debate_classics.json source samples:
   confucius ['《论语·泰伯》', '《论语·述而》']
   laozi ['《道德经·第二十二章》', '《道德经·第三十三章》']
   mozi ['《墨子·非乐上》', '《墨子·兼爱上》']
  -> citation label (book·chapter), NOT a data provider

lunyu_zhuxi.json top-level source: 朱熹《论语集注》
  per-item source: {'朱熹《论语集注》'}
  -> commentator attribution (朱熹《论语集注》), NOT a text provider/edition

classics_catalog.json sources (catalog-level only):
    中国哲学书电子化计划 https://ctext.org/zhs
    中国哲学书电子化计划·先秦两汉 https://ctext.org/pre-qin-and-han/zh
    维基文库 https://zh.wikisource.org/wiki/Portal:%E4%B8%AD%E5%9C%8B
  books with per-book source_url: 0
  books with per-book source_edition: 0
  books with per-book license: 0
  total books in catalog: 123

=== proofread / human-confirmation evidence search ===
keyword hits: NONE - no structured or prose human-review record found
```

### 3.3 逐文件判定

| 文件 | `source_provider` | `source_url` | `source_edition` | `license` | `verification_level` | `proofread_status` | 判定 |
|---|---|---|---|---|---|---|---|
| `lunyu.json` | 无 | 无 | 无 | 无 | 无 | 无 | **无来源字段，无法追溯底本** |
| `lunyu_quotes.json` | 无（`source`=篇章节号） | 无 | 无 | 无 | 无 | 无 | **无来源字段，无法追溯底本** |
| `debate_classics.json` | 无（`source`=书名篇名） | 无 | 无 | 无 | 无 | 无 | **无来源字段，无法追溯底本** |
| `classics_catalog.json` | 无（仅目录级 3 个 name） | **仅目录级 3 个** | 无 | 无 | 无 | 无 | 目录层有参考库名，**书目层与正文层无来源** |
| `knowledge_graph.json` | 无 | 无 | 无 | 无 | 无 | 无 | **无来源字段** |
| `quote_cards.json` | 无 | 无 | 无 | 无 | 无 | 无 | **无来源字段** |
| `timeline.json` | 无 | 无 | 无 | 无 | 无 | 无 | **无来源字段** |
| `idioms.json` | 无 | 无 | 无 | 无 | 无 | 无 | **无来源字段** |
| `comics.json` | 无 | 无 | 无 | 无 | 无 | 无 | **无来源字段** |
| `theater_scripts.json` | 无 | 无 | 无 | 无 | 无 | 无 | **无来源字段** |
| `backend/data/commentaries/lunyu_zhuxi.json` | 无（`source`=注疏者署名） | 无 | 无 | 无（仅散文称"公版"） | 无 | 无 | **无来源字段，无法追溯底本**；注疏者署名可考，但所据版本不可考 |

### 3.4 重要澄清 —— 现有 `source` 字段不是 PROJECT-BRIEF 要求的 source

必须避免把现有 `source` 误当作"有来源"。二者语义完全不同：

- 现有 `source`：**引用标签**（citation label）。回答"这句话出自哪一章"，供展示与校验用。
- PROJECT-BRIEF `source_provider`/`source_url`/`source_edition`：**数据溯源**（provenance）。回答"这段文本从哪个库、哪个版本、哪个 URL 抄来的"，供审计与授权用。

**当前系统有前者、完全没有后者。** `classics_catalog.json` 顶层的 ctext/wikisource URL 是**目录编写参考**，不能证明任何一条正文取自该处——因为 `build_lunyu.py` 实测无网络导入（见 4.1），且 123 部书 0 部带 `source_url`。

### 3.5 授权现状

- 唯一授权陈述：`lunyu_zhuxi.json` → `description`：「朱熹（1130-1200）…《四书章句集注》为元明清科举定本，公版已过版权期。」
  - 这是**散文陈述，非结构化字段**，且**未经独立核验**（外部访问受限）。
  - 就朱熹（1130–1200）著作而言，"公版"在常识上成立，但**当前仓库未记录所据底本、点校者、出版信息**——而现代点校本（如中华书局本）的**点校与标点本身可能仍有版权**。此处存在**授权风险，且当前无证据可判定**。
- 其余 10 个文件：**无任何授权陈述**。
- **禁止**：不得把上述"公版"散文当作已核验的 license 字段使用。

---

## 4. 原典真伪与质量抽查

### 4.1 生成方式取证 —— 语料是内置静态数据，非抓取

命令：
```powershell
python docs/kb-v1/audit/classical_audit_4_provenance.py
```
原始输出：
```
=== reproducibility: build_lunyu.py output vs on-disk lunyu.json ===
lunyu identical: True
quotes identical: True
...
=== script size / structure ===
build_lunyu.py lines: 677
contains network imports (requests/urllib/http): False
CH1/CH2/CH3 present: True
OTHER_CHAPTERS present: True
```

辅助计数：
```
V() call count in script: 107
A() call count: 86
```

**判定**：
- `build_lunyu.py` **无任何网络导入**（无 `requests`/`urllib`/`http.client`/`openai`），数据以 Python 字面量硬编码在脚本中（677 行，107 个 `V(...)` 调用）。
- 运行该脚本得到的对象与磁盘 `lunyu.json`/`lunyu_quotes.json` **完全相等（`identical: True`）** → 磁盘文件就是该脚本的产物，无后处理。
- 因此：**论语语料既非从 ctext/wikisource 抓取，也无任何可追溯的底本记录；它是人工编写（可能借助 LLM）后固化的静态字面量。**
- 结论对 PROJECT-BRIEF GATE-2「原典不得来自 LLM 生成」是**风险项**：无法从仓库内证明这些文本未经 LLM 生成或改写。**当前无法证实，也无法证伪。**

### 4.2 抽样核对（12 条，覆盖论语/道德经/墨子/韩非子/注疏）

以下逐条给出存储原文、内部一致性检查结果与不确定度。**"通行本一致性"因外部访问受限（见 8 节）无法最终断言，故只报告可本地证实的事实与疑点。**

| # | 位置 | 存储原文（截断） | 本地可证事实 | 不确定度 |
|---|---|---|---|---|
| 1 | `lunyu.json` 1.1 | 子曰：「学而时习之，不亦说乎？有朋自远方来，不亦乐乎？人不知而不愠，不亦君子乎？」 | 引号平衡；简体；`「」` 引号风格统一 | 与通行本字面高度相符（常识判断，未外部核验） |
| 2 | `lunyu.json` 2.4 | 子曰：「吾十有五而志于学，三十而立…七十而从心所欲，不逾矩。」 | 引号平衡；简体 | 同上 |
| 3 | `lunyu.json` 4.5 | 子曰：「富与贵，是人之所欲也；不以其道得之，不处也。贫与贱，是人之所恶也；**不以其道得之，不去也**。…」 | 引号平衡 | **疑点**：通行本此处多作「不以其道**去**之」（意为"不用正当手段摆脱它"），存储文本作「得之」。**本机无法外部核验，标记为待核验差异。** |
| 4 | `lunyu.json` 8.7 | 曾子曰：「士不可以不弘毅，任重而道远。仁以为己任，不亦重乎？死而后已，不亦远乎？」 | 引号平衡 | 与通行本相符（常识判断） |
| 5 | `lunyu.json` **3.22** | 子曰：「管仲之器小哉！」或曰：「管仲俭乎？」曰：「管氏有三归，官事不摄，焉得俭？」「然则管仲知礼乎？」**邦君树塞门，管氏亦树塞门。…管氏而知礼，孰不知礼？」** | **`「`×4 / `」`×5，引号不平衡（全库唯一一处）** | **确认缺陷**：`「然则管仲知礼乎？」` 之后缺少 `曰：「`，导致后文 3 处 `」` 无配对。见 4.3。 |
| 6 | `lunyu.json` 12.1 | 颜渊问仁。子曰：「克己复礼为仁。…非礼勿动。」颜渊曰：「回虽不敏，请事斯语矣。」 | 引号平衡 | 与通行本相符 |
| 7 | `lunyu.json` 12.2 | 仲弓问仁。子曰：「出门如见大宾，使民如承大祭。己所不欲，勿施于人。…」 | 引号平衡 | 与通行本相符 |
| 8 | `lunyu.json` 15.24 | 子贡问曰：「有一言而可以终身行之者乎？」子曰：「其恕乎！己所不欲，勿施于人。」 | 引号平衡 | 与通行本相符 |
| 9 | `debate_classics.json` `laozi/daodejing-08-01` | 上善若水，水善利万物而不争。 | 引号平衡；声称出处 `《道德经·第八章》` | **摘句非完整章**（通行本第八章尚有"处众人之所恶…"等句）。摘句本身与通行本前两句相符 |
| 10 | `debate_classics.json` `mozi/mozi-jianai-02` | 言必信，行必果。 | 声称出处 `《墨子·兼爱下》` | **强疑点**：「言必信，行必果」通行归《论语·子路》13.20（且原文为"言必信，行必果，硁硁然小人哉"）。见 6.2 冲突条目 |
| 11 | `debate_classics.json` `hanfeizi/hanfeizi-erbing-01` | 赏罚者，邦之利器也。 | 声称出处 `《韩非子·二柄》` | **待核验**：《韩非子·二柄》确有"明主之所导制其臣者，二柄而已矣。二柄者，刑德也"；「邦之利器」更近《韩非子·喻老》/《老子》"国之利器不可以示人"语境。**本机无法外部核验，标记待核验。** |
| 12 | `lunyu_zhuxi.json` `1.1` | 学之为言效也。人性皆善，而觉有先后…（朱熹注） | 引号平衡；注疏者署名 `朱熹《论语集注》`；与 `lunyu.json` 1.1 原文 **exact match** | 朱熹注文与通行《论语集注》风格相符；但**所据版本（点校本/标点）不可考** |

**繁体/简体与标点**：
- 全库正文为**简体**。逐文件扫描常见繁体字（說學為與禮樂無爲…）后，命中集合仅 `['仁','信','德','智','学'(部分)]` —— 这些字**简繁同形**，非真繁体。**不存在繁体版本**（`original_traditional` 字段亦缺失）。
- 标点：`lunyu.json` 使用 `「」『』《》，。：；！？、` 与 ASCII `.`（出现在 `10.x`/`18.x` 的 ID 中）。全库标点风格不统一（`debate_classics` 混用 `-`、`/`、`·`）。

### 4.3 确认缺陷明细：`lunyu.json` 3.22

原始输出（`repr` 级）：
```
original repr: '子曰：「管仲之器小哉！」或曰：「管仲俭乎？」曰：「管氏有三归，官事不摄，焉得俭？」「然则管仲知礼乎？」邦君树塞门，管氏亦树塞门。邦君为两君之好，有反坫，管氏亦有反坫。管氏而知礼，孰不知礼？」'
count「: 4  count」: 5
contains 曰：「邦君: False
```

- 缺陷：`「然则管仲知礼乎？」` 之后应为 `子曰：「邦君树塞门…`，存储文本**丢失 `子曰：「`**，导致 4 个 `「` 对应 5 个 `」`。
- 影响：该条被 `rag_service` 拼成检索文档时，引号残缺会污染 quote 逐字校验；也是 quote verifier 的天然对抗样本。
- **本报告不修改此文本**（任务明令禁止补写/修正原典）。仅记录，供 PHASE 1/2 修复流程处理。

### 4.4 不确定度声明

- 上述"与通行本相符"均为**基于常识的判断，未经外部权威库核验**。本机网络对 ctext.org / zh.wikisource.org 返回 `non-public IP address`，web_search 因缺 key 不可用。
- 因此：**本审计不主张任何一条文本"已核验为通行本"**。凡涉及版本比对的结论一律标注为"待外部核验"。
- 唯一**可本地确证**的缺陷是第 5 条（3.22 引号不平衡）与第 4.1 节（生成方式）。

---

## 5. 注疏层审计

### 5.1 命令与原始输出

```powershell
python docs/kb-v1/audit/classical_audit_2_scale.py   # C 段
python docs/kb-v1/audit/classical_audit_1_integrity.py
```
```
=== C. commentary layer (L2) ===
commentaries: 15 distinct commentators: {'朱熹《论语集注》'}
coverage: 15/107 lunyu verses = 14.0%
```
```
=== commentary original vs lunyu original exact match ===
exact matches: 13 / 15
   ('12.1', 'SUBSTRING')
   ('12.2', 'SUBSTRING')
```

### 5.2 事实表

| 项 | 值 |
|---|---|
| 注疏文件 | `backend/data/commentaries/lunyu_zhuxi.json`（8397 B） |
| 注疏条数 | **15** |
| 注疏者 | **仅 1 家：朱熹**（`source` 恒为 `朱熹《论语集注》`） |
| 注疏朝代 | 文件级 `dynasty: 南宋`；**条目级无 `commentary_dynasty` 字段** |
| 覆盖范围 | 15 / 107 = **14.0%** 的论语章节 |
| 与原文分离存储？ | **物理文件分离，但条目内嵌原文副本**（`commentary[i].original`），且与 `lunyu.json` **13/15 逐字相同**、2 条（12.1、12.2）为子串关系 → 构成**重复存储与潜在不一致源** |
| 是否只有朱熹一家 | **是**，仅朱熹。无郑玄、何晏、皇侃、邢昺、刘宝楠等任何其他注疏传统 |
| 其他典籍注疏 | **零**（孟子/老子/庄子/墨子/韩非子注疏全无） |

### 5.3 影响

- PROJECT-BRIEF 第五章 L2「历代注疏」当前**只有南宋一家、覆盖 14% 的一本书**。这不足以支撑「历代注疏检索」与「多学派差异真实存在」。
- 注疏者信息**只以字符串形式存在于 `source`**，无 `commentator` / `commentary_dynasty` 结构化字段 → Evidence Drawer 要求的「注疏者」字段目前**无结构化数据可展示**。
- 注疏条目内嵌原文副本，违反「原典和注疏必须分开储存」的**数据规范化**要求（尽管文件是分开的）。

---

## 6. 交叉引用完整性（内部一致性）

### 6.1 命令与原始输出

```powershell
python docs/kb-v1/audit/classical_audit_1_integrity.py
```
```
lunyu verse ids: 107

=== lunyu_quotes.json source -> verse_id resolution ===
unresolvable: 2
   ('q17', '里仁第四·17', '-> 4.17 NOT IN lunyu.json')
   ('q18', '里仁第四·19', '-> 4.19 NOT IN lunyu.json')

=== idioms.json chapter_num.verse_num -> verse_id resolution ===
unresolvable: 16
   ('见贤思齐', '4.17', '论语·里仁', '见贤思齐焉，见不贤而内自省也。')
   ('不耻下问', '5.15', ...)
   ('见利思义', '14.12', ...)
   ('不在其位不谋其政', '8.14', ...)
   ('后生可畏', '9.23', ...)
   ('匹夫不可夺志', '9.26', ...)
   ('岁寒知松柏', '9.28', ...)
   ('知者不惑', '9.29', ...)
   ('成人之美', '12.16', ...)
   ('名正言顺', '13.3', ...)
   ('言必信行必果', '13.20', ...)
   ('以德报怨', '14.34', ...)
   ('工欲善其事必先利其器', '15.10', ...)
   ('人无远虑必有近忧', '15.12', ...)
   ('当仁不让', '15.36', ...)
   ('有教无类', '15.39', ...)

=== idioms original_text vs lunyu original (substring check) ===
  MISMATCH 三十而立 2.4 | 吾十有五而志于学，三十而立，四十而不惑，五十而知天命，六十而耳顺，七十而从心所欲
  MISMATCH 从心所欲 2.4 | 七十而从心所欲不逾矩
text mismatches: 2

=== quote_cards.json quote -> lunyu original (substring check) ===
  NOT FOUND IN lunyu.json: qc_009 | 君子坦荡荡，小人长戚戚 | 《论语·述而》
  ... (共 9 条)
quote_cards not verbatim in lunyu.json: 9 / 22
```

### 6.2 内部出处冲突（**最高优先级发现**）

命令：`python docs/kb-v1/audit/classical_audit_3_layers.py`
```
=== internal attribution conflicts (same sentence, two claimed sources) ===
  CONFLICT: idioms.json says 论语/泰伯第八/任重道远  |  debate_classics[confucius] says 《论语·泰伯》
  CONFLICT: idioms.json says 论语/子路第十三/言必信行必果  |  debate_classics[mozi] says 《墨子·兼爱下》
```

- 第 1 条为**同一出处、不同粒度**，属正常（非冲突）。
- 第 2 条是**真冲突**：「言必信，行必果」
  - `idioms.json` 归 **《论语·子路》13.20**（且 `original_text` 为"言必信，行必果，硁硁然小人哉！抑亦可以为次矣。"）
  - `debate_classics.json` 归 **《墨子·兼爱下》**（`mozi-jianai-02`，原文仅"言必信，行必果。"）
  - **同一仓库内对同一句给出两个互斥出处。** 这正是 PROJECT-BRIEF 第十六章要求系统必须能区分的场景，而当前数据自身即已矛盾。
  - 本机无法外部裁决。**该条必须进入 PHASE 1 Source Registry 的强制复核队列。**
- 附带：`idioms.json` 的 13.20 条目本身**悬空**（`13.20` 不在 `lunyu.json` 的 107 条中，该篇只收了 13.6 与 13.17）。

### 6.3 悬空引用汇总

| 来源 | 问题 | 数量 |
|---|---|---|
| `lunyu_quotes.json` | `source` 指向 `lunyu.json` 中不存在的章节（4.17、4.19） | **2 / 36** |
| `idioms.json` | `chapter_num.verse_num` 指向 `lunyu.json` 中不存在的章节 | **16 / 39** |
| `quote_cards.json` | `quote` 无法在 `lunyu.json` 中逐字定位 | **9 / 22** |
| `idioms.json` | `original_text` 与 `lunyu.json` 对应章节文本不符（2.4 为摘引，属预期） | 2（低危） |

**含义**：`lunyu.json` 只收了 107/512 章（`description` 自述"共20篇512章（本数据集收录核心章节）"），而下游文件（quotes/idioms/quote_cards）按**完整论语**编号引用 → 大量引用落在语料之外。这直接破坏 Quote Verifier 的可验证性：**这些引文在当前知识库中找不到出处，会被判 `verifiable=false`，但它们其实是真实存在的论语章句。** 这是"知识库不完整"导致的**假阴性**，不是模型幻觉。

### 6.4 元数据不一致

| 文件 | 声明 | 实际 |
|---|---|---|
| `idioms.json` | `meta.total: 35` | **39** |
| `lunyu.json` | `description` 称"共20篇512章" | 收录 **107** 章 |
| `lunyu.json` | `total_chapters: 20` | 20（一致） |
| `lunyu_quotes.json` | `total: 36` | 36（一致） |

---

## 7. V1 目标书目覆盖表

### 7.1 命令与原始输出

```powershell
python docs/kb-v1/audit/classical_audit_2_scale.py   # D、E 段
```
```
=== D. V1 target booklist coverage ===
  论语       catalog=yes   corpus_passages=110
  孟子       catalog=yes   corpus_passages=0
  荀子       catalog=yes   corpus_passages=0
  大学       catalog=yes   corpus_passages=0
  中庸       catalog=yes   corpus_passages=0
  道德经      catalog=yes   corpus_passages=4
  庄子       catalog=yes   corpus_passages=0
  墨子       catalog=yes   corpus_passages=4
  韩非子      catalog=yes   corpus_passages=4
  商君书      catalog=yes   corpus_passages=0
  传习录      catalog=yes   corpus_passages=0
  孙子兵法     catalog=yes   corpus_passages=0
```

### 7.2 覆盖表（含缺口严重度）

| PROJECT-BRIEF 第四/二十章 书目 | 学派 | 目录中有 | 实际语料条数 | 缺口 | 严重度 |
|---|---|---|---|---|---|
| 《论语》 | 儒家 | 是 | **107 章**（另 3 条在 debate_classics 重复） | 完整本应为 512 章 → **缺 ~79%** | **高** |
| 《孟子》 | 儒家 | 是 | **0** | 全缺 | **blocker** |
| 《荀子》 | 儒家 | 是 | **0** | 全缺 | **blocker** |
| 《大学》 | 儒家 | 是 | **0** | 全缺 | **blocker** |
| 《中庸》 | 儒家 | 是 | **0** | 全缺 | **blocker** |
| 《道德经》 | 道家 | 是 | **4 条摘句** | 完整 81 章 → **缺 ~95%** | **blocker** |
| 《庄子》 | 道家 | 是 | **0** | 全缺 | **blocker** |
| 《墨子》 | 墨家 | 是 | **4 条摘句** | 完整 53 篇 → **缺 ~92%** | **blocker** |
| 《韩非子》 | 法家 | 是 | **4 条摘句** | 完整 55 篇 → **缺 ~93%** | **blocker** |
| 《商君书》 | 法家 | 是 | **0** | 全缺 | **blocker** |
| 《传习录》 | 心学 | 是 | **0** | 全缺 | **blocker** |
| 《孙子兵法》 | 兵家（可选） | 是 | **0** | 全缺 | 高 |

### 7.3 关键判断

- **PHASE 2 GATE-2「所有 passage 必须有 source；原典不得来自 LLM 生成」在当前数据上无法通过**：现有 passage **没有** `source_provider`/`source_url`/`source_edition`，且生成方式无法证明非 LLM（4.1）。
- **多学派"差异真实存在"缺乏数据基础**：道家 4 条、墨家 4 条、法家 4 条。以如此密度，所谓"多学派差异"在检索层**只能退化为角色扮演 prompt 差异**，而非证据差异。这与 PROJECT-BRIEF 第三章 Product P0「多学派差异真实存在」直接冲突。
- **`debate_classics.json` 还混入非 V1 目标的文学人物**：李白(2)、苏轼(1)、范仲淹(1)、王安石(1)、诸葛亮(1)。这些是文学/史传人物，不属于中国思想学派语料，会在"学派"维度污染 metadata filter。当前它们**无 `school` 字段**，无法被正确过滤或排除。

### 7.4 `classics_catalog.json` 的角色澄清

- 123 部书，字段为 `id/title/category/author/dynasty/description/coverColor/totalChapters`。
- **`totalChapters` 是"该书应有章数"的声明，不是"已收录章数"。** 例如论语 `totalChapters: 20`（篇数），孟子 14，庄子 33，墨子 53 —— 这些数字**与实际语料 0 条并存**，极易被误读为"已有数据"。
- 该文件**不含任何正文**。它是**书目展示层**，不是知识库语料层。任何统计都必须把它与 L1 语料严格区分。

---

## 8. L1–L5 五层结构现状映射

### 8.1 命令与原始输出

```powershell
python docs/kb-v1/audit/classical_audit_3_layers.py
```
```
=== L1-L5 layer inventory ===
L1 authoritative originals (text_type=original):
   lunyu.json verses: 107
   debate_classics.json verses: 21
L2 commentaries:
   lunyu_zhuxi.json: 15 commentator(s): {'朱熹《论语集注》'}
L3 persons/schools/relations (knowledge_graph.json):
   nodes: 21 persons: 16 concepts: 5 edges: 24
   persons: ['confucius', 'yanhui', 'zilu', 'zigong', 'zizhang', 'zixia', 'ziyou', 'ranqiu', 'minsun', 'ran_yong', 'zengzi', 'zisi', 'mencius', 'xunzi', 'dong_zhongshu', 'zhuxi']
   concepts: ['仁', '礼', '中庸', '孝', '学']
L4 thought concepts (other sources):
   concept-ish tags from idioms/quote_cards: 67 [...]
L5 modern problems:
   quote_cards.json modern_interpretation: 22
   lunyu_quotes.json scene (modern scenario): 36
   lunyu_quotes.json level: ['中级', '初级', '高级']
   theater_scripts.json modern_setting: ['职场', '职场', '校园', '职场', '职场', '校园']
   timeline.json events: 30
   idioms.json modern_usage: 39
```

### 8.2 五层映射表

| 层 | PROJECT-BRIEF 要求 | 现状 | 是否有独立存储/字段 | 缺口 |
|---|---|---|---|---|
| **L1 权威原典** | 权威原典 | 论语 107 章 + debate_classics 21 条摘句（含非思想类 6 条） | **无 `text_type` 字段**；靠文件区分 | **无来源字段**（3.3）；**无 `text_type`**（2.3）；覆盖 12 部中仅 3 部（7.2） |
| **L2 历代注疏** | 历代注疏 | 朱熹一家 15 条（14.0%） | 物理文件分离，但**条目内嵌原文副本**；**无 `commentator`/`commentary_dynasty` 字段** | 仅 1 家、1 部书、14%；无 `text_type='commentary'` 标记 |
| **L3 人物/学派/概念** | 人物、学派、概念 | `knowledge_graph.json`：21 node（16 person + 5 concept）、24 edge | 有独立文件与 `type`/`subtype` | **无 `school` 字段**；16 人物全为儒家一系（孔门+孟子/荀子/董仲舒/朱熹），**无老子/庄子/墨子/韩非**；concept 仅 5 个 |
| **L4 思想概念** | 思想概念 | 67 个自由文本 tag（散落在 `idioms.tags`、`quote_cards.tags`） | **无受控词表、无独立概念层** | 与 L3 的 5 个 concept 节点**互不关联**；`keywords`/`tags` 是自由文本，非本体 |
| **L5 现代问题** | 现代问题 | `lunyu_quotes.scene` 36、`idioms.modern_usage` 39、`quote_cards.modern_interpretation` 22、`theater_scripts.modern_setting` 6、`timeline` 30 | **全部为自由文本散文，无枚举、无本体** | PROJECT-BRIEF 第七章要求的 Modern Issue Ontology（career/workplace_conflict/fairness/anger…）**完全不存在**；无 `modern_scenarios` 结构化字段 |

### 8.3 核心结论

1. **五层没有在数据模型上分离。** 没有 `text_type` 字段，L1/L2 只靠"文件位置 + `doc_type` 字符串约定"区分，L3/L4/L5 分散在 6 个互不引用的 JSON 里。
2. **L3 是"儒家单线"图谱**，不是"人物/学派"图谱——缺全部非儒学派人物。以它做 `school` metadata filter 会**系统性漏检道家/墨家/法家**。
3. **L4 与 L3 脱节**：`knowledge_graph` 的 5 个 concept（仁/礼/中庸/孝/学）与 67 个 tag 之间**没有任何映射关系**。
4. **L5 是"散文"而非"本体"**：`scene`/`modern_usage`/`modern_interpretation` 都是给人读的句子，**无法用于结构化查询或 Concept Expansion**。PROJECT-BRIEF 第七章明确要求"不能直接丢给 embedding，先转换"，而当前数据**连转换所需的标注都不存在**。
5. **D 级内容（AI 解释）与 L1 原典在数据上无等级区分**：`quote_cards.modern_interpretation`、`comics`、`theater_scripts.moral` 是 AI 生成的现代解释，与 `lunyu.json` 的 `original` **没有任何 `verification_level` 字段加以区分**。前端无法据此分级展示，直接违背 PROJECT-BRIEF 第十四章「前端不得把 D 和 A 显示成同一等级」。

---

## 9. 不确定性与未核验项（诚实声明）

| 项 | 状态 | 原因 |
|---|---|---|
| 任何文本"与通行本一致" | **未核验** | ctext.org / zh.wikisource.org 访问被拒（`non-public IP address`）；web_search 缺 `DEEPSEEK_API_KEY` |
| 「言必信，行必果」归属（论语 13.20 vs 墨子 兼爱下） | **未裁决** | 同上；仅确认仓库内自相矛盾 |
| 4.5「不以其道得之，不去也」是否应作「去之」 | **待核验** | 同上 |
| `hanfeizi-erbing-01`「赏罚者，邦之利器也」出处 | **待核验** | 同上 |
| 朱熹注疏所据底本与点校版权 | **未核验** | 无版本记录；外部受限 |
| 语料是否曾由 LLM 生成/改写 | **无法证实也无法证伪** | 无生成日志、无 raw 底本、无 commit 记录（`git log --diff-filter=A` 显示语料在 `a275867` 一次性引入） |
| `quote_cards`/`comics`/`theater_scripts` 的 AI 生成性质 | **高度可疑但未确证** | 文本风格明显为现代 AI 生成；无生成记录 |
| 是否存在人工复核 | **确认不存在** | 关键词全文检索零命中（3.2） |

**必须强调**：上述"未核验"**不等于"错误"**。它们只是**当前仓库内无法判定**。任何后续文档（含 00-current-state.md）**不得**把这些条目写成"已确认"或"已核验"。

---

## 10. 对下游任务的输入（PHASE 1/2 直接可用）

### 10.1 阻塞项（blocker，必须先解决才能满足 GATE）

1. **无 Source Registry**：11 个语料文件全部缺 `source_provider`/`source_url`/`source_edition`/`license`。需新建 `sources/` 注册表 + 为每条 passage 绑定 `source_id`。
2. **无 `text_type` 分层**：L1/L2/D 级内容在数据上不可区分。需在 Schema 中强制 `text_type ∈ {original, commentary, translation, modern_explanation}`。
3. **无 `verification_level`/`proofread_status`**：无法区分 A/B/C/D。**当前全部语料只能标 C 或 D，禁止标 A**（无人复核记录）。
4. **V1 书目 12 部中 9 部零数据**，其中孟子/荀子/大学/中庸/庄子/商君书/传习录为完全缺失。
5. **语料不可追溯底本**：`build_lunyu.py` 为无网络内置字面量，`data/raw/` 为空。

### 10.2 高优先级缺陷

6. `lunyu.json` **3.22 引号不平衡**（全库唯一）——需修复，且应作为 quote verifier 的对抗样本。
7. `idioms.json` **16/39 悬空引用** + `lunyu_quotes.json` **2/36 悬空引用** + `quote_cards.json` **9/22 无法逐字定位** → 需在 ingestion 时做引用完整性校验并区分「语料缺失」与「引文伪造」。
8. **内部出处冲突**：「言必信，行必果」论语 vs 墨子 → 强制人工复核队列。
9. `debate_classics.json` 混入 6 条文学人物语料（李白/苏轼/范仲淹/王安石/诸葛亮），无 `school` 字段可过滤。
10. `idioms.json` `meta.total: 35` ≠ 实际 39。

### 10.3 Schema 设计建议（基于本次实测，供 PHASE 1 参考）

- 必须新增：`passage_id`（全局唯一，跨书统一）、`book_id`（slug，与 `classics_catalog.id` 对齐）、`text_type`、`source_id`→`source_provider/url/edition`、`license`、`verification_level`、`proofread_status`、`commentator`、`commentary_dynasty`、`school`、`concepts[]`（受控）、`original_traditional`/`original_simplified`。
- **原典与注疏必须拆表/拆 collection**：现状是同一 collection + `doc_type` 约定，需按 PROJECT-BRIEF 第六章要求物理或逻辑分离。
- **注疏不得内嵌原文副本**：改为 `commentary.passage_id → original.passage_id` 外键引用，消除 13/15 重复存储。
- `original` 必须保持**不可变且可溯源**；任何修复（如 3.22）必须走独立变更流程并留痕，不得就地静默改写。

### 10.4 对 GATE-2 可达性的判断

**当前数据无法通过 GATE-2。** 理由：
- "所有 passage 必须有 source" → 11 个文件全部无 source 字段（3.3）；
- "原典不得来自 LLM 生成" → 无法证明（4.1），且无 raw 底本（1.3）；
- 且 9/12 部目标书目为零数据（7.2）。

需先完成 PHASE 1（Schema + Source Registry）并从**可授权的真实来源**（如 ctext.org 或维基文库，须先核验其授权与可用性）导入正文，才可能满足。**本次审计未能访问外部来源，故导入可行性亦未验证。**

---

## 附录 A：本次审计的可复现命令清单

```powershell
cd D:\systemDir\Desktop\悟典
$env:PYTHONIOENCODING="utf-8"; [Console]::OutputEncoding=[System.Text.Encoding]::UTF8

python docs/kb-v1/audit/classical_audit_1_integrity.py        # 引文/典故交叉引用
python docs/kb-v1/audit/classical_audit_2_scale.py            # 规模/覆盖/Schema 字段
python docs/kb-v1/audit/classical_audit_3_layers.py           # L1-L5 分层/出处冲突
python docs/kb-v1/audit/classical_audit_4_provenance.py       # 生成器可复现性/缺陷
python docs/kb-v1/audit/classical_audit_5_source_semantics.py # source 语义/授权
```

## 附录 B：Git 取证

```
$ git log --diff-filter=A --format='%h %ad %s' --date=short -- data/processed/lunyu.json data/processed/debate_classics.json backend/data/commentaries/lunyu_zhuxi.json data/processed/idioms.json data/processed/quote_cards.json
a275867 2026-07-10 Prepare Wudian site for Sites deployment

$ git ls-files data/raw | Measure-Object -Line
0        # data/raw 未被 git 跟踪，且目录为空
```

## 附录 C：本次写入范围声明

- 新增（仅审计文档与只读脚本）：
  - `docs/kb-v1/audit/classical-knowledge.md`（本报告）
  - `docs/kb-v1/audit/classical_audit_{1..5}_*.py`（只读统计脚本）
- **未修改**：`data/**`、`backend/**`、`frontend/**`、`docs/kb-v1/PROJECT-BRIEF.md`。
- **未执行**：`git commit`、`git push`、任何部署或迁移。
- 未生成、未补写、未"修正"任何原典或注疏文本。
