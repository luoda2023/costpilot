# 造价通 CostPilot - 工程造价智能助手 v0.2.0

> 基于 H:\AI-model 21,000+ 原文件 + 17,864 条提炼价格 + 8 类文本格式谱开发的桌面单机版专业软件。

## 一、产品定位

**单机桌面端 + 离线 RAG 知识库 + 外部在线 AI**: 用户在 `config.yaml` 填一个 API 密钥即可获得专业造价助手能力,无需自训模型、无需显卡。

## 二、当前已完成的模块

| 模块 | 状态 | 说明 |
|---|---|---|
| 数据库 ORM | ✅ | 14 张表 SQLAlchemy;SQLite 默认,兼容 PostgreSQL |
| Alembic 迁移 | ✅ | `0001_initial` 全部建表 |
| 价格库导入 | ✅ | 17,864 条综合单价 + 370 专题 + 16 费率已入库 |
| 8 类文本格式谱入库 | ✅ | 8 模板 + 92 字段定义 |
| FastAPI 后端 | ✅ | **35 个 API 路径** |
| 报价组价算法 | ✅ | 八项单价 + 一/二/三类费用,精确到分 |
| Excel 报价表导出 | ✅ | 6 Sheet(封面/汇总/说明/分部分项/措施/规税费) |
| Word 报价表导出 | ✅ | 同上,docx 表格规范 |
| 文档生成 docx | ✅ | 8 类格式谱 Markdown→docx 渲染器 |
| Electron 主进程 | ✅ | 主进程+preload+IPC |
| Vue3 前端 | ✅ | **7 主页面**:工作台/价格库/报价生成/文本生成/文件预览/AI 聊天/系统设置 |
| 文件全格式预览 | ✅ | vue-office 整合 PDF/DOCX/XLSX,md/txt/csv 直读 |
| AI 多 Provider 适配层 | ✅ | DeepSeek/Qwen/智谱/Moonshot/OpenAI/Ollama 一键切 |
| 用户配置文件 | ✅ | `config.yaml` 单一入口,改完即生效 |
| AI 配置管理 API | ✅ | 查看/测试/切换/重载 5 路由 |
| RAG 向量库模块 | ✅ | ChromaDB + bge-m3 嵌入/检索代码就绪 |
| 知识库索引脚本 | ✅ | 批量分块+嵌入+断点续跑 |
| 知识库混合检索 API | ✅ | 语义 + SQL 价格库 4 路由 |
| chat 接入 RAG | ✅ | chat_engine 自动先检索再答,引用来源附在末尾 |

## 三、架构图(简)

```
┌───────────────────────────────────────────┐
│           Electron 31 桌面壳               │
│  ┌───────────────────────────────────────┐ │
│  │   Vue 3.4 + Element Plus + Pinia     │ │
│  │   工作台/价格库/报价/文本/预览/Chat/设置 │ │
│  └─────────────┬─────────────────────────┘ │
│                │ HTTP/REST (JSON)            │
│  ┌─────────────▼─────────────────────────┐ │
│  │     Vite 5 dev / 静态打包             │ │
│  └─────────────┬─────────────────────────┘ │
└────────────────┼────────────────────────────┘
                 │
        ┌────────▼────────┐
        │  FastAPI 后端    │ 35 路径
        │  ┌────────────┐ │
        │  │ 报价组价    │ │ → Excel/Word 导出
        │  │ 8 类格式谱  │ │ → docx 生成
        │  │ 价格库 SQL  │ │ → 17864 条结构化查
        │  │ AI 多适配层 │ │ → DeepSeek/Qwen/...
        │  │ RAG 检索    │ │ → ChromaDB + bge-m3
        │  └────────────┘ │
        └────────┬────────┘
                 │
        ┌────────▼────────────────┐
        │  外部 AI API(用户选)    │
        │  DeepSeek / Qwen / 智谱  │
        │  KIMI / OpenAI / Ollama  │
        └─────────────────────────┘
```

## 四、目录结构

