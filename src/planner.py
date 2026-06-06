'''
Author: scofiedluo scofiedluo@gmail.com
Date: 2026-05-31 18:12:47
LastEditors: scofiedluo scofiedluo@gmail.com
LastEditTime: 2026-06-06 18:22:47
Description: 

Copyright (c) 2026 by ${scofiedluo}, All Rights Reserved. 
'''

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from src.models import ALLOWED_SKILLS, PlanDecision, SkillCall
from src.prompts import SYSTEM_PROMPT, build_user_prompt
from src.vlm_client import QwenVLMClient

logger = logging.getLogger(__name__)


class DecisionPlanner:
    def __init__(self, vlm_client: QwenVLMClient | None = None) -> None:
        self.vlm_client = vlm_client

    def decide(self, image_path: str | Path, summary: dict[str, object]) -> PlanDecision:

        if self.vlm_client is None:
            return self.fallback("VLM client is not configured")

        prompt = build_user_prompt(summary)
        try:
            raw = self.vlm_client.analyze(image_path, prompt, SYSTEM_PROMPT)
            logger.info("Raw VLM response: %s", raw)
            return self.parse_decision(raw)
        except Exception as exc:
            logger.exception("VLM planning failed: %s", exc)
            return self.fallback(str(exc))

    def parse_decision(self, raw: str) -> PlanDecision:
        data = extract_json_object(raw)
        normalized = normalize_decision_payload(data)
        return PlanDecision.model_validate(normalized)

    @staticmethod
    def fallback(reason: str = "fallback") -> PlanDecision:
        return PlanDecision(
            plan_update=[],
            next_skill=SkillCall(name="explore", args={"radius": 8}, timeoutMs=15000),
            reason=reason,
            confidence=0.0,
        )



def extract_json_object(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in VLM response")

    parsed = json.loads(text[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("VLM JSON response must be an object")
    return parsed



def normalize_decision_payload(data: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = dict(data)

    next_skill_raw = normalized.get("next_skill")
    if not isinstance(next_skill_raw, dict):
        normalized["next_skill"] = {"name": "explore", "args": {"radius": 8}, "timeoutMs": 15000}
    else:
        next_skill = dict(next_skill_raw)
        name = next_skill.get("name")
        if name not in ALLOWED_SKILLS:
            logger.warning("Unsupported skill '%s', fallback to explore", name)
            next_skill["name"] = "explore"
            next_skill["args"] = {"radius": 8}
        if not isinstance(next_skill.get("args"), dict):
            next_skill["args"] = {}

        timeout_ms = next_skill.get("timeoutMs", 30000)
        try:
            timeout_ms_value = int(timeout_ms)
        except (TypeError, ValueError):
            timeout_ms_value = 30000
        next_skill["timeoutMs"] = max(1000, min(timeout_ms_value, 120000))
        normalized["next_skill"] = next_skill

    plan_update = normalized.get("plan_update")
    if not isinstance(plan_update, list):
        normalized["plan_update"] = []

    confidence = normalized.get("confidence", 0.0)
    try:
        conf = float(confidence)
    except (TypeError, ValueError):
        conf = 0.0
    normalized["confidence"] = max(0.0, min(conf, 1.0))

    if not isinstance(normalized.get("reason"), str):
        normalized["reason"] = str(normalized.get("reason", ""))

    if not isinstance(normalized.get("scene"), dict):
        normalized["scene"] = {
            "terrain": "unknown",
            "visible_blocks": [],
            "mobs": [],
            "risk": "unknown",
            "summary": "",
        }

    return normalized
