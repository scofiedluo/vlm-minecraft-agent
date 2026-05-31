'''
Author: scofiedluo scofiedluo@gmail.com
Date: 2026-05-31 18:13:13
LastEditors: scofiedluo scofiedluo@gmail.com
LastEditTime: 2026-05-31 21:53:06
FilePath: vlm-minecraft-agent/src/actions.py
Description: 

Copyright (c) 2026 by ${scofiedluo}, All Rights Reserved. 
'''


from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod

from src.models import ALLOWED_ACTIONS, ActionCommand

logger = logging.getLogger(__name__)


class ActionExecutor(ABC):
    @abstractmethod
    def execute(self, command: ActionCommand) -> None:
        raise NotImplementedError


class DryRunActionExecutor(ActionExecutor):
    def execute(self, command: ActionCommand) -> None:
        logger.info("[DRY-RUN] action=%s duration=%.2fs reason=%s", command.type, command.duration, command.reason)


class PyAutoGUIActionExecutor(ActionExecutor):
    def __init__(self, pause: float = 0.05) -> None:
        import pyautogui

        self.pyautogui = pyautogui
        self.pyautogui.PAUSE = pause
        self.pyautogui.FAILSAFE = True

    def execute(self, command: ActionCommand) -> None:
        logger.info("[PYAUTOGUI] action=%s duration=%.2fs", command.type, command.duration)
        action = command.type
        duration = command.duration

        if action == "look_around":
            self.pyautogui.moveRel(180, 0, duration=0.2)
            self.pyautogui.moveRel(-120, 0, duration=0.2)
        elif action == "move_forward":
            self._hold_key("w", duration)
        elif action == "move_backward":
            self._hold_key("s", duration)
        elif action == "turn_left":
            self.pyautogui.moveRel(-260, 0, duration=min(duration, 1.0))
        elif action == "turn_right":
            self.pyautogui.moveRel(260, 0, duration=min(duration, 1.0))
        elif action == "jump":
            self.pyautogui.press("space")
        elif action == "mine_or_attack":
            self.pyautogui.mouseDown(button="left")
            time.sleep(min(duration, 3.0))
            self.pyautogui.mouseUp(button="left")
        elif action == "escape":
            self._hold_key("s", min(duration, 2.0))
            self.pyautogui.moveRel(300, 0, duration=0.2)
        elif action == "idle":
            time.sleep(min(duration, 2.0))
        else:
            logger.warning("Unsupported action ignored: %s", action)

    def _hold_key(self, key: str, duration: float) -> None:
        self.pyautogui.keyDown(key)
        try:
            time.sleep(min(duration, 3.0))
        finally:
            self.pyautogui.keyUp(key)


def create_executor(mode: str) -> ActionExecutor:
    normalized = mode.strip().lower()
    if normalized == "dry-run":
        return DryRunActionExecutor()
    if normalized == "pyautogui":
        return PyAutoGUIActionExecutor()
    raise ValueError(f"Unsupported action mode: {mode}. Allowed: {', '.join(ALLOWED_ACTIONS)}")