```
H:\AI-model\造价通\
├── config.yaml                  ★ 用户唯一对外配置(AI/RAG/数据库/资源路径)
├── package.json
├── alembic.ini
├── apps/
│   ├── desktop/                 # Electron 主进程 + preload
│   └── web/                     # Vue3 前端
│       └── src/views/
│           ├── Workspace.vue      # 工作台
│           ├── Prices.vue         # 价格库
│           ├── Quote.vue          # 报价生成 ★
│           ├── TextGen.vue        # 文本生成
│           ├── Preview.vue        # 文件预览(vue-office)
│           ├── Chat.vue           # AI 聊天
│           └── Settings.vue       # 系统设置 ★
├── packages/
│   ├── server/
│   │   ├── config.py             ★ 配置加载器
│   │   ├── api/                  # 35 路由
│   │   │   ├── app.py
│   │   │   ├── prices.py / fees.py / projects.py
│   │   │   ├── quotes.py         ★ 报价生成+导出
│   │   │   ├── templates.py      ★ + render/docx 导出
│   │   │   ├── chat.py            ★ RAG 注入版
│   │   │   ├── knowledge.py       ★ RAG 检索 API
│   │   │   ├── ai_config.py      ★ 多 Provider 管理
│   │   │   ├── files.py / health.py
│   │   ├── ai/
│   │   │   ├── prompts.py         # 1188 字符专业 system prompt
│   │   │   ├── ollama.py          # 本地可选
│   │   │   ├── client.py          ★ 多 Provider 适配层
│   │   │   ├── chunking.py        ★ 文档分块
│   │   │   ├── rag.py             ★ ChromaDB 嵌入/检索
│   │   │   └── chat_engine.py     ★ RAG+ai 编排
│   │   ├── db/                   # ORM
│   │   └── templates/
│   │       ├── pricing.py         ★ 八项+三类组价算法
│   │       ├── excel_export.py     ★ 6 Sheet 报价 Excel
│   │       ├── word_export.py     ★ 报价 Word
│   │       └── doc_renderer.py    ★ Markdown→docx
│   └── db-migrations/            # Alembic
├── scripts/
│   ├── import_prices_to_db.py
│   ├── import_templates_to_db.py
│   └── build_rag_index.py        ★ 批量 RAG 索引
└── data/
    ├── sqlite/造价通.db          # 18,366 条记录 / 5.9 MB
    ├── chroma/                   # ChromaDB 向量库
    └── exports/                  # 已生成 Excel/Word/docx
```

## 五、线上启动步骤

> ⚠️ **原则**:
> - 数据库导入等基础验证可在开发机本地跑
> - `npm run dev` / `vite` / `uvicorn` long-running 服务**必须在线上环境执行**
> - `electron-builder` 打包 .exe **必须在线上环境执行**

### 5.1 准备环境

```bash
# 1. Python 依赖
pip install sqlalchemy alembic fastapi uvicorn pydantic openpyxl requests python-docx pyyaml
# 可选(启用 RAG):
pip install chromadb sentence-transformers pdfplumber

# 2. Node 依赖
npm install
cd apps/web && npm install && cd ../..
```

### 5.2 配置 AI(关键)

编辑 `H:\AI-model\造价通\config.yaml`, 改一行即可:

```yaml
ai:
  provider: "deepseek"        # 选 deepseek/qwen/zhipu/moonshot/openai/ollama
  api_key: "sk-你的密钥"        # ← 填这个
```

或在系统启动后,在前端"系统设置"页面切换 provider + 填密钥 + 点测试连接。

### 5.3 初始化数据库

```bash
alembic upgrade head
python scripts/import_prices_to_db.py
python scripts/import_templates_to_db.py
```

### 5.4 启动开发模式

```bash
# 终端 1：FastAPI 后端
python -m uvicorn packages.server.api.app:app --host 127.0.0.1 --port 8765 --reload

# 终端 2：Vite 前端
cd apps/web && npm run dev

# 终端 3：Electron 桌面壳
npm run dev:electron
```

访问 http://localhost:5173 或 Electron 窗口。

### 5.5 构建 RAG 知识库(可选,推荐)

```bash
# 增量索引 21,000+ 文件(首次约 30-60 分钟,取决于文件数)
python scripts/build_rag_index.py

# 限制只跑前 N 个文件做测试
python scripts/build_rag_index.py --limit 100 --dry-run

# 重置索引从头来
python scripts/build_rag_index.py --reset
```

