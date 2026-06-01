# Minecraft AI 相关工作文献调研

本文档整理了与基于 VLM 的 Minecraft AI 相关的代表性工作，包括环境平台、Agent 框架和端到端模型。

---

## 1. MineDojo

**论文**: *MineDojo: Building Open-Ended Embodied Agents with Internet-Scale Knowledge*  
**发表**: NeurIPS 2022  
**机构**: NVIDIA, Caltech, Stanford, etc.  
**开源**: https://github.com/MineDojo/MineDojo

### 1.1 主要思想

MineDojo 是一个**开放式的 Minecraft 智能体开发平台**，核心目标是解决传统 RL 环境中任务单一、知识受限的问题。它利用互联网规模的多元数据（Wiki、YouTube、Reddit）来构建丰富的任务空间和知识库。

**关键创新**:
- 提出数千种多样化的程序化任务（programmatic tasks）
- 将 Minecraft Wiki、教程视频、论坛讨论等多模态数据整合为外部知识源
- 支持自由形式（free-form）的语言指令和奖励函数定义

### 1.2 Agent 框架

MineDojo 本身**不是 Agent**，而是**环境和基准测试平台**：

```
┌─────────────────────────────────────────┐
│           MineDojo Platform             │
├─────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │  Diverse │  │ Internet │  │ Unified│ │
│  │  Tasks   │  │ Knowledge│  │  API   │ │
│  └──────────┘  └──────────┘  └────────┘ │
└─────────────────────────────────────────┘
                   │
         ┌─────────┴─────────┐
         ▼                   ▼
    ┌─────────┐         ┌─────────┐
    │   RL    │         │  VLM    │
    │  Agent  │         │  Agent  │
    └─────────┘         └─────────┘
```

**组件说明**:
- **任务空间**: 3000+ 程序化任务，涵盖生存、建造、战斗等
- **知识库**: 7000+ Wiki 页面、300k+ 视频转录、6M+ Reddit 帖子
- **统一接口**: 标准化的观察（RGB + 状态）和动作空间

### 1.3 所使用的模型

| 类型 | 模型/方法 | 说明 |
|------|----------|------|
| 基准模型 | RL (PPO) | 基础强化学习智能体 |
| 多模态 | CLIP | 用于视频-文本对齐 |
| 知识检索 | Dense Passage Retrieval | 从 Wiki 检索相关知识 |

**重要说明**: MineDojo **不是 VLM-based**，而是为后续 VLM Agent 提供了环境基础。

---

## 2. Voyager

**论文**: *Voyager: An Open-Ended Embodied Agent with Large Language Models*  
**发表**: arXiv 2023  
**机构**: Microsoft Research, Stanford, etc.  
**开源**: https://github.com/MineDojo/Voyager

### 2.1 主要思想

Voyager 是一个**终身学习的 Minecraft Agent**，首次将大型语言模型（LLM）的能力深度整合到开放世界游戏中。其核心思想是：**让 LLM 生成可执行代码（skills）来解决任务，并不断积累这些技能**。

**三大核心机制**:
1. **自动课程（Automatic Curriculum）**: 根据当前状态提出 progressively difficult 的探索目标
2. **技能库（Skill Library）**: 存储和检索可复用的代码技能（如 `craft_planks`, `fight_zombie`）
3. **迭代提示机制（Iterative Prompting）**: 通过代码执行反馈自我修正

### 2.2 Agent 框架

```
┌─────────────────────────────────────────────────────────┐
│                      Voyager Agent                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────┐     ┌─────────────────┐            │
│  │ Automatic       │───▶│ Skill Library   │            │
│  │ Curriculum      │     │ (Code Skills)   │            │
│  │ (GPT-4)         │◀───│                 │            │
│  └─────────────────┘     └─────────────────┘            │
│          │                      ▲                       │
│          ▼                      │                       │
│  ┌─────────────────┐     ┌─────────────────┐            │
│  │ Code Generation │───▶│ Iterative       │            │
│  │ (GPT-4)         │     │ Prompting       │            │
│  └─────────────────┘     └─────────────────┘            │
│          │                                              │
│          ▼                                              │
│  ┌─────────────────────────────────────────┐            │
│  │         Minecraft Environment           │            │
│  │         (via Mineflayer API)            │            │
│  └─────────────────────────────────────────┘            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**工作流程**:
1. **课程模块**提出当前要达成的目标（如"获得铁锭"）
2. **代码生成模块**编写实现该目标的 Python 代码
3. **技能库存储**成功的代码片段供将来复用
4. **执行失败时**，根据错误信息迭代修正代码

### 2.3 所使用的模型

| 模块 | 模型 | 作用 |
|------|------|------|
| 课程生成 | GPT-4 | 提出探索目标 |
| 代码生成 | GPT-4 | 生成可执行技能代码 |
| 视觉感知 | CLIP | 将游戏画面与文本描述对齐 |
| 动作执行 | Mineflayer API | 实际控制 Minecraft |

**技能表示示例**:
```python
# Skill: craft_crafting_table
async def craft_crafting_table(bot):
    """Craft a crafting table from planks"""
    await bot.craft_item('crafting_table', count=1)
    return True
