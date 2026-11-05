#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 nb/cells_*.py 里的教学单元格组装成一个 Jupyter Notebook。"""

import importlib
import sys
from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "nb"))

PARTS = [
    "cells_00_intro",
    "cells_01",
    "cells_02",
    "cells_03",
    "cells_04",
    "cells_05",
    "cells_99",
]

OUT = ROOT / "文献计量学实验_遥感变化检测.ipynb"

nb = nbf.v4.new_notebook()
nb.metadata = {
    "kernelspec": {
        "display_name": "Python 3 (pyBibX)",
        "language": "python",
        "name": "python3",
    },
    "language_info": {
        "name": "python",
        "version": "3.11",
        "mimetype": "text/x-python",
        "codemirror_mode": {"name": "ipython", "version": 3},
        "pygments_lexer": "ipython3",
        "nbconvert_exporter": "python",
        "file_extension": ".py",
    },
}

cells = []
for part in PARTS:
    mod = importlib.import_module(part)
    for kind, src in mod.CELLS:
        text = src.strip("\n")
        if kind == "md":
            cells.append(nbf.v4.new_markdown_cell(text))
        elif kind == "code":
            cells.append(nbf.v4.new_code_cell(text))
        else:
            raise ValueError(f"未知单元格类型: {kind}")

nb.cells = cells

with open(OUT, "w", encoding="utf-8") as f:
    nbf.write(nb, f)

n_md = sum(1 for c in cells if c.cell_type == "markdown")
n_code = sum(1 for c in cells if c.cell_type == "code")
print(f"✅ 已生成 {OUT.name}")
print(f"   共 {len(cells)} 个单元格（markdown {n_md} 个，code {n_code} 个）")
