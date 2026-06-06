'''
Author: scofiedluo scofiedluo@gmail.com
Date: 2026-05-31 18:13:13
LastEditors: scofiedluo scofiedluo@gmail.com
LastEditTime: 2026-06-06 18:18:48
FilePath: vlm-minecraft-agent/src/main.py
Description: 

Copyright (c) 2026 by ${scofiedluo}, All Rights Reserved. 
'''

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.agent import LayeredMinecraftAgent
from src.config import load_settings
from src.plan import PlanManager
from src.planner import DecisionPlanner
from src.screen_capture import ScreenCapture
from src.skill_client import SkillServerClient
from src.vlm_client import QwenVLMClient
from src.world_state import WorldStateMemory


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Layered VLM + Mineflayer Minecraft Agent")
    parser.add_argument("--steps", type=int, default=None, help="Maximum plan loop steps")
    parser.add_argument("--interval", type=float, default=None, help="Loop interval in seconds")
    parser.add_argument("--region", default=None, help="Capture region: left,top,width,height")
    parser.add_argument("--objective", default=None, help="Long-term objective")
    parser.add_argument("--once", action="store_true", help="Run exactly one planning cycle")
    parser.add_argument("--no-vlm", action="store_true", help="Skip VLM and use planner fallback")
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
        max_steps=args.steps,
        loop_interval=args.interval,
        capture_region=args.region,
        agent_objective=args.objective,
    )
    setup_logging(settings.log_dir)

    capture = ScreenCapture(settings.screenshot_dir, settings.capture_region)
    vlm_client = None if args.no_vlm else QwenVLMClient(settings)
    planner = DecisionPlanner(vlm_client)

    skill_client = SkillServerClient(
        settings.skill_server_url,
        timeout_seconds=settings.skill_timeout_ms / 1000,
    )
    world_state = WorldStateMemory()
    world_state.long_term_goal = settings.agent_objective
    plan_manager = PlanManager()

    agent = LayeredMinecraftAgent(
        capture=capture,
        planner=planner,
        skill_client=skill_client,
        world_state=world_state,
        plan_manager=plan_manager,
        loop_interval=settings.loop_interval,
    )

    agent.run(max_steps=settings.max_steps, once=args.once)


if __name__ == "__main__":
    main()
