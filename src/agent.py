'''
Author: scofiedluo scofiedluo@gmail.com
Date: 2026-05-31 18:13:13
LastEditors: scofiedluo scofiedluo@gmail.com
LastEditTime: 2026-06-06 18:17:19
FilePath:
Description: 

Copyright (c) 2026 by ${scofiedluo}, All Rights Reserved. 
'''

from __future__ import annotations

import logging
import time
from pathlib import Path

from src.plan import PlanManager
from src.planner import DecisionPlanner
from src.skill_client import SkillServerClient
from src.world_state import WorldStateMemory
from src.models import SkillCall, SkillResult

from src.screen_capture import ScreenCapture

logger = logging.getLogger(__name__)


class LayeredMinecraftAgent:
    def __init__(
        self,
        capture: ScreenCapture,
        planner: DecisionPlanner,
        skill_client: SkillServerClient,
        world_state: WorldStateMemory,
        plan_manager: PlanManager,
        *,
        loop_interval: float = 0.5,
    ) -> None:
        self.capture = capture
        self.planner = planner
        self.skill_client = skill_client
        self.world_state = world_state
        self.plan_manager = plan_manager
        self.loop_interval = loop_interval

    def run(self, *, max_steps: int = 10, once: bool = False) -> None:
        total_steps = 1 if once else max_steps
        logger.info("Layered agent started: steps=%s", total_steps)

        for i in range(1, total_steps + 1):
            if self.plan_manager.all_done():
                logger.info("Plan completed, stop loop")
                break
            self.run_step(i)
            if i < total_steps:
                time.sleep(self.loop_interval)

        logger.info("Layered agent finished")

    def run_step(self, step: int) -> Path:
        snapshot = self.skill_client.get_state()
        self.world_state.update_snapshot(snapshot)
        self.world_state.current_plan = self.plan_manager.steps

        image_path = self.capture.capture(prefix=f"step_{step:03d}")
        summary = self.world_state.build_planner_summary()

        decision = self.planner.decide(image_path, summary)
        self.plan_manager.apply_plan_update(decision.plan_update)

        skill = SkillCall.model_validate(decision.next_skill)
        current_step = self.plan_manager.get_current_step()
        if current_step and not skill.args and current_step.args:
            skill = SkillCall(name=skill.name, args=current_step.args, timeoutMs=skill.timeoutMs)

        logger.info(
            "[PLAN] step=%s skill=%s args=%s reason=%s confidence=%.2f",
            step,
            skill.name,
            skill.args,
            decision.reason,
            decision.confidence,
        )

        try:
            result = self.skill_client.run_skill(skill)
        except Exception as err:  # noqa: BLE001
            logger.warning("[SKILL-ERROR] skill=%s error=%s", skill.name, err)
            result = SkillResult(success=False, reason=f"skill call failed: {err}")

        self.world_state.apply_skill_result(skill, result, current_step.goal if current_step else None)


        if current_step:
            if result.success:
                self.plan_manager.mark_current_done(current_step.id)
            else:
                current_step.fail_count += 1
                logger.warning("[SKILL-FAIL] goal=%s fail_count=%s reason=%s", current_step.goal, current_step.fail_count, result.reason)
                if current_step.fail_count >= 2:
                    self.plan_manager.mark_current_failed(current_step.id)

        logger.info("[SKILL] success=%s reason=%s diff=%s", result.success, result.reason, result.diff)
        return image_path
