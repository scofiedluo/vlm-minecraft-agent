'''
Author: scofiedluo scofiedluo@gmail.com
Date: 2026-05-31 18:12:47
LastEditors: scofiedluo scofiedluo@gmail.com
LastEditTime: 2026-06-06 18:22:25
Description: 

Copyright (c) 2026 by ${scofiedluo}, All Rights Reserved. 
'''

from __future__ import annotations

import json

from src.models import ALLOWED_SKILLS


SYSTEM_PROMPT = """你是 Minecraft 生存智能体的高层规划器。
你只负责：更新计划(todo)与选择下一步技能调用。
你绝不能输出低层键鼠动作，也不要输出坐标角度控制指令。
必须返回单个 JSON 对象，不要包含 markdown 代码块。
"""


def build_user_prompt(summary: dict[str, object]) -> str:

    skills = ", ".join(ALLOWED_SKILLS)
    schema = {
        "scene": {
            "terrain": "森林/平原/洞穴/水域/未知/其他",
            "visible_blocks": ["oak_log"],
            "mobs": ["zombie"],
            "risk": "low|medium|high|unknown",
            "summary": "一句话场景总结",
        },
        "plan_update": [
            {"id": "1", "status": "done"},
            {"id": "2", "status": "in_progress"},
        ],
        "next_skill": {
            "name": "collect_block",
            "args": {"block": "oak_log", "count": 3, "maxDistance": 32},
            "timeoutMs": 30000,
        },
        "reason": "为什么选这个技能",
        "confidence": 0.0,
    }

    return (
        "请根据当前状态摘要和截图做一次高层规划。\n"
        f"允许技能白名单：{skills}\n"
        "输出要求：\n"
        "1) 只输出JSON对象；2) next_skill.name必须来自白名单；\n"
        "3) args只能是语义参数（如block/count/mobType/dir），不要输出坐标和角度；\n"
        "4) 不要把当前正在执行的步骤主动标记为done，当前步骤完成由系统依据技能执行结果判定。\n\n"

        "当前状态摘要：\n"
        f"{json.dumps(summary, ensure_ascii=False, indent=2)}\n\n"
        "目标输出JSON Schema示例：\n"
        f"{json.dumps(schema, ensure_ascii=False, indent=2)}"
    )
