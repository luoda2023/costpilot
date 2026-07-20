# 造价通 v0.2.0 - 架构调整说明

## 一、本次调整原因

用户明确指示:
1. **不做 LoRA 自训练**(原 M6 砍掉)
2. **资料库 → 知识库 RAG**: 21,000+ 原文件 + 17,864 条价格 + 8 类格式谱全部向量化入库作为外部知识
3. **AI 走外部在线 API**: 用户在 config.yaml 填 API 地址/密钥/模型名,应用统一调用,**支持任何 OpenAI 兼容接口**
4. **不依赖本地 Ollama**(原 Ollama 路径改为可选,默认走在线)

## 二、核心理由

| 项 | 自训练 LoRA | 外部 API + RAG(本次) |
|---|---|---|
| 显卡要求 | 8-24GB VRAM | 无,办公本可跑 |
| 维护成本 | 模型升级需重训 | 云端自动,只改 endpoint |
| 数据时效 | 静态快照 | 可任意时刻重新向量化 |
| 切换灵活 | 改模型重训 | 改一行 yaml 即可 |
| 数据安全 | 训练后泄漏风险 | RAG 数据留在本机,只发出 query |

## 三、新增/改动文件

### 新增(13 个)
- `config.yaml`                     ★ 用户唯一对外配置
- `.gitignore`                      防密钥泄漏
- `packages/server/config.py`      配置加载器
- `packages/server/ai/client.py`    ★ 多 Provider 适配层
- `packages/server/ai/rag.py`       ★ ChromaDB + bge-m3 模块
- `packages/server/ai/chunking.py`  ★ 文档分块器
- `packages/server/ai/chat_engine.py` ★ RAG+AI 编排
- `packages/server/api/ai_config.py`  AI 配置管理 API
- `packages/server/api/knowledge.py`  RAG 检索 API
- `packages/server/templates/pricing.py`     报价组价算法
- `packages/server/templates/excel_export.py` Excel 6 Sheet 导出
- `packages/server/templates/word_export.py`  Word 报价导出
- `packages/server/templates/doc_renderer.py`  Markdown→docx 渲染器
- `apps/web/src/views/Quote.vue`     报价生成前端
- `apps/web/src/views/Settings.vue`  系统设置前端
- `scripts/build_rag_index.py`      批量索引脚本

### 改动
- `packages/server/api/app.py`      注册新 router,35 路径
- `packages/server/api/chat.py`     重写为 RAG 注入版
- `apps/web/src/views/Preview.vue`  升级 vue-office 全格式预览
- `apps/web/src/views/TextGen.vue`  接入真实 docx 渲染 API
- `apps/web/src/router/index.js`    加入 quote / settings 路由
- `apps/web/src/App.vue`             加入对应菜单项
- `apps/web/package.json`            加入 @vue-office 依赖
- `README.md`                       重写为 v0.2.0

## 四、不改动的设计

- 数据库 ORM 14 张表(仍 SQLite 默认)
- 14 个核心路由(价格库/费率/模板/项目/聊天/文件)
- 8 类格式谱入库的 92 字段定义
- 17,864 条综合单价已入库

## 五、API 路径总数演变

| 版本 | 路径数 | 新增项 |
|---|---|---|
| v0.1.0 | 20 | M1 主体 |
| v0.2.0 | **35** | +报价4 +AI配置5 +知识库4 +模板渲染2 |

## 六、用户使用路径

1. `pip install ...` 装依赖
2. 编辑 `config.yaml` 填 AI `api_key`(一个密钥即可)
3. `python scripts/import_prices_to_db.py` 等导入数据
4. `python scripts/build_rag_index.py` 建 RAG 索引(可选,推荐)
5. `npm run dev` 起 Vite,`uvicorn` 起后端,`electron` 起桌面
6. 在系统设置页测试 AI 连接,即可使用

## 七、保留的扩展点

- M5 PostgreSQL 升级(只需改 database.url)
- M5 多人协同(Web 版部署)
- M6 vLLM 自托管 API(若未来某用户要内网部署)
- LoRA 微调(若未来真需要领域微调,可在 RAG 之外叠加)

v0.2.0 ready
