'''
Author: scofiedluo scofiedluo@gmail.com
Date: 2026-05-31 18:12:47
LastEditors: scofiedluo scofiedluo@gmail.com
LastEditTime: 2026-05-31 22:48:50
Description: 

Copyright (c) 2026 by ${scofiedluo}, All Rights Reserved. 
'''
from __future__ import annotations

import base64
import logging
from pathlib import Path

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import Settings
from src.model_config import ModelCallConfig

logger = logging.getLogger(__name__)


class QwenVLMClient:
    def __init__(self, settings: Settings) -> None:
        if not settings.dashscope_api_key:
            raise RuntimeError("DASHSCOPE_API_KEY is not configured. Copy .env.example to .env and fill it.")
        self.model_config: ModelCallConfig = settings.model_call
        self.model: str = self.model_config.model_name
        self.client: OpenAI = OpenAI(api_key=settings.dashscope_api_key, base_url=self.model_config.base_url)

    @staticmethod
    def encode_image_to_base64(image_path: str | Path) -> str:
        with open(image_path, "rb") as file:
            return base64.b64encode(file.read()).decode("utf-8")

    @retry(wait=wait_exponential(multiplier=1, min=1, max=8), stop=stop_after_attempt(3), reraise=True)
    def analyze(self, image_path: str | Path, prompt: str, system_prompt: str) -> str:
        logger.info("Calling VLM model=%s image=%s", self.model, image_path)
        base64_image = self.encode_image_to_base64(image_path)
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}},
                        {"type": "text", "text": prompt},
                    ],
                },
            ],
            temperature=self.model_config.temperature,
            max_tokens=self.model_config.max_output_tokens,
            extra_body=self.model_config.extra_body(),
        )
        content = completion.choices[0].message.content
        if isinstance(content, list):
            return "".join(str(item) for item in content)
        return content or ""