```

---

## 3. AgentStudio

**论文**: *AgentStudio: A Toolkit for Building General Virtual Agents*  
**发表**: ICLR 2024  
**机构**: University of Illinois Urbana-Champaign, etc.  
**开源**: https://github.com/computer-agents/AgentStudio

### 3.1 主要思想

AgentStudio 是一个**通用的 GUI Agent 开发工具包**，支持包括 Minecraft 在内的多种虚拟环境。其核心思想是**统一的观察-动作抽象**，让同一个 VLM Agent 可以在不同环境中工作。

**设计目标**:
- **通用性**: 一套代码支持 Web、桌面应用、游戏（Minecraft）
- **可扩展性**: 易于添加新环境和任务
- **可复现性**: 标准化评估和基准测试

### 3.2 Agent 框架

```
┌─────────────────────────────────────────────────────────┐
│                   AgentStudio Framework                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │              Unified Interface                  │    │
│  │  ┌─────────┐  ┌─────────┐   ┌─────────────────┐ │    │
│  │  │ Action  │  │Observation│ │  Task Config    │ │    │
│  │  │ Space   │  │ Encoder  │  │                 │ │    │
│  │  └─────────┘  └─────────┘   └─────────────────┘ │    │
│  └─────────────────────────────────────────────────┘    │
│                          │                              │
│          ┌───────────────┼───────────────┐              │
│          ▼               ▼               ▼              │
│    ┌──────────┐    ┌──────────┐    ┌──────────┐         │
│    │   Web    │    │ Desktop  │    │Minecraft │         │
│    │  Env     │    │   Env    │    │   Env    │         │
│    └──────────┘    └──────────┘    └──────────┘         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Observation 格式**:
```python
{
    "screenshot": np.array(...),  # RGB 截图
    "accessibility_tree": {...},   # UI 元素层次结构（桌面/Web）
    "status": {...}                # 环境特定状态（如生命值）
}
```

**Action Space**:
- `click(x, y)`: 鼠标点击
- `type(text)`: 键盘输入
- `hotkey(keys)`: 快捷键
- `execute(code)`: 执行代码（Minecraft 特有）

### 3.3 所使用的模型

| 类型 | 模型 | 说明 |
|------|------|------|
| VLM | GPT-4V | 主决策模型 |
| VLM | Claude 3 | 备选模型 |
| VLM | Qwen-VL | 开源备选 |
| 规划 | 各种 LLM | 高层任务分解 |

**特点**: AgentStudio 强调**模型无关性**，用户可接入任意 VLM。

---

## 4. STEVE-1

**论文**: *STEVE-1: A Generative Model for Text-Guided Minecraft Agents*  
**发表**: ICML 2023  
**机构**: University of Alberta, etc.  
**开源**: https://github.com/Shalev-Lifshitz/STEVE-1

### 4.1 主要思想

STEVE-1 是一个**从文本指令生成 Minecraft 行为的生成式模型**。它解决了从自然语言到低层动作的端到端映射问题，无需人工设计中间表示。

**核心方法**:
1. 使用预训练的 **VPT (Video PreTraining)** 模型作为行为先验
2. 通过 **CLIP** 将文本指令与视觉观察对齐
3. 训练条件策略网络，根据指令生成动作序列

### 4.2 Agent 框架

