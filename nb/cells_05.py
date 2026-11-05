# -*- coding: utf-8 -*-
"""Notebook 第 5 部分：实验五 —— AI 语义聚类、主题建模、词向量"""

CELLS = [
("md", r"""
---
# 🤖 实验五：基于 AI 的文献语义聚类、主题建模与词向量

**这是全实验最"现代"的部分**，也是最能出彩的部分。

## 5.0 先搞懂：为什么前四个实验不够？

前面所有方法（词频、共词、共被引）都有一个共同的软肋：

> **它们只认得"字面"，不认得"意思"。**

举个真实的例子：
- 论文 A 的关键词是 `building change detection`
- 论文 B 的关键词是 `urban structure monitoring`

从字面上看，这俩毫无关系；但从语义上看，它们在做同一件事。
**词频统计永远发现不了这一点。**

**AI 方法解决的就是这个问题**：把每一段文字变成一个**向量**（一串数字），
"意思相近"的文本，向量在空间里的**距离也近**。这就是**语义嵌入（Semantic Embedding）**。

## 5.1 三个核心概念（用大白话）

| 概念 | 干什么 | 类比 |
|---|---|---|
| **Embedding（嵌入）** | 把文本变成向量 | 给每篇论文在地图上定一个坐标 |
| **降维（UMAP / t-SVD / PCA）** | 把 768 维压到 2 维 | 把地球仪摊平成一张地图（会损失信息，但能看了） |
| **聚类（K-Means / HDBSCAN）** | 把靠得近的点归成一堆 | 在地图上圈出"城市群" |

> **为什么必须降维？** 因为人眼只能看 2 维或 3 维。BERT 的输出是 768 维——
> 你可以想象成"768 维空间里的一个点"，人类的大脑根本无法可视化。
> UMAP 的任务就是**在尽量保留"谁离谁近"这个信息的前提下，把它压到 2 维**。

## 5.2 文献语义聚类散点图

`docs_projection()` 完整流程：

```
709 篇摘要 ──TF-IDF/SciBERT──> 高维向量 ──UMAP──> 2 维坐标 ──K-Means──> 5 个簇
```

**参数怎么选**：

| 参数 | 含义 | 建议 |
|---|---|---|
| `corpus_type` | 用什么文本 | `'abs'` 摘要（信息最全） |
| `n_clusters` | 分几类 | 5–8。太多会碎，太少没区分度 |
| `method` | 降维方法 | `'umap'` 效果好但慢；`'tsvd'` 快但粗糙 |
| `cluster_method` | 聚类算法 | `'kmeans'` 需要预先定簇数；`'hdbscan'` 自动定但可能全归一类 |
"""),

("code", r'''
# ============================================================
# 5.3 【绘图任务 5】基于 UMAP + K-Means 的文献摘要二维语义投影
# ============================================================
projection, labels = bibfile.docs_projection(
    view           = "notebook",
    corpus_type    = "abs",
    stop_words     = ["en"],
    n_components   = 2,
    n_clusters     = 5,
    method         = "umap",        # 想快一点就改成 'tsvd'
    cluster_method = "kmeans",
)

print("\n各聚类包含的文献数：")
display(pd.Series(labels).value_counts().sort_index().rename("文献数").to_frame())
'''),

("md", r"""
### 📖 读图指南

**看三件事**：

1. **簇与簇之间分得开不开**？
   - 分得很开 → 领域内存在**明显的研究流派**；
   - 混在一起 → 领域高度融合，大家都在做同一件事。
2. **有没有"离群点"**（孤零零的几个点）？
   那些就是**边缘选题**——往往是创新点所在，也可能是数据噪声。
3. **各簇的交界处**：交界处的论文往往**同时涉及两个主题**，是跨领域研究的候选。

> ✍️ **报告模板（回答"AI 聚类出的核心主题有哪些"）**：
> "基于 UMAP 降维与 K-Means 聚类的语义投影显示，709 篇文献在二维语义空间中
> 清晰分化为 5 个簇，其中最大簇（N 篇）集中于深度学习变化检测方法，
> 次大簇（M 篇）聚焦于多源遥感数据融合。
> 两簇在图中存在明显重叠区域，表明'深度学习方法'与'多源数据融合'
> 是本领域结合最紧密的两个研究板块。"

> ⚠️ **注意**：K-Means 的簇编号（0,1,2…）是**随机**的，每次运行可能不同。
> **簇编号本身没有含义**，只有"分成几堆"这件事有意义。
> 想让它可复现，在调用前设置 `np.random.seed(42)`。

---

## 5.3 主题建模（Topic Modeling）

### 和"聚类"有什么区别？

- **聚类**（上一节）：把**文献**分组 → "这 5 堆论文分别是什么"；
- **主题建模**：把**词**分组 → "这些论文里隐含了哪几个主题，每个主题由哪些词构成"。

**BERTopic** 的流程（pyBibX 底层用的就是它）：

```
摘要 ──Embedding──> 向量 ──UMAP 降维──> ──HDBSCAN 聚类──> ──c-TF-IDF──> 每个主题的关键词
```

最后那步 **c-TF-IDF** 是关键：它不是按"全局词频"选词，而是按
"**这个词在这个主题里比在别的主题里特殊多少**"来选词——
所以选出来的词才能真正代表这个主题。

**核心参数**：
- `embeddings=False` → 用 BERTopic 默认的 MiniLM 模型（快，通用）；
- `embeddings=True` → 用 SciBERT（`allenai/scibert_scivocab_uncased`，专为科技文献训练，效果更好但要下载 400MB）。

> 📌 指导书默认用 `embeddings=False`，**建议先用 False 跑通**，有精力再换 True 对比效果。
"""),

("code", r'''
# ============================================================
# 5.4 【绘图任务 5】NLP 主题建模（首次运行会下载约 90MB 模型）
# ============================================================
bibfile.topics_creation(
    stop_words       = ["en"],
    rmv_custom_words = ["study", "paper", "method", "results", "proposed", "based", "using"],
    embeddings       = False,
)

print("\n【表 5-1】各主题的规模与代表词")
display(bibfile.topic_info[["Topic", "Count", "Name"]].head(15))
'''),

("md", r"""
### 📖 读图指南（表 5-1）

- `Topic = -1` 的那一行是 **outlier（离群文献）**——算法认为它们不属于任何主题，
  通常占 20%–40%，**这是正常的**，别慌。
- `Name` 列里用下划线连起来的几个词，就是这个主题的"标签"。
  **读这些标签，自己给主题起个中文名**——这是实验报告里最能体现你理解深度的部分。

> ✍️ **报告模板**：
> "BERTopic 共识别出 K 个有效主题（另有 N 篇归为离群）。
> 其中 Topic 0（'change_detection_building'，XX 篇）对应**建筑物变化检测**，
> Topic 1（'deep_learning_transformer'，XX 篇）对应**深度学习方法**，
> Topic 2（'sentinel_landsat_time'，XX 篇）对应**多时相遥感监测**……"

---

## 5.4 五张主题可视化图

`topics_creation()` 建好模型后，五个 `graph_topics_*()` 从不同角度展示它：

| 函数 | 画什么 | 回答什么问题 |
|---|---|---|
| `graph_topics_distribution` | 主题规模分布 | **哪个主题最大**？ |
| `graph_topics` | 每个主题的核心词权重 | **每个主题到底在讲什么**？ |
| `graph_topics_projection` | 主题在二维空间的投影 | **哪些主题离得近**？ |
| `graph_topics_heatmap` | 主题间相似度矩阵 | **哪两个主题最像**（可能该合并）？ |
| `graph_topics_time` | 主题随时间的兴衰 | **哪个主题在崛起/衰退**？ |
"""),

("code", r'''
# ============================================================
# 5.5 【绘图任务 5】五张主题可视化图
# ============================================================
print("\n▶ (1) 主题分布")
bibfile.graph_topics_distribution(view="notebook")

print("\n▶ (2) 各主题核心词权重")
bibfile.graph_topics(view="notebook")

print("\n▶ (3) 主题向量空间投影")
bibfile.graph_topics_projection(view="notebook")
'''),

("code", r'''
# ============================================================
# 5.6 【绘图任务 5】主题相似度热力图 + 主题时间演化
# ============================================================
print("\n▶ (4) 主题相似度热力图")
bibfile.graph_topics_heatmap(view="notebook")

print("\n▶ (5) 研究主题随时间动态演化")
bibfile.graph_topics_time(view="notebook")
'''),

("md", r"""
### 📖 读图指南

**主题相似度热力图**（第 4 张）：
- 对角线一定是 1.0（自己和自己最像）；
- **非对角线上的深色格子** = 两个主题高度相似 → 说明它们**实际上是一个主题被拆开了**，
  可以回头把 `n_clusters` / BERTopic 的参数调小一点。

**主题时间演化图**（第 5 张）—— **这张最重要**：
- **持续上升的线** = 上升期主题（前沿）；
- **持续下降的线** = 衰退期主题（传统方法）；
- **某年突然出现的线** = 新兴主题。

> ✍️ **报告模板**：
> "主题演化图显示，'深度学习/Transformer'主题自 2019 年起快速上升，
> 至 2024 年已成为占比最高的主题；
> 而'面向对象分类/SVM'主题自 2020 年后持续衰减，目前仅占 X%。
> 两条曲线的交叉点出现在 **2020 年前后**，标志本领域主流范式的正式更替。"

这部分结论 **和实验二的突现词检测互相印证**，两处都提到"范式更替"，
报告的说服力会强很多——这是拿高分的关键。

---

## 5.5 Word2Vec 领域词向量

### 什么是词向量？

**Word2Vec** 把每个词变成一个 100 维的向量，而且**语义相近的词，向量也相近**。

它最神奇的性质是**向量运算**：

```
    向量("国王") - 向量("男人") + 向量("女人") ≈ 向量("女王")
```

在遥感领域，你可以试试：
```
    向量("sentinel") - 向量("landsat") + 向量("sar") ≈ ?
```

如果训练数据够大，它会告诉你"从 Sentinel 换到 SAR，类比于从 Landsat 换到 X"——
这就是**语义类比**。

### ⚠️ 一个必须先打的补丁

pyBibX 5.9.5 的 `word_embeddings()` 有一个**代码顺序 bug**：
`vocab` 变量在被赋值之前就被使用了（`UnboundLocalError`）。
这是原库的 bug，不是你的错。下面的代码给它打了个补丁，**用法完全不变**。
"""),

("code", r'''
# ============================================================
# 5.7 【补丁】修复 pyBibX 5.9.5 的 word_embeddings 变量顺序 bug
# ============================================================
import re as _re
from pybibx.base.pbx import pbx_probe, _get_fasttext


def _word_embeddings_fixed(self, stop_words=["en"], lowercase=True, rmv_accents=True,
                           rmv_special_chars=False, rmv_numbers=True, rmv_custom_words=[],
                           vector_size=100, window=5, min_count=1, epochs=10):
    """与官方实现逻辑一致，只是把 vocab 的定义提到了使用之前。"""
    FastText = _get_fasttext()
    if FastText is None:
        raise ImportError("word_embeddings() 需要 gensim，请先 pip install gensim")

    def tokenize(text):
        return _re.findall(r"\b\w+\b", text)

    corpus = self.data["abstract"].tolist()
    corpus = self.clear_text(corpus, stop_words=stop_words, lowercase=lowercase,
                             rmv_accents=rmv_accents, rmv_special_chars=rmv_special_chars,
                             rmv_numbers=rmv_numbers, rmv_custom_words=rmv_custom_words,
                             verbose=False)
    corpus = [tokenize(doc) for doc in corpus]

    model  = FastText(sentences=corpus, vector_size=vector_size, window=window,
                      min_count=min_count, epochs=epochs)
    vocab  = model.wv.index_to_key          # ← 官方代码把这行写在了后面，导致 UnboundLocalError
    w_emb  = [model.wv[w] for w in vocab]
    w_dict = {w: model.wv[w] for w in vocab}
    self.model_wv, self.model_cp, self.model_vc, self.model_wd = model, corpus, vocab, w_dict
    print(f"W2V Embeddings Ready（词表大小 {len(vocab)}）")
    return w_emb


pbx_probe.word_embeddings = _word_embeddings_fixed
print("✅ 补丁已应用")
'''),

("code", r'''
# ============================================================
# 5.8 【绘图任务 5】训练 Word2Vec + 语义相似度与向量运算
# ============================================================
w_emb = bibfile.word_embeddings(
    stop_words  = ["en"],
    vector_size = 100,
    window      = 5,
    min_count   = 2,
    epochs      = 10,
)

# --- (1) 语义相似度：两个词有多像 ---
print("\n【表 5-2】领域核心词的语义相似度（取值 -1 ~ 1，越大越像）")
_pairs = [("change", "detection"), ("deep", "learning"), ("sentinel", "landsat"),
          ("building", "urban"), ("transformer", "attention")]
_rows = []
for w1, w2 in _pairs:
    try:
        _rows.append({"词 1": w1, "词 2": w2, "相似度": round(bibfile.word_embeddings_sim(w1, w2), 3)})
    except KeyError:
        _rows.append({"词 1": w1, "词 2": w2, "相似度": "（词表中没有该词）"})
display(pd.DataFrame(_rows))

# --- (2) 向量加减：语义类比 ---
print("\n【表 5-3】向量运算 —— 'change + detection' 最接近的词")
try:
    for w, score in bibfile.word_embeddings_operations(positive=["change", "detection"],
                                                       negative=[], topn=6):
        print(f"   {w:<22} 余弦相似度 {score:.3f}")
except Exception as e:
    print("   （当前语料太小，无法完成该运算）", e)
'''),

("code", r'''
# ============================================================
# 5.9 【绘图任务 5】词向量语义空间关联图
# ============================================================
# positive 里每个子列表代表一组"相加"的词，可以填自己方向的核心概念
bibfile.plot_word_embeddings(
    view     = "notebook",
    positive = [["change", "detection"], ["deep", "learning"]],
    negative = [[], []],
    topn     = 5,
)
'''),

("md", r"""
### 📖 读图指南

**相似度表（表 5-2）**：
- `change` 和 `detection` 的相似度通常很高（>0.6），因为它们总是一起出现；
- `sentinel` 和 `landsat` 的相似度也高，因为它们是"同类事物的两种名字"。
- **相似度很低（<0.2）说明这两个词在语料中从不处于相似语境**。

> ⚠️ **诚实提示**：Word2Vec 的效果**高度依赖语料规模**。
> 700 篇摘要训练出来的词向量很可能"不太聪明"——这是正常的。
> 真实研究中要用几万篇甚至几十万篇摘要训练。
> 在报告里写"受语料规模限制，词向量效果的稳定性有限"是**加分项**，不是减分项。

---

## 5.6 用 BERT 自动生成文献综述段落（选做）

`summarize_ext_bert()` 用 BERT 做**抽取式摘要**：从一堆摘要里挑出最重要的句子拼成一段话。

**它是"抽取式"不是"生成式"**——意思是它**只是挑句子，不会自己造句**。
所以生成的结果是"像摘要的一段话"，而不是 ChatGPT 那种流畅的综述。
它的原理是：把每个句子都编码成向量，挑出那些"**和全文语义最接近、又彼此不重复**"的句子。

> ⚠️ **重要**：这个函数会把**传入的所有摘要拼成一大段**再处理。
> 709 篇摘要拼起来有 8 万多词，直接跑会**非常慢甚至卡死**。
> 所以下面用 `article_ids` **只取被引最高的 25 篇论文**——
> 这样既快，结果也更聚焦（高被引论文的摘要本来就更有代表性）。

### ⚠️ 但这里有两个"坑"，必须先处理

**坑 1：`summarizer` 库和 `transformers` 5.x 不兼容。**
`bert-extractive-summarizer` 这个库是老代码，它 `import TransfoXLModel`，
而这个类在新版 transformers 里已经被删掉了 → 一导入就报 `ImportError`。

**坑 2：它的默认模型是 `bert-large-uncased`，有 1.3 GB。**
下载慢、占内存，而且我们只是演示，完全没必要。

**解决办法**（下面代码干了三件事，都是"打补丁"，不影响用法）：
1. 给 transformers 临时补上两个缺失的类名；
2. 把默认模型换成 `paraphrase-MiniLM-L6-v2`（只有 90 MB，效果够用）；
3. 然后正常调用 `summarize_ext_bert()`。

> 💡 **这段代码本身就是很好的学习材料**：真实科研中你经常要"给别人的库打补丁"。
> 遇到报错时，**读 traceback → 找到是哪一行 import 失败 → 想办法补上**，这就是工程能力。
"""),

("code", r'''
# ============================================================
# 5.10 抽取式摘要：为"高被引文献"自动生成综述段落
# ============================================================
import sys, functools, warnings
warnings.filterwarnings("ignore")

# --- 补丁 1：先让 transformers 完成真实导入，再补上被删掉的两个类名 ---
from transformers import BertModel, BertTokenizer, PreTrainedModel, PreTrainedTokenizer
_tf = sys.modules["transformers"]
_tf.TransfoXLModel     = PreTrainedModel      # 占位符，实际不会用到
_tf.TransfoXLTokenizer = PreTrainedTokenizer

from summarizer import Summarizer
from summarizer.transformer_embeddings.bert_embedding import BertEmbedding
import pybibx.base.pbx as _pbx

# --- 补丁 2：注册一个"小号"模型，替掉默认的 1.3GB bert-large-uncased ---
_SMALL_MODEL = "sentence-transformers/paraphrase-MiniLM-L6-v2"
BertEmbedding.MODELS[_SMALL_MODEL] = (BertModel, BertTokenizer)
_pbx._get_bert_extractive_summarizer = lambda: functools.partial(Summarizer, model=_SMALL_MODEL)

# --- 正式调用 ---
_top25_ids = list(
    pd.Series(bibfile.citation, index=range(len(bibfile.citation)))
      .sort_values(ascending=False)
      .head(25).index
)

summary = bibfile.summarize_ext_bert(article_ids=_top25_ids)

print("\n【生成的综述段落】\n")
print(summary)
'''),

("md", r"""
### 怎么用这段文字

**直接抄进实验报告是不行的**——它是机器抽取的原句拼接，语言不通顺。
正确用法：

1. 读一遍，**提取它挑出了哪些"高频句式"**（比如都在强调 "accuracy", "challenge", "propose"）；
2. 把这些句式当成**"本领域论文的标准写法"**，反过来指导你自己的英文写作；
3. 从中挑 2–3 句**你觉得有代表性的话**，改写成你自己的综述句子。

> ✍️ **报告模板**：
> "利用 BERT 抽取式摘要对 25 篇高被引文献的摘要进行自动综述生成，
> 生成的文本集中于'变化检测的挑战性''多尺度特征融合''精度与效率的权衡'三个论述主题，
> 反映出本领域高被引论文的典型论述框架。"

---

## ✅ 实验五小结

产出物清单：
- 图 5-1 UMAP 语义聚类散点图
- 图 5-2 ~ 5-6 主题分布 / 核心词 / 空间投影 / 相似度热力图 / 时间演化
- 表 5-2 语义相似度、图 5-7 词向量空间图、自动综述段落

**五个实验全部完成！** 最后收个尾 →
"""),
]
