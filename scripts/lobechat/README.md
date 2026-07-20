# 造价通 - AI 聊天前端 LobeChat 启动说明

造价通的「AI 助手」标签页采用开源项目 [LobeChat](https://github.com/lobehub/lobe-chat) 通过 iframe 嵌入。
所有聊天 UI、多会话管理、模型切换、消息历史、Markdown 渲染都由 LobeChat 完成,造价通只做配置接入。

## 一、选 LobeChat 的理由

| 项 | 评估 |
|---|---|
| 代码协议 | MIT,可商用 |
| UI 质量 | 业内评价最高,中文支持完整 |
| 模型接入 | OpenAI 兼容(DeepSeek/通义/智谱/KIMI/OpenAI/Ollama 全部支持) |
| 部署方式 | Docker 一行 / Node 自部署 / 官方 SaaS 三选 |
| 维护活跃度 | GitHub 50k+ star,周更 |
| 嵌入可行 | 纯前端 Next.js,可 iframe |

## 二、三种部署方式选一种

### 方式 A: Docker 一键启动(强烈推荐)

```bash
# Linux/Mac
bash scripts/lobechat/start_lobechat.sh

# Windows
scripts\lobechat\start_lobechat.bat
```

或手动:

```bash
docker run -d --name lobechat \
  -p 3210:3210 \
  -e OPENAI_API_KEY=sk-你的-deepseek-密钥 \
  -e OPENAI_PROXY_URL=https://api.deepseek.com/v1 \
  -e DEFAULT_AGENT_CONFIG=deepseek-chat \
  lobehub/lobe-chat:latest
```

启动后访问 http://localhost:3210 验证。

### 方式 B: Node 自部署

```bash
git clone --depth=1 https://github.com/lobehub/lobe-chat
cd lobe-chat
pnpm install
OPENAI_API_KEY=sk-... OPENAI_PROXY_URL=https://api.deepseek.com/v1 pnpm dev
```

### 方式 C: 直接用官方 SaaS(0 部署)

打开 https://chat-preview.lobehub.com ,在它的"设置 → 语言模型"里填你的 DeepSeek/Qwen/智谱/KIMI 任一密钥。

然后在造价通的 `config.yaml` 改 `ai.lobechat_url` 指向实际访问地址。

## 三、把造价通指向 LobeChat

编辑 `H:\AI-model\造价通\config.yaml`:

```yaml
ai:
  lobechat_url: "http://localhost:3210"   # 改成你的 LobeChat 实例地址
```

或在系统设置页改 → 重启造价通后端 → Chat 标签页自动加载该地址。

## 四、DeepSeek 密钥怎么填

DeepSeek 目前最便宜且能力最强,作为首选。

1. 注册 https://platform.deepseek.com
2. 充值 10 元(约 200 万 tokens)
3. 创建 API Key → 复制 sk-xxxxxxxx
4. 粘贴到 LobeChat 的"设置 → 语言模型 → OpenAI → API Key"
   - 接口地址填: https://api.deepseek.com/v1
   - 模型填: deepseek-chat

## 五、换成别的 Provider

LobeChat 内置 Provider 模版,直接在 UI 里切:

| Provider | base_url | 模型 |
|---|---|---|
| DeepSeek | https://api.deepseek.com/v1 | deepseek-chat |
| 通义千问 | https://dashscope.aliyuncs.com/compatible-mode/v1 | qwen-plus |
| 智谱 GLM | https://open.bigmodel.cn/api/paas/v4 | glm-4-plus |
| KIMI | https://api.moonshot.cn/v1 | moonshot-v1-32k |
| OpenAI | https://api.openai.com/v1 | gpt-4o-mini |

## 六、常见问题

**Q: 必须先启动 LobeChat 才能开造价通的 AI 助手?**
A: 是。造价通只做容器,聊天能力全在 LobeChat。LobeChat 未启动时 AI 助手标签页会弹启动指引。

**Q: 能让造价通自动拉起 LobeChat 吗?**
A: M4 阶段会在 Electron 主进程内加 docker 自启逻辑。当前先手动起一次。

**Q: 多人共用一个 LobeChat 实例?**
A: 推荐运维部署在服务器,Docker Compose + Nginx 反代,造价通的 `lobechat_url` 指向服务器地址即可。

**Q: LobeChat 能访问造价通本地的 RAG 知识库吗?**
A: 当前 Chat.vue 通过 iframe 嵌入, LobeChat 独立运行, 不直连本机 ChromaDB。
后续 M4 给 LobeChat 加自定义 plugin 调造价通的 `/api/v1/kb/search` 接口即可。
