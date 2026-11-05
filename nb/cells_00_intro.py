# -*- coding: utf-8 -*-
"""Notebook 第 0 部分：开场、环境准备、数据加载"""

CELLS = [
("md", r"""
# 基于 Python (pyBibX) 与 Web of Science 的文献计量学可视化分析

**教学版 Notebook —— 从零开始，一步一步做完 5 个子实验**

---

## 先说清楚：文献计量学到底在干什么？

你写了一篇开题报告，要写"国内外研究现状"。传统做法是**读文献**——读 30 篇、50 篇，然后靠记忆总结。
问题是：一个人一年能精读 100 篇就不错了，可你那个方向一年会发 3000 篇。

**文献计量学（Bibliometrics）就是：把"文献"当成"数据"，用统计方法去数、去算、去画图。**

打个比方：

| 你想知道的事 | 传统做法 | 文献计量学的做法 |
|---|---|---|
| 这个方向火不火？ | 凭感觉"好像挺火" | 数每年发文量，画折线 |
| 谁是这个方向的大牛？ | 听导师说、看谁老出现 | 算 H-index、合作网络中心性 |
| 这些论文在研究什么？ | 一篇篇读摘要 | 词云 + 主题建模，机器自动归类 |
| 这个领域的源头是哪几篇文章？ | 翻综述的参考文献 | 参考文献出版年谱（RPYS）找峰值 |
| 未来会往哪走？ | 猜 | 突现词检测（Burst Detection） |

**核心思想只有一句：一篇论文的"元数据"（作者、机构、关键词、参考文献、被引次数）本身就携带了大量信息，不需要读懂全文也能挖出来。**

---

## 这个实验的完整流程

```
   [1] 在 Web of Science 检索          ← 你去做（本 Notebook 用示例数据代替）
              │  导出 BibTeX（全记录 + 引用的参考文献）
              ▼
   [2] pyBibX 读入 .bib 并解析          ← pbx_probe()
              │
              ▼
   [3] 数据体检 → 清洗 → 规范同义词      ← 实验一
              │
              ▼
   [4] 看图说话：趋势 / 热点 / 引文 / 合作 / AI 主题
              │
              ▼
   [5] 写进实验报告：图 + 你的解读
```

---

## ⚠️ 关于本 Notebook 使用的数据

你现在看到的这份数据 **`work/wos_demo.bib` 是我为你生成的「模拟数据」**，不是真实文献。
它的期刊名、作者名、关键词分布都仿照"遥感变化检测"这个方向的真实生态构造，
**唯一目的是让你先把 15 个步骤全部跑通、看懂每张图在讲什么。**

等你从 WOS 导出真实的 `wos.bib` 之后：

> **只要改下面第 1 个代码单元格里的 `BIB_FILE` 这一行，其它代码一个字都不用动。**

真实数据的导出方法，见文件夹里的 `WOS检索与导出_操作手册.md`。
"""),

("md", r"""
## 0. 环境准备（只跑一次）

下面这个单元格做 4 件事，**不需要你改任何东西，直接运行**：

1. 把 HuggingFace 的模型缓存目录指到项目文件夹里（否则会去写你的家目录，可能没权限）；
2. 设定图片保存目录 `figs/`；
3. 装一个"小机关"：让 pyBibX 每次画完图，自动把图 **存成 PNG 文件**——这样你写实验报告时直接从 `figs/` 里拖图片就行，不用截图；
4. 打印环境版本，确认没装错。
"""),

("code", r'''
# ============================================================
# 0. 环境准备
# ============================================================
import os, re, sys, json, warnings, pathlib

# --- 路径设定：如果你把文件放在别处，只改这两行 ---
BIB_FILE = "work/wos_demo.bib"      # ← 换成你自己的 wos.bib 路径
FIG_DIR  = "figs"                   # ← 图片自动保存到这里

warnings.filterwarnings("ignore")
pathlib.Path(FIG_DIR).mkdir(exist_ok=True)
pathlib.Path("work/.mpl").mkdir(parents=True, exist_ok=True)

# 让 matplotlib 的字体缓存也待在工作目录里（避免没权限的报错）
os.environ.setdefault("MPLCONFIGDIR", os.path.abspath("work/.mpl"))
# HuggingFace 模型下载缓存（实验五要用）
os.environ.setdefault("HF_HOME", os.path.abspath("work/.hf"))
os.environ.setdefault("HF_HUB_CACHE", os.path.abspath("work/.hf/hub"))
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import numpy as np
import pandas as pd
from tabulate import tabulate
import plotly.io as pio
import plotly.graph_objects as go
import matplotlib.pyplot as plt

# 中文字体（macOS 自带，用于我们自己画的图）
plt.rcParams["font.sans-serif"] = ["PingFang SC", "Heiti SC", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# --- 在 Jupyter 里用交互式渲染；在命令行/无头环境用静态 PNG ---
try:
    get_ipython()
    pio.renderers.default = "notebook"   # JupyterLab 里鼠标可缩放、可悬停
    IN_NOTEBOOK = True
except NameError:
    pio.renderers.default = "png"
    IN_NOTEBOOK = False

# --- 小机关：pyBibX 内部调用 fig.show() 时，顺手把图存成 PNG ---
# 注意：这里用"指纹"保证幂等 —— 本单元格重复运行时不会再套一层，
#       否则每张图会被保存/显示 2 遍、3 遍……（就是"图片重复出现"的元凶）
from plotly.basedatatypes import BaseFigure

if getattr(BaseFigure.show, "_lab_patched", False):
    print("ℹ️ 图片保存补丁已存在，跳过（避免重复运行后每张图显示多遍）")
else:
    # 全新内核：先清空上一次留下的旧图，避免编号错乱
    _old = [f for f in os.listdir(FIG_DIR) if f.lower().endswith(".png")]
    for _f in _old:
        os.remove(os.path.join(FIG_DIR, _f))
    if _old:
        print(f"🧹 已清理 {len(_old)} 张上一次遗留的旧图")

    _orig_show = BaseFigure.show
    _fig_counter = {"n": 0}

    def _show_and_save(self, *args, **kwargs):
        _fig_counter["n"] += 1
        title = getattr(self.layout.title, "text", None) or "figure"
        slug  = re.sub(r"[^0-9A-Za-z]+", "_", str(title)).strip("_")[:45] or "figure"
        path  = os.path.join(FIG_DIR, f"{_fig_counter['n']:02d}_{slug}.png")
        try:
            self.write_image(path, scale=2, width=1150, height=680)
            print(f"   💾 图片已保存 → {path}")
        except Exception as exc:
            print("   ⚠️ 图片保存失败（不影响显示）:", exc)
        return _orig_show(self, *args, **kwargs)

    _show_and_save._lab_patched = True     # ← 幂等指纹
    BaseFigure.show = _show_and_save
    print("✅ 图片自动保存补丁已安装（只装一次）")


def save_mpl(name, facecolor=None):
    """把当前 matplotlib 图保存到 figs/ 目录"""
    fig = plt.gcf()
    path = os.path.join(FIG_DIR, name)
    fig.savefig(path, dpi=220, bbox_inches="tight",
                facecolor=facecolor or "white")
    print(f"   💾 图片已保存 → {path}")


print("=" * 62)
print("Python :", sys.version.split()[0])
import pybibx, plotly, matplotlib
print("pyBibX :", getattr(pybibx, "__version__", "5.x"))
print("plotly :", plotly.__version__)
print("matplotlib:", matplotlib.__version__)
print("运行模式:", "Jupyter 交互" if IN_NOTEBOOK else "脚本/无头")
print("=" * 62)
'''),

("md", r"""
### 这段输出的意思是

- `pyBibX : 5.9.5` —— 库版本，实验指导书就是按 5.x 写的；
- `运行模式: Jupyter 交互` —— 说明你在 JupyterLab 里，图表可以缩放；
- `✅ 图片自动保存补丁已安装` —— 之后每画一张图，都会自动存进 `figs/`；
- 如果出现 `图片保存失败` 的警告，说明 `kaleido` 没装好，**不影响看图**，只是需要自己截图。

> ⚠️ **这个单元格只应该在新内核里运行一次。**
> 它已经做了保护：即使你不小心又点了一次，也只会提示
> `ℹ️ 图片保存补丁已存在，跳过`，**不会再让图重复出现**。
>
> 如果你之前遇到过"同一张图出现好几遍"，那是因为旧版本的补丁被重复安装了。
> 解决办法：菜单 **Kernel → Restart Kernel**，然后重跑本单元格即可。

> 💡 **小知识**：为什么这里要设 `HF_HOME`？
> 实验五要用 BERT 类模型，模型文件有上百 MB，默认会下载到 `~/.cache/huggingface`。
> 在你自己的电脑上可能没权限写那里，所以提前指到项目目录里，一劳永逸。
"""),

("md", r"""
## 1. 载入数据：`pbx_probe`

### 先搞懂一个名词：`.bib` 文件里到底有什么？

Web of Science 导出 BibTeX 时，**每条文献就是一条记录**，长这样（简化版）：

```bibtex
@article{WOS:000123456700001,
Author          = {Zhang, Yong and Bruzzone, Lorenzo},        ← 作者
Title           = {Deep siamese network for change detection}, ← 标题
Journal         = {REMOTE SENSING OF ENVIRONMENT},             ← 期刊
Year            = {2020},
Abstract        = {Building change detection ...},             ← 摘要
Affiliation     = {Zhang, Y (Zhang, Yong)[1], Wuhan Univ, ...},← 作者单位+国家
Times-Cited     = {215},                                        ← 被引次数
Keywords        = {change detection; deep learning},            ← 作者关键词
Keywords-Plus   = {CONVOLUTIONAL NEURAL-NETWORK; ...},          ← 索引关键词
Cited-References= {Singh A, 1989, INT J REMOTE SENS, V10, P989; ...}  ← 参考文献
}
```

**加粗记一下：最后那个 `Cited-References`（引用的参考文献）是全实验的命根子。**

实验三的出版年谱、睡美人、主路径，实验四的突现词，全都只能从这一行里算出来。
所以在 WOS 导出时那个 **"Full Record and Cited References（全记录与引用的参考文献）"** 复选框 **必须勾上**，否则实验三、四直接做不了。

---

### `pbx_probe()` 在干什么？

一句话：**把 .bib 文本"翻译"成 pandas 表格**，并顺手算好一堆统计量（作者列表、期刊列表、国家列表、H-index……）。

看见 `A Total of 709 Documents were Found ( 730 Documents and 21 Duplicates )` 这行输出，说明：
- 文件里原本有 730 条记录；
- pyBibX 发现有 21 条是重复的（同一篇被导出两次）；
- 参数 `del_duplicated=True` 自动去掉了它们，剩下 **709 条有效文献**。

> 为什么要去重？因为 WOS 检索时如果一篇论文同时属于两个检索词，可能被重复导出。
> 不去重的话，后续所有"发文量"统计都会偏大。
"""),

("code", r'''
# ============================================================
# 1. 载入 .bib 数据
# ============================================================
from pybibx.base import pbx_probe

bibfile = pbx_probe(
    file_bib      = BIB_FILE,
    db            = "wos",     # 数据来源：wos / scopus / pubmed / openalex
    del_duplicated= True,      # 自动去重
)

print()
print("文献总数 :", bibfile.data.shape[0])
print("时间跨度 :", bibfile.date_str, "—", bibfile.date_end)
print("作者总数 :", len(bibfile.u_aut))
print("期刊总数 :", len(bibfile.u_jou))
print("国家总数 :", len(bibfile.u_ctr))
print("参考文献条数:", len(bibfile.u_ref))
'''),

("md", r"""
### 读一下这几个数字

- **文献总数 709** —— 落在指导书建议的 200～1000 篇区间里，合适。
  太多（>2000）跑 AI 模型会慢到崩，太少（<100）统计没意义。
- **时间跨度 2015—2026** —— 你导出时选的年份区间。
- **参考文献条数 261** —— 注意：这是**去重之后**的独立参考文献数。
  709 篇论文一共引用了 261 种不同的文献，平均每篇引 20 篇左右——这个比例是正常的。

> 🔍 **自查清单**（换成你自己的数据后，先看这 4 个数）
> | 检查项 | 正常范围 | 不正常说明什么 |
> |---|---|---|
> | 文献总数 | 200–1000 | 太少→检索式太窄；太多→加限定词 |
> | 参考文献条数 | > 文献总数的 1/3 | 太小→**导出时没勾 Cited References** |
> | 国家总数 | 20–80 | 只有 1–2 个→Affiliation 字段没导出来 |
> | 作者总数 | > 文献总数 | 明显偏少→作者字段串行解析出错 |
"""),
]
