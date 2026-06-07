# 基于 VLM 的 Minecraft AI Agent（方案一：纯视觉 + 键鼠模拟）

> 本分支（`main`）实现的是项目的 **第一代方案（方案一）**：基于「**纯视觉理解 + 同步键鼠模拟控制**」的 Minecraft 生存智能体。
>
> 它使用 `mss` 截取游戏画面，直接送入多模态视觉语言模型（VLM，默认通义千问 Qwen-VL），由模型逐帧输出底层动作（如前进、转向、挖掘），再用 `pyautogui` 模拟键鼠执行。
>
> **设计取舍**：方案一最大的优点是 **跨游戏通用性极高、结构简单**（完全不依赖游戏 Mod / 协议），但在 Minecraft 实战中存在 VLM 高延迟、盲操作无成败判定、几何控制精度差等痛点。针对这些问题，项目在 **`hierarchical_control` 分支**重构出了 **方案二（VLM 规划 + Mineflayer 闭环分层控制）**。

---

## 一、核心原理

方案一是一个经典的 **Observe → Think → Act（观察—思考—执行）** 同步循环：

```
        ┌─────────────────────────────┐
        │  Minecraft 客户端（游戏画面）  │
        └──────────────┬──────────────┘
                       │ 1. 截图 (mss)
                       ▼
        ┌─────────────────────────────┐
        │  VLM（Qwen-VL，逐帧单步决策）  │
        │  输入: 截图 + 长期目标 + 历史   │
        │  输出: 结构化 JSON 动作决策     │
        └──────────────┬──────────────┘
                       │ 2. 解析为 ActionCommand
                       ▼
        ┌─────────────────────────────┐
        │  pyautogui（键鼠模拟执行）      │
        │  move/turn/mine/jump/escape   │
        └──────────────┬──────────────┘
                       │ 3. 作用于游戏，进入下一帧
                       ▼
                    （回到截图）
```

- **观察**：`ScreenCapture` 用 `mss` 截全屏或指定区域，存到 `runs/screenshots/`。
- **思考**：`DecisionPlanner` 把截图 + `AgentState`（长期目标、最近 5 步历史）发给 VLM，模型返回严格 JSON（场景理解 `scene` + 短期目标 `goal` + 动作 `action` + 置信度）。解析层带有 JSON 抽取、字段归一化与异常 `fallback`（退化为 `look_around`）的容错。
- **执行**：`ActionExecutor` 将动作转为键鼠操作。`turn/look_around` 通过「角速度 × 时长 → 角度 → 鼠标相对位移计数」映射，尽量缓解 VLM 难以精确控角的问题。

---

## 二、运行环境要求

| 项目 | 要求 / 推荐 |
|------|------------|
| 操作系统 | **Windows 11**（推荐，与开发/测试环境一致；`pyautogui` 真实控制依赖前台窗口聚焦） |
| Python | **3.11**（3.10+ 即可） |
| 包管理 | Conda（推荐，环境名示例 `vlm_minecraft`）或 venv |
| Minecraft | **Java 版 1.20.1**（其它版本理论可用，方案一不依赖具体版本/Mod，只要画面能被截取、窗口能被键鼠控制即可） |
| VLM | 阿里云百炼 DashScope（OpenAI 兼容接口），默认 `qwen-3.6-flash`，需要 `DASHSCOPE_API_KEY` |

### Python 依赖（见 [`requirements.txt`](requirements.txt)）

| 依赖 | 版本 | 用途 |
|------|------|------|
| `openai` | `>=1.30.0` | 调用 DashScope OpenAI 兼容接口 |
| `python-dotenv` | `>=1.0.1` | 读取 `.env` 配置 |
| `pydantic` | `>=2.7.0` | 配置与决策数据模型校验 |
| `mss` | `>=9.0.1` | 屏幕截图 |
| `Pillow` | `>=10.3.0` | 图像保存 |
| `pyautogui` | `>=0.9.54` | 键鼠模拟执行 |
| `tenacity` | `>=8.3.0` | VLM 调用失败指数退避重试 |
| `pytest` | `>=8.2.0` | 单元测试 |

---

## 三、目录结构

```text
vlm-minecraft-agent/
├── src/
│   ├── main.py            # 入口：解析参数、装配组件、启动循环
│   ├── agent.py           # Observe-Think-Act 主循环、动作时长适配、短期记忆
│   ├── screen_capture.py  # mss 截图（全屏 / 指定区域）
│   ├── planner.py         # 组织 prompt、调用 VLM、解析 + 归一化 + 容错
│   ├── vlm_client.py      # Qwen-VL 客户端（图像 base64 + Chat 接口 + 重试）
│   ├── prompts.py         # System / User Prompt 模板
│   ├── models.py          # 动作集、决策/状态等 pydantic 数据模型
│   ├── actions.py         # 动作执行器（dry-run / pyautogui）
│   ├── config.py          # .env 加载与 Settings
│   └── model_config.py    # 多模型配置加载
├── config/model_configs.json  # 各 VLM 模型名 / base_url / 采样参数
├── scripts/run_agent.ps1      # Windows 一键运行脚本
├── tests/                     # 单元测试
├── requirements.txt
├── .env.example
└── report.md                  # 代码报告（方案一/二设计与对比）
```

---

## 四、安装

```powershell
# 1) 克隆并进入项目
git clone https://github.com/scofiedluo/vlm-minecraft-agent.git
cd vlm-minecraft-agent

# 2) 创建并激活 Conda 环境（推荐）
conda create -n vlm_minecraft python=3.11 -y
conda activate vlm_minecraft

# 3) 安装依赖
python -m pip install -r requirements.txt
```

---

## 五、配置

复制环境模板并填写：

