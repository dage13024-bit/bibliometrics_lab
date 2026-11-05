#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_demo_bib.py
================
生成一份 **结构与字段完全仿照 Web of Science BibTeX 导出** 的示例数据集，
主题为 "Remote Sensing Change Detection (遥感变化检测)"，时间跨度 2015-2026。

⚠️ 重要声明：本文件生成的是【教学用模拟数据】，不是真实文献。
   它的唯一目的是让你在没有校园网 / 尚未导出 WOS 数据时，
   也能把 pyBibX 的 15 个步骤全部跑通、看懂每张图在讲什么。
   等你从 WOS 导出真实的 wos.bib 后，直接替换文件名即可，代码一行都不用改。

字段对照（pyBibX 解析 WOS 时真正需要的）：
    Author            作者，' and ' 分隔
    Title             标题
    Journal           期刊全名
    Volume / Pages / Year
    Abstract          摘要（词云、主题建模、语义聚类的原料）
    Affiliation       作者-机构-国家，多段之间用 '. ' 分隔（不是 ';'！）
    Times-Cited       被引次数
    DOI               用于识别"本地引用"（文献之间互相引用）
    Document-Type     Article / Review
    Language
    Keywords          作者关键词，';' 分隔
    Keywords-Plus     索引关键词，';' 分隔
    Cited-References  参考文献，';' 分隔，格式 '作者, 年份, 期刊, V卷, P页'
