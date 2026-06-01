'''
Author: scofiedluo scofiedluo@gmail.com
Date: 2026-05-31 18:12:47
LastEditors: scofiedluo scofiedluo@gmail.com
LastEditTime: 2026-06-02 00:30:43
FilePath: \vlm-minecraft-agent\src\prompts.py
Description: 

Copyright (c) 2026 by ${scofiedluo}, All Rights Reserved. 
'''

from __future__ import annotations

from src.models import ALLOWED_ACTIONS, AgentState


SYSTEM_PROMPT = """你是一个 Minecraft 生存模式视觉智能体。
为完成长期目标，请分析截图，提出短期目标，并只选择一个合适的下一步动作。
必须只返回合法 JSON，不要包含 Markdown 代码块或任何额外文本。
"""


def build_user_prompt(state: AgentState) -> str:
    allowed = ", ".join(ALLOWED_ACTIONS)
    return f"""
你正在通过第一人称画面观察来控制一个 Minecraft 玩家。

## 游戏基础知识
* 当你瞄准的花、草、石头等方出现了黑色框，表明你瞄准的物块是可挖掘的，挖掘之后才可以收集
* 画面的中间最底部是物品栏

## 允许的动作：
{allowed}

动作含义：
- look_around：短暂旋转视角，观察周围环境。
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
    "duration": "动作执行时间, 单位秒，0.5-2.0之间",
    "reason": "说明为什么这个动作合适"
  }},
  "confidence": 0.0
}}
""".strip()
