# Psy 文献追踪周报

一个面向心理学、数字健康与心理生理研究的自动化文献追踪工具。它从 PubMed 和 Crossref 收集候选论文，经过本地规则预筛与 DeepSeek 语义筛选后，生成可直接阅读和分享的中文文献 Newsletter。

## 主要功能

本工具每周追踪以下三条研究主线：

1. **心脑轴**：覆盖心脑交互/耦合、迷走神经、自主神经系统、HRV、RSA、HEP、神经内脏整合等；其中 HRV、迷走神经和自主神经系统相关研究必须具有心理、行为或心理健康语境才会被纳入。
2. **生态瞬时干预**：覆盖 EMA/ESM、密集纵向测量、EMI、JITAI、MRT、数字表型、被动感知与实时个体化干预。
3. **心理微干预**：覆盖以心理、情绪、行为、主观体验或心理生理为结局的微干预、简短干预、数字/移动自助干预与身心干预。

每周一北京时间 12:00，GitHub Actions 自动检索上一个完整自然周的 PubMed 与 Crossref 文献。候选文献依次经过：

1. 基于 2026 年 JCR 数据的期刊分区过滤：排除未列入例外名单的 Q3/Q4 期刊；
2. 本地关键词和心理学语境预筛；
3. DeepSeek 相关性判断、中文标题与摘要解读、关键词提取及主题标注。

最终报告固定使用三个标准标签：`心脑轴`、`生态瞬时干预`、`心理微干预`。每篇入选论文包含中文标题、中文摘要、关键词、作者、期刊、IF、JCR 分区、发表时间和原文链接；跨主线或高优先级论文会进入“重点推荐”板块。

周报以 Markdown 和 HTML 两种格式保存于 `newsletters/`，便于在 GitHub 中阅读、下载或分享。

## 数据分析

每次成功生成周报时，工具会同时生成无需额外模型调用的数据分析内容：

- **关键词云图**：根据入选论文的 DeepSeek 关键词展示本周高频研究主题；
- **三主线趋势图**：以三条折线显示各主线每周的收录数量变化；
- **热门主题**：列出本周出现频次最高的主题词；
- **统计报告**：在 Newsletter 末尾展示唯一论文数、三条主线数量和相对上一统计周的变化。

图表按周独立存放在 `newsletters/assets/`，不会被后来周报覆盖。周度历史指标保存在 `analytics/weekly_metrics.json`；重跑同一周时只替换该周记录，不会重复累计。由于交叉研究可带有多个主题标签，三条主线的总数可能高于当周唯一论文数。

## 运行方式

### 自动运行

完成配置后，`Download tracker metadata` 工作流会在每周一北京时间 12:00 自动运行。元数据下载成功后，`Generate three-track Newsletter` 工作流会自动调用 DeepSeek 并提交新的周报、图表和统计数据。

### 手动重跑指定日期范围

1. 打开仓库的 **Actions** 页面；
2. 选择 **Download tracker metadata**；
3. 点击 **Run workflow**；
4. 填写 `start_date` 和 `end_date`，格式为 `YYYY-MM-DD`；
5. 下载工作流成功后，报告工作流会自动接续执行。

例如，重跑 2026-08-24 至 2026-08-30 时填写：

```text
start_date: 2026-08-24
end_date:   2026-08-30
```

### 本地运行

```bash
python -m pip install -r requirements.txt
python Paper_metadata_download.py --start-date 2026-08-24 --end-date 2026-08-30
python Psy-day-paper-deepseek.py --start-date 2026-08-24 --end-date 2026-08-30
```

本地运行前同样需要设置下文所列的环境变量。第二条命令会调用 DeepSeek，因此会消耗相应额度。

## 项目结构

```text
.
├── .github/workflows/
│   ├── Paper_metadata_download.yaml      # 每周下载与本地预筛工作流
│   └── Psy-day-paper-deepseek.yaml       # DeepSeek、Newsletter 与分析工作流
├── Paper_metadata_download.py            # PubMed/Crossref 获取、JCR 分区过滤与本地预筛
├── Psy-day-paper-deepseek.py              # DeepSeek 语义筛选与中文解读
├── domain_config.py                       # 三条主线关键词、别名与心理学语境规则
├── journal_registry.py                    # 期刊 ISSN、IF、JCR 分区与 Q3/Q4 例外名单
├── data/jcr_2026_journals.csv             # 2026 年 JCR 期刊分区与 IF 索引
├── newsletter.py                          # Markdown/HTML Newsletter 生成
├── analytics.py                           # 词云、趋势图、热门主题和周度指标生成
├── requirements.txt                       # Python 依赖
├── tests/                                 # 筛选、标签、Newsletter 与分析功能测试
├── newsletters/                           # 已发布的 Markdown/HTML 周报
│   └── assets/                            # 每周词云和趋势图（首次成功运行后生成）
├── analytics/                             # 周度统计历史（首次成功运行后生成）
├── Paper_metadata_download/               # 历史保留的原始候选数据
└── Psy-day-paper-deepseek/                # 历史保留的 DeepSeek 清洗数据
```

常规自动运行会通过 GitHub Actions Artifact 在两个工作流间临时传递候选元数据，保留一天；新的原始候选数据和中间筛选文件不会自动提交到仓库。

## 安装与配置

### Python 依赖

本地运行时安装：

```bash
python -m pip install -r requirements.txt
```

其中数据分析功能依赖 `matplotlib`、`wordcloud`、`Pillow` 和 `jieba`。GitHub Actions 会自动安装中文字体，以确保词云和趋势图可正确显示中文。

### GitHub Secrets 与变量

在仓库中打开 **Settings → Secrets and variables → Actions**，配置以下内容：

| 类型 | 名称 | 用途 |
| --- | --- | --- |
| Secret | `DEEPSEEK_API_KEY` | DeepSeek 语义筛选、中文解读与关键词生成 |
| Secret | `NCBI_API_KEY` | 提高 PubMed/NCBI 请求配额 |
| Secret | `NCBI_EMAIL` | PubMed/NCBI 请求联系邮箱 |
| Variable | `CROSSREF_MAILTO` | Crossref 请求联系邮箱 |

不要把 API Key 直接写入代码或提交到仓库。Fork 后请在自己的仓库中重新配置这些值。

## 期刊与关键词维护

- 修改三条主线的关键词、心理学语境规则或主题标签别名：编辑 `domain_config.py`；
- 修改 Q3/Q4 例外期刊、ISSN 匹配或分区过滤逻辑：编辑 `journal_registry.py`；
- 更新 JCR 原始数据后，运行 `scripts/build_jcr_registry.py` 重新生成 `data/jcr_2026_journals.csv`；
- 修改 Newsletter 的栏目与排版：编辑 `newsletter.py`；
- 修改词云、趋势图与统计口径：编辑 `analytics.py`。

期刊分区过滤默认启用。带 ISSN 的论文会优先按 ISSN 精确匹配；Q1/Q2 及未识别分区的期刊保留，Q3/Q4 期刊仅在例外名单中时保留。多学科分区按该期刊的最高分区判断。
