'''
Author: scofiedluo scofiedluo@gmail.com
Date: 2026-05-31 18:12:47
LastEditors: scofiedluo scofiedluo@gmail.com
LastEditTime: 2026-05-31 22:48:50
FilePath: vlm-minecraft-agent/src/screen_capture.py
Description: 

Copyright (c) 2026 by ${scofiedluo}, All Rights Reserved. 
'''

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PIL import Image
import mss

from src.config import CaptureRegion


class ScreenCapture:
    def __init__(self, output_dir: Path, region: CaptureRegion | None = None) -> None:
        self.output_dir = output_dir
        self.region = region
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def capture(self, *, prefix: str = "step") -> Path:
        with mss.mss() as sct:
            monitor = self._monitor(sct)
            raw = sct.grab(monitor)
            image = Image.frombytes("RGB", raw.size, raw.rgb)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        path = self.output_dir / f"{prefix}_{timestamp}.png"
        image.save(path)
        return path

    def _monitor(self, sct: mss.mss) -> dict[str, int]:
        if self.region is None:
            return dict(sct.monitors[1])
        return {
            "left": self.region.left,
            "top": self.region.top,
            "width": self.region.width,
            "height": self.region.height,
        }
