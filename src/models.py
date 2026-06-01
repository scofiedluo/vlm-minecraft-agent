'''
Author: scofiedluo scofiedluo@gmail.com
Date: 2026-05-31 18:12:47
LastEditors: scofiedluo scofiedluo@gmail.com
LastEditTime: 2026-05-31 22:27:03
FilePath: vlm-minecraft-agent/src/models.py
Description: 

Copyright (c) 2026 by ${scofiedluo}, All Rights Reserved. 
'''

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


ActionType = Literal[
    "look_around",
    "move_forward",
    "move_backward",
    "turn_left",
    "turn_right",
    "jump",
    "mine_or_attack",
    "escape",
    "idle",
]

ALLOWED_ACTIONS: tuple[str, ...] = tuple(ActionType.__args__)  # type: ignore[attr-defined]


class SceneInfo(BaseModel):
    terrain: str = Field(default="unknown", description="Main terrain or biome visible in the screenshot")
    visible_blocks: list[str] = Field(default_factory=list)
    mobs: list[str] = Field(default_factory=list)
    risk: Literal["low", "medium", "high", "unknown"] = "unknown"
    summary: str = ""


class ActionCommand(BaseModel):
    type: ActionType = "idle"
    duration: float = Field(default=1.0, ge=0.1, le=5.0)
    reason: str = ""


class AgentDecision(BaseModel):
    scene: SceneInfo = Field(default_factory=SceneInfo)
    goal: str = "observe"
    action: ActionCommand = Field(default_factory=ActionCommand)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class AgentState(BaseModel):
    step: int = 0
    objective: str = "收集木头并保证生存"
    health: int | None = None
    food: int | None = None
    inventory: list[str] = Field(default_factory=list)
    notes: str = ""