```powershell
Copy-Item .env.example .env
```

`.env` 关键项说明：

| 变量 | 说明 | 默认 |
|------|------|------|
| `DASHSCOPE_API_KEY` | 百炼 API Key（**必填**，请勿提交真实密钥） | `sk-your-api-key` |
| `VLM_MODEL` | 模型配置键，见 `config/model_configs.json` | `qwen-vl-plus` |
| `MODEL_CONFIG_FILE` | 自定义模型配置文件路径（可选） | `config/model_configs.json` |
| `AGENT_OBJECTIVE` | Agent 长期目标，会写入 prompt | `收集木头并保证生存` |
| `ACTION_MODE` | `dry-run`（只打印动作）/ `pyautogui`（真实控制键鼠） | `dry-run` |
| `CAPTURE_REGION` | 截图区域 `left,top,width,height`，留空为全屏 | 空（全屏） |
| `LOOP_INTERVAL` | 每步之间的间隔（秒） | `2.0` |
| `MAX_STEPS` | 最大步数 | `5` |
| `SCREENSHOT_DIR` / `LOG_DIR` | 截图与日志输出目录 | `runs/screenshots`、`runs/logs` |

可用模型见 `config/model_configs.json`，例如 `qwen-vl-plus`、`qwen-vl-max`、`qwen3-vl-flash`、`qwen3-vl-plus` 等；切换模型只需改 `VLM_MODEL`。

---

## 六、运行

### 1. 先用 dry-run 验证链路（不会操作键鼠，安全）

`dry-run` 模式只截图、调用 VLM 并把决策打印到控制台/日志，不会真正控制游戏，适合先确认 API、截图、解析全链路是否正常。

```powershell
# 直接运行（默认 dry-run）
python -m src.main --steps 5

# 仅跑一步
python -m src.main --once

# 不调用 VLM，仅走 fallback（自检代码流程）
python -m src.main --no-vlm
```

### 2. 真实控制游戏（pyautogui）

1. 打开 Minecraft，进入一个生存世界，确保 **游戏窗口处于前台且未被遮挡**。
2. 建议先用 `CAPTURE_REGION` 把截图区域对齐到游戏窗口（例如游戏放在主屏左上角、分辨率 `1280x720`）。
3. 运行：

```powershell
python -m src.main --mode pyautogui --steps 50 --interval 2.0 --region 0,0,1280,720
```

> **安全提示**：`pyautogui` 启用了 FailSafe——把鼠标快速甩到屏幕左上角即可紧急中止程序。

### 3. Windows 一键脚本

```powershell
# 默认 dry-run，5 步
.\scripts\run_agent.ps1

# 真实控制、10 步、仅跑一步等
.\scripts\run_agent.ps1 -Mode pyautogui -Steps 10
.\scripts\run_agent.ps1 -Once
```

### 命令行参数

| 参数 | 说明 |
|------|------|
| `--mode {dry-run,pyautogui}` | 动作执行模式（覆盖 `.env`） |
| `--steps N` | 最大步数 |
| `--interval S` | 每步间隔秒数 |
| `--region l,t,w,h` | 截图区域 |
| `--objective "..."` | 覆盖长期目标 |
| `--once` | 只执行一步 |
| `--no-vlm` | 跳过 VLM，使用 fallback 决策 |

运行产物：截图存于 `runs/screenshots/`，日志存于 `runs/logs/agent.log`（含 `[OBSERVE]` / `[DECISION]` / 动作执行记录）。

---

## 七、动作空间

VLM 只能从以下白名单中选择一个动作（`src/models.py`），动作 `duration` 单位为秒，范围 `0.1–6.0`：

| 动作 | 含义 |
|------|------|
| `look_around` | 左右扫视观察环境 |
| `move_forward` / `move_backward` | 短暂前进 / 后退 |
| `turn_left` / `turn_right` | 向左 / 向右转动视角（`duration` 越大转角越大） |
| `jump` | 跳跃一次 |
| `mine_or_attack` | 按住左键挖掘正前方方块或攻击威胁 |
| `escape` | 后退并转向，用于躲避危险 |
| `idle` | 短暂停留 |

---

## 八、键鼠标定与调参

由于 VLM 难以精确控角，转向通过「**角速度 × 时长 → 角度 → 鼠标相对计数**」映射实现。如果发现转向过大/过小，可在 `src/actions.py` 的 `PyAutoGUIActionExecutor` 中调整：

- `counts_per_degree`：每度对应的鼠标移动计数（与系统鼠标灵敏度强相关，最需要标定）。
- `turn_speed_deg_per_sec` / `look_sweep_deg_per_sec`：转向 / 扫视的角速度。

在 Windows 上转向使用 `user32.mouse_event` 发送相对移动，原始输入更贴近游戏视角控制；其他平台回退到 `pyautogui.moveRel`。

---

## 九、测试

```powershell
python -m pytest tests/ -q
```

---

## 十、已知局限（→ 方案二）

方案一在真实 Minecraft 生存中存在以下难以靠 Prompt 调优解决的痛点）：

1. **VLM 高延迟（1~7s）** 导致逐帧同步动作破碎、反复空挖，token 成本高。
2. **盲操作无反馈**：`pyautogui` 单向发指令，无法判定动作成败与重试。
3. **几何控制精度差**：难以精确转向到目标方块。
4. **隐性状态缺失**：截图看不到精确背包/血量/饱食度。
5. **缺乏毫秒级安全反射**：等待 VLM 推理期间易被怪物围殴致死。

如需打通「采木 → 木板 → 工作台 → 木镐 → 采石 → 狩猎」完整生存链路，请切换到分层控制方案二：

```powershell
git checkout hierarchical_control
```
