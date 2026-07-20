# 造价通一键启动器 (CostPilot Launcher)

> 双击 `start.exe` 即可拉起整个造价通运行环境（LobeChat + 桌面壳），用户无需打开 Docker Desktop、无需敲命令行。

## 一、 principio 重要原则

> **本启动器源码可在本地写,但 `start.exe` 的构建必须在线上环境执行**:
>   - 本地不能 `go build`
>   - 本地不能 `electron-builder`
>   - 所有打包/编译全部在线上构建服务器跑

## 二、源码结构

```
launcher/
├── go.mod          # Go 模块定义,依赖 github.com/lxn/walk (Windows GUI 库)
├── main.go         # 301 行, 一键拉起逻辑 + GUI 进度窗
├── build.bat       # Windows 线上构建脚本 (GOOS=windows)
├── build.sh        # Linux/Mac 线上构建脚本 (交叉编译 Windows EXE)
└── README.md       # 本说明
```

## 三、 start.exe 双击后做的事

```
[1/4] 检测 Docker
   ├─ docker.exe 在 PATH 里? 不在则查 C:\Program Files\Docker\...
   ├─ docker info 通? 不通则启动 Docker Desktop, 等最长 60s
   └─ 通过 → 进入 [2/4]

[2/4] 启动 LobeChat 容器
   ├─ docker ps -a 看 lobechat 容器是否存在
   ├─ 存在: docker start lobechat
   └─ 不存在: docker run -d --name lobechat -p 3210:3210 \
              -e OPENAI_API_KEY=sk-... \
              -e OPENAI_PROXY_URL=https://api.deepseek.com/v1 \
              -e DEFAULT_AGENT_CONFIG=deepseek-chat \
              lobehub/lobe-chat:latest

[3/4] 等待 http://localhost:3210 就绪
   └─ HTTP GET 30 次每次 1s, 任一次 200-499 即视为就绪

[4/4] 启动造价通桌面壳
   ├─ 优先找同目录的 costpilot.exe
   ├─ 次找 ../dist-electron/win-unpacked/造价通.exe
   ├─ 再次找 ../apps/desktop/dist/造价通.exe
   └─ 兜底 npm run dev:electron (开发期)
```

UI:
- 560×380 像素的小窗口,带 4 步进度条 + 实时日志框
- 4 步完成后启用「打开造价通」按钮
- 失败时弹错误对话框

## 四、 构建线上 start.exe

线上构建服务器执行:

```bash
# Linux/Mac 交叉编译 Windows EXE (推荐,无 Windows 依赖)
cd launcher
bash build.sh
# 产出 dist/start.exe (~5 MB 单文件)

# 或 Windows 本地 (如有 Go 环境)
build.bat
# 产出 dist/start.exe
```

构建脚本会:
1. 装 Go 1.21+
2. `go mod tidy`
3. `go build -ldflags="-s -w -H windowsgui" -o dist/start.exe`
   `-H windowsgui` 让 EXE 双击后不开黑色 cmd 窗口

## 五、 用户使用

1. 把 `start.exe` 与 `costpilot.exe` 放到同一目录 (推荐: `C:\Program Files\造价通\`)
2. 双击 `start.exe`
3. 等 4 步进度完成
4. 点「打开造价通」按钮,桌面 应用出现,选「AI 助手」标签页即可聊天

## 六、 配置 LobeChat 环境变量

`main.go` 默认环境变量在 `defaultEnv` map,可改:

```go
var defaultEnv = map[string]string{
    "OPENAI_API_KEY":       "sk-你的-deepseek-密钥",
    "OPENAI_PROXY_URL":     "https://api.deepseek.com/v1",
    "DEFAULT_AGENT_CONFIG": "deepseek-chat",
    "ACCESS_CODE":          "",
}
```

或运行时让用户在 LobeChat 的"设置 → 语言模型"页面里改。

## 七、 故障排查

| 现象 | 原因 | 解决 |
|---|---|---|
| 进度卡在 [1/4] 60s 后报错 | Docker Desktop 未安装/未启动 | 安装 https://www.docker.com/products/docker-desktop/ |
| [2/4] 报 `image not found` | 网络慢,首次拉 lobehub/lobe-chat:latest 失败 | 手动 `docker pull lobehub/lobe-chat:latest` 后重试 |
| [3/4] 30s 未就绪 | LobeChat 内部错误 | 命令行 `docker logs lobechat` 看 |
| [4/4] 找不到造价通.exe | costpilot.exe 没放到同目录 | 重新跑 electron-builder 打 Setup.exe |

## 八、 LobeChat 容器日常维护

```bash
docker stop lobechat                        # 停止
docker start lobechat                        # 启动
docker logs -f lobechat                      # 看日志
docker pull lobehub/lobe-chat:latest         # 升级
docker rm -f lobechat                        # 删除容器,下次 start.exe 会重建
```

## 九、 体积与依赖

| 项 | 大小 |
|---|---|
| start.exe | ~5 MB 单文件 |
| Go 运行时 | 编译进 EXE,无需用户装 |
| walk GUI 库 | 静态链接,无需 DLL |
| 反依赖 | 仅 Windows 系统 |

## 十、 协议

launcher 自身代码 MIT。包含 walk 库 (BSD-3-Clause)。
