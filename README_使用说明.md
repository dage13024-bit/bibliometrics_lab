# 文献计量学实验使用说明

**实验课题：基于 Python (pyBibX) 与 Web of Science 的文献计量学可视化分析**
**研究方向：遥感变化检测（Remote Sensing Change Detection）**

---

## 一、这个文件夹里有什么

```
bibliometrics_lab/
│
├── 文献计量学实验_遥感变化检测.ipynb    ← ★ 主文件：教学版 Notebook（77 个单元格）
├── WOS检索与导出_操作手册.md            ← ★ 先读这个：怎么从 WOS 导出真实数据
├── 实验报告_遥感变化检测.docx            ← 自动生成的实验报告（含全部图表）
│
├── work/                                ← 数据和中间文件
│   ├── wos_demo.bib                     ← 模拟数据（730 篇，2015-2026）
│   ├── make_demo_bib.py                 ← 生成模拟数据的脚本
│   ├── results_summary.json             ← Notebook 跑完后导出的核心数字
│   └── .hf/                             ← HuggingFace 模型缓存（约 90MB）
│
├── figs/                                ← Notebook 自动保存的所有图表（PNG，可直接拖进 Word）
│
├── venv/                                ← 已装好 pyBibX 全套依赖的 Python 环境
├── runtime_py/                          ← 便携版 Python 3.11（不用装 conda 也能跑）
│
├── nb/                                  ← Notebook 的"源码"（拆成模块方便维护，不用管）
├── build_notebook.py                    ← 把 nb/ 组装成 .ipynb
└── make_report.py                       ← 用 figs/ + results_summary.json 生成 Word 报告
```

---

## 二、怎么启动 JupyterLab

打开 **「终端」** App（在"启动台"里搜"终端"），粘贴下面两行，每行按一次回车：

```bash
cd /Users/meilin/Desktop/bibliometrics_lab
./venv/bin/jupyter lab
```

成功的话，终端会打印一串 `http://localhost:8888/lab?token=...` 的网址，
**浏览器会自动打开**。如果没自动打开，就把那个网址复制到浏览器里。

在左侧文件列表里，双击 **`文献计量学实验_遥感变化检测.ipynb`** 打开。

> ⚠️ **关掉 JupyterLab 后如何再次打开？**
> 终端窗口关掉 = 服务停止。下次重新执行上面两行命令即可，数据不会丢。

> 💡 **为什么不用 Anaconda？**
> 你的 miniconda 默认环境是 Python 3.14，而 pyBibX 依赖的 torch / gensim
> 还没有 3.14 的安装包，装不上。所以我给你准备了一个 **独立的 Python 3.11 环境**
> （就是 `venv/` 文件夹），它和你的 miniconda 完全隔离，**不会影响你其他项目**。

---

## 三、第一次运行：怎么跑

打开 Notebook 后，按这个顺序做：

### 方式 A：一次跑完全部（推荐第一次用）

菜单栏 → **Run** → **Restart Kernel and Run All Cells**

然后去泡杯茶。第一次跑约 **3–6 分钟**（实验五的模型加载最慢）。
跑完后 `figs/` 里会自动出现 36 张图（PNG，220 dpi）。

### 方式 B：一节一节地跑（推荐理解用）

点击某个单元格 → 按 **Shift + Enter** 运行当前格并跳到下一格。

**建议按这种方式**：每跑完一个图，就停下来读一读下面的「📖 读图指南」，
对照着看你的图长什么样，再继续。这样 5 个实验跑完，你就真的学会了。

---

## 四、换用你自己的真实数据

现在 Notebook 跑的是**模拟数据**（`work/wos_demo.bib`），目的是让你先把流程跑通。

换成真实数据的完整步骤见 **`WOS检索与导出_操作手册.md`**，核心就 3 步：

1. 从 WOS 导出 `wos.bib`（**记录内容必须选「全记录与引用的参考文献」**），放进 `work/`；
2. 把 Notebook 第 1 个代码单元格里的
   ```python
   BIB_FILE = "work/wos_demo.bib"
   ```
   改成
   ```python
   BIB_FILE = "work/wos.bib"
   ```
3. **Kernel → Restart Kernel and Run All Cells**（必须全部重跑）。

图会自动重新生成，`figs/` 里的旧图会被新的覆盖。

---

## 五、生成实验报告

Notebook 全部跑完后，在终端里执行：

```bash
cd /Users/meilin/Desktop/bibliometrics_lab
./venv/bin/python make_report.py
```

会生成 / 更新 **`实验报告_遥感变化检测.docx`**，
里面已经排版好了五个实验的图表和文字解读框架。

> ⚠️ **报告里的「解读」文字是根据模拟数据写的**。
> 换成真实数据后，**必须自己重新跑 `make_report.py`，并修改文字里的结论**——
> 因为真实数据的 Top 期刊、突现词、主题都和模拟数据不一样。
> 报告里凡是出现 `XXX` 的地方，都是留给你填自己结论的。

---

## 六、常见问题

| 问题 | 解决办法 |
|---|---|
| `jupyter: command not found` | 没先 `cd` 到项目文件夹，或路径打错了 |
| 打开 Notebook 后选不到内核 | 菜单 Kernel → Change Kernel → 选 `Python 3` |
| 跑了半天卡住不动 | 实验五在下载模型。等 2 分钟；或在 Notebook 顶部环境单元格里加 `os.environ["HF_ENDPOINT"]="https://hf-mirror.com"` |
| 图里的中文变成方块 | 重新跑第 1 个代码单元格（字体设置在那里面） |
| 报错 `No module named xxx` | 在终端跑 `./venv/bin/python -m pip install xxx` |
| 想彻底重来 | 删掉 `figs/` 文件夹，Kernel → Restart & Run All |

---

## 七、学习建议（重要）

这份 Notebook 有 **43 个 Markdown 单元格**是讲解，**34 个代码单元格**是操作。
**代码你可以照抄，但讲解必须读懂**——因为实验报告要你自己写解读。

如果你只有一个小时，按这个优先级看：

1. **实验二的关键词演化图**（最能体现"你会做文献分析"）
2. **实验四的突现词检测**（直接回答"近三年前沿是什么"）
3. **实验五的主题演化图**（AI 部分，最出彩）
4. 实验一、三挑着看

写报告时，把每张图的解读按"**现象 → 原因 → 启示**"三段式写，
比单纯描述"图里有什么"高级得多。
