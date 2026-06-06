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
from typing import Any

from src.plan import PlanManager
from src.planner import DecisionPlanner
from src.skill_client import SkillServerClient
from src.world_state import WorldStateMemory
from src.models import SkillCall, SkillResult

from src.screen_capture import ScreenCapture

logger = logging.getLogger(__name__)

SURVIVAL_SKILLS = {"flee", "eat", "attack_nearest"}


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
        self.bad_scene_streak = 0

    def run(self, *, max_steps: int = 10, once: bool = False) -> None:
        total_steps = 1 if once else max_steps
        logger.info("Layered agent started: steps=%s", total_steps)

        for i in range(1, total_steps + 1):
            if self.plan_manager.all_done():
                if self.plan_manager.has_failed():
                    logger.warning("Plan terminated with failures, stop loop")
                else:
                    logger.info("Plan completed successfully, stop loop")
                break
            self.run_step(i)
            if i < total_steps:
                time.sleep(self.loop_interval)


        logger.info("Layered agent finished")

    def _sanitize_plan_update(self, updates: list[dict[str, Any]], active_step_id: str | None) -> list[dict[str, Any]]:
        if not active_step_id:
            return updates

        sanitized: list[dict[str, Any]] = []
        for upd in updates:
            if str(upd.get("id", "")).strip() == active_step_id and upd.get("status") == "done":
                safe_upd = dict(upd)
                safe_upd.pop("status", None)
                sanitized.append(safe_upd)
                continue
            sanitized.append(upd)
        return sanitized

    def _track_scene_quality(self, terrain: str | None, summary: str | None) -> None:
        terrain_text = (terrain or "").strip().lower()
        summary_text = (summary or "").strip().lower()
        bad_scene = terrain_text in {"unknown", "未知"} or any(
            marker in summary_text for marker in ["terminal", "ide", "desktop", "编辑器", "终端", "桌面"]
        )

        if bad_scene:
            self.bad_scene_streak += 1
            if self.bad_scene_streak >= 3:
                logger.warning("[CAPTURE-CHECK] scene seems invalid for %s steps, please verify game window/observer state", self.bad_scene_streak)
        else:
            self.bad_scene_streak = 0

    def run_step(self, step: int) -> Path:
        snapshot = self.skill_client.get_state()
        self.world_state.update_snapshot(snapshot)
        self.world_state.current_plan = self.plan_manager.steps

        # 先锁定本轮目标步骤，避免被 plan_update 改写后错位
        active_step = self.plan_manager.get_current_step()
        image_path = self.capture.capture(prefix=f"step_{step:03d}")

        if snapshot.safety.danger:
            skill = SkillCall(name="flee", args={"distance": 10}, timeoutMs=8000)
            try:
                result = self.skill_client.run_skill(skill)
            except Exception as err:  # noqa: BLE001
                logger.warning("[SKILL-ERROR] skill=%s error=%s", skill.name, err)
                result = SkillResult(success=False, reason=f"skill call failed: {err}")

            self.world_state.apply_skill_result(skill, result, None)
            logger.warning("[REFLEX] danger=%s -> flee", snapshot.safety.reason)
            return image_path

        need_planning = active_step is None or active_step.skill is None or active_step.fail_count > 0

        if need_planning:
            summary = self.world_state.build_planner_summary()
            decision = self.planner.decide(image_path, summary)
            self._track_scene_quality(decision.scene.terrain, decision.scene.summary)

            updates = self._sanitize_plan_update(decision.plan_update, active_step.id if active_step else None)
            self.plan_manager.apply_plan_update(updates)
            skill = decision.next_skill
            reason = decision.reason
            confidence = decision.confidence
        else:
            skill = SkillCall(name=active_step.skill, args=active_step.args, timeoutMs=30000)
            reason = "deterministic fast path"
            confidence = 1.0

        if active_step and active_step.skill and skill.name != active_step.skill:
            logger.warning(
                "[PLAN-OVERRIDE] active_goal=%s expected_skill=%s got=%s -> force expected skill",
                active_step.goal,
                active_step.skill,
                skill.name,
            )
            skill = SkillCall(name=active_step.skill, args=active_step.args or skill.args, timeoutMs=skill.timeoutMs)

        if active_step and not skill.args and active_step.args:
            skill = SkillCall(name=skill.name, args=active_step.args, timeoutMs=skill.timeoutMs)


        logger.info(
            "[PLAN] step=%s skill=%s args=%s reason=%s confidence=%.2f",
            step,
            skill.name,
            skill.args,
            reason,
            confidence,
        )

        try:
            result = self.skill_client.run_skill(skill)
        except Exception as err:  # noqa: BLE001
            logger.warning("[SKILL-ERROR] skill=%s error=%s", skill.name, err)
            result = SkillResult(success=False, reason=f"skill call failed: {err}")

        self.world_state.apply_skill_result(skill, result, active_step.goal if active_step else None)

        if active_step and skill.name not in SURVIVAL_SKILLS:
            if result.success and (active_step.skill is None or skill.name == active_step.skill):
                self.plan_manager.mark_current_done(active_step.id)
            elif not result.success:
                active_step.fail_count += 1
                logger.warning(
                    "[SKILL-FAIL] goal=%s fail_count=%s reason=%s",
                    active_step.goal,
                    active_step.fail_count,
                    result.reason,
                )
                if active_step.fail_count >= 2:
                    self.plan_manager.mark_current_failed(active_step.id)

        logger.info("[SKILL] success=%s reason=%s diff=%s", result.success, result.reason, result.diff)
        return image_path


