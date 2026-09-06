# 心脑、生态瞬时干预与数字心理健康文献周报

该工具每周追踪三条主线：

1. 心脑轴；
2. 生态瞬时干预（覆盖 EMA/ESM、EMI、JITAI、MRT 与数字表型）；
3. 心理健康与数字心理干预。

每周一北京时间 12:00，GitHub Actions 下载上一个完整自然周的 PubMed 与 Crossref 候选文献。候选先经过本地关键词与心理学语境预筛，再由 DeepSeek 进行语义筛选。成功运行后只提交一份 Newsletter 的两种阅读格式：Markdown 与 HTML。

## 输出

输出位于 `newsletters/`：

- `<日期范围>_weekly_paper.md`：GitHub 内直接阅读；
- `<日期范围>_weekly_paper.html`：便于下载和分享。

Newsletter 固定包含“重点推荐”、心脑轴、生态瞬时干预、心理健康与数字心理干预四个板块。

## 配置

主题词与本地预筛规则集中在 `domain_config.py`：

- `TOPIC_GROUPS`：三条主线的 PubMed 标题/摘要检索词；
- `CROSSREF_QUERY_TERMS`：Crossref 补充检索词；
- `HEART_BRAIN_CONTEXT_REQUIRED_TERMS`：HRV、迷走神经、自主神经系统等必须带心理学语境的词；
- `HEART_BRAIN_PSYCHOLOGICAL_CONTEXT_TERMS`：允许上述心脑词进入 DeepSeek 的心理/行为语境。

`journal_registry.py` 是默认启用的 ISSN 白名单。只有与三条主线直接相关、并经审计为 JCR Q1/Q2 的期刊会在抓取阶段保留。

名单中的 IF 与 JCR 分区来自 `impact_factor 1.1.3`（2025-11-25 发布）。

## GitHub Secrets 与变量

在仓库 Settings → Secrets and variables → Actions 中配置：

- Secret `DEEPSEEK_API_KEY`
- Secret `NCBI_API_KEY`
- Secret `NCBI_EMAIL`
- Variable `CROSSREF_MAILTO`

候选元数据在两个工作流之间以一天有效期的 Actions Artifact 传递，不会提交到仓库。
