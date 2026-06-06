'''
Author: scofiedluo scofiedluo@gmail.com
Date: 2026-05-31 18:12:47
LastEditors: scofiedluo scofiedluo@gmail.com
LastEditTime: 2026-06-06 18:19:18
Description: 

Copyright (c) 2026 by ${scofiedluo}, All Rights Reserved. 
'''

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


# ===== Legacy models (for compatibility with old tests/executors) =====
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
    terrain: str = "unknown"
    visible_blocks: list[str] = Field(default_factory=list)
    mobs: list[str] = Field(default_factory=list)
    risk: Literal["low", "medium", "high", "unknown"] = "unknown"
    summary: str = ""


class ActionCommand(BaseModel):
    type: ActionType = "idle"
    duration: float = Field(default=1.0, ge=0.1, le=6.0)
    reason: str = ""


class RecentStepContext(BaseModel):
    step: int = 0
    action_type: str = "idle"
    action_duration: float = 0.0
    action_reason: str = ""
    goal: str = ""
    scene_summary: str = ""
    terrain: str = "unknown"
    risk: Literal["low", "medium", "high", "unknown"] = "unknown"
    visible_blocks: list[str] = Field(default_factory=list)
    mobs: list[str] = Field(default_factory=list)


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
    recent_context: list[RecentStepContext] = Field(default_factory=list)


# ===== New layered-architecture models =====
PlanStatus = Literal["pending", "in_progress", "done", "failed", "cancelled"]
SkillName = Literal[
    "collect_block",
    "goto",
    "craft",
    "attack_nearest",
    "flee",
    "eat",
    "look_at",
    "explore",
]

ALLOWED_SKILLS: tuple[str, ...] = tuple(SkillName.__args__)  # type: ignore[attr-defined]


class InventoryItem(BaseModel):
    name: str
    count: int = 0


class Position(BaseModel):
    x: float
    y: float
    z: float


class NearbyBlock(BaseModel):
    name: str
    count: int = 0
    nearest: Position | None = None
    distance: float | None = None
    dir: str | None = None


class NearbyEntity(BaseModel):
    name: str
    kind: str | None = None
    distance: float | None = None
    dir: str | None = None


class LastSkillResult(BaseModel):
    name: str = ""
    success: bool = False
    reason: str = ""


class StateSnapshot(BaseModel):
    ok: bool = True
    tick: int = 0
    health: int | None = None
    food: int | None = None
    position: Position | None = None
    yaw: float = 0.0
    pitch: float = 0.0
    onGround: bool = False
    timeOfDay: str = "unknown"
    lightLevel: int | None = None
    inventory: list[InventoryItem] = Field(default_factory=list)
    heldItem: str | None = None
    nearbyBlocks: list[NearbyBlock] = Field(default_factory=list)
    nearbyEntities: list[NearbyEntity] = Field(default_factory=list)
    lastSkillResult: LastSkillResult | None = None


class PlanStep(BaseModel):
    id: str
    goal: str
    status: PlanStatus = "pending"
    skill: str | None = None
    args: dict[str, Any] = Field(default_factory=dict)
    fail_count: int = 0


class SkillCall(BaseModel):
    name: SkillName
    args: dict[str, Any] = Field(default_factory=dict)
    timeoutMs: int = Field(default=30000, ge=1000, le=120000)


class SkillResult(BaseModel):
    success: bool
    reason: str = ""
    stateBefore: dict[str, Any] = Field(default_factory=dict)
    stateAfter: dict[str, Any] = Field(default_factory=dict)
    diff: dict[str, Any] = Field(default_factory=dict)


class PlanDecision(BaseModel):
    scene: SceneInfo = Field(default_factory=SceneInfo)
    plan_update: list[dict[str, Any]] = Field(default_factory=list)
    next_skill: SkillCall
    reason: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
