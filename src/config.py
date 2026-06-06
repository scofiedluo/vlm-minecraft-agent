'''
Author: scofiedluo scofiedluo@gmail.com
Date: 2026-05-31 18:12:47
LastEditors: scofiedluo scofiedluo@gmail.com
LastEditTime: 2026-06-06 18:18:01
FilePath: vlm-minecraft-agent/src/config.py
Description: 

Copyright (c) 2026 by ${scofiedluo}, All Rights Reserved. 
'''

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

from src.model_config import ModelCallConfig, load_model_config


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class CaptureRegion(BaseModel):
    left: int
    top: int
    width: int
    height: int


class Settings(BaseModel):
    project_root: Path = PROJECT_ROOT
    dashscope_api_key: str | None = None
    vlm_model: str = "qwen3-vl-flash"
    model_call: ModelCallConfig = Field(default_factory=lambda: load_model_config("qwen3-vl-flash"))

    agent_objective: str = "收集木头并保证生存"
    action_mode: str = "dry-run"  # legacy only
    capture_region: CaptureRegion | None = None

    loop_interval: float = Field(default=2.0, ge=0.2, le=60.0)
    max_steps: int = Field(default=5, ge=1, le=1000)
    screenshot_dir: Path = PROJECT_ROOT / "runs" / "screenshots"
    log_dir: Path = PROJECT_ROOT / "runs" / "logs"

    skill_server_url: str = "http://127.0.0.1:3000"
    skill_timeout_ms: int = Field(default=30000, ge=1000, le=120000)
    planner_fail_retry_threshold: int = Field(default=2, ge=1, le=10)

    @field_validator("action_mode")
    @classmethod
    def validate_action_mode(cls, value: str) -> str:
        value = value.strip().lower()
        if value not in {"dry-run", "pyautogui"}:
            raise ValueError("ACTION_MODE must be 'dry-run' or 'pyautogui'")
        return value



def _parse_capture_region(raw: str | None) -> CaptureRegion | None:
    if not raw:
        return None
    parts = [part.strip() for part in raw.split(",") if part.strip()]
    if len(parts) != 4:
        raise ValueError("CAPTURE_REGION must use format: left,top,width,height")
    left, top, width, height = [int(part) for part in parts]
    if width <= 0 or height <= 0:
        raise ValueError("CAPTURE_REGION width and height must be positive")
    return CaptureRegion(left=left, top=top, width=width, height=height)



def _path_from_env(name: str, default: Path) -> Path:
    raw = os.getenv(name)
    path = Path(raw) if raw else default
    return path if path.is_absolute() else PROJECT_ROOT / path



def load_settings(
    *,
    env_file: str | Path | None = None,
    action_mode: str | None = None,
    max_steps: int | None = None,
    loop_interval: float | None = None,
    capture_region: str | None = None,
    agent_objective: str | None = None,
) -> Settings:
    _ = load_dotenv(dotenv_path=env_file or PROJECT_ROOT / ".env")

    vlm_model = os.getenv("VLM_MODEL", "qwen3-vl-flash")
    model_call = load_model_config(vlm_model, os.getenv("MODEL_CONFIG_FILE"))

    settings = Settings(
        dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"),
        vlm_model=vlm_model,
        model_call=model_call,
        agent_objective=agent_objective or os.getenv("AGENT_OBJECTIVE", "收集木头并保证生存"),
        action_mode=action_mode or os.getenv("ACTION_MODE", "dry-run"),
        capture_region=_parse_capture_region(capture_region if capture_region is not None else os.getenv("CAPTURE_REGION")),
        loop_interval=loop_interval if loop_interval is not None else float(os.getenv("LOOP_INTERVAL", "2.0")),
        max_steps=max_steps if max_steps is not None else int(os.getenv("MAX_STEPS", "5")),
        screenshot_dir=_path_from_env("SCREENSHOT_DIR", PROJECT_ROOT / "runs" / "screenshots"),
        log_dir=_path_from_env("LOG_DIR", PROJECT_ROOT / "runs" / "logs"),
        skill_server_url=os.getenv("SKILL_SERVER_URL", "http://127.0.0.1:3000"),
        skill_timeout_ms=int(os.getenv("SKILL_TIMEOUT_MS", "30000")),
        planner_fail_retry_threshold=int(os.getenv("PLANNER_FAIL_RETRY_THRESHOLD", "2")),
    )

    settings.screenshot_dir.mkdir(parents=True, exist_ok=True)
    settings.log_dir.mkdir(parents=True, exist_ok=True)
    return settings
