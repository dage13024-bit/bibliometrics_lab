#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_report.py
==============
根据 work/results_summary.json + figs/*.png 自动生成 Word 实验报告。

用法：
    ./venv/bin/python make_report.py

输出：
    实验报告_遥感变化检测.docx
"""

import json
import os
import re
from datetime import date

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(ROOT, "figs")
SUMMARY = os.path.join(ROOT, "work", "results_summary.json")
OUT = os.path.join(ROOT, "实验报告_遥感变化检测.docx")

HEI = "黑体"
SONG = "宋体"
KAI = "楷体"

# ---------------------------------------------------------------- 工具函数

def set_font(run, name=SONG, size=12, bold=False, color=None):
    run.font.name = name
    run.font.size = Pt(size)
    run.font.bold = bold
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:eastAsia"), name)
    rfonts.set(qn("w:ascii"), name)
    rfonts.set(qn("w:hAnsi"), name)
    if color is not None:
        run.font.color.rgb = color


def body(doc, text, indent=True, size=12, space_after=6, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.space_before = Pt(0)
    if indent:
        p.paragraph_format.first_line_indent = Pt(size * 2)
    p.alignment = align
    r = p.add_run(text)
    set_font(r, SONG, size)
    return p


def heading(doc, text, level=1):
    h = doc.add_heading(level=level)
    h.paragraph_format.space_before = Pt(14 if level == 1 else 10)
    h.paragraph_format.space_after = Pt(8)
    r = h.add_run(text)
    if level == 1:
        set_font(r, HEI, 16, True, RGBColor(0, 0, 0))
    elif level == 2:
        set_font(r, HEI, 14, True, RGBColor(0, 0, 0))
    else:
        set_font(r, HEI, 12, True, RGBColor(0, 0, 0))
    return h


def fig(doc, filename, caption, width_cm=15.5):
    path = os.path.join(FIG_DIR, filename)
    if not os.path.exists(path):
        body(doc, f"[图片缺失：{filename}]", indent=False)
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(path, width=Cm(width_cm))
    c = doc.add_paragraph()
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.space_after = Pt(12)
    r = c.add_run(caption)
    set_font(r, KAI, 10.5)


def table(doc, caption, headers, rows, widths=None, font_size=9, keep_together=True):
    c = doc.add_paragraph()
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.space_before = Pt(10)
    c.paragraph_format.space_after = Pt(3)
    c.paragraph_format.keep_with_next = True
    r = c.add_run(caption)
    set_font(r, KAI, 10.5)

    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    tblPr = t._tbl.tblPr
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblPr.append(layout)

    hdr = t.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].text = ""
        p = hdr[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        run = p.add_run(str(h))
        set_font(run, HEI, font_size, True)
        shd = OxmlElement("w:shd")
        shd.set(qn("w:fill"), "E7E6E6")
        hdr[i]._tc.get_or_add_tcPr().append(shd)

    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            txt = str(v)
            p.alignment = (WD_ALIGN_PARAGRAPH.LEFT if len(txt) > 14
                           else WD_ALIGN_PARAGRAPH.CENTER)
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            run = p.add_run(txt)
            set_font(run, SONG, font_size)

    # 固定列宽
    if widths:
        for i, w in enumerate(widths):
            t.columns[i].width = Cm(w)
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Cm(w)

    # 表格不跨页断开：除最后一行外，全部 keep_with_next
    n = len(t.rows)
    for ri, row in enumerate(t.rows):
        trPr = row._tr.get_or_add_trPr()
        cant = OxmlElement("w:cantSplit")
        trPr.append(cant)
        if keep_together and ri < n - 1:
            for cell in row.cells:
                for p in cell.paragraphs:
                    p.paragraph_format.keep_with_next = True

    # 表头跨页重复
    trPr = t.rows[0]._tr.get_or_add_trPr()
    th = OxmlElement("w:tblHeader")
    trPr.append(th)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    return t


def no_borders(t):
    tblPr = t._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement(f"w:{edge}")
        e.set(qn("w:val"), "none")
        e.set(qn("w:sz"), "0")
        borders.append(e)
    tblPr.append(borders)


COUNTRY_ZH = {
    "China": "中国", "Germany": "德国", "Italy": "意大利", "Netherlands": "荷兰",
    "France": "法国", "Japan": "日本", "Sweden": "瑞典", "Canada": "加拿大",
    "USA": "美国", "United States of America": "美国", "United Kingdom": "英国",
    "Spain": "西班牙", "Switzerland": "瑞士", "Iceland": "冰岛", "Iran": "伊朗",
    "Turkey": "土耳其", "Brazil": "巴西", "Singapore": "新加坡", "Malaysia": "马来西亚",
    "Hong Kong": "中国香港", "South Korea": "韩国", "India": "印度", "Australia": "澳大利亚",
}

JOURNAL_SHORT = {
    "remote sensing": "Remote Sensing",
    "ieee journal of selected topics in applied earth observations and remote sensing": "IEEE JSTARS",
    "remote sensing of environment": "Remote Sensing of Environment",
    "ieee transactions on geoscience and remote sensing": "IEEE TGRS",
    "ieee geoscience and remote sensing letters": "IEEE GRSL",
    "isprs journal of photogrammetry and remote sensing": "ISPRS J. Photogramm.",
    "international journal of applied earth observation and geoinformation": "Int. J. Appl. Earth Obs.",
    "international journal of remote sensing": "Int. J. Remote Sens.",
    "remote sensing letters": "Remote Sens. Lett.",
    "photogrammetric engineering and remote sensing": "PE&RS",
    "computers & geosciences": "Comput. Geosci.",
    "giscience & remote sensing": "GISci. Remote Sens.",
    "international journal of digital earth": "Int. J. Digit. Earth",
    "journal of hydrology": "J. Hydrol.",
    "journal of applied remote sensing": "J. Appl. Remote Sens.",
}


def _country(name):
    return COUNTRY_ZH.get(str(name), str(name))


def _jshort(name):
    return JOURNAL_SHORT.get(str(name).lower(), _title(name))


def _fmt_list(items, fmt="{name}（{n} 篇）", topn=3):
    return "、".join(fmt.format(name=n, n=v) for n, v in items[:topn])


def _title(name):
    """把全小写的期刊/机构名还原成好看的标题大小写"""
    keep_upper = {"ieee", "isprs", "jstars", "giscience", "uav", "sar", "lidar"}
    words = []
    for w in str(name).split():
        words.append(w.upper() if w.lower() in keep_upper else w.capitalize())
    return " ".join(words)


def _clean_inst(name):
    """机构名美化：wuhan univ → Wuhan University"""
    s = str(name)
    rep = [
        (r"\buniv\b", "University"), (r"\bacad\b", "Academy"), (r"\binst\b", "Institute"),
        (r"\bctr\b", "Center"), (r"\btechnol\b", "Technology"), (r"\baerosp\b", "Aerospace"),
        (r"\binformat\b", "Information"), (r"\bres\b", "Research"), (r"\bgeosci\b", "Geosciences"),
        (r"\bpolytech\b", "Polytechnic"), (r"\btech\b", "Technical"), (r"\bsci\b", "Sciences"),
        (r"\bnatl\b", "National"), (r"\bdef\b", "Defense"),
    ]
    for pat, sub in rep:
        s = re.sub(pat, sub, s, flags=re.I)
    return " ".join(w.capitalize() if not w.isupper() else w for w in s.split())


def add_page_number(section):
    p = section.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    for tag, txt in (("begin", None), (None, "PAGE"), ("end", None)):
        if tag:
            fld = OxmlElement("w:fldChar")
            fld.set(qn("w:fldCharType"), tag)
            run._r.append(fld)
        else:
            it = OxmlElement("w:instrText")
            it.set(qn("xml:space"), "preserve")
            it.text = txt
            run._r.append(it)
    set_font(run, SONG, 9)


# ---------------------------------------------------------------- 数据

with open(SUMMARY, encoding="utf-8") as f:
    D = json.load(f)

DS = D["dataset"]
N = DS["n_docs"]
Y0, Y1 = DS["year_start"], DS["year_end"]
VAULT = DS["file"]

dpy = {int(k): v for k, v in D["docs_per_year"].items()}
y_first = dpy.get(Y0, 0)
y_last_full = dpy.get(Y1 - 1, 0)
growth = y_last_full / y_first if y_first else 0

journals = [(j["name"], j["docs"]) for j in D["top_journals"]]
insts = [(_clean_inst(i["name"]), i["docs"]) for i in D["top_institutions"]]
countries = [(c["name"], c["docs"]) for c in D["top_countries"]]
authors = D["top_authors"]
keywords = [(k["name"], k["count"]) for k in D["top_keywords"]]
bursts = D.get("bursts", [])
topics = D.get("topics", [])
sleep = D.get("sleeping_beauties", [])
mpath = D.get("main_path", [])
port = D.get("portfolio", [])
pairs = D.get("country_pairs", [])
toprefs = D.get("top_refs", [])
health = D.get("health", [])
clusters = D.get("clusters", [])

j_top3 = sum(v for _, v in journals[:3])
j_top3_pct = j_top3 / N * 100 if N else 0

recent_bursts = [b for b in bursts if str(b.get("end_year", "0")).isdigit()
                 and int(b["end_year"]) >= Y1 - 1]
old_bursts = [b for b in bursts if str(b.get("start_year", "0")).isdigit()
              and int(b["start_year"]) <= Y0 + 3]

# ---------------------------------------------------------------- 文档

doc = Document()

sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
sec.top_margin = sec.bottom_margin = Cm(2.5)
sec.left_margin = sec.right_margin = Cm(2.5)
add_page_number(sec)

style = doc.styles["Normal"]
style.font.name = SONG
style.font.size = Pt(12)
style.element.rPr.rFonts.set(qn("w:eastAsia"), SONG)

# ---------------- 封面
for _ in range(2):
    doc.add_paragraph()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("实 验 报 告")
set_font(r, HEI, 30, True)

doc.add_paragraph()
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("基于 Python（pyBibX）与 Web of Science 的\n文献计量学可视化分析")
set_font(r, HEI, 18, True)

doc.add_paragraph()
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("——以遥感变化检测（Remote Sensing Change Detection）方向为例")
set_font(r, KAI, 13)

for _ in range(2):
    doc.add_paragraph()

info = [
    ("学　　院", "计算机与信息工程学院"),
    ("　实验室", "摄影测量与遥感实验室"),
    ("指导教师", "谢智颖"),
    ("研究方向", "遥感变化检测"),
    ("姓　　名", ""),
    ("学　　号", ""),
    ("班　　级", ""),
]
for k, v in info:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.left_indent = Cm(4.9)
    p.paragraph_format.space_after = Pt(14)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.line_spacing = 1.0
    r0 = p.add_run(f"{k}：")
    set_font(r0, SONG, 13)
    r1 = p.add_run(v if v else "　　　　　　　")
    set_font(r1, SONG, 13)
    if not v:
        r1.font.underline = True

p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(28)
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run(f"{date.today().year} 年 {date.today().month} 月")
set_font(r, SONG, 12)

doc.add_page_break()

# ---------------- 数据来源说明
p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(2)
r = p.add_run("⚠ 数据来源说明")
set_font(r, HEI, 11, True, RGBColor(0xC0, 0x00, 0x00))
p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(10)
r = p.add_run(
    f"本报告的全部图表由 make_report.py 依据 {os.path.basename(VAULT)} 自动生成。"
    "该 .bib 文件为教学演示用的模拟数据集（结构与字段完全仿照 WOS BibTeX 导出格式），"
    "用于在尚未取得真实检索数据时跑通完整分析流程。"
    "正式提交前，请按《WOS检索与导出_操作手册.md》导出本人检索结果 wos.bib，"
    "在 Notebook 中替换 BIB_FILE 后重新运行，再执行本脚本生成最终报告，"
    "并据真实结果改写各部分的分析结论。"
)
set_font(r, KAI, 10.5)
r.font.color.rgb = RGBColor(0x80, 0x80, 0x80)

# ---------------- 一、实验目的
heading(doc, "一、实验目的", 1)
for txt in [
    "掌握在 Web of Science 核心合集中围绕个人研究方向构建专业检索式、筛选高水平文献，"
    "并导出包含引文全记录的 BibTeX（.bib）数据集的方法。",

    "了解并掌握 Python 文献计量学与科学计量学前沿开源库 pyBibX（配合 numpy、pandas、"
    "tabulate、plotly 等包）的安装、数据清洗、实体消歧（Entity Normalization）与健康度诊断。",

    "从个人科研课题或毕业设计方向出发，通过 5 个由浅入深的子实验，掌握领域发文趋势统计、"
    "热点词云与演化分析、引文历史与睡美人文献挖掘、全球科研合作网络地图，以及基于人工智能"
    "（SciBERT / UMAP / BERTopic / Word2Vec）的文献语义聚类与主题演化成图技术，"
    "为撰写高水平文献综述与开题报告提供定量可视化图表支撑。",
]:
    body(doc, txt, indent=False)

# ---------------- 二、数据
heading(doc, "二、实验数据与检索策略", 1)

heading(doc, "2.1 检索策略", 2)
body(doc, "本实验以“遥感变化检测”为研究方向，检索策略设计采用概念分组法："
          "先拆出“变化检测”与“遥感数据源”两个核心概念，再用 OR 补齐各自的同义词，"
          "概念之间用 AND 连接，最后以发表年份与文献类型加以限定。")
table(
    doc, "表 2-1  检索策略与参数设置",
    ["项目", "设置"],
    [
        ["数据库", "Web of Science 核心合集（Web of Science Core Collection，SCI-Expanded）"],
        ["检索字段", "主题（TS = Topic，涵盖标题、摘要、作者关键词、Keywords Plus）"],
        ["检索式", 'TS=("change detection" AND ("remote sensing" OR satellite OR '
                   '"high resolution") AND ("deep learning" OR transformer OR siamese))'],
        ["时间跨度", f"{Y0} — {Y1} 年"],
        ["文献类型", "Article、Review"],
        ["语种", "English"],
        ["导出格式", "BibTeX"],
        ["记录内容", "全记录与引用的参考文献（Full Record and Cited References）"],
        ["去重后有效文献", f"{N} 篇"],
    ],
    widths=[3.6, 12.0], font_size=10,
)
body(doc, "需要特别说明的是，导出时“记录内容”必须选择“全记录与引用的参考文献”。"
          "该选项决定了 .bib 文件中是否包含 Cited-References 字段，而实验三的参考文献出版年谱（RPYS）、"
          "睡美人文献检测与主路径分析，以及实验四的突现词检测，均完全依赖这一字段。"
          "若导出时误选为“作者、标题、来源出版物”，上述两个子实验将无法开展。")

heading(doc, "2.2 数据概况", 2)
body(doc, f"本次分析共纳入 {Y0}—{Y1} 年间的文献 {N} 篇，其中 Article {DS['doc_types'].get('Article', 0)} 篇、"
          f"Review {DS['doc_types'].get('Review', 0)} 篇、"
          f"Proceedings Paper {DS['doc_types'].get('Proceedings Paper', 0)} 篇；"
          f"涉及作者 {DS['n_authors']} 位、机构 {DS['n_institutions']} 家、"
          f"国家或地区 {DS['n_countries']} 个、来源期刊 {DS['n_journals']} 种、"
          f"独立参考文献 {DS['n_refs']} 条；篇均被引 {DS['avg_citations']} 次，"
          f"篇均作者数 {DS['avg_authors']} 人，单作者论文 {DS['single_author']} 篇。")
table(
    doc, "表 2-2  数据集基本情况",
    ["指标", "数值", "指标", "数值"],
    [
        ["文献总数", f"{N} 篇", "独立参考文献", f"{DS['n_refs']} 条"],
        ["时间跨度", f"{Y0}—{Y1}", "篇均被引频次", f"{DS['avg_citations']}"],
        ["作者总数", f"{DS['n_authors']} 人", "篇均作者数", f"{DS['avg_authors']}"],
        ["机构总数", f"{DS['n_institutions']} 家", "单作者论文", f"{DS['single_author']} 篇"],
        ["国家/地区", f"{DS['n_countries']} 个", "来源期刊", f"{DS['n_journals']} 种"],
    ],
    widths=[3.6, 4.2, 3.6, 4.2],
)

if health:
    heading(doc, "2.3 字段完整度体检", 2)
    body(doc, "在开展任何分析之前，先调用 health_bib() 检查各字段的完整度，"
              "以避免在数据残缺的前提下得出错误结论。结果如表 2-3 所示。")
    table(
        doc, "表 2-3  数据集字段完整度体检结果",
        ["字段", "完整度"],
        [[h["field"], h["pct"]] for h in health],
        widths=[7.5, 5.0],
    )
    body(doc, "体检结果显示，摘要、参考文献、作者单位、作者关键词等关键字段的完整度均为 100%，"
              "说明数据集可用于全部五个子实验。实际使用真实 WOS 数据时，早期文献常出现摘要或关键词缺失，"
              "一般完整度达到 85% 以上即可开展分析，但需在报告中予以说明。")

# ---------------- 三、实验环境
heading(doc, "三、实验环境", 1)
table(
    doc, "表 3-1  实验软硬件环境",
    ["项目", "配置"],
    [
        ["操作系统", "macOS（Apple Silicon / arm64）"],
        ["Python", "3.11.18（独立虚拟环境，与系统 miniconda 隔离）"],
        ["核心库", "pyBibX 5.9.5、numpy 2.4、pandas 3.1、plotly 5.24、matplotlib 3.11"],
        ["AI 相关库", "sentence-transformers 6.2、BERTopic 0.17、umap-learn 0.5、gensim 4.4、torch 2.15"],
        ["可视化与交互", "JupyterLab 4.6、kaleido 0.2（plotly 静态导出）、WordCloud 1.9"],
    ],
    widths=[3.6, 12.0], font_size=10,
)

doc.add_page_break()

# ---------------- 四、实验一
heading(doc, "四、实验一：数据体检、实体规范化与基础计量分析", 1)

heading(doc, "4.1 操作步骤", 2)
for i, s in enumerate([
    "在 Web of Science 核心合集按表 2-1 的检索式检索，精炼文献类型后导出 BibTeX 全记录文件；",
    "调用 pbx_probe(file_bib='wos.bib', db='wos', del_duplicated=True) 载入数据并自动去重；",
    "调用 health_bib() 检查字段完整度，调用 eda_bib() 输出基本统计表；",
    "调用 normalize_entities(entity='kwa', method='fuzzy', threshold=0.88) 检测同义关键词变体；",
    "计算核心学者的 H-index、G-index、E-index 与 M-index；",
    "调用 plot_bars() 分别绘制年度发文量（dpy）、年度被引频次（cpy）与布拉德福核心期刊区（bdf_1）柱状图；",
    "调用 tree_map(entry='jou', topn=20) 绘制前 20 大载文期刊矩形树图。",
], 1):
    body(doc, f"（{i}）{s}", indent=False, space_after=3)

heading(doc, "4.2 实验结果", 2)
fig(doc, "01_Documents_per_Year.png", "图 4-1  年度发文量分布（2015—2026）")
fig(doc, "03_Bradford_s_Law_Core_Sources_1.png", "图 4-2  布拉德福核心期刊区分布")
fig(doc, "04_Sources.png", "图 4-3  前 20 大载文期刊矩形树图")

table(
    doc, "表 4-1  按 H-index 排名的前 10 位核心学者",
    ["排名", "作者", "H 指数", "G 指数", "M 指数", "发文量"],
    [[i, a["name"].title(), a["h"], a["g"], round(a["m"], 2), a["docs"]]
     for i, a in enumerate(authors[:10], 1)],
    widths=[1.4, 4.6, 2.0, 2.0, 2.0, 2.0],
)

heading(doc, "4.3 结果分析", 2)
body(doc, f"（1）发文趋势。{Y0}—{Y1} 年间，本领域年度发文量由 {y_first} 篇增至 {y_last_full} 篇，"
          f"增长约 {growth:.1f} 倍，年均复合增长率约 {(growth ** (1 / max(1, Y1 - 1 - Y0)) - 1) * 100:.1f}%。"
          f"曲线在 2018—2019 年与 2021—2022 年出现两次明显提速，前者与卷积神经网络、Siamese 网络"
          f"被大规模引入遥感变化检测的时间节点吻合，后者对应 Transformer 架构向遥感领域的迁移。"
          f"需要说明的是，{Y1} 年仅统计到部分月份（{dpy.get(Y1, 0)} 篇），其柱状图下凹属数据未完整所致，"
          f"不代表领域衰减。")

body(doc, f"（2）核心期刊。布拉德福核心区分析显示，载文量前三的期刊依次为 "
          f"{_fmt_list([(_jshort(j), v) for j, v in journals[:3]])}，"
          f"三刊合计载文 {j_top3} 篇，占全部文献的 {j_top3_pct:.1f}%，"
          f"呈现典型的布拉德福集中分布特征。矩形树图（图 4-3）进一步表明，期刊格局呈"
          f"“核心集中 + 长尾分散”的双重特征：既有稳定的主流阵地，也存在大量跨学科投稿渠道。")

body(doc, f"（3）核心学者。按 H-index 排序，本领域最具影响力的学者为 "
          f"{_fmt_list([(a['name'].title(), a['h']) for a in authors[:3]], fmt='{name}（H={n}）')}。"
          f"切换至 M-index 后，{authors[0]['name'].title()}（M={authors[0]['m']:.2f}）仍居前列，"
          f"说明其影响力并非单纯依靠资历积累，而是近五年保持高强度产出。"
          f"H-index 奖励“又多又好”，M-index 则消除了从业年限差异，二者结合可以区分"
          f"“资深高产型”与“新锐高影响型”两类学者。")

# ---------------- 五、实验二
heading(doc, "五、实验二：研究热点挖掘、关键词演化与多维关系可视化", 1)

heading(doc, "5.1 操作步骤", 2)
for i, s in enumerate([
    "调用 word_cloud_plot(entry='abs') 基于摘要绘制热点词云，并以自定义停用词表剔除 study、method 等学术废词；",
    "调用 get_top_ngrams(ngrams=2 / 3) 提取高频二元与三元专业词组；",
    "调用 plot_evolution_year(key='kwa', topn=10) 绘制关键词年度演化堆叠图；",
    "调用 term_growth(source='kwa', cumulative=True, line=True, bubble=True) 绘制累积增长气泡折线图；",
    "调用 sankey_diagram(entry=['cout','aut','jou']) 绘制国家—作者—期刊三维桑基图；",
    "调用 plot_heatmap_y_per_x(x='kwa', y='aut') 绘制高频关键词与核心作者交叉热力图；",
    "调用 institution_productivity() 与 authors_productivity() 绘制高产机构与作者的时间分布图。",
], 1):
    body(doc, f"（{i}）{s}", indent=False, space_after=3)

heading(doc, "5.2 实验结果", 2)
fig(doc, "Exp2_01_wordcloud_abstract.png", "图 5-1  基于摘要的高频热点词云图", width_cm=14.5)
fig(doc, "07_figure.png", "图 5-2  近十年研究热点关键词年度演化图")
fig(doc, "10_Sankey_Diagram_Countries_Authors_Journals.png",
    "图 5-3  国家—作者—期刊三维桑基图")
fig(doc, "11_Distribution_of_b_Authors_b_per_b_Auhors_Keyw.png",
    "图 5-4  高频关键词 × 核心作者交叉热力图")

heading(doc, "5.3 结果分析", 2)
body(doc, f"（1）热点主题。词云与 N-gram 统计显示，除 “change detection”“remote sensing” 两个主题词外，"
          f"“deep learning”“convolutional neural network”“transformer”“siamese network” 等方法词，"
          f"以及 “sentinel-2”“landsat”“UAV”“high resolution” 等数据源词构成第二梯队，"
          f"说明本领域已形成“多源遥感数据 + 深度学习方法”的基本技术格局。"
          f"按作者关键词频次统计，排名前 10 的关键词为："
          f"{_fmt_list([(k, v) for k, v in keywords[:10]], fmt='{name}（{n}）')}。")

body(doc, "（2）范式迁移。关键词年度演化图（图 5-2）呈现出清晰的三阶段结构："
          "2015—2017 年以 SVM、随机森林、面向对象分类等传统机器学习方法为主；"
          "2018—2020 年卷积神经网络与 Siamese 网络快速取代传统方法；"
          "2021 年以后 Transformer、自监督学习与基础模型成为新的增长点。"
          "各条累积增长曲线的斜率在 2020 年前后出现明显分化，正是范式更替的直接体现。")

body(doc, f"（3）合作与流向。桑基图显示，中国学者的产出占比最高，"
          f"并主要流向 {_jshort(journals[0][0])} 与 {_jshort(journals[1][0])}；"
          f"德国、意大利团队则更多流向 IEEE TGRS 与 ISPRS J Photogramm，"
          f"体现出“中方侧重工程应用、欧方侧重方法创新”的差异化发表格局。"
          f"交叉热力图表明，部分核心作者在单一主题上高度集中，属于技术专精型学者；"
          f"另一部分作者则在多个主题上均有高强度产出，呈平台化布局。")

# ---------------- 六、实验三
heading(doc, "六、实验三：引文轨迹、参考文献出版年谱与主路径分析", 1)

heading(doc, "6.1 操作步骤", 2)
for i, s in enumerate([
    "调用 plot_top_refs(topn=10) 识别领域被引次数最多的前 10 篇经典参考文献；",
    "按参考文献被引频次反查其在 pyBibX 中的编号，调用 plot_citation_trajectory(ref_ids=...) "
    "绘制前 3 篇代表作历年被引轨迹曲线；",
    "调用 plot_rpys(peaks_only=False) 绘制参考文献出版年谱高斯滤波寻峰图；",
    "调用 detect_sleeping_beauties(topn=10, min_count=5) 挖掘睡美人文献；",
    "调用 plot_co_citation_network() 绘制核心文献共被引网络；",
    "调用 network_hist() 绘制本地文献引文历史网络图；",
    "调用 main_path_analysis(method='spc') 提取领域技术演进主路径。",
], 1):
    body(doc, f"（{i}）{s}", indent=False, space_after=3)

heading(doc, "6.2 实验结果", 2)
fig(doc, "14_Top_Cited_References.png", "图 6-1  领域 Top 10 高被引经典参考文献")
fig(doc, "16_Reference_Publication_Year_Spectroscopy_RPYS.png",
    "图 6-2  参考文献出版年谱（RPYS）高斯滤波寻峰图")
fig(doc, "17_figure.png", "图 6-3  核心文献共被引网络图")

if sleep:
    table(
        doc, "表 6-1  睡美人文献检测结果（按 B 指数排序）",
        ["编号", "B 指数", "沉睡年数 t_a", "唤醒后被引 c_m", "文献信息"],
        [[s["ref_id"], f"{s['B']:.1f}", s["t_a"], s["cm"], s["text"][:52]]
         for s in sleep[:6]],
        widths=[1.6, 2.0, 2.6, 3.0, 6.4], font_size=8.5,
    )

if mpath:
    table(
        doc, "表 6-2  技术演进主路径（SPC 搜索路径计数法）",
        ["步骤", "年份", "文献标题", "第一作者"],
        [[m["step"], m["year"], m["title"][:56], m["author"].split(" and ")[0]]
         for m in mpath],
        widths=[1.4, 1.6, 9.4, 3.2], font_size=8.5,
    )

heading(doc, "6.3 结果分析", 2)
if toprefs:
    body(doc, f"（1）知识基础。被引频次最高的参考文献为 {toprefs[0]['text']}（被引 {toprefs[0]['count']} 次），"
              f"其次为 {toprefs[1]['text']}（{toprefs[1]['count']} 次）"
              f"与 {toprefs[2]['text']}（{toprefs[2]['count']} 次）。"
              f"值得注意的是，方法论文献与遥感领域文献同列前茅，说明本领域的方法创新"
              f"高度依赖计算机视觉的溢出效应，属于典型的“方法驱动型”研究方向。")

_peaks = D.get("rpys_peaks", [])
if _peaks:
    _top_peaks = sorted(_peaks, key=lambda x: -x["count"])[:5]
    _years_txt = "、".join(str(p["year"]) for p in _top_peaks)
    if len(_peaks) >= 3:
        body(doc, f"（2）历史脉络。参考文献出版年谱（RPYS）共识别出 {len(_peaks)} 个显著峰值，"
                  f"按高斯平滑后的被引强度排序，前五位峰值年份依次为 {_years_txt}。"
                  f"峰值所在年份即该领域知识基础的形成节点：早期峰值对应像元级变化检测理论框架"
                  f"与奠基性综述的发表，而近年峰值则对应深度学习通用架构被引入遥感领域。"
                  f"峰值之间的时间间隔较早期明显缩短，反映本领域知识积累与更新的节奏在持续加快。")
    else:
        body(doc, f"（2）历史脉络。RPYS 仅识别出 {len(_peaks)} 个显著峰值（年份：{_years_txt}），"
                  f"说明本文献集的引文基础高度集中在近期，缺乏可供回溯的早期知识节点。"
                  f"这一现象在检索时间跨度较短（如近 10 年）或领域本身较为年轻时十分常见，"
                  f"并不表示分析失败。若要挖掘更完整的知识谱系，应扩大检索时间跨度（如回溯至 1990 年），"
                  f"使参考文献年份分布覆盖更长的历史区间后再行分析。")
else:
    body(doc, "（2）历史脉络。RPYS 寻峰图显示，参考文献出版年谱存在若干显著峰值，"
              "分别对应本领域理论框架的确立、奠基性综述的发表以及深度学习方法的引入。")

if sleep:
    body(doc, f"（3）睡美人文献。检测结果显示，B 指数最高的文献为 {sleep[0]['text']}，"
              f"其沉睡期长达 {sleep[0]['t_a']} 年，唤醒后累计被引 {sleep[0]['cm']} 次，B 指数达 {sleep[0]['B']:.1f}。"
              f"这类文献的共同特征是“理论或方法超前于当时的数据条件与算力水平”，"
              f"直至相关技术成熟后才被重新发现，属于本领域被低估的知识节点。")

if mpath:
    body(doc, f"（4）主路径。SPC 算法共提取出 {len(mpath)} 步技术演进链，"
              f"起于 {mpath[0]['year']} 年的《{mpath[0]['title'][:40]}…》，"
              f"止于 {mpath[-1]['year']} 年的《{mpath[-1]['title'][:40]}…》。"
              f"该路径勾勒出本领域由传统特征工程向端到端深度网络演进的主干。"
              f"需说明的是，主路径长度受数据集内部引用密度的直接约束："
              f"若本批文献大量引用数据集之外的文献，路径会明显缩短，这属于数据本身的限制而非方法缺陷。")

# ---------------- 七、实验四
heading(doc, "七、实验四：合作网络、全球合作地图与突现检测", 1)

heading(doc, "7.1 操作步骤", 2)
for i, s in enumerate([
    "调用 network_collab(entry='aut', topn=12, rows=4, cols=3) 绘制核心作者合作网格子图；",
    "调用 network_adj(adj_type='aut', centrality='degree' / 'betw') 分别按度中心性与介数中心性着色的合作网络图；",
    "调用 network_adj_map(connections=True) 绘制全球国家/地区科研合作连线世界地图；",
    "调用 portfolio_analysis(entity='jou', impact='citations', thresholds='median') 绘制期刊生产力—影响力四象限图；",
    "调用 burst_detection(source='kwa', method='kleinberg') 检测研究前沿突现词；",
    "调用 knowledge_diffusion(mechanism='citation', viz='chord') 绘制知识跨国扩散弦图。",
], 1):
    body(doc, f"（{i}）{s}", indent=False, space_after=3)

heading(doc, "7.2 实验结果", 2)
fig(doc, "Exp4_02_network_degree.png", "图 7-1  基于度中心性着色的核心作者合作网络", width_cm=14.5)
fig(doc, "21_figure.png", "图 7-2  全球国家/地区科研合作连线世界地图")
fig(doc, "22_b_Portfolio_Analysis_Sources_b_br_span_style_.png",
    "图 7-3  期刊生产力—影响力四象限组合分析")
fig(doc, "23_b_Burst_Detection_Author_Keywords_b_br_span_s.png",
    "图 7-4  Kleinberg 研究前沿突现词检测")

if pairs:
    table(
        doc, "表 7-1  跨国合作最紧密的 8 组国家",
        ["排名", "国家 A", "国家 B", "合作论文数"],
        [[i, _country(p["a"]), _country(p["b"]), p["n"]] for i, p in enumerate(pairs[:8], 1)],
        widths=[1.6, 4.4, 4.4, 3.6],
    )

if bursts:
    table(
        doc, "表 7-2  突现词检测结果（按爆发强度排序前 10）",
        ["关键词", "起始年", "结束年", "持续年数", "爆发强度", "出现次数"],
        [[b.get("term", ""), b.get("start_year", ""), b.get("end_year", ""),
          b.get("length", ""),
          round(float(b.get("burst_strength", 0)), 1), b.get("total_count", "")]
         for b in bursts[:10]],
        widths=[5.0, 1.8, 1.8, 2.0, 2.4, 2.2], font_size=8.5,
    )

heading(doc, "7.3 结果分析", 2)
body(doc, f"（1）合作格局。合作子图矩阵显示，本领域存在若干个高密度合作团队，"
          f"多数呈“星型”结构（单一 PI 为核心），少数呈“网状”结构（成员间充分协作）。"
          f"按度中心性着色可识别出合作者最多的核心学者，按介数中心性着色则能发现"
          f"“度中心性不高但介数中心性突出”的结构洞中介者——这类学者在多个团队之间承担知识传递功能，"
          f"往往是跨学科创新的源头。")

body(doc, f"（2）国际合作。世界地图与表 7-1 显示，本领域形成了以中国、美国、德国、意大利为核心的合作枢纽，"
          f"最紧密的跨国合作对为 {_country(pairs[0]['a'])}—{_country(pairs[0]['b'])}（{pairs[0]['n']} 篇）"
          f"与 {_country(pairs[1]['a'])}—{_country(pairs[1]['b'])}（{pairs[1]['n']} 篇）。"
          f"中国是绝大多数跨国合作对的一端，说明其在全球合作网络中处于枢纽位置。")

if port:
    stars = [p for p in port if str(p.get("quadrant", "")).lower().startswith("star")]
    body(doc, f"（3）期刊定位。四象限分析显示，位于“高生产力—高影响力”明星象限的期刊有 "
              f"{len(stars)} 种，其中 {_fmt_list([(_jshort(p['entity']), int(float(p['productivity']))) for p in stars[:3]], fmt='{name}（{n} 篇）')}。"
              f"需要说明，此处“影响力”采用的是该刊在本研究样本内的总被引频次，而非 JCR 官方影响因子，"
              f"因此结论应表述为“在本研究样本中的表现”。")

if bursts:
    new_terms = [b for b in bursts if str(b.get("end_year", "")).isdigit() and int(b["end_year"]) >= Y1 - 1]
    body(doc, f"（4）研究前沿。Kleinberg 突现检测共识别出 {len(bursts)} 个显著突现词，"
              f"其中爆发窗口延续至 {Y1 - 1}—{Y1} 年的“仍在爆发”关键词有 {len(new_terms)} 个，"
              + (f"分别为 {_fmt_list([(b.get('term',''), round(float(b.get('burst_strength', 0)), 1)) for b in new_terms[:5]], fmt='{name}（强度 {n}）')}。" if new_terms else "。")
              + f"这些词集中指向基础模型、提示学习与可解释学习等方向，"
                f"可判定为本领域当前最前沿的研究主题。")

# ---------------- 八、实验五
heading(doc, "八、实验五：AI 语义聚类、主题建模与词向量", 1)

heading(doc, "8.1 操作步骤", 2)
for i, s in enumerate([
    "调用 docs_projection(corpus_type='abs', method='umap', cluster_method='kmeans', n_clusters=5) "
    "将文献摘要投影至二维语义平面并绘制聚类散点图；",
    "调用 topics_creation(stop_words=['en'], embeddings=False) 构建 BERTopic 主题模型；",
    "依次调用 graph_topics_distribution()、graph_topics()、graph_topics_projection()、"
    "graph_topics_heatmap()、graph_topics_time() 绘制五张主题可视化图；",
    "调用 word_embeddings() 训练领域专属 Word2Vec 词向量模型（此前需修复 pyBibX 5.9.5 的变量顺序缺陷）；",
    "调用 plot_word_embeddings() 绘制词向量语义空间关联图；",
    "调用 summarize_ext_bert(article_ids=Top25) 对高被引文献摘要生成抽取式综述段落。",
], 1):
    body(doc, f"（{i}）{s}", indent=False, space_after=3)

heading(doc, "8.2 实验结果", 2)
fig(doc, "25_figure.png", "图 8-1  基于 UMAP + K-Means 的文献摘要二维语义聚类散点图")
fig(doc, "26_figure.png", "图 8-2  各主题规模分布")
fig(doc, "30_Topic_Trends_Over_Time.png", "图 8-3  研究主题随时间动态演化趋势")
fig(doc, "31_figure.png", "图 8-4  Word2Vec 专业词汇语义空间关联图", width_cm=14.5)

if topics:
    table(
        doc, "表 8-1  BERTopic 识别出的主要研究主题",
        ["主题编号", "文献数", "主题标签（代表性词）"],
        [[t["topic"], t["count"], t["name"]] for t in topics[:10]],
        widths=[2.4, 2.4, 10.8], font_size=8.5,
    )

if clusters:
    body(doc, "K-Means 各簇的文献数分布为：" +
         "、".join(f"簇 {c['cluster']}（{c['docs']} 篇）" for c in clusters) + "。")

heading(doc, "8.3 结果分析", 2)
body(doc, "（1）语义结构。UMAP 投影图显示，文献在二维语义空间中呈现明显的分块结构，"
          "表明本领域存在若干可辨识的研究流派；同时各簇交界区域存在一定重叠，"
          "说明流派之间并非截然分立，跨主题的融合研究正在增加。"
          "需注意 K-Means 的簇编号本身不具含义，且受随机初始化影响，"
          "重复运行时编号可能变化，应设置随机种子以保证可复现。")

if topics:
    body(doc, f"（2）主题构成。BERTopic 共识别出 {len([t for t in topics if t['topic'] != -1])} 个有效主题"
              f"（编号为 -1 的离群文献属正常现象，通常占 20%—40%）。"
              f"规模最大的三个主题为：{_fmt_list([(t['name'].replace('_', ' '), t['count']) for t in topics if t['topic'] != -1][:3])}。"
              f"主题演化图进一步显示，方法类主题自 2019 年起持续上升，"
              f"而传统方法类主题同步衰减，两条曲线的交叉点即本领域主流范式的更替时点。")

body(doc, "（3）语义关联。Word2Vec 词向量结果显示，“change”与“detection”、“deep”与“learning”"
          "等共现频繁的词对具有较高的余弦相似度，说明模型已学习到本领域的基本语义结构。"
          "但需客观指出，受语料规模（数百篇摘要）限制，词向量的稳定性与泛化能力有限，"
          "语义类比运算的结果仅供参考，实际研究中应使用数万至数十万篇文献训练。")

# ---------------- 九、综合结论
heading(doc, "九、综合结论与讨论", 1)
body(doc, f"综合五个子实验的结果，可以得到以下结论：")

conclusions = [
    f"本领域处于快速上升期。{Y0}—{Y1} 年发文量增长约 {growth:.1f} 倍，"
    f"且增长主要由方法创新驱动，而非研究对象的扩张。",

    f"期刊格局呈现高度集中特征。前三甲期刊合计载文占比 {j_top3_pct:.1f}%，"
    f"投稿时应优先考虑核心区期刊。",

    "技术范式已经完成一次更替。关键词演化、主题时间演化与突现词检测三处证据相互印证，"
    "共同指向“传统机器学习 → 深度卷积网络 → Transformer / 基础模型”的三阶段演进路径，"
    "更替时点集中在 2020 年前后。",

    "知识基础呈“方法溢出”特征。高被引经典文献中既有遥感领域的综述，也有计算机视觉的通用架构论文，"
    "说明本领域的方法创新高度依赖外部学科的输入。",

    "国际合作呈枢纽型结构。中国在绝大多数跨国合作对中占据一端，"
    "德国、意大利团队则在方法输出上更为突出。",
]
for i, c in enumerate(conclusions, 1):
    body(doc, f"（{i}）{c}", indent=False, space_after=4)

body(doc, "从方法学角度，本实验完整走通了“数据检索清洗 → 热点演化分析 → 引文主路径追踪 → "
          "合作网络与突现检测 → AI 主题建模”的文献计量学闭环。"
          "其中，可视化只是手段，真正的价值在于：**把“读文献”这种无法规模化的个体劳动，"
          "转化为可复现、可量化、可比较的集体知识生产过程**。"
          "这也正是文献计量学在开题报告与综述写作中的意义所在。")

# ---------------- 十、问题与反思
heading(doc, "十、问题与反思", 1)
for i, s in enumerate([
    "pyBibX 5.9.5 的 word_embeddings() 存在变量顺序缺陷（vocab 在赋值前被引用），"
    "会抛出 UnboundLocalError；本实验通过 monkey patch 重新绑定了修正后的实现，用法保持不变。",

    "pyBibX 的 word_cloud_plot(entry='kwa') 实际读取的是 Keywords-Plus 字段而非作者关键词，"
    "属库内实现瑕疵；本实验改用 entry='abs' 规避，并在报告中予以说明。",

    "summarize_ext_bert() 依赖的 bert-extractive-summarizer 与 transformers 5.x 不兼容，"
    "且默认加载 1.3 GB 的 bert-large-uncased；本实验通过补充缺失类名、"
    "替换为 90 MB 的 paraphrase-MiniLM-L6-v2 解决。",

    "plot_bars(statistic='bdf_1') 实现的是“按发文量排序的前 N 种期刊”，"
    "并非严格的布拉德福分区算法，因此报告中表述为“核心期刊区”而非“严谨分区”。",

    "主路径长度受数据集内部引用密度约束。真实 WOS 数据中，文献大量引用数据集之外的成果，"
    "主路径往往只有 1—3 步，这属于数据本身的限制，不能据此否定方法的价值。",

    "本次分析使用的为教学模拟数据，各项结论的具体数值需在替换为真实 WOS 数据后重新生成。"
    "方法流程、图表规范与解读框架可直接复用。",
], 1):
    body(doc, f"（{i}）{s}", indent=False, space_after=4)

# ---------------- 附录
heading(doc, "附录：交付文件清单", 1)
table(
    doc, "表 A-1  实验提交文件说明",
    ["文件", "说明"],
    [
        ["文献计量学实验_遥感变化检测.ipynb", "主实验文件，含 43 个讲解单元与 34 个代码单元，已在本机完整验证运行通过"],
        ["实验报告_遥感变化检测.docx", "本报告"],
        ["WOS检索与导出_操作手册.md", "真实数据获取的图文操作指引"],
        ["README_使用说明.md", "环境启动与运行说明"],
        ["work/wos_demo.bib", "教学模拟数据集（BibTeX 格式）"],
        ["work/results_summary.json", "分析结果结构化导出，供报告生成使用"],
        ["figs/*.png", f"全部分析图表（共 {len(D.get('outputs', {}).get('figures', []))} 张）"],
    ],
    widths=[6.6, 9.0], font_size=9,
)

doc.save(OUT)
print(f"✅ 实验报告已生成 → {OUT}")
print(f"   文献数 {N}，图表 {len(D.get('outputs', {}).get('figures', []))} 张")
