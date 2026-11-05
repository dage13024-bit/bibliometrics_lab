# 文献计量学实验使用说明

**实验课题：基于 Python (pyBibX) 与 Web of Science 的文献计量学可视化分析**
**研究方向：遥感变化检测（Remote Sensing Change Detection）**

本项目是一套教学用文献计量分析流程：先用模拟的 Web of Science (WOS) 数据跑通分析，再可替换为自己从 WOS 导出的 BibTeX 数据。项目默认数据是模拟数据，不代表真实检索结果。

## 项目内容

- `文献计量学实验_遥感变化检测.ipynb`：主 Notebook，包含五组分析和逐步讲解。
- `work/wos_demo.bib`：用于演示的模拟文献数据。
- `nb/` 和 `build_notebook.py`：Notebook 单元格的源文件和组装脚本。
- `figs/`：示例分析图；运行 Notebook 会生成/更新图表。
- `work/results_summary.json`：示例分析摘要；Notebook 运行后会更新。
- `make_report.py`：根据分析结果和图表生成 Word 报告。
- `requirements.txt`：Python 依赖版本。
- `WOS检索与导出_操作手册.md`：从 WOS 检索并导出真实数据的说明。

本仓库不包含 Python 虚拟环境或模型缓存。每位使用者都应在自己的电脑上创建环境；Notebook 运行时产生的 Hugging Face 模型缓存会保存在 `work/.hf/`，不会提交到 Git。

## 运行环境

- Python **3.11**（推荐使用 3.11.18；不要使用系统 Python 或项目外的环境来代替下面创建的虚拟环境）。
- 已验证的基准环境为 macOS Apple Silicon。Linux/Windows 可能可用，但尚未在本项目中验证；安装 PyTorch 时应确保对应平台有可用的 Python 3.11 wheel。
- 安装依赖和首次下载 AI 模型需要网络。PyTorch 等科学计算依赖较大，请预留磁盘空间。

## Clone、安装并启动

### 1. Clone 仓库

```bash
git clone https://github.com/dage13024-bit/bibliometrics_lab.git
cd bibliometrics_lab
```

### 2. 创建并激活 Python 3.11 虚拟环境

macOS / Linux：

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell：

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

如果系统找不到 Python 3.11，请先安装 Python 3.11，再重新执行以上命令。

### 3. 安装依赖并注册 Notebook 内核

在已激活的虚拟环境中执行：

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m ipykernel install --user --name bibliometrics-lab --display-name "Python 3.11 (bibliometrics-lab)"
```

### 4. 启动 JupyterLab

仍在仓库根目录、且虚拟环境已激活时执行：

```bash
python -m jupyter lab
```

在浏览器中打开 `文献计量学实验_遥感变化检测.ipynb`。如果 Jupyter 提示选择内核，选择 **Python 3.11 (bibliometrics-lab)**。运行菜单中的 **Run → Restart Kernel and Run All Cells**，或逐格按 **Shift + Enter** 执行。

Notebook 默认读取 `work/wos_demo.bib`。它会将图表保存到 `figs/`，并将结构化结果写入 `work/results_summary.json`。第一次运行包含模型加载的实验可能需要额外等待；初次运行后缓存会复用。

## 使用自己的 WOS 数据

1. 按 [WOS 检索与导出操作手册](./WOS检索与导出_操作手册.md) 导出 BibTeX，记录内容选择 **Full Record and Cited References（全记录与引用的参考文献）**。
2. 将导出的文件命名为 `wos.bib`，放到仓库的 `work/` 目录。
3. 打开 Notebook 第一个代码单元格，将：

   ```python
   BIB_FILE = "work/wos_demo.bib"
   ```

   改为：

   ```python
   BIB_FILE = "work/wos.bib"
   ```

4. 选择 **Kernel → Restart Kernel and Run All Cells**，完整重跑 Notebook。

真实 WOS 文件可能包含受订阅条款限制的文献元数据。`work/wos.bib` 和 `work/wos_part*.bib` 已加入 `.gitignore`，不会被 Git 自动提交；请不要将这些文件或含真实数据的导出结果推送到公开仓库。

## 生成 Word 实验报告

Notebook 全部运行完成后，在仓库根目录、且虚拟环境已激活时执行：

```bash
python make_report.py
```

脚本会生成或更新 `实验报告_遥感变化检测.docx`。报告中的示例分析和结论基于模拟数据；换成真实 WOS 数据后，请检查并修改报告解读，确保结论对应实际结果。

## 常见问题

| 问题 | 解决办法 |
|---|---|
| 找不到 `python3.11` 或 `py -3.11` | 安装 Python 3.11，并确认终端能找到它。 |
| Notebook 选不到内核 | 重新激活 `.venv`，执行上面的 `ipykernel install` 命令，然后在 Jupyter 中选择 `Python 3.11 (bibliometrics-lab)`。 |
| 安装依赖失败或耗时较长 | 确认网络可用、磁盘空间充足，并确认当前 Python 是 3.11。PyTorch 等依赖较大。 |
| 实验五第一次运行卡在模型加载 | 首次运行需从 Hugging Face 下载模型；检查网络连接并等待下载完成。模型缓存位于 `work/.hf/`。 |
| Plotly 图表无法导出 PNG | 确认 `requirements.txt` 中的 Kaleido 已安装；也可以先在 Notebook 中查看交互图。 |
| 图里的中文字体显示不理想 | Notebook 优先使用 macOS 常见中文字体；其他系统可能需要安装中文字体，或调整字体设置。 |
| 报错 `No module named xxx` | 确认已激活本项目 `.venv`，然后在仓库根目录重新执行 `python -m pip install -r requirements.txt`。 |

## 学习建议

Notebook 按“现象 → 原因 → 启示”的顺序引导分析。建议重点阅读实验二的关键词演化、实验四的突现词检测和实验五的主题演化，并结合自己的检索范围解释结果；不要直接把模拟数据结论当作真实研究发现。
