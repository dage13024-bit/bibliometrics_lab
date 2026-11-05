#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重新生成 5 张 matplotlib 图（plotly 图不受影响）。

用途：figs/ 里这 5 张图丢失时补回来，不需要重跑整个 Notebook。
    ./venv/bin/python work/rebuild_mpl_figs.py
"""

import os
import sys
import warnings

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
os.environ.setdefault("MPLCONFIGDIR", os.path.join(ROOT, "work", ".mpl"))
warnings.filterwarnings("ignore")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import plotly.io as pio

pio.renderers.default = "png"

from pybibx.base import pbx_probe

FIG_DIR = "figs"
os.makedirs(FIG_DIR, exist_ok=True)

bibfile = pbx_probe(file_bib="work/wos_demo.bib", db="wos", del_duplicated=True)


def save(name, facecolor=None):
    path = os.path.join(FIG_DIR, name)
    plt.gcf().savefig(path, dpi=220, bbox_inches="tight", facecolor=facecolor or "white")
    print("  💾", path, os.path.getsize(path) // 1024, "KB")


print("1) 词云")
bibfile.word_cloud_plot(
    entry="abs", size_x=15, size_y=10, wordsn=300,
    rmv_custom_words=["study", "paper", "method", "results", "proposed",
                      "based", "using", "data", "approach", "however",
                      "also", "can", "may", "show", "shows", "propose"],
)
plt.gcf().set_facecolor("white")
save("Exp2_01_wordcloud_abstract.png", facecolor="white")
plt.close("all")

print("2) 本地引文历史图")
bibfile.network_hist(view="main", min_links=1, node_size=20, font_size=10, node_labels=True)
save("Exp3_04_local_citation_historiograph.png")
plt.close("all")

print("3) 核心作者合作子图")
plt.figure(figsize=(16, 12))
bibfile.network_collab(entry="aut", topn=12, rows=4, cols=3,
                       node_size=300, font_size=8, verbose=False)
save("Exp4_01_collaboration_subgraphs.png")
plt.close("all")

print("4) 度中心性网络")
plt.figure(figsize=(14, 11))
bibfile.network_adj(view="main", adj_type="aut", min_count=2,
                    node_labels=True, label_type="name", centrality="degree")
save("Exp4_02_network_degree.png")
plt.close("all")

print("5) 介数中心性网络")
plt.figure(figsize=(14, 11))
bibfile.network_adj(view="main", adj_type="aut", min_count=2,
                    node_labels=True, label_type="name", centrality="betw")
save("Exp4_03_network_betweenness.png")
plt.close("all")

print("\n✅ 完成")
