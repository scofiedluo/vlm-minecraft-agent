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

import ctypes
import logging
import sys
import time
from abc import ABC, abstractmethod
from typing import Protocol, cast

from src.models import ALLOWED_ACTIONS, ActionCommand

logger = logging.getLogger(__name__)


class _PyAutoGUIModule(Protocol):
    PAUSE: float
    FAILSAFE: bool

    def press(self, key: str) -> None: ...
    def mouseDown(self, button: str) -> None: ...
    def mouseUp(self, button: str) -> None: ...
    def moveRel(self, xOffset: int, yOffset: int, duration: float = 0) -> None: ...
    def keyDown(self, key: str) -> None: ...
    def keyUp(self, key: str) -> None: ...


class _User32(Protocol):
    def mouse_event(self, dwFlags: int, dx: int, dy: int, dwData: int, dwExtraInfo: int) -> None: ...


class ActionExecutor(ABC):
    @abstractmethod
    def execute(self, command: ActionCommand) -> None:
        raise NotImplementedError


class DryRunActionExecutor(ActionExecutor):
    def execute(self, command: ActionCommand) -> None:
        logger.info("[DRY-RUN] action=%s duration=%.2fs reason=%s", command.type, command.duration, command.reason)


class PyAutoGUIActionExecutor(ActionExecutor):
    MOUSEEVENTF_MOVE: int = 0x0001

    def __init__(self, pause: float = 0.05) -> None:
        import pyautogui

        self.pyautogui: _PyAutoGUIModule = cast(_PyAutoGUIModule, pyautogui)  # pyright: ignore[reportInvalidCast]
        self.pyautogui.PAUSE = pause
        self.pyautogui.FAILSAFE = True
        self._user32: _User32 | None = None
        if sys.platform == "win32":
            self._user32 = cast(_User32, ctypes.windll.user32)  # pyright: ignore[reportInvalidCast]

    def execute(self, command: ActionCommand) -> None:
        logger.info("[PYAUTOGUI] action=%s duration=%.2fs", command.type, command.duration)
        action = command.type
        duration = command.duration

        if action == "look_around":
            self._turn(900, duration=0.35)
            time.sleep(0.15)
            self._turn(-1800, duration=0.55)
            time.sleep(0.15)
            self._turn(900, duration=0.35)
        elif action == "move_forward":
            self._hold_key("w", duration)
        elif action == "move_backward":
            self._hold_key("s", duration)
        elif action == "turn_left":
            self._turn(-1200, duration=min(duration, 1.0))
        elif action == "turn_right":
            self._turn(1200, duration=min(duration, 1.0))
        elif action == "jump":
            self.pyautogui.press("space")
        elif action == "mine_or_attack":
            self.pyautogui.mouseDown(button="left")
            time.sleep(min(duration, 3.0))
            self.pyautogui.mouseUp(button="left")
        elif action == "escape":
            self._hold_key("s", min(duration, 2.0))
            self._turn(1000, duration=0.35)
        elif action == "idle":
            time.sleep(min(duration, 2.0))
        else:
            logger.warning("Unsupported action ignored: %s", action)

    def _turn(self, pixels: int, *, duration: float) -> None:
        """用相对鼠标事件转向；Windows 下绕过 pyautogui.moveRel 对游戏视角不生效的问题。"""
        duration = max(duration, 0.01)
        steps = max(1, min(80, int(abs(pixels) / 80)))
        sent = 0
        sleep_time = duration / steps

        for step in range(1, steps + 1):
            target = round(pixels * step / steps)
            delta = target - sent
            self._move_mouse_relative(delta, 0)
            sent = target
            time.sleep(sleep_time)

    def _move_mouse_relative(self, dx: int, dy: int) -> None:
        if dx == 0 and dy == 0:
            return
        if self._user32 is not None:
            self._user32.mouse_event(self.MOUSEEVENTF_MOVE, int(dx), int(dy), 0, 0)
            return
        self.pyautogui.moveRel(int(dx), int(dy), duration=0)

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