构建后, Chat 页 AI 回答会自动 RAG 引用 H:\AI-model 中的具名文件。

### 5.6 打包安装包

```bash
npm run build:win    # → dist-electron/造价通 Setup 0.2.0.exe
npm run build:mac
npm run build:linux
```

## 六、API 速查

35 个路径,Swagger UI: http://localhost:8765/docs

主要分组:
- 健康检查: `/health`
- 价格库: `/api/v1/prices/*` (5 个)
- 费率: `/api/v1/fees`
- 模板: `/api/v1/templates/*` (含 `/render` 生成 docx,6 个)
- 项目+工程量: `/api/v1/projects/*` (5 个)
- **报价生成**: `/api/v1/quotes/compose | /export/excel | /export/word | /download/{file}` (4 个)
- AI 聊天: `/api/v1/chat/sessions*` (3 个)
- **AI 配置**: `/api/v1/ai/config | /providers | /test | /switch | /reload` (5 个)
- **知识库 RAG**: `/api/v1/kb/stats | /search | /hybrid | /progress` (4 个)
- 文件浏览: `/api/v1/files/list`
- 文件预览: `/api/v1/preview/text | /file`

## 七、技术栈

| 类别 | 选型 |
|---|---|
| 桌面壳 | Electron 31 |
| 前端 | Vue 3.4 + Element Plus 2.7 + Pinia + Vite 5 |
| 文档全格式预览 | @vue-office/pdf + docx + excel |
| 后端 | Python 3.10+ FastAPI |
| ORM | SQLAlchemy 2.0 + Alembic |
| 数据库 | SQLite (默认) / PostgreSQL (M5) |
| Excel/Word | openpyxl + python-docx |
| **AI** | **外部 API**: DeepSeek/Qwen/智谱/KIMI/OpenAI 任选 + Ollama 本地可选 |
| **RAG** | ChromaDB + BAAI/bge-m3 (中英 1024 维,本地无需 API) |
| 文档解析 | pdfplumber + python-docx + openpyxl |

## 八、关键设计决策

1. **不自训练模型**: 21,000 文件做成 RAG 知识库,更省机器、更易升级,模型由云端兜底
2. **不绑厂商**: OpenAI 兼容协议,DeepSeek/通义/智谱/KIMI 任切只改一行配置
3. **专业提示词**: 1188 字符 system prompt 让任意 AI 立刻具备造价师风格
4. **RAG 强引用**: AI 回答必须给出 `t_price_unit` 结构化查 + 语义检索 chunks 双来源
5. **本地优先**: SQLite + ChromaDB 持久化,断网仍可工作,密钥仅本地一份

## 九、许可证

MIT

## 十、v0.2.1 - LobeChat 嵌入补充说明

> **重要**: 造价通的「AI 助手」聊天 UI 采用开源项目 **LobeChat** 通过 iframe 嵌入,
> 不自写聊天界面,不自训练模型。

### 启动 LobeChat(一次)

```bash
# Linux/Mac
bash scripts/lobechat/start_lobechat.sh

# Windows
scripts\lobechat\start_lobechat.bat

# 或手动: docker run -d --name lobechat -p 3210:3210 \
#   -e OPENAI_API_KEY=sk-... -e OPENAI_PROXY_URL=https://api.deepseek.com/v1 \
#   lobehub/lobe-chat:latest
```

### 配置造价通指向它

`config.yaml`:

```yaml
ai:
  lobechat_url: "http://localhost:3210"  # 改成你的 LobeChat 实例地址
```

LobeChat 启动后，造价通的「AI 助手」标签页自动加载，**所有聊天能力（多会话、Markdown、模型切换、文件上传）由 LobeChat 提供**，造价通只做容器。

详见 `LOBECHAT_INTEGRATION.md`。

## 十一、协议复用清单

所有上游开源项目协议保留:
- LobeChat (MIT)
- Vue 3 (MIT) + Element Plus (MIT)
- Electron (MIT)
- FastAPI (MIT) + SQLAlchemy (MIT)
- ChromaDB (Apache 2.0) + sentence-transformers (Apache 2.0)
- python-docx (MIT) + openpyxl (MIT)
- @vue-office (MIT)
