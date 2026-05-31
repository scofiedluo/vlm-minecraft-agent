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
from pathlib import Path

from src.actions import ActionExecutor
from src.models import AgentState
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
    ) -> None:
        self.capture = capture
        self.planner = planner
        self.executor = executor
        self.loop_interval = loop_interval

    def run(self, *, max_steps: int = 5, once: bool = False) -> None:
        total_steps = 1 if once else max_steps
        logger.info("Agent started: steps=%s interval=%.2fs", total_steps, self.loop_interval)

        for step in range(1, total_steps + 1):
            self.run_step(step)
            if step < total_steps:
                time.sleep(self.loop_interval)

        logger.info("Agent finished")

    def run_step(self, step: int) -> Path:
        state = AgentState(step=step, notes="Screen-only MVP; inventory/health can be filled manually later.")
        image_path = self.capture.capture(prefix=f"step_{step:03d}")
        logger.info("[OBSERVE] screenshot=%s", image_path)

        decision = self.planner.decide(image_path, state)
        logger.info(
            "[DECISION] goal=%s action=%s confidence=%.2f scene=%s",
            decision.goal,
            decision.action.type,
            decision.confidence,
            decision.scene.summary,
        )

        self.executor.execute(decision.action)
        return image_path
