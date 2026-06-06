# VLM Minecraft Agent（分层重构版）

本项目已从“截图 + 低层动作逐步控制”重构为**分层架构**：
- **Python 规划层**：截图 + VLM 规划 + 计划更新。
- **Node 执行层**：mineflayer 闭环技能执行（`/skill`）。
- **状态记忆层**：外部 symbolic world state（`/state` + Python memory）。

## 架构与主链路

- 规划输出：`plan_update + next_skill`
- 执行输入：`POST /skill`
- 执行反馈：`success/reason/diff`
- 状态读取：`GET /state`

关键设计文档：`docs/架构重构设计方案.md`

## 环境准备

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
```

Minecraft 连接相关（Node 执行层）：

```text
MC_HOST=localhost
MC_PORT=25565
MC_USERNAME=vlm_agent
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
conda run -n vlm_minecraft python -m src.main --steps 5
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

## 当前能力

- 已打通闭环：`collect_block`（采木头）
- 已提供最小生存技能：`goto`、`explore`、`craft`、`attack_nearest`、`flee`、`eat`
- 规划层为事件驱动：每次技能执行后再规划，而非固定高频循环

## 测试

```powershell
conda run -n vlm_minecraft pytest -q
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