# Finance Radar Pro · 融合版

> **TrendRadar 全网热点雷达 + daily_stock_analysis 盯盘** 深度融合 · 每日 **07:00 (Asia/Shanghai)** 自动生成《财经早报》 · **GitHub Pages 网页查看** · 自选股/基金在网页实时调整

[![Daily Finance Radar](https://github.com/259773138/finance-radar-pro/actions/workflows/daily.yml/badge.svg)](https://github.com/259773138/finance-radar-pro/actions/workflows/daily.yml)

**在线查看:** `https://259773138.github.io/finance-radar-pro/`

## 1. 这是什么？

结合两个最强开源项目的优点：

| 能力 | 来源 | 说明 |
|---|---|---|
| 全网抓取 | **TrendRadar** | 财联社/华尔街见闻/新浪/东方财富/政府网等10+源，35平台可扩展，120+关键词全面覆盖 宏观/政策/监管/行业/国际 |
| 个股基金 | **daily_stock_analysis** | A股/港股/美股/ETF 多源行情(AKShare/YFinance)，技术面+筹码 |
| AI整理 | 融合升级 | 统一 **ModelScope OpenAI兼容**，自动拉取服务器模型列表，默认 **魔搭最强Qwen3旗舰 (Qwen3-235B)** |
| 网页端 | 本项目新增 | GitHub Pages 静态托管，响应式仪表盘，支持浏览器端实时改自选/关键词并同步到云端 |

## 2. 如何使用网页调整自选？

1. 打开 Pages 站点，右上角 **⚙️ 配置自选 & 关键词**
2. 添加代码：`600519 / hk00700 / AAPL / 510050`，选择市场，备注名可选
3. **立即生效**：保存到浏览器 localStorage，页面立即可筛选查看
4. **次日生效**：点 **同步到云端**（粘贴一个细粒度PAT，仅contents:write）或手动去 `config/watchlist.json` 修改，下一次07:00任务就会用新清单生成完整AI分析

关键词同理，默认已内置120+非常全面的政策/行业词，你在末尾追加即可。

## 3. AI模型配置

在仓库 `Settings -> Secrets and variables -> Actions` 添加：

- `MODELSCOPE_API_KEY` — 魔搭API Key（推荐）
- 或 `OPENAI_API_KEY` + `OPENAI_BASE_URL` — 任意OpenAI兼容服务
- `MODEL_NAME` — 可选，强制指定模型；不填则自动从服务器 `GET /v1/models` 挑选最强的 Qwen3

> 不配置也能跑，会自动降级为 Mock 演示分析，保证页面不空。

## 4. 定时任务

`.github/workflows/daily.yml` 已配置 `cron: '0 23 * * *'` = 北京时间07:00，每次自动：
1. 抓热点 + 抓行情
2. 调魔搭Qwen生成JSON早报
3. 提交 `docs/data/latest.json` + `history/`
4. 部署到 GitHub Pages

也可手动触发：Actions -> Daily Finance Radar -> Run workflow，可临时传入 `stocks` JSON 和 `extra_keywords`。

## 5. 本地开发

```bash
pip install -r requirements.txt
export MODELSCOPE_API_KEY=ms-xxx
python src/generate_report.py
# 报告在 docs/data/latest.json
```

## 6. 融合亮点

- **去重+评分**：命中关键词越多分越高，政策类额外+2分
- **AI融合Prompt**：把大势+个股一起喂给LLM，输出统一JSON，早报可直接渲染为飞书卡片/网页
- **自适应ModelScope**：自动 `GET /v1/models` 选最强Qwen，兼容任意OpenAI接口
- **零成本**：全跑在 GitHub Actions + Pages，无需服务器
