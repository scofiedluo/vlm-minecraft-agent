'''
Author: scofiedluo scofiedluo@gmail.com
Date: 2026-05-31 18:12:47
LastEditors: scofiedluo scofiedluo@gmail.com
LastEditTime: 2026-05-31 22:48:50
Description: 

Copyright (c) 2026 by ${scofiedluo}, All Rights Reserved. 
'''
from __future__ import annotations

from collections import deque

from src.models import PlanStep, SkillCall, SkillResult, StateSnapshot


class WorldStateMemory:
    def __init__(self, max_recent_results: int = 5) -> None:
        self.current_snapshot = StateSnapshot()
        self.recent_skill_results: deque[dict] = deque(maxlen=max_recent_results)
        self.failure_count_by_goal: dict[str, int] = {}
        self.current_plan: list[PlanStep] = []
        self.long_term_goal: str = "收集木头并保证生存"

    def update_snapshot(self, snapshot: StateSnapshot) -> None:
        self.current_snapshot = snapshot

    def apply_skill_result(self, skill: SkillCall, result: SkillResult, current_step_goal: str | None = None) -> None:
        self.recent_skill_results.append(
            {
                "skill": skill.name,
                "args": skill.args,
                "success": result.success,
                "reason": result.reason,
                "diff": result.diff,
            }
        )
        if current_step_goal:
            if result.success:
                self.failure_count_by_goal[current_step_goal] = 0
            else:
                self.failure_count_by_goal[current_step_goal] = self.failure_count_by_goal.get(current_step_goal, 0) + 1

    def build_planner_summary(self) -> dict:
        inventory = {it.name: it.count for it in self.current_snapshot.inventory}
        nearby_threats = [
            {"name": e.name, "distance": e.distance, "dir": e.dir}
            for e in self.current_snapshot.nearbyEntities
            if (e.kind or "") in {"hostile", "mob"}
        ]
        return {
            "goal": self.long_term_goal,
            "position": self.current_snapshot.position.model_dump() if self.current_snapshot.position else None,
            "health": self.current_snapshot.health,
            "food": self.current_snapshot.food,
            "timeOfDay": self.current_snapshot.timeOfDay,
            "safety": self.current_snapshot.safety.model_dump(),

            "inventory": inventory,
            "nearbyBlocks": [b.model_dump() for b in self.current_snapshot.nearbyBlocks[:10]],
            "nearbyThreats": nearby_threats[:8],
            "lastSkillResult": self.current_snapshot.lastSkillResult.model_dump() if self.current_snapshot.lastSkillResult else None,
            "recentResults": list(self.recent_skill_results),
            "plan": [s.model_dump() for s in self.current_plan],
            "failureCountByGoal": self.failure_count_by_goal,
        }
