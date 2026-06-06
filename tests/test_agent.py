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
from src.models import PlanStep, SkillCall, SkillResult, StateSnapshot

from src.plan import PlanManager
from src.world_state import WorldStateMemory


class FakeCapture:
    def capture(self, prefix: str) -> Path:
        return Path(f"{prefix}.png")


class FakeDecision:
    def __init__(self, *, plan_update=None, next_skill=None, reason="test", confidence=1.0):
        self.plan_update = plan_update or []
        self.next_skill = next_skill or SkillCall(name="collect_block", args={"block": "oak_log", "count": 1}, timeoutMs=30000)
        self.reason = reason
        self.confidence = confidence

        class Scene:
            terrain = "forest"
            summary = "minecraft scene"

        self.scene = Scene()


class FakePlanner:
    vlm_client = object()

    def __init__(self, decision=None):
        self.decision = decision or FakeDecision()

    def decide(self, image_path: str, summary: dict):
        return self.decision


class FakeSkillClient:
    def __init__(self, *, success=True, safety_danger=False):
        self.success = success
        self.safety_danger = safety_danger
        self.last_skill_name = None

    def get_state(self):
        return StateSnapshot(ok=True, safety={"danger": self.safety_danger, "reason": "hostile_nearby" if self.safety_danger else "safe"})

    def run_skill(self, skill):
        self.last_skill_name = skill.name
        return SkillResult(success=self.success, reason="ok" if self.success else "failed")



def test_plan_manager_can_use_configured_initial_steps() -> None:
    custom_steps = [
        PlanStep(id="x1", goal="先吃一口", status="pending", skill="eat"),
        PlanStep(id="x2", goal="再探索", status="pending", skill="explore", args={"radius": 6}),
    ]
    plan = PlanManager(initial_steps=custom_steps)

    assert plan.steps[0].id == "x1"
    assert plan.steps[0].status == "in_progress"
    assert plan.steps[1].id == "x2"


def test_event_loop_can_advance_plan() -> None:

    plan = PlanManager()
    agent = LayeredMinecraftAgent(
        capture=FakeCapture(),
        planner=FakePlanner(),
        skill_client=FakeSkillClient(success=True),
        world_state=WorldStateMemory(),
        plan_manager=plan,
        loop_interval=0.0,
    )

    agent.run(max_steps=1, once=True)

    assert plan.steps[0].status == "done"


def test_survival_skill_does_not_advance_plan() -> None:
    plan = PlanManager()
    plan.steps[0].skill = None

    decision = FakeDecision(next_skill=SkillCall(name="flee", args={"distance": 10}, timeoutMs=8000))
    agent = LayeredMinecraftAgent(
        capture=FakeCapture(),
        planner=FakePlanner(decision=decision),
        skill_client=FakeSkillClient(success=True),
        world_state=WorldStateMemory(),
        plan_manager=plan,
        loop_interval=0.0,
    )

    agent.run_step(1)

    assert plan.steps[0].status == "in_progress"


def test_plan_update_done_is_not_directly_accepted_for_active_step() -> None:
    plan = PlanManager()
    plan.steps[0].skill = None

    decision = FakeDecision(
        plan_update=[{"id": "1", "status": "done"}],
        next_skill=SkillCall(name="collect_block", args={"block": "oak_log", "count": 1}, timeoutMs=30000),
    )
    agent = LayeredMinecraftAgent(
        capture=FakeCapture(),
        planner=FakePlanner(decision=decision),
        skill_client=FakeSkillClient(success=False),
        world_state=WorldStateMemory(),
        plan_manager=plan,
        loop_interval=0.0,
    )

    agent.run_step(1)

    assert plan.steps[0].status == "in_progress"
    assert plan.steps[0].fail_count == 1

