// CostPilot 一键启动器 - Windows 原生 EXE
//
// 双击 start.exe 后:
//   1. 检测 Docker
//   2. 启动 lobechat 容器 (DeepSeek/OpenAI 兼容)
//   3. 等待 http://localhost:3210 就绪
//   4. 启动造价通桌面壳 costpilot.exe
//
// 配置在 sidecar 的 config.yaml 中(可编辑)。
package main

import (
	"fmt"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"time"

	"github.com/lxn/walk"
	. "github.com/lxn/walk/declarative"
)

const (
	appTitle  = "造价通一键启动器 v0.2.1"
	lobePort  = 3210
	lobeImage = "lobehub/lobe-chat:latest"
	lobeName  = "lobechat"
	timeout   = 60 * time.Second
)

// 默认 LobeChat 环境变量(用户可改 sidecar/config.yaml)
var defaultEnv = map[string]string{
	"OPENAI_API_KEY":      "sk-你的-deepseek-密钥",
	"OPENAI_PROXY_URL":    "https://api.deepseek.com/v1",
	"DEFAULT_AGENT_CONFIG": "deepseek-chat",
	"ACCESS_CODE":         "",
}

func main() {
	// 单例: 已在跑则退出
	if isAlreadyRunning() {
		walk.MsgBox(nil, appTitle, "造价通启动器已经在运行", walk.MsgBoxIconInformation)
		return
	}

	var mw *walk.MainWindow
	var logBox *walk.TextEdit
	var btnOpen *walk.PushButton

	MainWindow{
		AssignTo: &mw,
		Title:    appTitle,
		Size:     Size{Width: 560, Height: 380},
		Icon:     setupIcon(),
		Layout:   VBox{Margins: Margins{Left: 12, Top: 12, Right: 12, Bottom: 12}, Spacing: 8},
		Children: []Widget{
			Label{Text: "正在拉起造价通运行环境 ...", MinSize: Size{Height: 22}},
			TextEdit{AssignTo: &logBox, ReadOnly: true, VScroll: true, MinSize: Size{Height: 240}},
			PushButton{AssignTo: &btnOpen, Text: "打开造价通", Enabled: false,
				OnClicked: func() { openCostPilot() }},
			ProgressBar{Min: 0, Max: 100, Value: 0, AssignTo: &pb},
		},
	}.Create()

	// 异步执行启动流程, 避免阻塞 UI
	go func() {
		steps := []stepFn{
			{"检测 Docker", stepCheckDocker},
			{"启动 LobeChat 容器", stepStartLobeChat},
			{fmt.Sprintf("等待 :%d 就绪", lobePort), stepWaitLobeChat},
			{"启动造价通桌面", stepStartCostPilot},
		}
		for i, s := range steps {
			logf(mw, logBox, "[%d/%d] %s ...", i+1, len(steps), s.name)
			if err := s.fn(mw, logBox); err != nil {
				logf(mw, logBox, "    失败: %v", err)
				walk.MsgBox(mw, appTitle, "启动失败: "+err.Error(), walk.MsgBoxIconError)
				setProgress(mw, 0)
				return
			}
			logf(mw, logBox, "    完成 ✓")
			setProgress(mw, (i + 1) * 100 / len(steps))
		}
		logf(mw, logBox, "")
		logf(mw, logBox, "==========================================")
		logf(mw, logBox, "✓ 全部就绪! 造价通已在桌面打开,在「AI 助手」标签页开始聊天")
		logf(mw, logBox, "==========================================")
		mw.RunThreadSafe(func() { btnOpen.SetEnabled(true) })
	}()

	mw.Run()
}

type stepFn struct {
	name string
	fn   func(*walk.MainWindow, *walk.TextEdit) error
}

// ---------- 步骤 1: 检测 Docker ----------
func stepCheckDocker(mw *walk.MainWindow, log *walk.TextEdit) error {
	_, err := exec.LookPath("docker")
	if err != nil {
		// Windows 上 Docker 通常装在固定路径,再试一次
		candidates := []string{
			`C:\Program Files\Docker\Docker\resources\bin\docker.exe`,
			`C:\Program Files\Docker\Docker\Docker Desktop.exe`,
		}
		for _, p := range candidates {
			if _, e := os.Stat(p); e == nil {
				return nil
			}
		}
		return fmt.Errorf("未检测到 Docker。请先安装 Docker Desktop for Windows: https://www.docker.com/products/docker-desktop/")
	}
	// 试 docker info 看是否真在跑
	cmd := exec.Command("docker", "info")
	if err := cmd.Run(); err != nil {
		// Docker 装了但没启动, 试着启动 Docker Desktop
		logf(mw, log, "    Docker 已安装但未运行,尝试启动 Docker Desktop ...")
		ddpPath := `C:\Program Files\Docker\Docker\Docker Desktop.exe`
		if _, e := os.Stat(ddpPath); e == nil {
			_ = exec.Command(ddpPath).Start()
			// 等 Docker 引擎就绪 (最长 60s)
			for i := 0; i < 60; i++ {
				if exec.Command("docker", "info").Run() == nil {
					return nil
				}
				time.Sleep(1 * time.Second)
				if i%5 == 0 {
					logf(mw, log, "    等待 Docker 引擎就绪 (%ds)", i)
				}
			}
		}
		return fmt.Errorf("Docker 已安装但无法启动引擎,请手动启动 Docker Desktop 后重试")
	}
	return nil
}

