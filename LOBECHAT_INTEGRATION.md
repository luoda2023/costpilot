# 造价通 v0.2.1 - LobeChat 嵌入说明

## 一、决策回溯

用户明确：
1. **不要自己训练模型**
2. **AI 聊天用现成的开源工具嵌入，不自写聊天 UI**
3. 在第二次澄清后，选定 **LobeChat**（GitHub 50k+ star，MIT 协议，主流 OpenAI 兼容 Provider 全支持）

## 二、改造范围（v0.2.0 → v0.2.1）

### 改动文件 (4 个)
| 文件 | 改动 |
|---|---|
| `apps/web/src/views/Chat.vue` | **从自写聊天 UI → 改为 iframe 嵌入 LobeChat 容器**，含健康探测 + 启动指引弹窗 + 新窗口打开 |
| `config.yaml` | 新增 `ai.lobechat_url` 字段，默认 `http://localhost:3210` |
| `packages/server/config.py` | `AIConfig` 加 `lobechat_url` 字段 + `resolved()` 输出 |
| `packages/server/api/ai_config.py` | `AIConfigOut` + `SwitchIn` 加 `lobechat_url` 字段，`/ai/config` 暴露给前端 |

### 新增文件 (3 个)
| 文件 | 用途 |
|---|---|
| `scripts/lobechat/start_lobechat.sh` | Linux/Mac 一键启动（Docker 优先，回退 Node） |
| `scripts/lobechat/start_lobechat.bat` | Windows 一键启动（Docker） |
| `scripts/lobechat/README.md` | 三种部署方式 + 切 Provider 指南 + FAQ |

## 三、用户使用路径

```
1. 启动 LobeChat（一次）:
   bash scripts/lobechat/start_lobechat.sh
   → Docker 拉起 lobehub/lobe-chat:latest, 监听 :3210
   → 填好 OPENAI_API_KEY (默认 DeepSeek)

2. 启动造价通:
   npm run dev:electron   # 自动加载 LobeChat iframe
   或访问 http://localhost:5173 → 点 "AI 助手" 标签页

3. 在 LobeChat 内:
   - 设置 → 语言模型 → 切 DeepSeek/Qwen/智谱/KIMI 任一 Provider
   - 多会话、Markdown、代码高亮、文件上传全部开箱可用
   - 不需要造价通这边写任何聊天 UI 代码
```

## 四、不动的部分

- 35 个 FastAPI 路由全部保留（ precios / quotes / templates / kb / chat_session 等）
- `chat_engine.py + rag.py + chunking.py` RAG 链路保留（未来给 LobeChat 写 plugin 调用）
- 18,366 条数据 + 92 字段 + 14 张表不动
- 报价组价、Excel/Word/docx 生成不动
- 7 个前端页面不动（Chat.vue 只升级为 iframe 容器）

## 五、造价通这一侧后续还要做的（可选）

| 项 | 价值 | 优先级 |
|---|---|---|
| 给 LobeChat 写 plugin 调 `/api/v1/kb/search` | 让聊天能引用 RAG 知识 | M4 |
| Electron 主进程自动拉起 LobeChat 容器 | 用户感知不到 LobeChat 存在 | M4 |
| 在系统设置页加「测试 LobeChat 连接」按钮 | UX | M4 |

