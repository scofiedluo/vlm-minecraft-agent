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
        decision = AgentDecision.model_validate(data)
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