```
┌─────────────────────────────────────────────────────────┐
│                     STEVE-1 Agent                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   Text Instruction: "Find a diamond"                    │
│              │                                          │
│              ▼                                          │
│   ┌─────────────────────┐                               │
│   │   CLIP Text Encoder │                               │
│   └─────────────────────┘                               │
│              │                                          │
│              ▼                                          │
│   ┌─────────────────────────────────────────┐           │
│   │      Conditional Policy Network         │           │
│   │  (Fine-tuned from VPT Foundation Model) │           │
│   │                                         │           │
│   │   Input: Visual Observation + Text Embedding │      │
│   │   Output: Action Distribution               │       │
│   └─────────────────────────────────────────┘           │
│              │                                          │
│              ▼                                          │
│   Actions: [move, look, jump, attack, use]              │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**两阶段训练**:
1. **预训练阶段**: 在大量 Minecraft 视频上训练 VPT（模仿学习）
2. **微调阶段**: 在带文本注释的数据上微调条件策略

### 4.3 所使用的模型

| 组件 | 模型 | 说明 |
|------|------|------|
| 视觉编码 | VPT (Video PreTraining) | 基于 Transformer 的视频理解模型 |
| 文本编码 | CLIP | 文本-视觉对齐 |
| 策略网络 | VPT-based Conditional Policy | 根据文本条件生成动作 |

**与 VLM 的关系**: STEVE-1 训练了一个专门的视觉-语言-动作模型，但**不是直接使用 GPT-4V 这类通用 VLM**。

---

## 5. JARVIS-VLA

**论文**: *JARVIS-VLA: Post-Training Large-Scale Vision Language Models to Play Visual Games with Keyboards and Mouse*  
**发表**: ACL 2025 (Main Conference)  
**机构**: 清华大学、北京智源人工智能研究院等  
**开源**: https://craftjarvis.github.io/JarvisVLA

### 6.1 主要思想

JARVIS-VLA 提出了 **"Act from Visual Language Post-Training"** 新范式，核心创新在于**直接对基础 VLM 进行后训练**，而非仅微调动作头（Action Head）。传统 VLA 方法通常保持 VLM 冻结，只训练下游动作策略；而 JARVIS-VLA 发现，**增强 VLM 本身的世界知识、视觉识别和空间定位能力**，能显著提升开放世界任务性能。

**关键突破**:
- 首个能完成 **1000+ 种不同原子任务** 的 Minecraft VLA 模型
- 通过**视觉和语言指导**进行自监督后训练
- 覆盖制作、冶炼、烹饪、采矿、击杀等多样化操作

### 6.2 Agent 框架

```
┌─────────────────────────────────────────────────────────┐
│                  JARVIS-VLA Framework                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Stage 1: Foundation VLM Pre-training                   │
│  ┌─────────────────────────────────────────┐            │
│  │     Large-Scale Web Data (图文对)        │            │
│  │         ↓                               │            │
│  │    Pre-trained VLM (Qwen/InternVL)      │            │
│  └─────────────────────────────────────────┘            │
│                      │                                  │
│                      ▼                                  │
│  Stage 2: Visual-Language Post-Training                 │
│  ┌─────────────────────────────────────────┐            │
│  │  Visual & Linguistic Guidance           │            │
│  │  ┌─────────────┐    ┌─────────────┐     │            │
│  │  │ World       │    │ Visual      │     │            │
│  │  │ Knowledge   │ +  │ Recognition │     │            │
│  │  │ Enhancement │    │ & Spatial   │     │            │
│  │  │             │    │ Grounding   │     │            │
│  │  └─────────────┘    └─────────────┘     │            │
│  │              ↓                          │            │
│  │    Refined VLM (Self-supervised)        │            │
│  └─────────────────────────────────────────┘            │
│                      │                                  │
│                      ▼                                  │
│  Stage 3: Action Alignment                              │
│  ┌─────────────────────────────────────────┐            │
│  │  Input: Screenshot + Text Instruction   │            │
│  │         ↓                               │            │
│  │  VLM → Action Decoder → Key/Mouse       │            │
│  │         ↓                               │            │
│  │  Actions: WASD, Mouse Move, Click, etc. │            │
│  └─────────────────────────────────────────┘            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**训练流程**:
1. **预训练**: 使用大规模网络图文数据训练基础 VLM
2. **视觉-语言后训练**: 用自监督方式增强模型的世界知识和空间理解
3. **动作对齐**: 将精炼后的 VLM 与动作空间对齐，输出键鼠控制

### 6.3 所使用的模型

