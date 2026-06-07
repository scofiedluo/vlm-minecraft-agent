# VLM Minecraft Agent（双层控制）

本项目已从“截图 + 低层动作逐步控制”重构为**分层架构**：
- **Python 规划层**：截图 + VLM 规划 + 计划更新。
- **Node 执行层**：mineflayer 闭环技能执行（`/skill`）。
- **状态记忆层**：外部 symbolic world state（`/state` + Python memory）。

## 架构与主链路

- 规划输出：`plan_update + next_skill`
- 执行输入：`POST /skill`
- 执行反馈：`success/reason/diff`
- 状态读取：`GET /state`

## 环境准备

### Minecraft及mineflayer相关依赖安装
详细见[docs/minecraft.md]

### Python

```powershell
conda activate vlm_minecraft
conda run -n vlm_minecraft python -m pip install -r requirements.txt
```

### Node

```powershell
cd bot
npm install
```

## 配置

复制并编辑 `.env`：

```powershell
Copy-Item .env.example .env
```

建议最小配置：

```text
DASHSCOPE_API_KEY=sk-xxxx
VLM_MODEL=qwen3-vl-flash
MODEL_CONFIG_FILE=config/model_configs.json
SKILL_SERVER_URL=http://127.0.0.1:3000
SKILL_TIMEOUT_MS=30000
PLANNER_FAIL_RETRY_THRESHOLD=2
INITIAL_PLAN_JSON=[{"id":"1","goal":"先收集2个木头","status":"in_progress","skill":"collect_block","args":{"block":"oak_log","count":2}},{"id":"2","goal":"合成木板和工作台","status":"pending"}]
```

Minecraft 连接相关（Node 执行层）：

```text
MC_HOST=localhost
MC_PORT=25565
MC_USERNAME=vlm_agent_bot_01
MC_VERSION=1.20.1
SKILL_SERVER_HOST=127.0.0.1
SKILL_SERVER_PORT=3000

# prismarine-viewer 观测（方式二）
BOT_VIEWER_ENABLED=true
BOT_VIEWER_PORT=3007
BOT_VIEWER_FIRST_PERSON=true
```


## 运行方式

### 方式一：分别启动

1) 启动 Node 技能服务：

```powershell
cd bot
npm start
```

启动成功后会看到类似日志：

```text
[viewer] ready: http://127.0.0.1:3007 (firstPerson=true)
```

在浏览器打开该地址即可观察 `vlm_agent` 的第一人称视角。

若提示缺少 `canvas`（例如 `Cannot find module 'canvas'`），可先关闭 viewer 不影响主链路：

```powershell
$env:BOT_VIEWER_ENABLED="false"
```

或尝试安装：

```powershell
cd bot
npm i canvas
```


2) 启动 Python 规划代理：


```powershell
conda run --no-capture-output -n vlm_minecraft python -u -m src.main --steps 5
```

> 不要直接用系统 `python -m src.main`，否则可能因缺少 `pydantic` 等依赖出现“没反应/直接报错”。


### 方式二：一键启动（Windows）

```powershell
.\scripts\run_all.ps1 -PythonEnv vlm_minecraft -Steps 5
```

仅走 fallback（不调用 VLM）：

```powershell
.\scripts\run_all.ps1 -NoVLM
```

## 推荐联调顺序（避免 VLM 截图错误）

> 目标：让 `vlm_agent_bot_01` 执行、`vlm_agent` 客户端观察，并确保 VLM 看到的是 Minecraft 画面而不是 IDE/终端。

- **步骤 1（终端A）**：启动 Minecraft 服务端（Paper/Vanilla），保持窗口不关闭。
- **步骤 2（终端B）**：启动 Node 执行层并固定 bot 名称。

```powershell
cd d:/vla/vlm-minecraft-agent/bot
$env:MC_USERNAME="vlm_agent_bot_01"
$env:BOT_VIEWER_ENABLED="false"
npm start
```

- **步骤 3（Prism 客户端）**：用你的玩家账号（例如 `vlm_agent`）加入 `localhost:25565`。
- **步骤 4（终端C）**：启动 Python 规划层（VLM 主循环）。

```powershell
cd d:/vla/vlm-minecraft-agent
conda run --no-capture-output -n vlm_minecraft python -u -m src.main --steps 50 --region 0,0,1280,760
```

- **步骤 5（旁观/跟拍）**：客户端观察 `vlm_agent_bot_01` 行为。
  - 有权限时：`/tp <你的ID> vlm_agent_bot_01`，然后 `/gamemode spectator` 进行旁观。
  - 没权限时：在服务端控制台执行 `op <你的ID>` 后再使用上面命令。

### 截图命中检查（非常关键）

- **窗口位置**：Minecraft 客户端放在主屏左上角，分辨率与 `CAPTURE_REGION` 一致（例如 `1280x760`）。
- **前台状态**：跑 VLM 时不要让 IDE/终端挡住该区域。
- **结果核对**：检查 `runs/screenshots/` 最新图片，必须是 Minecraft 画面。
- **日志核对**：`runs/logs/agent.log` 中应持续出现 `[PLAN]` 与 `[SKILL]`。

## 当前能力

- **全自动合成木镐闭环**：完全打通了从「采集原木」->「合成木板」->「合成工作台并放置」->「补齐木棍等前置原料」->「在工作台上合成木镐」的复杂多步逻辑，具有极高的合成容错率。
- **环境自保反射（Safety Reflex）**：在采集或合成途中遭遇怪围攻、或者血量过低时，bot 能瞬时中断当前技能并自动执行 `flee` 撤跑自保，保障生存。
- **事件驱动高层规划**：规划层仅在“动作结束/状态需要变更/失败重试”时按需调用 VLM（支持快速决策路径），无需高频空转，大幅度降低了 API Token 成本和延迟。
- **精准的生物类型判定**：正确区分敌对生物（僵尸/骷髅等）与被动友好生物（猪/牛/羊等），避免误报危险或无故攻击家畜。
- **丰富的底闭环技能集**：集成 `collect_block`、`goto`、`explore`、`craft`、`attack_nearest`、`flee`、`eat`（饱食度满自动跳过）。


## 测试

```powershell
conda run -n vlm_minecraft python -m pytest tests/test_agent.py -q
```

## 目录变化（重构后）

```text
bot/
  server.js
  botFactory.js
  state.js
  safety.js
  skills/
    index.js
    collectBlock.js
    navigate.js
    craft.js
    combat.js

src/
  main.py
  agent.py
  planner.py
  prompts.py
  skill_client.py
  world_state.py
  plan.py
  models.py
  config.py
```

## 常用调试命令（PowerShell）

如果需要避免与客户端同名导致互踢，可临时指定 bot 名称：

```powershell
$env:MC_USERNAME="vlm_agent_bot_01"
cd d:/vla/vlm-minecraft-agent/bot
npm start
```