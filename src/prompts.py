'''
Author: scofiedluo scofiedluo@gmail.com
Date: 2026-05-31 18:12:47
LastEditors: scofiedluo scofiedluo@gmail.com
LastEditTime: 2026-06-03 00:12:22
FilePath: /vlm-minecraft-agent/src/prompts.py
Description: 

Copyright (c) 2026 by ${scofiedluo}, All Rights Reserved. 
'''

from __future__ import annotations

from typing import cast

from src.models import ALLOWED_ACTIONS, AgentState, RecentStepContext


def _format_recent_context(state: AgentState) -> str:
    recent_context = cast(list[RecentStepContext], getattr(state, "recent_context", []))
    if not recent_context:
        return "- 无历史记录（当前为初始阶段）"

    lines: list[str] = []
    for item in recent_context:
        blocks = "、".join(item.visible_blocks[:4]) if item.visible_blocks else "无"
        mobs = "、".join(item.mobs[:4]) if item.mobs else "无"
        lines.append(
            f"- step={item.step} | action={item.action_type}({item.action_duration:.2f}s) | "
            + f"risk={item.risk} | terrain={item.terrain} | goal={item.goal} | "
            + f"scene={item.scene_summary} | blocks={blocks} | mobs={mobs}"
        )
    return "\n".join(lines)


SYSTEM_PROMPT = """你是一个 Minecraft 生存模式视觉智能体。
为完成长期目标，请分析截图，提出短期目标，并只选择一个合适的下一步动作。
必须只返回合法 JSON，不要包含 Markdown 代码块或任何额外文本。
"""


def build_user_prompt(state: AgentState) -> str:
    allowed = ", ".join(ALLOWED_ACTIONS)
    recent_context_text = _format_recent_context(state)
    return f"""
你正在通过第一人称画面观察来控制一个 Minecraft 玩家。

## 游戏基础知识
* 收集物品，如花、橡木、泥土等的步骤：
  1. 寻找并靠近目标；
  2. 移动或转向瞄准目标，当你瞄准的花、草、石头等方出现了黑色框才是瞄准了；
  3. 执行mine_or_attack挖掘目标，挖掘成功会有一个缩小版的方块掉落。
  4. 靠近缩小版方块即可拾取。
* 画面的中间最底部是物品栏

## 允许的动作：
{allowed}

动作含义：
- move_forward：短暂向前移动。
- move_backward：短暂向后移动。
- turn_left / turn_right：向左/向右旋转视角或玩家朝向。
- jump：跳跃一次，适合通过地形障碍。
- mine_or_attack：短暂按住左键，用于挖掘正前方方块或攻击正前方威胁。
- escape：后退并转向，用于避开危险。
- idle：短暂停留不动。

## 当前长期目标：
{state.objective}

## 执行原则：
1. 生存安全优先于长期目标。
2. 如果画面中可见敌对生物、岩浆、悬崖、溺水或其他明确危险，选择 escape。
3. 如果当前环境安全，选择最有助于推进长期目标的动作。
4. 如果视野不清楚，选择 look_around。
5. 优先选择短暂、安全的动作。不要编造允许列表以外的动作。

## duration 填写规则（很重要）：
- duration 统一单位为秒，范围 0.1-6.0，挖掘木头需要执行6秒。
- move_forward / move_backward / mine_or_attack / idle / escape：按“动作持续时间”填写。
- turn_left / turn_right：duration 代表“想转多大角度”的强弱信号，越大表示希望转角越大。
  - 建议：小角度微调用 0.2-0.5；中等转向用 0.6-1.0；大幅转向用 1.0-1.6。
- 除非非常必要，不要输出超过 2.0 的 duration。

## 最近5次动作与场景变化（按时间从旧到新）
{recent_context_text}

请利用以上历史判断：
- 上一个动作是否有效（例如已经后退过但仍危险，需升级策略）；
- 场景风险是否在上升/下降；
- 是否持续卡在同一地形或同一目标上（避免无效重复动作）。

## 当前结构化状态：
{state.model_dump_json(ensure_ascii=False)}

## 输出要求
请严格按照以下结构返回 JSON：

{{
  "scene": {{
    "terrain": "森林/平原/洞穴/水域/未知/其他",
    "visible_blocks": ["草方块", "橡木原木"],
    "mobs": ["僵尸"],
    "risk": "low|medium|high|unknown",
    "summary": "简短的画面描述"
  }},
  "goal": "为完成长期目标，简短描述当前目标",
  "action": {{
    "type": "允许动作列表中的一个动作",
    "duration": "动作强度/时长信号，单位秒，0.1-6.0（turn/look_around 越大表示转角或扫描范围越大）",
    "reason": "说明为什么这个动作合适"
  }},
  "confidence": 0.0
}}
""".strip()