| 组件 | 模型 | 说明 |
|------|------|------|
| 基础 VLM | Qwen-VL / InternVL | 大规模视觉语言模型 |
| 后训练 | Self-supervised Learning | 视觉-语言指导信号 |
| 动作解码 | Action Decoder | 将 VLM 输出映射到键鼠动作 |
| 任务验证 | Minecraft Environment | 1000+ 原子任务测试 |

**性能表现**:
- 相比最佳基线提升 **40%**
- 超越传统模仿学习策略，达到 SOTA
- 成功处理非轨迹任务（Non-trajectory Tasks）

---

## 7. 各工作对比总结

| 特性 | MineDojo | Voyager | AgentStudio | STEVE-1 | JARVIS-VLA |
|------|----------|---------|-------------|---------|------------|
| **类型** | 环境平台 | Agent 框架 | 通用工具包 | 端到端模型 | VLA 后训练 |
| **年份** | 2022 | 2023 | 2024 | 2023 | 2025 |
| **VLM-based** | ❌ | ⚠️ 部分 | ✅ | ⚠️ 专用模型 | ✅ |
| **代码生成** | ❌ | ✅ | ✅ | ❌ | ❌ |
| **视觉输入** | ✅ | ⚠️ 辅助 | ✅ | ✅ | ✅ |
| **技能学习** | ❌ | ✅ | ⚠️ 可扩展 | ⚠️ 隐式 | ⚠️ 隐式 |
| **知识检索** | ✅ 环境提供 | ⚠️ 技能库 | ❌ | ❌ | ❌ |
| **模型后训练** | ❌ | ❌ | ❌ | ✅ | ✅ 核心创新 |
| **开源** | ✅ | ✅ | ✅ | ✅ | ✅ |

**图例说明**:
- ✅ 完全支持
- ⚠️ 部分支持/有限支持
- ❌ 不支持

---

## 8. 对本项目的启示

基于以上调研，针对本次 VLM Minecraft Agent 任务的推荐架构：

```
参考 Voyager 的代码生成思想
        +
参考 AgentStudio 的 VLM 接入方式
        +
参考 JARVIS-VLA 的视觉-语言对齐 (零样本)
        ↓
我们的 VLM Minecraft Agent
```

**核心设计决策**:

| 决策 | 选择 | 理由 |
|------|------|------|
| **VLM 选择** | GPT-4V / Qwen-VL / InternVL | 通用模型，无需训练，即插即用 |
| **动作执行** | PyAutoGUI 键鼠模拟 | 符合题目"视觉理解游戏画面"的要求 |
| **技能表示** | 自然语言 + JSON 动作 | 可解释、易调试，参考 Voyager |
| **视觉输入** | 屏幕截图 (RGB) | 真实游戏画面，VLM 直接理解 |
| **开发策略** | 增量式 | 从采集木头开始，逐步扩展 |

**从 JARVIS-VLA 学到的关键经验**:
- **空间定位很重要**: VLM 需要理解"哪里有什么"，我们在 prompt 中要强调空间信息
- **原子任务拆解**: 像 JARVIS-VLA 一样，把复杂任务拆成 1000+ 原子操作，便于组合
- **视觉-语言对齐质量**: 使用高质量的 VLM（如 GPT-4V）比复杂架构更重要

**技术路线定位**:

本项目属于 **"零样本/少样本 VLM Agent"**，与 JARVIS-VLA 的主要区别在于：
- JARVIS-VLA: 大规模后训练 → 高性能但需要算力和数据
- 本项目: 直接调用 API → 快速验证想法，工程导向

这种选择符合作业要求：**展示工程实现能力** 和 **对 VLM 的理解应用**。

---

## 参考文献

1. Fan, L., et al. (2022). MineDojo: Building Open-Ended Embodied Agents with Internet-Scale Knowledge. *NeurIPS*.
2. Wang, G., et al. (2023). Voyager: An Open-Ended Embodied Agent with Large Language Models. *arXiv*.
3. Xie, T., et al. (2024). AgentStudio: A Toolkit for Building General Virtual Agents. *ICLR*.
4. Lifshitz, S., et al. (2023). STEVE-1: A Generative Model for Text-Guided Minecraft Agents. *ICML*.
5. Li, M., et al. (2025). JARVIS-VLA: Post-Training Large-Scale Vision Language Models to Play Visual Games with Keyboards and Mouse. *ACL 2025*.