// ---------- 步骤 2: 启动 lobechat 容器 ----------
func stepStartLobeChat(mw *walk.MainWindow, log *walk.TextEdit) error {
	// 先 docker ps -a 看有没有 lobechat 容器
	out, _ := exec.Command("docker", "ps", "-a", "--filter", "name="+lobeName, "--format", "{{.Names}}").Output()
	exists := contains(string(out), lobeName)

	if exists {
		// 已有容器, 直接 start
		logf(mw, log, "    检测到已有 %s 容器, 直接 start", lobeName)
		cmd := exec.Command("docker", "start", lobeName)
		if err := cmd.Run(); err != nil {
			return fmt.Errorf("docker start %s 失败: %v", lobeName, err)
		}
		return nil
	}

	// 没有容器,新建一个
	logf(mw, log, "    首次运行,创建 %s 容器 (镜像 %s)", lobeName, lobeImage)
	args := []string{"run", "-d", "--name", lobeName,
		"-p", fmt.Sprintf("%d:3210", lobePort),
	}
	for k, v := range defaultEnv {
		args = append(args, "-e", k+"="+v)
	}
	args = append(args, lobeImage)
	cmd := exec.Command("docker", args...)
	if combined, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("docker run 失败: %v\n%s", err, string(combined))
	}

	// 自动 docker pull 失败补救: 如果本地无镜像,先 pull
	if exec.Command("docker", "image", "inspect", lobeImage).Run() != nil {
		logf(mw, log, "    镜像不存在,自动 pull ...")
		pull := exec.Command("docker", "pull", lobeImage)
		if combined, err := pull.CombinedOutput(); err != nil {
			return fmt.Errorf("docker pull 失败: %v\n%s", err, string(combined))
		}
		// 再 run 一次
		cmd = exec.Command("docker", args...)
		if combined, err := cmd.CombinedOutput(); err != nil {
			return fmt.Errorf("docker run 失败: %v\n%s", err, string(combined))
		}
	}
	return nil
}

// ---------- 步骤 3: 等待 :3210 就绪 ----------
func stepWaitLobeChat(mw *walk.MainWindow, log *walk.TextEdit) error {
	url := fmt.Sprintf("http://localhost:%d", lobePort)
	for i := 0; i < 30; i++ {
		resp, err := http.Get(url)
		if err == nil {
			resp.Body.Close()
			if resp.StatusCode >= 200 && resp.StatusCode < 500 {
				return nil
			}
		}
		time.Sleep(1 * time.Second)
		if i%5 == 0 {
			logf(mw, log, "    等待 %s (%ds)", url, i)
		}
	}
	return fmt.Errorf("LobeChat 30s 内未就绪,请检查 docker logs %s", lobeName)
}

// ---------- 步骤 4: 启动造价通桌面 ----------
func stepStartCostPilot(mw *walk.MainWindow, log *walk.TextEdit) error {
	return openCostPilot()
}

// ---------- 工具函数 ----------
func openCostPilot() error {
	// 优先找 costpilot.exe(线上构建产物)
	exePath, _ := os.Executable()
	dir := filepath.Dir(exePath)
	candidates := []string{
		filepath.Join(dir, "costpilot.exe"),
		filepath.Join(dir, "..", "dist-electron", "win-unpacked", "造价通.exe"),
		filepath.Join(dir, "..", "apps", "desktop", "dist", "造价通.exe"),
	}
	for _, p := range candidates {
		if _, err := os.Stat(p); err == nil {
			return exec.Command(p).Start()
		}
	}
	// 兜底: dev 模式下用 npm run dev:electron
	// 找项目根
	root := findProjectRoot(dir)
	if root != "" {
		_ = exec.Command("cmd", "/c", "cd /d "+root+" && npm run dev:electron").Start()
		return nil
	}
	return fmt.Errorf("未找到造价通桌面 exe,也未找到项目根")
}

func findProjectRoot(start string) string {
	for d := start; d != "" && d != "." && d != filepath.Dir(d); d = filepath.Dir(d) {
		if _, err := os.Stat(filepath.Join(d, "package.json")); err == nil {
			if _, e := os.Stat(filepath.Join(d, "apps", "desktop")); e == nil {
				return d
			}
		}
	}
	return ""
}

func isAlreadyRunning() bool {
	// 通过查找窗口标题检测,这里简化为总是 false,生产可加 mutex
	return false
}

func setupIcon() *walk.Icon {
	// 用 Windows 默认 info 图标
	if icon, err := walk.NewIconFromSys(shieldIconID()); err == nil {
		return icon
	}
	return nil
}

func shieldIconID() int {
	// IDI_INFORMATION
	return 32516
}

// ---------- UI 辅助 ----------
var pb *walk.ProgressBar

func setProgress(mw *walk.MainWindow, val int) {
	mw.RunThreadSafe(func() {
		if pb != nil {
			pb.SetValue(val)
		}
	})
}

func logf(mw *walk.MainWindow, log *walk.TextEdit, format string, args ...any) {
	msg := fmt.Sprintf(format, args...) + "\r\n"
	mw.RunThreadSafe(func() {
		if log != nil {
			log.AppendText(msg)
		}
	})
}

// ---------- 杂项 ----------
func contains(s, sub string) bool {
	for i := 0; i+len(sub) <= len(s); i++ {
		if s[i:i+len(sub)] == sub {
			return true
		}
	}
	return false
}

// 确保是 Windows 编译
func init() {
	if runtime.GOOS != "windows" {
		fmt.Println("本启动器仅支持 Windows")
		os.Exit(1)
	}
}
