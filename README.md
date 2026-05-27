# quant_data_spider_v1

量化数据自动化采集与同步系统 —— 多源金融数据的自动采集、清洗、入库、监控与 Web 可视化面板。

## 技术栈

| 层 | 技术 |
|---|---|
| Web 框架 | FastAPI + Jinja2 服务端渲染 |
| 前端交互 | HTMX (CDN) 无刷新更新 |
| 金融图表 | ECharts (CDN) K线图/成交量 |
| CSS | Pico.css (CDN) 暗色主题 |
| 数据库 | MySQL 8.0 + SQLAlchemy ORM + Alembic 迁移 |
| 调度 | APScheduler 定时任务 |
| 数据源 | AKShare 金融数据接口 |
| CLI | Typer |

纯 Python 栈，无需 Node.js。

## 项目结构

```
quant_data_spider_v1/
├── config/                     # 配置文件
│   ├── settings.py             # Pydantic-settings 统一配置
│   ├── sources.toml            # 数据源定义（AKShare 端点）
│   ├── schedules.toml          # 定时任务 cron 表达式
│   └── thresholds.toml         # 监控告警阈值
├── src/
│   ├── core/                   # 核心模块：ORM 模型、数据库、异常、类型
│   ├── acquisition/            # 数据获取：限流器、AKShare 客户端、数据源注册
│   ├── processing/             # 数据处理：校验→清洗→转换 管道
│   ├── storage/                # 数据存储：Repository + 同步服务
│   ├── scheduler/              # 定时调度：APScheduler 封装 + 任务定义
│   ├── monitoring/             # 系统监控：规则评估引擎 + 告警分发
│   ├── web/                    # Web 面板：FastAPI + 路由 + 模板 + 静态文件
│   └── cli/                    # CLI 入口：Typer 命令行
├── tests/                      # 测试（186 项）
├── scripts/run_web.py          # Web 服务器入口
├── Dockerfile                  # Docker 多阶段构建
├── docker-compose.yml          # MySQL + Web 一键部署
└── pyproject.toml              # 项目元数据与依赖
```

## 快速开始

### 1. 环境要求

- Python >= 3.10
- MySQL 8.0（或 Docker）

### 2. 安装

```bash
git clone https://github.com/youshijiuli/quant_data_spider_v1.git
cd quant_data_spider_v1

# 安装依赖
pip install -e ".[dev]"
```

### 3. 配置

```bash
cp .env.example .env
```

编辑 `.env`，填入 MySQL 连接信息：

```env
QUANT_DB_HOST=127.0.0.1
QUANT_DB_PORT=3306
QUANT_DB_USER=root
QUANT_DB_PASSWORD=your_password
QUANT_DB_NAME=quant_data
```

数据库表会在首次启动时自动创建。

### 4. 启动 Web 面板

```bash
python scripts/run_web.py
```

浏览器打开 `http://localhost:8000`，即可使用数据仪表盘。

### 5. Docker 部署（推荐）

```bash
docker compose up -d
```

自动启动 MySQL 8.0 + Web 面板，无需手动配置数据库。

## 使用方式

### Web 面板

| 路由 | 功能 |
|------|------|
| `/` | 仪表盘首页：数据统计卡片、最新同步、活跃告警 |
| `/data/stocks` | 股票浏览器：搜索、筛选、分页 |
| `/data/indexes` | 指数日线数据浏览 |
| `/data/financials` | 财务数据按报告期筛选 |
| `/data/sources` | 数据源配置状态 |
| `/charts` | K 线图（ECharts）：OHLC + 成交量 |
| `/sync` | 同步控制：触发采集、查看历史 |
| `/monitoring` | 告警中心：严重度颜色标记、确认/解决 |
| `/monitoring/rules` | 监控规则查看与编辑 |
| `/scheduler` | 定时任务：暂停/恢复/立即执行 |
| `/api/health` | 健康检查 JSON API |

### CLI 命令行

```bash
# 启动 Web 服务
python -m src.cli.main serve --host 0.0.0.0 --port 8000
python -m src.cli.main serve --reload    # 开发模式热重载

# 单次数据同步
python -m src.cli.main sync --source akshare_stock_basic
python -m src.cli.main sync --source akshare_stock_daily --symbol 000001 --start 20240101 --end 20241231
python -m src.cli.main sync --source akshare_index_daily

# 启动定时调度器（后台运行）
python -m src.cli.main schedule
```

### 支持的同步源

| source_code | 说明 |
|-------------|------|
| `akshare_stock_basic` | A 股股票基本信息（沪深京） |
| `akshare_stock_daily` | A 股日线 OHLCV 行情 |
| `akshare_index_daily` | 指数日线（上证/深证/沪深300） |
| `akshare_financial` | A 股财务报表摘要（营收/利润/EPS/ROE） |

## 运行测试

```bash
# 全部测试（186 项）
pytest

# 覆盖率报告
pytest --cov=src --cov-report=html

# 单独模块
pytest tests/test_storage/
pytest tests/test_web/
pytest tests/test_monitoring/
```

## 监控告警

系统内置 8 条监控规则（`config/thresholds.toml`），支持以下检查类型：

| 检查类型 | 说明 |
|----------|------|
| `null_rate` | 空值率检测 |
| `row_count` | 行数下限检测 |
| `stale_data` | 数据过期检测 |
| `value_range` | 失败同步数检测 |
| `duplicate_rate` | 重复率检测 |

告警支持 console、文件（JSONL）两种分发方式，可在 `config/settings.py` 中配置。
