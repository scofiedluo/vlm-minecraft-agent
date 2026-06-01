'''
Author: scofiedluo scofiedluo@gmail.com
Date: 2026-06-01 15:25:32
LastEditors: scofiedluo scofiedluo@gmail.com
LastEditTime: 2026-06-01 15:49:03
FilePath: vlm-minecraft-agent/src/model_config.py
Description: 

Copyright (c) 2026 by ${scofiedluo}, All Rights Reserved. 
'''

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_CONFIG_PATH = PROJECT_ROOT / "config" / "model_configs.json"


class ModelCallConfig(BaseModel):
    key: str = ""
    model_name: str
    base_url: str
    max_output_tokens: int = Field(default=300, ge=1, le=8192)
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    enable_thinking: bool = False

    def extra_body(self) -> dict[str, bool]:
        return {"enable_thinking": self.enable_thinking}


def load_model_config(model_key: str, config_path: str | Path | None = None) -> ModelCallConfig:
    path = Path(config_path) if config_path else DEFAULT_MODEL_CONFIG_PATH
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    if not path.exists():
        raise FileNotFoundError(f"Model config file not found: {path}")

    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Model config file must be a JSON object")

    configs = raw.get("models", raw)
    if not isinstance(configs, dict):
        raise ValueError("Model config must be an object or contain a 'models' object")
    if model_key not in configs:
        available = ", ".join(sorted(str(key) for key in configs.keys()))
        raise KeyError(f"VLM_MODEL={model_key!r} is not configured in {path}. Available: {available}")

    data = configs[model_key]
    if not isinstance(data, dict):
        raise ValueError(f"Model config for {model_key!r} must be a JSON object")

    return ModelCallConfig(key=model_key, **dict[str, Any](data))