"""

import random
import re
from collections import Counter

random.seed(20261103)

N_DOCS_TARGET = 740

# ----------------------------------------------------------------------------
# 1. 时间分布：领域持续升温（2015 起步，2023-2025 爆发）
# ----------------------------------------------------------------------------
YEAR_COUNTS = {
    2015: 30, 2016: 34, 2017: 40, 2018: 50, 2019: 56,
    2020: 62, 2021: 70, 2022: 78, 2023: 84, 2024: 92,
    2025: 98, 2026: 36,
}

# ----------------------------------------------------------------------------
# 2. 期刊池（布拉德福核心区效应：前 3 种刊吃掉约 1/3 的论文）
# ----------------------------------------------------------------------------
JOURNALS = [
    ("REMOTE SENSING",                                     0.165),
    ("IEEE TRANSACTIONS ON GEOSCIENCE AND REMOTE SENSING", 0.105),
    ("REMOTE SENSING OF ENVIRONMENT",                      0.070),
    ("IEEE JOURNAL OF SELECTED TOPICS IN APPLIED EARTH OBSERVATIONS AND REMOTE SENSING", 0.090),
    ("ISPRS JOURNAL OF PHOTOGRAMMETRY AND REMOTE SENSING", 0.058),
    ("INTERNATIONAL JOURNAL OF REMOTE SENSING",            0.072),
    ("IEEE GEOSCIENCE AND REMOTE SENSING LETTERS",         0.080),
    ("INTERNATIONAL JOURNAL OF APPLIED EARTH OBSERVATION AND GEOINFORMATION", 0.058),
    ("REMOTE SENSING LETTERS",                             0.038),
    ("JOURNAL OF APPLIED REMOTE SENSING",                  0.038),
    ("GISCIENCE & REMOTE SENSING",                         0.030),
    ("INTERNATIONAL JOURNAL OF DIGITAL EARTH",             0.034),
    ("COMPUTERS & GEOSCIENCES",                            0.026),
    ("PHOTOGRAMMETRIC ENGINEERING AND REMOTE SENSING",     0.028),
    ("JOURNAL OF HYDROLOGY",                               0.028),
]
J_NAMES = [j for j, _ in JOURNALS]
J_WEIGHTS = [w for _, w in JOURNALS]

# 期刊代号（用于参考文献池里的缩写）
J_ABBR = {
    "REMOTE SENSING": "REMOTE SENS-BASEL",
    "IEEE TRANSACTIONS ON GEOSCIENCE AND REMOTE SENSING": "IEEE T GEOSCI REMOTE",
    "REMOTE SENSING OF ENVIRONMENT": "REMOTE SENS ENVIRON",
    "IEEE JOURNAL OF SELECTED TOPICS IN APPLIED EARTH OBSERVATIONS AND REMOTE SENSING": "IEEE J-STARS",
    "ISPRS JOURNAL OF PHOTOGRAMMETRY AND REMOTE SENSING": "ISPRS J PHOTOGRAMM",
    "INTERNATIONAL JOURNAL OF REMOTE SENSING": "INT J REMOTE SENS",
    "IEEE GEOSCIENCE AND REMOTE SENSING LETTERS": "IEEE GEOSCI REMOTE S",
    "INTERNATIONAL JOURNAL OF APPLIED EARTH OBSERVATION AND GEOINFORMATION": "INT J APPL EARTH OBS",
    "REMOTE SENSING LETTERS": "REMOTE SENS LETT",
    "JOURNAL OF APPLIED REMOTE SENSING": "J APPL REMOTE SENS",
    "GISCIENCE & REMOTE SENSING": "GISCI REMOTE SENS",
    "INTERNATIONAL JOURNAL OF DIGITAL EARTH": "INT J DIGIT EARTH",
    "COMPUTERS & GEOSCIENCES": "COMPUT GEOSCI-UK",
    "PHOTOGRAMMETRIC ENGINEERING AND REMOTE SENSING": "PHOTOGRAMM ENG REM S",
    "JOURNAL OF HYDROLOGY": "J HYDROL",
}

# ----------------------------------------------------------------------------
# 3. 机构池：名称, 国家（机构名必须含 Univ/Acad/Inst/Ctr/Lab 等关键词）
# ----------------------------------------------------------------------------
INSTITUTIONS = [
    ("Wuhan Univ, State Key Lab Informat Engn Surveying Mapping & Remote Sensing, Wuhan, Peoples R China", "China", 0.20),
    ("Wuhan Univ, Sch Remote Sensing & Informat Engn, Wuhan, Peoples R China", "China", 0.08),
    ("Chinese Acad Sci, Aerosp Informat Res Inst, Beijing, Peoples R China", "China", 0.13),
    ("Chinese Acad Sci, Inst Remote Sensing & Digital Earth, Beijing, Peoples R China", "China", 0.06),
    ("China Univ Geosci, Sch Geog & Informat Engn, Wuhan, Peoples R China", "China", 0.05),
    ("Natl Univ Def Technol, Coll Elect Sci & Technol, Changsha, Peoples R China", "China", 0.04),
    ("Sun Yat Sen Univ, Sch Geog & Planning, Guangzhou, Peoples R China", "China", 0.03),
    ("Beijing Normal Univ, Fac Geog Sci, Beijing, Peoples R China", "China", 0.03),
    ("Peking Univ, Inst Remote Sensing & GIS, Beijing, Peoples R China", "China", 0.03),
    ("Tsinghua Univ, Dept Earth Syst Sci, Beijing, Peoples R China", "China", 0.03),
    ("Zhejiang Univ, Sch Earth Sci, Hangzhou, Peoples R China", "China", 0.02),
    ("Tongji Univ, Coll Surveying & Geoinformat, Shanghai, Peoples R China", "China", 0.02),
    ("Hong Kong Polytech Univ, Dept Land Surveying & Geoinformat, Hong Kong, Peoples R China", "Hong Kong", 0.04),
    ("Univ Trento, Dept Informat Engn & Comp Sci, Trento, Italy", "Italy", 0.045),
    ("Fdn Bruno Kessler, Remote Sensing Unit, Trento, Italy", "Italy", 0.02),
    ("Univ Pavia, Dept Elect Comp & Biomed Engn, Pavia, Italy", "Italy", 0.015),
    ("German Aerosp Ctr, Remote Sensing Technol Inst, Wessling, Germany", "Germany", 0.05),
    ("Tech Univ Munich, Dept Aerosp & Geodesy, Munich, Germany", "Germany", 0.03),
    ("Helmholtz Zentrum Dresden Rossendorf, Dept Explorat Technol, Freiberg, Germany", "Germany", 0.015),
    ("KTH Royal Inst Technol, Dept Urban Planning & Environm, Stockholm, Sweden", "Sweden", 0.025),
    ("Univ Twente, Fac Geoinformat Sci & Earth Observat, Enschede, Netherlands", "Netherlands", 0.03),
    ("Wageningen Univ, Lab Geoinformat Sci & Remote Sensing, Wageningen, Netherlands", "Netherlands", 0.02),
    ("Swiss Fed Inst Technol, Lab Geoinformat, Zurich, Switzerland", "Switzerland", 0.02),
    ("Ecole Polytech Fed Lausanne, Inst Civil Engn, Lausanne, Switzerland", "Switzerland", 0.012),
    ("Univ Maryland, Dept Geog Sci, College Pk, MD USA", "USA", 0.025),
    ("Boston Univ, Dept Earth & Environm, Boston, MA USA", "USA", 0.015),
    ("DigitalGlobe Inc, Westminster, CO USA", "USA", 0.012),
    ("Univ Calif Berkeley, Dept Environm Sci Policy & Management, Berkeley, CA USA", "USA", 0.012),
    ("Canadian Forest Serv, Pacific Forestry Ctr, Victoria, BC, Canada", "Canada", 0.02),
    ("Univ Quebec, Inst Natl Rech Sci, Quebec, PQ, Canada", "Canada", 0.012),
    ("Univ Tokyo, Inst Ind Sci, Tokyo, Japan", "Japan", 0.02),
    ("RIKEN, Ctr Adv Intelligence Project, Tokyo, Japan", "Japan", 0.012),
    ("Seoul Natl Univ, Dept Civil & Environm Engn, Seoul, South Korea", "South Korea", 0.02),
    ("Korea Adv Inst Sci & Technol, Dept Civil & Environm Engn, Daejeon, South Korea", "South Korea", 0.012),
    ("Indian Inst Technol, Dept Civil Engn, Mumbai, India", "India", 0.018),
    ("Indian Inst Remote Sensing, Dehra Dun, India", "India", 0.012),
    ("Univ Iceland, Fac Elect & Comp Engn, Reykjavik, Iceland", "Iceland", 0.018),
    ("Univ Grenoble Alpes, Gipsa Lab, Grenoble, France", "France", 0.018),
    ("Ctr Etud Spatiales Biosphere, Toulouse, France", "France", 0.012),
    ("Univ Extremadura, Dept Technol Comp & Commun, Caceres, Spain", "Spain", 0.012),
    ("Univ Valencia, Image Proc Lab, Valencia, Spain", "Spain", 0.012),
    ("Univ Tehran, Fac Geog, Tehran, Iran", "Iran", 0.015),
    ("Middle East Tech Univ, Dept Geomat Engn, Ankara, Turkey", "Turkey", 0.012),
    ("Univ Fed Rio de Janeiro, Dept Geog, Rio De Janeiro, Brazil", "Brazil", 0.012),
    ("Nanyang Technol Univ, Sch Elect & Elect Engn, Singapore, Singapore", "Singapore", 0.012),
    ("Univ Technol Malaysia, Fac Geoinformat & Real Estate, Johor Bahru, Malaysia", "Malaysia", 0.01),
    ("Chinese Univ Hong Kong, Inst Space & Earth Informat Sci, Hong Kong, Peoples R China", "Hong Kong", 0.012),
]
INST_NAMES = [i for i, _, _ in INSTITUTIONS]
INST_COUNTRY = {i: c for i, c, _ in INSTITUTIONS}
INST_WEIGHTS = [w for _, _, w in INSTITUTIONS]

# ----------------------------------------------------------------------------
# 4. 核心学者（决定 H-index 排行、核心作者合作网络、桑基图）
# ----------------------------------------------------------------------------
CORE_AUTHORS = [
    # (姓名, 机构索引, 主导时间段起, 主导时间段止)
    ("Zhang, Yong",        0, 2015, 2026),   # 高被引"睡美人"制造者
    ("Li, Deren",          0, 2015, 2020),
    ("Zhang, Liangpei",    0, 2015, 2024),
    ("Huang, Xin",         1, 2016, 2026),
    ("Deng, Jing",         0, 2015, 2023),
    ("Gong, Jianya",       0, 2015, 2021),
    ("Yang, Bisheng",      0, 2016, 2022),
    ("Chen, Jing",         2, 2015, 2026),
    ("Wang, Lei",          3, 2016, 2026),
    ("Liu, Xiaoping",      6, 2017, 2026),
    ("Du, Peijun",         4, 2017, 2026),
    ("Shi, Wenzhong",     12, 2015, 2026),
    ("Zhu, Xiaoxiang",    16, 2016, 2026),   # 德国 DLR
    ("Bruzzone, Lorenzo", 13, 2015, 2026),
    ("Bovolo, Francesca", 14, 2015, 2024),
    ("Gamba, Paolo",      15, 2015, 2022),
    ("Reinartz, Peter",   16, 2015, 2023),
    ("Schmitt, Michael",  17, 2017, 2026),
    ("Datcu, Mihai",      16, 2015, 2022),
    ("Ban, Yifang",       19, 2015, 2026),
    ("Persello, Claudio", 20, 2017, 2026),
    ("Yokoya, Naoto",     31, 2018, 2026),
    ("Hong, Danfeng",     17, 2018, 2026),
    ("Chanussot, Jocelyn",37, 2015, 2023),
    ("Tuia, Devis",       21, 2016, 2024),
    ("Ghamisi, Pedram",   18, 2017, 2024),
    ("Woodcock, Curtis",  25, 2015, 2023),
    ("Zhu, Zhe",          24, 2015, 2022),
    ("Wulder, Michael",   28, 2015, 2023),
    ("Wuhan, Tang",       10, 2019, 2026),
]
# 兼容：给个别名字取个更好记的中文团队标签（仅注释用，不写进 bib）
CORE_AUTHORS = [a for a in CORE_AUTHORS if a[0] != "Wuhan, Tang"]

# 常见姓氏 + 名首字母，用来"批量生产"普通作者（每人 1-3 篇）
SURNAMES = [
    "Wang", "Li", "Zhang", "Liu", "Chen", "Yang", "Zhao", "Huang", "Zhou", "Wu",
    "Xu", "Sun", "Ma", "Hu", "Guo", "He", "Lin", "Deng", "Cao", "Peng",
    "Tang", "Jiang", "Feng", "Shen", "Han", "Xiao", "Cheng", "Yuan", "Pan", "Dong",
    "Smith", "Kumar", "Kim", "Park", "Sato", "Rossi", "Muller", "Garcia", "Silva", "Nguyen",
]
GIVEN = [
    "Wei", "Jian", "Hao", "Qiang", "Yun", "Ming", "Feng", "Tao", "Lei", "Bo",
    "Xin", "Yu", "Kai", "Ning", "Chao", "Rui", "Peng", "Jun", "Zhen", "Yan",
    "Anna", "Marco", "Luca", "Elena", "David", "Sarah", "Mohamed", "Ravi", "Hiroshi", "Jin",
]
FILLER_AUTHORS = []
_used = set()
for sn in SURNAMES:
    for gv in GIVEN:
        name = f"{sn}, {gv}"
        if name in _used:
            continue
        _used.add(name)
        FILLER_AUTHORS.append(name)
random.shuffle(FILLER_AUTHORS)
FILLER_AUTHORS = FILLER_AUTHORS[:420]

# ----------------------------------------------------------------------------
# 5. 关键词池：按年代分档，制造"技术范式迁移"的演化曲线
# ----------------------------------------------------------------------------
KW_EARLY = [  # 2015-2017 传统机器学习 / 像元级方法
    "change detection", "remote sensing", "landsat", "sentinel-2", "multispectral imagery",
    "object-based image analysis", "support vector machine", "random forest",
    "post-classification comparison", "change vector analysis", "principal component analysis",
    "spectral mixture analysis", "image differencing", "markov random field",
    "land cover change", "urban expansion", "vegetation index", "ndvi", "texture analysis",
    "image segmentation", "supervised classification", "thresholding", "bitemporal images",
]
KW_MID = [  # 2018-2020 深度学习登场
    "deep learning", "convolutional neural network", "cnn", "u-net", "siamese network",
    "fully convolutional network", "transfer learning", "feature fusion", "attention mechanism",
    "very high resolution", "high resolution imagery", "unmanned aerial vehicle", "uav",
    "sentinel-1", "sar imagery", "time series analysis", "google earth engine",
    "building extraction", "damage assessment", "hyperspectral image", "semantic segmentation",
    "conditional random field", "sparse representation", "multi-scale features",
]
KW_LATE = [  # 2021-2023 Transformer / 自监督
    "transformer", "self-attention", "vision transformer", "contrastive learning",
    "self-supervised learning", "domain adaptation", "few-shot learning",
    "semi-supervised learning", "bitemporal", "change captioning", "foundation model",
    "pretraining", "building change detection", "semantic change detection",
    "weakly supervised learning", "uncertainty analysis", "explainable ai", "insar",
    "digital elevation model", "graph neural network", "knowledge distillation",
]
KW_NEW = [  # 2024-2026 基础模型 / 多模态
    "foundation model", "segment anything model", "sam", "prompt learning",
    "large language model", "multimodal large language model", "remote sensing large model",
    "mamba", "state space model", "diffusion model", "zero-shot learning",
    "open vocabulary", "cross-modal retrieval", "vision-language model",
    "continual learning", "3d change detection", "sar-optical fusion", "multi-temporal",
    "parameter efficient fine tuning", "edge computing", "tiny model",
]
TASKS = [
    "building change detection", "urban change detection", "land cover change detection",
    "cropland change detection", "informal settlement mapping", "earthquake damage assessment",
    "coastline change detection", "forest disturbance detection", "water body change detection",
    "road network change detection", "land use change mapping", "mining area monitoring",
    "wetland change detection", "glacier change monitoring", "flood mapping",
    "post-disaster damage assessment", "urban sprawl monitoring", "change detection",
]
DATASETS = [
    "Sentinel-2 imagery", "Landsat-8 OLI imagery", "Sentinel-1 SAR data",
    "very high resolution satellite images", "UAV aerial imagery", "hyperspectral images",
    "Gaofen-2 imagery", "PlanetScope imagery", "multitemporal SAR imagery",
    "aerial photographs", "ZY-3 stereo imagery", "WorldView-3 imagery",
]
METHOD_TMPL = {
    "early": ["object-based image analysis", "support vector machine classifier",
              "random forest classifier", "post-classification comparison",
              "change vector analysis", "spectral mixture analysis",
              "markov random field model", "unsupervised clustering framework"],
    "mid": ["convolutional neural network", "U-Net architecture", "siamese neural network",
            "fully convolutional network", "transfer learning strategy",
            "attention-based network", "generative adversarial network",
            "deep belief network"],
    "late": ["transformer network", "vision transformer", "self-supervised contrastive framework",
             "multi-scale feature fusion network", "domain adaptation framework",
             "graph neural network", "bitemporal attention network",
             "semi-supervised learning framework"],
    "new": ["foundation model", "segment anything model", "vision-language model",
            "mamba state space network", "diffusion model", "prompt learning framework",
            "large remote sensing model", "zero-shot transfer framework"],
}

# ----------------------------------------------------------------------------
# 6. 参考文献池（真实存在的领域经典 + 高被引方法论文）
#    每条: (作者串, 年份, 期刊缩写, 卷, 页, 被引权重)
# ----------------------------------------------------------------------------
REFS = [
    ("Singh A", 1989, "INT J REMOTE SENS", "10", "989", 6.0),
    ("Bruzzone L", 2000, "IEEE T GEOSCI REMOTE", "38", "1171", 7.0),
    ("Coppin P", 2004, "REMOTE SENS ENVIRON", "39", "1", 8.0),
    ("Lu D", 2004, "INT J REMOTE SENS", "25", "2365", 8.0),
    ("Bovolo F", 2007, "IEEE T GEOSCI REMOTE", "45", "1248", 4.5),
    ("Chen G", 2012, "REMOTE SENS ENVIRON", "124", "382", 5.5),
    ("Hussain M", 2013, "REMOTE SENS ENVIRON", "130", "197", 5.5),
    ("Ronneberger O", 2015, "LECT NOTES COMPUT SC", "9351", "234", 9.0),
    ("Szegedy C", 2015, "PROC CVPR", "0", "1", 5.0),
    ("He K", 2016, "PROC CVPR", "0", "770", 8.0),
    ("Vaswani A", 2017, "ADV NEUR INF PROC", "30", "5998", 10.0),
    ("Zhu XX", 2017, "IEEE GEOSCI REMOTE M", "5", "58", 7.0),
    ("Chen LC", 2018, "IEEE T PATTERN ANAL", "40", "834", 6.5),
    ("Daudt RC", 2018, "PROC INT CONF 3D VIS", "0", "1", 5.0),
    ("Zhang Z", 2016, "IEEE T GEOSCI REMOTE", "54", "4801", 5.5),
    ("Longbotham N", 2012, "IEEE T GEOSCI REMOTE", "50", "4239", 3.5),
    ("Huang X", 2014, "IEEE T GEOSCI REMOTE", "52", "5572", 4.0),
    ("Wulder MA", 2016, "REMOTE SENS ENVIRON", "185", "271", 4.5),
    ("Woodcock CE", 2008, "REMOTE SENS ENVIRON", "112", "1839", 6.0),
    ("Zhu Z", 2014, "REMOTE SENS ENVIRON", "144", "152", 7.5),
    ("Chen H", 2020, "REMOTE SENS ENVIRON", "242", "111758", 6.0),
    ("Chen K", 2021, "IEEE T GEOSCI REMOTE", "59", "1", 4.5),
    ("Bandara WGC", 2022, "IEEE T GEOSCI REMOTE", "60", "1", 4.0),
    ("Bai T", 2021, "ISPRS J PHOTOGRAMM", "178", "231", 4.0),
    ("Shi W", 2020, "ISPRS J PHOTOGRAMM", "161", "214", 4.5),
    ("Kirillov A", 2023, "PROC CVPR", "0", "1", 5.5),
    ("Radford A", 2021, "PROC ICML", "0", "8748", 6.0),
    ("Krizhevsky A", 2012, "ADV NEUR INF PROC", "25", "1097", 6.5),
    ("Zhang Y", 2019, "IEEE T GEOSCI REMOTE", "57", "7821", 4.0),
    ("Zhao J", 2019, "IEEE J-STARS", "12", "4056", 3.0),
    ("Liang Y", 2019, "REMOTE SENS-BASEL", "11", "1444", 2.5),
    ("Tan K", 2016, "INT J REMOTE SENS", "37", "3275", 2.0),
    ("Gamba P", 2011, "PROC GRSS", "0", "1", 2.5),
    ("Benediktsson JA", 2013, "PROC IEEE", "101", "583", 3.0),
    ("Plaza A", 2011, "REMOTE SENS ENVIRON", "115", "1843", 3.5),
    ("Chanussot J", 2006, "IEEE T GEOSCI REMOTE", "44", "1", 2.0),
    ("Inglada J", 2015, "IEEE T GEOSCI REMOTE", "53", "4653", 3.5),
    ("Gong P", 2020, "REMOTE SENS ENVIRON", "239", "111621", 5.0),
    ("Wang L", 2018, "REMOTE SENS ENVIRON", "216", "14", 3.5),
    ("Liu Y", 2018, "ISPRS J PHOTOGRAMM", "144", "1", 3.0),
    ("Zhang C", 2018, "IEEE T GEOSCI REMOTE", "56", "1", 2.5),
    ("Minh V", 2019, "REMOTE SENS-BASEL", "11", "1", 2.0),
    ("Peng D", 2019, "IEEE J-STARS", "12", "1", 2.0),
    ("Li J", 2019, "IEEE T GEOSCI REMOTE", "57", "1", 2.5),
    ("Boulila W", 2019, "REMOTE SENS-BASEL", "11", "1", 1.5),
    ("Zhang L", 2019, "IEEE GEOSCI REMOTE M", "7", "1", 2.0),
    ("Mou L", 2018, "IEEE T GEOSCI REMOTE", "56", "2123", 3.5),
    ("Farabet C", 2013, "IEEE T PATTERN ANAL", "35", "1915", 3.0),
    ("Kwan C", 2018, "J APPL REMOTE SENS", "12", "1", 2.0),
    ("Tuia D", 2016, "IEEE T GEOSCI REMOTE", "54", "1", 2.5),
    ("Persello C", 2017, "REMOTE SENS ENVIRON", "198", "170", 2.5),
    ("Wegner JD", 2018, "REMOTE SENS ENVIRON", "204", "80", 2.0),
    ("Maggiori E", 2017, "IEEE T GEOSCI REMOTE", "55", "3141", 3.5),
    ("Ghosh S", 2018, "IEEE T GEOSCI REMOTE", "56", "1", 2.0),
    ("Valdivia C", 2021, "REMOTE SENS ENVIRON", "0", "1", 2.0),
    ("Gong J", 2020, "IEEE T GEOSCI REMOTE", "58", "1", 2.5),
    ("Chen Y", 2020, "REMOTE SENS-BASEL", "12", "1", 2.0),
    ("Wei S", 2021, "REMOTE SENS-BASEL", "13", "1", 2.0),
    ("Zhang X", 2021, "ISPRS J PHOTOGRAMM", "180", "1", 2.0),
    ("Wang H", 2021, "IEEE T GEOSCI REMOTE", "59", "1", 2.0),
    ("Zhu H", 2021, "IEEE J-STARS", "14", "1", 1.8),
    ("Fang S", 2021, "IEEE T GEOSCI REMOTE", "59", "1", 1.8),
    ("Huang J", 2022, "REMOTE SENS-BASEL", "14", "1", 1.8),
    ("Lin Y", 2022, "IEEE GEOSCI REMOTE S", "19", "1", 1.5),
    ("Sun X", 2022, "ISPRS J PHOTOGRAMM", "190", "1", 1.8),
    ("Chen Z", 2022, "IEEE T GEOSCI REMOTE", "60", "1", 1.8),
    ("Li Z", 2023, "IEEE T GEOSCI REMOTE", "61", "1", 1.5),
    ("Zhou W", 2023, "REMOTE SENS ENVIRON", "284", "1", 1.8),
    ("Ma X", 2023, "ISPRS J PHOTOGRAMM", "200", "1", 1.5),
    ("Xu Y", 2024, "IEEE T GEOSCI REMOTE", "62", "1", 1.2),
    ("Yang K", 2024, "REMOTE SENS-BASEL", "16", "1", 1.2),
    ("Guo Q", 2024, "ISPRS J PHOTOGRAMM", "210", "1", 1.2),
    ("Ding L", 2024, "IEEE J-STARS", "17", "1", 1.0),
    ("Han P", 2025, "REMOTE SENS-BASEL", "17", "1", 1.0),
    ("Zhao Y", 2025, "IEEE T GEOSCI REMOTE", "63", "1", 1.0),
]

# ----------------------------------------------------------------------------
# 7. 生成文档
# ----------------------------------------------------------------------------
docs = []


def era_of(year):
    if year <= 2017:
        return "early"
    if year <= 2020:
        return "mid"
    if year <= 2023:
        return "late"
    return "new"


def pick_journal():
    return random.choices(J_NAMES, weights=J_WEIGHTS, k=1)[0]


def make_authors(year):
    """返回 [(姓名, 机构名, 国家), ...]"""
    era = era_of(year)
    n_core = random.choices([0, 1, 2, 3], weights=[0.28, 0.44, 0.22, 0.06], k=1)[0]
    active = [a for a in CORE_AUTHORS if a[2] <= year <= a[3]]
    cores = random.sample(active, min(n_core, len(active))) if active else []
    n_filler = random.choices([1, 2, 3, 4, 5], weights=[0.18, 0.30, 0.28, 0.16, 0.08], k=1)[0]
    fillers = random.sample(FILLER_AUTHORS, n_filler)

    people = []
    for name, idx, _, _ in cores:
        inst = INST_NAMES[idx]
        people.append((name, inst, INST_COUNTRY[inst]))
    for name in fillers:
        inst = random.choices(INST_NAMES, weights=INST_WEIGHTS, k=1)[0]
        people.append((name, inst, INST_COUNTRY[inst]))

    # 同一作者在同一篇里不能重复，且顺序随机
    seen, ordered = set(), []
    for p in people:
        if p[0] in seen:
            continue
        seen.add(p[0])
        ordered.append(p)
    random.shuffle(ordered)
    return ordered, era


def make_title(era, task, dataset):
    method = random.choice(METHOD_TMPL[era])
    patterns = [
        f"A {method} for {task} using {dataset}",
        f"{method.capitalize()} for {task} in {dataset}",
        f"Automatic {task} with {method} and {dataset}",
        f"Towards robust {task}: a {method} approach on {dataset}",
        f"Comparing {method} and baseline models for {task}",
        f"Multi-temporal {task} via {method}",
        f"An improved {method} for {task} from {dataset}",
        f"{task.capitalize()} under limited labels: a {method} perspective",
    ]
    title = random.choice(patterns)
    title = title[0].upper() + title[1:]
    return title.replace("{", "").replace("}", "").replace("=", " ")


def make_abstract(year, era, task, dataset):
    method = random.choice(METHOD_TMPL[era])
    acc = round(random.uniform(86.0, 97.5), 1)
    f1 = round(min(acc + random.uniform(-3, 2), 98.0), 1)
    koa = round(random.uniform(72.0, 92.0), 1)
    s1 = (f"{task.capitalize()} plays a critical role in environmental monitoring and urban management, "
          f"yet it remains challenging due to seasonal variations, registration errors and heterogeneous land surfaces.")
    s2 = (f"In this study, we propose a {method} that exploits {dataset} to detect changed regions at multiple time steps.")
    s3 = (f"The proposed framework integrates multi-scale feature fusion, hard negative mining and a lightweight "
          f"post-processing module to suppress false alarms caused by illumination and phenology differences.")
    s4 = (f"Experiments were conducted on three public benchmarks and one newly collected dataset covering urban, "
          f"agricultural and coastal scenes.")
    s5 = (f"Results show that the proposed method achieves an overall accuracy of {acc} percent, an F1 score of {f1} percent "
          f"and a kappa coefficient of {koa} percent, outperforming several state of the art baselines while keeping the "
          f"inference cost acceptable for large area mapping.")
    s6 = (f"Ablation studies further confirm that the {era} design choices, including attention based aggregation and "
          f"self-supervised pretraining, are essential for robust transfer across sensors and regions.")
    parts = [s1, s2, s3, s4, s5]
    if random.random() < 0.55:
        parts.append(s6)
    random.shuffle(parts[2:4])  # 轻微打乱句子顺序，增加文本多样性
    return " ".join(parts).replace("{", "").replace("}", "").replace("=", " ")


def make_keywords(year, era, task):
    pools = {
        "early": KW_EARLY,
        "mid": KW_MID + KW_EARLY[:6],
        "late": KW_LATE + KW_MID[:6],
        "new": KW_NEW + KW_LATE[:6],
    }
    kws = {task, "change detection", "remote sensing"}
    kws |= set(random.sample(pools[era], k=random.randint(3, 5)))
    kws.discard("")
    return sorted(kws)[:7]


def make_kwplus(year, era):
    """索引关键词（WOS 里是大写、带连字符的受控词表）"""
    pool = {
        "early": ["LAND-COVER CHANGE", "OBJECT-BASED APPROACH", "SUPPORT VECTOR MACHINE",
                  "MULTI-TEMPORAL IMAGES", "SPECTRAL MIXTURE ANALYSIS", "LAND-USE CHANGE",
                  "URBAN-GROWTH", "CLASSIFICATION", "SATELLITE IMAGERY", "SPATIAL-RESOLUTION"],
        "mid": ["CONVOLUTIONAL NEURAL-NETWORKS", "DEEP-LEARNING", "SEMANTIC SEGMENTATION",
                "TRANSFER-LEARNING", "FEATURE-FUSION", "TIME-SERIES", "U-NET",
                "HIGH-RESOLUTION IMAGERY", "BUILDING EXTRACTION", "ATTENTION MECHANISM"],
        "late": ["TRANSFORMER", "SELF-ATTENTION", "DOMAIN ADAPTATION", "CONTRASTIVE LEARNING",
                 "WEAKLY SUPERVISED", "BITEMPORAL IMAGES", "FOUNDATION MODELS",
                 "MULTI-SCALE FEATURES", "SEMANTIC CHANGE DETECTION", "UNCERTAINTY"],
        "new": ["FOUNDATION MODEL", "SEGMENT ANYTHING MODEL", "PROMPT LEARNING",
                "VISION-LANGUAGE MODEL", "ZERO-SHOT", "MULTIMODAL LEARNING",
                "LARGE LANGUAGE MODELS", "STATE-SPACE MODEL", "MULTI-TEMPORAL ANALYSIS",
                "CROSS-MODAL FUSION"],
    }[era]
    return sorted(set(random.sample(pool, k=random.randint(5, 8))))


def make_refs(year, doi, title, era):
    """构造 Cited-References：池中经典 + 一条可被识别的自引（带 DOI）"""
    n = random.randint(14, 28)
    pool = [r for r in REFS if r[1] <= year]
    chosen = []
    weights = [r[5] for r in pool]
    picked_idx = set()
    while len(chosen) < min(n, len(pool)):
        i = random.choices(range(len(pool)), weights=weights, k=1)[0]
        if i in picked_idx:
            continue
        picked_idx.add(i)
        chosen.append(pool[i])
    lines = [f"{a}, {y}, {j}, V{v}, P{p}" for a, y, j, v, p, _w in chosen]
    # 少量文献引用"本数据集内"的其他文献（带 DOI），构建本地引文网络
    if random.random() < 0.30:
        first = docs[random.randrange(max(1, len(docs)))] if docs else None
        if first and first["year"] < year:
            a = first["authors"][0][0]
            j = J_ABBR[first["journal"]]
            lines.append(f"{a}, {first['year']}, {j}, V{random.randint(1, 60)}, P{random.randint(1, 999)}, DOI {first['doi']}")
    return "; ".join(lines)


# 先按年份展开，再用"逐年生成"保证跨年引用只指向更早的文献
for year in sorted(YEAR_COUNTS):
    for _ in range(YEAR_COUNTS[year]):
        era = era_of(year)
        journal = pick_journal()
        task = random.choice(TASKS)
        dataset = random.choice(DATASETS)
        people, era = make_authors(year)
        if not people:
            continue
        idx = len(docs) + 1
        doi = f"10.1016/j.rse.{year}.{100000 + idx}"
        title = make_title(era, task, dataset)
        abstract = make_abstract(year, era, task, dataset)
        refs = make_refs(year, doi, title, era)
        docs.append({
            "id": idx,
            "authors": people,
            "title": title,
            "journal": journal,
            "volume": random.randint(1, 320),
            "issue": random.randint(1, 24) if random.random() < 0.5 else None,
            "pages": f"{random.randint(1, 900)}-{random.randint(901, 1200)}" if random.random() < 0.5 else str(random.randint(1000, 99999)),
            "year": year,
            "abstract": abstract,
            "doi": doi,
            "citations": max(0, int(round(random.expovariate(1 / max(2.0, 4.0 + 2.6 * (2026 - year))) * random.uniform(0.4, 1.9)))),
            "doc_type": random.choices(["Article", "Review", "Proceedings Paper"], weights=[0.86, 0.09, 0.05], k=1)[0],
            "keywords": make_keywords(year, era, task),
            "kwplus": make_kwplus(year, era),
            "refs": refs,
            "language": "English",
        })

# ----------------------------------------------------------------------------
# 8. 写出 WOS 风格 BibTeX
# ----------------------------------------------------------------------------
CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def sanitize(text):
    text = str(text).replace("{", "(").replace("}", ")")
    text = text.replace("=", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def affiliation_field(people):
    """WOS 风格：多段用 '. ' 分隔（pyBibX 会把 '.' 还原成 ';'），段内不能出现句点。"""
    segs = []
    for i, (name, inst, country) in enumerate(people):
        # 形如 "Zhang, Yong (Zhang, Yong)[1], Wuhan Univ, ..., Peoples R China"
        segs.append(f"{name} ({name})[{i + 1}], {inst}")
    return ". ".join(segs)


def wos_entry(d):
    L = []
    L.append(f"@article{{WOS:{d['year']}{d['id']:09d},")
    L.append("Author = {" + " and ".join(p[0] for p in d["authors"]) + "},")
    L.append("Title = {" + sanitize(d["title"]) + "},")
    L.append("Journal = {" + d["journal"] + "},")
    L.append(f"Volume = {{{d['volume']}}},")
    if d["issue"]:
        L.append(f"Issue = {{{d['issue']}}},")
    L.append(f"Pages = {{{d['pages']}}},")
    L.append(f"Year = {{{d['year']}}},")
    L.append("Abstract = {" + sanitize(d["abstract"]) + "},")
    L.append("Affiliation = {" + affiliation_field(d["authors"]) + "},")
    L.append(f"Times-Cited = {{{d['citations']}}},")
    L.append(f"DOI = {{{d['doi']}}},")
    L.append("Language = {English},")
    L.append(f"Document-Type = {{{d['doc_type']}}},")
    L.append("Research-Areas = {Environmental Sciences & Ecology; Remote Sensing},")
    L.append("Web-of-Science-Categories = {Environmental Sciences; Remote Sensing},")
    L.append("Keywords = {" + "; ".join(d["keywords"]) + "},")
    L.append("Keywords-Plus = {" + "; ".join(d["kwplus"]) + "},")
    L.append("Cited-References = {" + d["refs"] + "},")
    L.append("}")
    return "\n".join(L)


out = "wos_demo.bib"
with open(out, "w", encoding="utf-8") as f:
    for d in docs:
        f.write(wos_entry(d) + "\n\n")

print(f"✅ 已生成 {out}")
print(f"   文献数: {len(docs)}")
print(f"   年份:   {min(d['year'] for d in docs)} - {max(d['year'] for d in docs)}")
print(f"   作者数: {len({p[0] for d in docs for p in d['authors']})}")
print(f"   期刊数: {len({d['journal'] for d in docs})}")
print(f"   国家数: {len({p[2] for d in docs for p in d['authors']})}")
print("   前 5 大期刊:")
for j, c in Counter(d["journal"] for d in docs).most_common(5):
    print(f"     {c:4d}  {j}")
