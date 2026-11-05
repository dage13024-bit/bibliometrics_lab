# -*- coding: utf-8 -*-
"""Notebook 收尾：结果导出 + 换成自己数据的指引"""

CELLS = [
("md", r"""
---
# 🎯 收尾：把结果导出，自动生成实验报告

五个实验做完了，你现在手里有一堆图。最后一步是**把关键数字存下来**，
这样生成实验报告时就不用一个个手抄了。

下面这段代码会把本次分析的核心数字写进 `work/results_summary.json`，
然后运行 `../make_report.py` 就能自动生成一份带所有图表的 Word 实验报告。
"""),

("code", r'''
# ============================================================
# 6.1 导出核心结果到 JSON（供生成实验报告使用）
# ============================================================
import json, math
from collections import Counter

def _py(o):
    """把 numpy / pandas 类型转成 Python 原生类型，方便写 JSON"""
    if isinstance(o, (np.integer,)):  return int(o)
    if isinstance(o, (np.floating,)): return float(o)
    if isinstance(o, (np.ndarray,)):  return o.tolist()
    if isinstance(o, (pd.Timestamp,)):return str(o)
    return str(o)

def _safe(fn, default=None):
    """某些分析如果没跑过就跳过，不让导出报错"""
    try:
        return fn()
    except Exception as exc:
        print(f"   ⚠️ 跳过一项: {exc}")
        return default

N_DOCS = bibfile.data.shape[0]

summary = {
    "dataset": {
        "file"          : BIB_FILE,
        "n_docs"        : N_DOCS,
        "year_start"    : int(bibfile.date_str),
        "year_end"      : int(bibfile.date_end),
        "n_authors"     : len(bibfile.u_aut),
        "n_journals"    : len(bibfile.u_jou),
        "n_countries"   : len(bibfile.u_ctr),
        "n_institutions": len(bibfile.u_uni),
        "n_refs"        : len(bibfile.u_ref),
        "avg_citations" : float(bibfile.av_c_doc),
        "avg_authors"   : float(bibfile.av_doc_aut),
        "single_author" : int(bibfile.aut_single),
        "doc_types"     : {str(k): int(v) for k, v in bibfile.doc_types.items()},
    },
    "top_journals": [
        {"name": j, "docs": int(c)} for j, c in
        sorted(zip(bibfile.u_jou, bibfile.jou_count), key=lambda x: -x[1])[:15]
    ],
    "top_institutions": [
        {"name": i, "authors": int(c),
         "docs": int(sum(1 for row in bibfile.uni if i in row))}
        for i, c in
        sorted(zip(bibfile.u_uni, bibfile.uni_count), key=lambda x: -x[1])[:15]
    ],
    # 注意：ctr_count 统计的是"作者出现次数"，下面另外算一个"论文篇数"口径
    "top_countries": [
        {"name": c, "authors": int(n),
         "docs": int(sum(1 for row in bibfile.ctr if c in row))}
        for c, n in sorted(zip(bibfile.u_ctr, bibfile.ctr_count), key=lambda x: -x[1])[:15]
    ],
    "top_authors": [
        {"name": a, "h": int(h), "g": int(g), "m": float(m), "docs": int(d)}
        for a, h, g, m, d in sorted(
            zip(bibfile.u_aut, bibfile.aut_h, bibfile.aut_g,
                bibfile.m_index(CURRENT_YEAR), bibfile.doc_aut),
            key=lambda x: (-x[1], -x[3]))[:15]
    ],
    "top_keywords": [
        {"name": k, "count": int(c)} for k, c in
        sorted(zip(bibfile.u_auk, bibfile.auk_count), key=lambda x: -x[1])[:25]
    ],
    "docs_per_year": {
        int(y): int((bibfile.data["year"] == str(y)).sum())
        for y in range(int(bibfile.date_str), int(bibfile.date_end) + 1)
    },
}

# --- 字段完整度体检表 ---
if "health" in dir() and health is not None:
    summary["health"] = [
        {"field": str(r.iloc[0]), "pct": str(r.iloc[1])}
        for _, r in health.iterrows()
    ]

# --- RPYS 峰值 ---
if getattr(bibfile, "rpys_pk", None) is not None and len(bibfile.rpys_pk):
    summary["rpys_peaks"] = [
        {"year": int(r["Peak Years"]), "count": float(r["Counts"])}
        for _, r in bibfile.rpys_pk.sort_values("Counts", ascending=False).head(15).iterrows()
    ]

# --- 突现词 ---
if "burst_kw" in dir() and burst_kw is not None and len(burst_kw):
    cols = {c.lower(): c for c in burst_kw.columns}
    summary["bursts"] = [
        {str(k): _py(v) for k, v in row.items()}
        for row in burst_kw.head(20).to_dict(orient="records")
    ]

# --- 睡美人 ---
if "sleeping_beauties" in dir() and sleeping_beauties is not None and len(sleeping_beauties):
    _sb = []
    for _, row in sleeping_beauties.head(8).iterrows():
        _idx = int(str(row["ref"]).split("_")[1])
        _sb.append({
            "ref_id": str(row["ref"]),
            "text"  : bibfile.u_ref[_idx],
            "B"     : float(row.get("B", 0)),
            "t_a"   : int(row.get("t_a", 0)),
            "cm"    : int(row.get("cm", 0)),
        })
    summary["sleeping_beauties"] = _sb

# --- 主路径 ---
if "mp" in dir() and mp is not None and len(mp.get("path_table", [])):
    summary["main_path"] = [
        {"step": int(r["Step"]), "year": int(r["Year"]),
         "title": str(r["Title"])[:120], "author": str(r["Author"])[:90]}
        for _, r in mp["path_table"].iterrows()
    ]

# --- 主题模型 ---
if getattr(bibfile, "topic_info", None) is not None:
    summary["topics"] = [
        {"topic": int(r["Topic"]), "count": int(r["Count"]), "name": str(r["Name"])}
        for _, r in bibfile.topic_info.head(12).iterrows()
    ]

# --- 语义聚类结果 ---
if "labels" in dir() and labels is not None:
    _lab = pd.Series(list(labels)).value_counts().sort_index()
    summary["clusters"] = [{"cluster": int(k), "docs": int(v)} for k, v in _lab.items()]

# --- 期刊四象限 ---
if "port_jou" in dir() and port_jou is not None and len(port_jou):
    summary["portfolio"] = [
        {str(k): _py(v) for k, v in row.items()}
        for row in port_jou.head(25).to_dict(orient="records")
    ]

# --- 高被引经典参考文献 ---
_cnt = Counter(ref for refs in bibfile.ref for ref in refs)
summary["top_refs"] = [
    {"text": ref, "count": int(n), "year": int(bibfile.dy_ref[bibfile.u_ref.index(ref)])
     if ref in bibfile.u_ref and bibfile.dy_ref[bibfile.u_ref.index(ref)] > 0 else None}
    for ref, n in _cnt.most_common(12)
]

# --- 国家合作对 ---
_pair = Counter()
for countries in bibfile.ctr:
    real = sorted({c for c in countries if str(c).upper() != "UNKNOWN"})
    for i in range(len(real)):
        for j in range(i + 1, len(real)):
            _pair[(real[i], real[j])] += 1
summary["country_pairs"] = [
    {"a": a, "b": b, "n": int(n)} for (a, b), n in _pair.most_common(10)
]

# --- 关键词演化（每年 Top 关键词） ---
summary["outputs"] = {
    "figures": sorted(os.listdir(FIG_DIR)) if os.path.isdir(FIG_DIR) else [],
}

os.makedirs("work", exist_ok=True)
with open("work/results_summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2, default=_py)

print("✅ 结果已导出 → work/results_summary.json")
print("   收录字段:", ", ".join(summary.keys()))
print("   已生成图片 %d 张" % len(summary["outputs"]["figures"]))
'''),

("md", r"""
---
# 📌 换用你自己的真实数据（重要！）

本 Notebook 目前跑的是**模拟数据**。换成真实数据只需要 3 步：

### 第 1 步：在 Web of Science 导出数据

详细图文步骤见项目文件夹里的 **`WOS检索与导出_操作手册.md`**，要点是：

1. 检索式示例（主题检索，TS 表示检索"主题"字段，包括标题、摘要、关键词）：
   ```
   TS=("change detection" AND ("remote sensing" OR satellite OR "high resolution"))
   ```
2. 时间跨度选 **2015-2026**；
3. 数据库选 **Web of Science Core Collection**（核心合集），
   文献类型勾 **Article** 或 **Review**；
4. 导出 → 格式选 **BibTeX** → 记录内容选 **Full Record and Cited References**（全记录与引用的参考文献）。

> 🔴 **最容易出错的地方**：记录内容如果选成了"作者、标题、来源出版物"，
> 导出的 .bib 里**没有参考文献**，实验三、四会直接废掉。**一定要选全记录！**

### 第 2 步：改一行代码

回到本文档最上面第 0 个代码单元格，把：
```python
BIB_FILE = "work/wos_demo.bib"
```
改成：
```python
BIB_FILE = "work/wos.bib"      # 你的文件名
```

### 第 3 步：从头到尾重新运行

菜单栏 **Kernel → Restart Kernel and Run All Cells**。

> ⚠️ **换数据后必须重跑全部单元格**，因为 `bibfile` 对象是全局的，
> 只跑后面几个单元格的话，用的还是旧数据。

---

# 🧭 常见问题速查

| 现象 | 原因 | 解决 |
|---|---|---|
| `参考文献条数 = 0` | 导出时没勾 Cited References | 回 WOS 重新导出 |
| `国家总数 = 1` | .bib 里没有 Affiliation 字段 | 导出时选全记录 |
| 词云一片空白 | `Abstract` 字段全空 / 被 stopwords 过滤光 | 检查 `health_bib()` 结果 |
| 突现词全是领域大词 | `min_frequency` 太低 | 调到 5~8 |
| `docs_projection` 报错缺 umap | 没装 umap-learn | `pip install umap-learn` |
| 主题建模卡住不动 | 在下载 HuggingFace 模型 | 设置 `HF_ENDPOINT=https://hf-mirror.com` |
| `word_embeddings` 报 `UnboundLocalError` | pyBibX 5.9.5 的 bug | 已在上方打了补丁 |
| 图表里的字是方块 | 中文字体没设 | 第 0 个单元格已设置 PingFang SC |
| 主路径只有 1 步 | 数据集内部引用太少 | 正常现象，报告中如实说明 |

---

# 📝 写实验报告的检查清单

对照指导书的"五、实验报告要求"，逐项打勾：

- [ ] 写明**研究方向名称**（遥感变化检测）
- [ ] 写明**检索式**、**检索时间范围**、**有效文献篇数**
- [ ] 五个实验**各自的操作步骤**（可以直接抄本 Notebook 的代码说明）
- [ ] 每个子实验 **2~3 幅代表性图表**
- [ ] 每幅图配**针对本方向的文字解读**（不是描述图长什么样，而是**得出学术结论**）
- [ ] 回答指导书的三个具体问题：
  - 领域内**排名前三的期刊与机构**是谁？
  - **近三年突现**的研究前沿关键词是什么？
  - **AI 聚类**出的核心主题有哪些？
- [ ] 提交 `.ipynb` 源文件 + 实验报告文档

> 💡 **一个提分技巧**：每张图的解读都按"**现象 → 原因 → 启示**"三段式来写。
> 例："2020 年发文量陡增（现象）→ 因为 Transformer 被引入遥感领域（原因）
> → 说明该方向已进入方法快速迭代期，选题时应关注最新架构（启示）"。
"""),
]
