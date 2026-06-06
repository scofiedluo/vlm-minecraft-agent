'''
Author: scofiedluo scofiedluo@gmail.com
Date: 2026-06-06 16:01:34
LastEditors: scofiedluo scofiedluo@gmail.com
LastEditTime: 2026-06-06 18:27:14
Description: 

Copyright (c) 2026 by ${scofiedluo}, All Rights Reserved. 
'''

from pathlib import Path

from src.agent import LayeredMinecraftAgent
from src.models import SkillResult, StateSnapshot
from src.plan import PlanManager
from src.world_state import WorldStateMemory


class FakeCapture:
    def capture(self, prefix: str) -> Path:
        return Path(f"{prefix}.png")


class FakePlanner:
    def decide(self, image_path: str, summary: dict):
        class D:
            plan_update = []
            next_skill = {"name": "collect_block", "args": {"block": "oak_log", "count": 1}, "timeoutMs": 30000}
            reason = "test"
            confidence = 1.0

        return D()


class FakeSkillClient:
    def get_state(self):
        return StateSnapshot(ok=True)

    def run_skill(self, skill):
        return SkillResult(success=True, reason="ok")


def test_event_loop_can_advance_plan() -> None:
    plan = PlanManager()
    agent = LayeredMinecraftAgent(
        capture=FakeCapture(),
        planner=FakePlanner(),
        skill_client=FakeSkillClient(),
        world_state=WorldStateMemory(),
        plan_manager=plan,
        loop_interval=0.0,
    )

    agent.run(max_steps=1, once=True)

    assert plan.steps[0].status == "done"
