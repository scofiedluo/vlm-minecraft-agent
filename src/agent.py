'''
Author: scofiedluo scofiedluo@gmail.com
Date: 2026-05-31 18:13:13
LastEditors: scofiedluo scofiedluo@gmail.com
LastEditTime: 2026-05-31 22:01:27
FilePath: vlm-minecraft-agent/src/agent.py
Description: 

Copyright (c) 2026 by ${scofiedluo}, All Rights Reserved. 
'''

from __future__ import annotations

import logging
import time
from collections import deque
from pathlib import Path
from typing import Literal

from src.actions import ActionExecutor
from src.models import ActionCommand, AgentState, RecentStepContext
from src.planner import DecisionPlanner
from src.screen_capture import ScreenCapture

logger = logging.getLogger(__name__)


class VLMMinecraftAgent:
    def __init__(
        self,
        capture: ScreenCapture,
        planner: DecisionPlanner,
        executor: ActionExecutor,
        *,
        loop_interval: float = 2.0,
        objective: str = "收集木头并保证生存",
    ) -> None:
        self.capture: ScreenCapture = capture
        self.planner: DecisionPlanner = planner
        self.executor: ActionExecutor = executor
        self.loop_interval: float = loop_interval
        self.objective: str = objective
        self.recent_context: deque[RecentStepContext] = deque(maxlen=5)

    def run(self, *, max_steps: int = 5, once: bool = False) -> None:
        total_steps = 1 if once else max_steps
        logger.info("Agent started: steps=%s interval=%.2fs", total_steps, self.loop_interval)

        for step in range(1, total_steps + 1):
            _ = self.run_step(step)
            if step < total_steps:
                time.sleep(self.loop_interval)

        logger.info("Agent finished")

    def run_step(self, step: int) -> Path:
        state = AgentState(
            step=step,
            objective=self.objective,
            notes="Screen-only MVP; inventory/health can be filled manually later.",
            recent_context=list(self.recent_context),
        )
        image_path = self.capture.capture(prefix=f"step_{step:03d}")

        logger.info("[OBSERVE] screenshot=%s", image_path)

        decision = self.planner.decide(image_path, state)
        adapted_action = self._adapt_action_for_execution(decision.action)
        logger.info(
            "[DECISION] goal=%s action=%s raw_duration=%.2f adapted_duration=%.2f confidence=%.2f scene=%s",
            decision.goal,
            adapted_action.type,
            decision.action.duration,
            adapted_action.duration,
            decision.confidence,
            decision.scene.summary,
        )

        self.executor.execute(adapted_action)
        self._append_recent_context(
            step=step,
            goal=decision.goal,
            action=adapted_action,
            scene_summary=decision.scene.summary,
            terrain=decision.scene.terrain,
            risk=decision.scene.risk,
            visible_blocks=decision.scene.visible_blocks,
            mobs=decision.scene.mobs,
        )
        return image_path

    def _adapt_action_for_execution(self, action: ActionCommand) -> ActionCommand:
        """把 VLM 的 duration 压到更稳定的控制区间，减少过转或转向太小。"""
        action_type = action.type
        duration = action.duration

        if action_type in {"turn_left", "turn_right"}:
            # 转向动作映射到 0.20~1.20s，角度由执行器做 speed->degree 映射
            normalized = self._normalize(duration, src_low=0.1, src_high=6.0)
            tuned_duration = self._lerp(0.20, 1.20, normalized)
            return action.model_copy(update={"duration": tuned_duration})

        if action_type == "look_around":
            # 扫视需要略大范围，映射到 0.40~1.60s
            normalized = self._normalize(duration, src_low=0.1, src_high=6.0)
            tuned_duration = self._lerp(0.40, 1.60, normalized)
            return action.model_copy(update={"duration": tuned_duration})

        return action

    def _append_recent_context(
        self,
        *,
        step: int,
        goal: str,
        action: ActionCommand,
        scene_summary: str,
        terrain: str,
        risk: Literal["low", "medium", "high", "unknown"],
        visible_blocks: list[str],
        mobs: list[str],
    ) -> None:
        self.recent_context.append(
            RecentStepContext(
                step=step,
                action_type=action.type,
                action_duration=action.duration,
                action_reason=action.reason,
                goal=goal,
                scene_summary=scene_summary,
                terrain=terrain,
                risk=risk,
                visible_blocks=visible_blocks,
                mobs=mobs,
            )
        )

    @staticmethod
    def _normalize(value: float, *, src_low: float, src_high: float) -> float:
        if src_high <= src_low:
            return 0.0
        clipped = max(src_low, min(value, src_high))
        return (clipped - src_low) / (src_high - src_low)

    @staticmethod
    def _lerp(low: float, high: float, t: float) -> float:
        return low + (high - low) * max(0.0, min(t, 1.0))
