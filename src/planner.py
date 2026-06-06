'''
Author: scofiedluo scofiedluo@gmail.com
Date: 2026-05-31 18:12:47
LastEditors: scofiedluo scofiedluo@gmail.com
LastEditTime: 2026-05-31 22:34:03
FilePath: vlm-minecraft-agent/src/planner.py
Description: 

Copyright (c) 2026 by ${scofiedluo}, All Rights Reserved. 
'''

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from src.models import ALLOWED_ACTIONS, ActionCommand, AgentDecision, AgentState, SceneInfo
from src.prompts import SYSTEM_PROMPT, build_user_prompt
from src.vlm_client import QwenVLMClient

logger = logging.getLogger(__name__)


class DecisionPlanner:
    def __init__(self, vlm_client: QwenVLMClient | None = None) -> None:
        self.vlm_client = vlm_client

    def decide(self, image_path: str | Path, state: AgentState) -> AgentDecision:
        if self.vlm_client is None:
            return self.fallback("VLM client is not configured")

        prompt = build_user_prompt(state)
        try:
            raw = self.vlm_client.analyze(image_path, prompt, SYSTEM_PROMPT)
            logger.info("Raw VLM response: %s", raw)
            return self.parse_decision(raw)
        except Exception as exc:
            logger.exception("VLM decision failed: %s", exc)
            return self.fallback(str(exc))

    def parse_decision(self, raw: str) -> AgentDecision:
        data = extract_json_object(raw)
        normalized = normalize_decision_payload(data)
        decision = AgentDecision.model_validate(normalized)
        if decision.action.type not in ALLOWED_ACTIONS:
            raise ValidationError.from_exception_data("AgentDecision", [])
        return decision

    @staticmethod
    def fallback(reason: str = "fallback") -> AgentDecision:
        return AgentDecision(
            scene=SceneInfo(risk="unknown", summary=reason),
            goal="recover_from_invalid_or_missing_vlm_output",
            action=ActionCommand(type="look_around", duration=1.0, reason=reason),
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

    action_raw = normalized.get("action")
    if not isinstance(action_raw, dict):
        logger.warning("VLM action payload is invalid, fallback to look_around")
        normalized["action"] = {
            "type": "look_around",
            "duration": 1.0,
            "reason": "invalid_action_payload",
        }
        return normalized

    action = dict(action_raw)

    action_type = action.get("type")
    if action_type not in ALLOWED_ACTIONS:
        logger.warning("VLM action type unsupported: %s, fallback to look_around", action_type)
        action["type"] = "look_around"

    raw_duration = action.get("duration", 1.0)
    try:
        duration = float(raw_duration)
    except (TypeError, ValueError):
        duration = 1.0

    clamped_duration = max(0.1, min(duration, 6.0))
    if clamped_duration != duration:
        logger.warning("VLM duration %.3f is out of range, clamped to %.3f", duration, clamped_duration)
    action["duration"] = clamped_duration

    reason = action.get("reason")
    if not isinstance(reason, str):
        action["reason"] = "" if reason is None else str(reason)

    normalized["action"] = action

    confidence = normalized.get("confidence")
    if confidence is None:
        conf_value = 0.0
    else:
        try:
            conf_value = float(confidence)
        except (TypeError, ValueError):
            conf_value = 0.0
    normalized["confidence"] = max(0.0, min(conf_value, 1.0))

    return normalized
