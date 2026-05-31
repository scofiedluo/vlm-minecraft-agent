'''
Author: scofiedluo scofiedluo@gmail.com
Date: 2026-05-31 18:12:47
LastEditors: scofiedluo scofiedluo@gmail.com
LastEditTime: 2026-05-31 22:47:34
FilePath: vlm-minecraft-agent/src/prompts.py
Description: 

Copyright (c) 2026 by ${scofiedluo}, All Rights Reserved. 
'''

from __future__ import annotations

from src.models import ALLOWED_ACTIONS, AgentState


SYSTEM_PROMPT = """You are a Minecraft survival visual agent.
Analyze the screenshot and choose exactly one safe next action.
You must return only valid JSON. Do not include markdown fences or extra text.
"""


def build_user_prompt(state: AgentState) -> str:
    allowed = ", ".join(ALLOWED_ACTIONS)
    return f"""
You are controlling a Minecraft player from first-person screen observation.

Allowed actions:
{allowed}

Action meanings:
- look_around: rotate camera briefly to inspect surroundings.
- move_forward: walk forward briefly.
- move_backward: walk backward briefly.
- turn_left / turn_right: rotate camera/player.
- jump: jump once, useful for terrain.
- mine_or_attack: hold left click briefly to mine a block or attack a threat directly in front.
- escape: move backward and turn to avoid danger.
- idle: do nothing briefly.

Survival priorities:
1. If a hostile mob, lava, cliff, drowning, or other clear danger is visible, choose escape.
2. If a tree/log/wood block is visible and close, choose move_forward or mine_or_attack.
3. If the view is unclear, choose look_around.
4. Prefer short, safe actions. Never invent actions outside the allowed list.

Current structured state:
{state.model_dump_json(ensure_ascii=False)}

Return JSON in exactly this schema:
{{
  "scene": {{
    "terrain": "forest/plains/cave/water/unknown/etc",
    "visible_blocks": ["grass", "oak_log"],
    "mobs": ["zombie"],
    "risk": "low|medium|high|unknown",
    "summary": "brief visual description"
  }},
  "goal": "short current goal",
  "action": {{
    "type": "one of the allowed actions",
    "duration": 1.0,
    "reason": "why this action is appropriate"
  }},
  "confidence": 0.0
}}
""".strip()
