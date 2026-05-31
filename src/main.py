'''
Author: scofiedluo scofiedluo@gmail.com
Date: 2026-05-31 18:13:13
LastEditors: scofiedluo scofiedluo@gmail.com
LastEditTime: 2026-05-31 22:22:52
FilePath: vlm-minecraft-agent/src/main.py
Description: 

Copyright (c) 2026 by ${scofiedluo}, All Rights Reserved. 
'''

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.actions import create_executor
from src.agent import VLMMinecraftAgent
from src.config import load_settings
from src.planner import DecisionPlanner
from src.screen_capture import ScreenCapture
from src.vlm_client import QwenVLMClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Python VLM Minecraft Agent")
    parser.add_argument("--mode", choices=["dry-run", "pyautogui"], default=None, help="Action execution mode")
    parser.add_argument("--steps", type=int, default=None, help="Maximum agent steps")
    parser.add_argument("--interval", type=float, default=None, help="Loop interval in seconds")
    parser.add_argument("--region", default=None, help="Capture region: left,top,width,height")
    parser.add_argument("--once", action="store_true", help="Run exactly one observe-think-act step")
    parser.add_argument("--no-vlm", action="store_true", help="Skip API calls and use fallback decisions")
    return parser.parse_args()


def setup_logging(log_dir: Path) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "agent.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(log_file, encoding="utf-8")],
    )


def main() -> None:
    args = parse_args()
    settings = load_settings(
        action_mode=args.mode,
        max_steps=args.steps,
        loop_interval=args.interval,
        capture_region=args.region,
    )
    setup_logging(settings.log_dir)

    capture = ScreenCapture(settings.screenshot_dir, settings.capture_region)
    vlm_client = None if args.no_vlm else QwenVLMClient(settings)
    planner = DecisionPlanner(vlm_client)
    executor = create_executor(settings.action_mode)

    agent = VLMMinecraftAgent(
        capture=capture,
        planner=planner,
        executor=executor,
        loop_interval=settings.loop_interval,
    )
    agent.run(max_steps=settings.max_steps, once=args.once)


if __name__ == "__main__":
    main()
