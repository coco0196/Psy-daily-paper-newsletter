# 心脑与数字心理健康文献周报

本工具每周追踪四条相互独立的研究线，并优先呈现其交叉研究：

1. 心脑轴、心脑耦合、神经内脏整合、HRV/RSA 与心搏诱发电位；
2. 生态瞬时评估（EMA）、经验取样（ESM）与密集纵向测量；
3. 生态瞬时干预（EMI）、即时自适应干预（JITAI）、微随机试验与数字表型；
4. 心理健康、情绪调节及数字/移动心理干预。

## 产物

每次运行会把原始元数据、DeepSeek 中文解读、Markdown/HTML 周报、词云、趋势图、海报和中文 MP3 写入仓库。工具本身不发送电子邮件。

## 工作流

`Download tracker metadata` 每周一北京时间 12:00 下载上周一至周日的 PubMed 与 Crossref 记录；成功后触发 `Generate heart-brain and digital mental-health report`。后者用 DeepSeek 判定相关性、主题标签和优先级，并生成完整报告。

## 配置

主题词集中在 `domain_config.py`：

- `TOPIC_GROUPS`：四个独立的 PubMed 标题/摘要检索组；
- `CROSSREF_QUERY_TERMS`：Crossref 的高特异性补充检索词；
- `REPORT_TITLE`：报告、海报和语音的领域名称。

默认不限制期刊，以保证四条研究线的覆盖范围。若希望启用 `journal_registry.py` 中的白名单，在 GitHub 仓库变量中设置：

```text
JOURNAL_FILTER_ENABLED=true
```

## GitHub 配置

在仓库的 `Settings → Secrets and variables → Actions` 添加：

```text
DEEPSEEK_API_KEY=你的 DeepSeek API 密钥
NCBI_API_KEY=你的 NCBI API 密钥（建议）
NCBI_EMAIL=你的联系邮箱
```

建议在 Actions 变量中添加：

```text
CROSSREF_MAILTO=你的联系邮箱
JOURNAL_FILTER_ENABLED=false
```

首次部署请通过 Actions 的手动触发指定一周日期，核对 `Paper_metadata_download/`、`Psy-day-paper-deepseek/` 与 `newsletters/` 产物后再依赖定时运行。

## 本地运行

```powershell
python -m pip install -r requirements.txt
$env:DEEPSEEK_API_KEY = "你的密钥"
$env:NCBI_API_KEY = "你的 NCBI 密钥"
$env:NCBI_EMAIL = "you@example.org"
python Paper_metadata_download.py --start-date 2026-08-17 --end-date 2026-08-23
python Psy-day-paper-deepseek.py --start-date 2026-08-17 --end-date 2026-08-23
```

第二个命令会依次生成海报、统计、周报与语音。
