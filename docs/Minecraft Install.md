# Minecraft 安装与当前测试记录

本文记录当前阶段的测试结论，以及 Windows 环境下安装 Minecraft Java Edition 的推荐步骤。

## 1. 当前阶段测试结论

当前项目还没有接入 `mineflayer`，已经完成的是基于屏幕截图和键鼠模拟的 Python MVP：

```text
Minecraft 画面截图
  -> Qwen VLM 视觉理解
  -> JSON 动作决策
  -> dry-run 或 pyautogui 执行动作
```

当前可测试能力：

- `pytest` 单元测试：验证决策解析、fallback、dry-run 执行器。
- `test_qwen_llm.py`：验证 DashScope 普通 LLM 调用。
- `test_qwen_vlm.py`：验证 DashScope VLM 图片理解调用。
- `python -m src.main --no-vlm --once`：不调用 VLM，验证截图、fallback 决策和日志闭环。
- `python -m src.main --mode dry-run --steps 5`：调用 VLM，但不真实控制游戏。
- `python -m src.main --mode pyautogui --steps 3`：真实控制 Minecraft 窗口，进行小步数验证。

当前阶段测试重点：

1. 截图区域是否准确覆盖 Minecraft 窗口。
2. `runs/screenshots/` 是否生成 Minecraft 画面截图。
3. `runs/logs/agent.log` 是否记录观察、VLM 原始输出、动作决策。
4. VLM 输出是否能被解析为允许动作。
5. `pyautogui` 模式下 Minecraft 是否处于前台并获得焦点。

## 2. 推荐 Minecraft 版本

后续计划接入 `mineflayer`，推荐安装：

```text
Minecraft Java Edition 1.20.1
```

推荐理由：

- `mineflayer` 生态支持较稳定。
- 适合后续接入 `mineflayer-pathfinder` 和 `prismarine-viewer`。
- 比最新版本更少遇到协议兼容问题。
- 对 Demo 来说足够新，也容易复现。

不建议当前阶段使用：

- Bedrock 版。
- Snapshot 快照版。
- Forge / Fabric 模组环境。
- 光影、高清材质包。
- 最新 `1.21.x` 小版本。

## 3. Windows 安装 Java 17

Minecraft `1.20.1` 和后续 Paper Server 推荐使用 Java 17。

PowerShell 安装：

```powershell
winget install EclipseAdoptium.Temurin.17.JDK
```

验证：

```powershell
java -version
```

看到 `17.x.x` 即可。

## 4. 推荐使用 Prism Launcher

相比官方 Minecraft Launcher，Prism Launcher 更适合本项目：

- 多版本实例管理方便。
- Java 路径和启动参数更可控。
- 日志更清楚，方便调试。
- 后续如果需要测试不同版本更方便。

官网下载：

```text
https://prismlauncher.org/
```

安装步骤：

1. 下载 Windows 版本 Prism Launcher。
2. 安装并启动。
3. 进入 `设置 -> 账号`。
4. 添加微软账号并登录。
5. 点击 `添加实例`。
6. 选择 `Vanilla`。
7. Minecraft 版本选择 `1.20.1`。
8. 实例名称建议填写：

```text
minecraft-1.20.1-vlm-demo
```

9. 启动实例，等待客户端下载完成。
10. 成功进入 Minecraft 主菜单后，说明客户端安装完成。

## 5. 创建测试世界

进入 Minecraft 后创建本地单人世界：

```text
Singleplayer -> Create New World
```

推荐设置：

```text
World Name: vlm_test
Game Mode: Survival
Difficulty: Peaceful
Cheats: 可开可不开
Version: 1.20.1
```

建议先使用和平难度，避免测试时被怪物打断。

## 6. 游戏画面设置

为了让 VLM 更容易识别画面，建议使用原版视觉效果：

```text
FOV: 70
Brightness: Bright
Render Distance: 8~12
GUI Scale: 2 或 3
Clouds: Off
Particles: Minimal
Fullscreen: Off
Window Size: 1280x720 或 1600x900
```

建议测试环境：

- 白天。
- 草地、森林、平原等明亮场景。
- 附近有树。
- 不开光影。
- 不使用额外材质包。
- 保持默认键位。

当前代码用到的默认控制：

```text
W: 前进
S: 后退
Space: 跳跃
鼠标移动: 转向
鼠标左键: 挖掘 / 攻击
```

## 7. 当前 Python Agent 测试流程

进入项目目录：

```powershell
cd D:\vla\vlm-minecraft-agent
conda activate vlm_minecraft
```

安装依赖：

```powershell
python -m pip install -r requirements.txt
```

运行单元测试：

```powershell
pytest -q
```

不调用 VLM，验证本地闭环：

```powershell
python -m src.main --no-vlm --once
```

测试 Qwen LLM：

```powershell
python test_qwen_llm.py
```

测试 Qwen VLM：

```powershell
python test_qwen_vlm.py
```

打开 Minecraft，并把窗口放在屏幕左上角后，测试 dry-run：

```powershell
python -m src.main --mode dry-run --steps 5 --interval 2 --region 0,0,1280,760
```

确认截图和 VLM 决策都正常后，再小步测试真实控制：

```powershell
python -m src.main --mode pyautogui --steps 3 --interval 2 --region 0,0,1280,760
```

`pyautogui` 模式注意：

- Minecraft 必须在前台。
- 鼠标焦点必须在游戏窗口内。
- 第一次只跑少量 steps。
- 鼠标快速移动到屏幕左上角可触发 failsafe 中断。

## 8. 截图区域说明

当前项目通过 `mss` 截屏，默认截主屏幕。如果 IDE 在前台，可能会截到 IDE 页面。

建议使用 `--region` 或 `.env` 中的 `CAPTURE_REGION` 固定 Minecraft 窗口区域：

```text
CAPTURE_REGION=0,0,1280,760
```

格式含义：

```text
left,top,width,height
```

即从屏幕左上角 `(left, top)` 开始，截取指定宽高区域。

## 9. 后续接入 mineflayer 的准备

当前阶段不需要 `mineflayer`。后续接入时建议额外准备：

```text
Node.js 20 LTS
Paper Server 1.20.1
mineflayer
mineflayer-pathfinder
prismarine-viewer
```

后续推荐架构：

```text
VLM 负责观察和高层决策
mineflayer 负责稳定执行移动、寻路、挖掘、背包和合成
```

这样比纯 `pyautogui` 更稳定，也更适合后续 Demo。