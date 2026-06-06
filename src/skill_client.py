'''
Author: scofiedluo scofiedluo@gmail.com
Date: 2026-05-31 18:12:47
LastEditors: scofiedluo scofiedluo@gmail.com
LastEditTime: 2026-06-06 18:25:31
Description: 

Copyright (c) 2026 by ${scofiedluo}, All Rights Reserved. 
'''
from __future__ import annotations

import json
from urllib import error, request

from src.models import SkillCall, SkillResult, StateSnapshot


class SkillServerClient:
    def __init__(self, base_url: str, timeout_seconds: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def _json_request(self, method: str, path: str, payload: dict | None = None) -> dict:
        data = None
        headers = {"Content-Type": "application/json"}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")

        req = request.Request(f"{self.base_url}{path}", data=data, headers=headers, method=method)
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body) if body else {}
        except error.HTTPError as e:
            body = e.read().decode("utf-8") if e.fp else ""
            raise RuntimeError(f"skill server http error {e.code}: {body}") from e
        except error.URLError as e:
            raise RuntimeError(f"skill server unreachable: {e.reason}") from e

    def get_state(self) -> StateSnapshot:
        data = self._json_request("GET", "/state")
        return StateSnapshot.model_validate(data)

    def run_skill(self, skill: SkillCall) -> SkillResult:
        payload = {
            "name": skill.name,
            "args": {**skill.args, "timeoutMs": skill.timeoutMs},
            "timeoutMs": skill.timeoutMs,
        }
        data = self._json_request("POST", "/skill", payload)
        if not data.get("ok", False):
            raise RuntimeError(data.get("error", "skill execution failed"))
        return SkillResult.model_validate(data)
