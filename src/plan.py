'''
Author: scofiedluo scofiedluo@gmail.com
Date: 2026-06-06 16:00:10
LastEditors: scofiedluo scofiedluo@gmail.com
LastEditTime: 2026-06-07 16:00:25
Description: 

Copyright (c) 2026 by ${scofiedluo}, All Rights Reserved. 
'''

from __future__ import annotations

from src.models import PlanStep


class PlanManager:
    def __init__(self, initial_steps: list[PlanStep] | None = None) -> None:
        self.steps: list[PlanStep] = initial_steps or [
            PlanStep(id="1", goal="砍 3 个木头原木", status="in_progress", skill="collect_block", args={"block": "oak_log", "count": 3}),  # birch_log
            PlanStep(id="2", goal="合成木板和工作台", status="pending", skill="craft", args={"item": "crafting_table", "count": 1}),
            PlanStep(id="3", goal="合成木镐", status="pending", skill="craft", args={"item": "wooden_pickaxe", "count": 1}),
            PlanStep(id="4", goal="采集 5 块泥土", status="pending", skill="collect_block", args={"block": "dirt", "count": 5, "maxDistance": 48, "timeoutMs": 90000}),
            PlanStep(id="5", goal="采集 3 块石头", status="pending", skill="collect_block", args={"block": "stone", "count": 3, "maxDistance": 48, "timeoutMs": 90000}),
            PlanStep(id="6", goal="寻找并猎杀两只鸡", status="pending", skill="hunt", args={"mob": "chicken", "count": 2, "maxDistance": 64, "timeoutMs": 60000}),
            PlanStep(id="7", goal="寻找并猎杀一头猪", status="pending", skill="hunt", args={"mob": "pig", "count": 1, "maxDistance": 64, "timeoutMs": 60000}),
            PlanStep(id="8", goal="寻找并猎杀一只羊", status="pending", skill="hunt", args={"mob": "sheep", "count": 1, "maxDistance": 64, "timeoutMs": 60000}),

            PlanStep(id="9", goal="采集 5 块粘土", status="pending", skill="collect_block", args={"block": "clay", "count": 5, "maxDistance": 48, "timeoutMs": 90000})
        ]




        self._promote_next_pending()


    def get_current_step(self) -> PlanStep | None:
        for step in self.steps:
            if step.status == "in_progress":
                return step
        for step in self.steps:
            if step.status == "pending":
                step.status = "in_progress"
                return step
        return None

    def mark_current_done(self, step_id: str) -> None:
        for step in self.steps:
            if step.id == step_id:
                step.status = "done"
                break
        self._promote_next_pending()

    def mark_current_failed(self, step_id: str) -> None:
        for step in self.steps:
            if step.id == step_id:
                step.status = "failed"
                break

    def _promote_next_pending(self) -> None:
        has_active = any(s.status == "in_progress" for s in self.steps)
        if has_active:
            return
        for step in self.steps:
            if step.status == "pending":
                step.status = "in_progress"
                return

    def apply_plan_update(self, updates: list[dict]) -> None:
        for upd in updates:
            sid = str(upd.get("id", "")).strip()
            if not sid:
                continue
            matched = next((s for s in self.steps if s.id == sid), None)
            if matched:
                if "status" in upd:
                    matched.status = upd["status"]
                if "goal" in upd:
                    matched.goal = upd["goal"]
                if "skill" in upd:
                    matched.skill = upd["skill"]
                if "args" in upd and isinstance(upd["args"], dict):
                    matched.args = upd["args"]
            else:
                self.steps.append(
                    PlanStep(
                        id=sid,
                        goal=str(upd.get("goal", "新任务")),
                        status=upd.get("status", "pending"),
                        skill=upd.get("skill"),
                        args=upd.get("args", {}) if isinstance(upd.get("args"), dict) else {},
                    )
                )
        self._promote_next_pending()

    def all_done(self) -> bool:
        return not any(s.status in {"pending", "in_progress"} for s in self.steps)

    def has_failed(self) -> bool:
        return any(s.status == "failed" for s in self.steps)


