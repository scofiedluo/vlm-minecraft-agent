from __future__ import annotations

import argparse
import base64
import json
import os
import statistics
import sys
import time
import uuid
from pathlib import Path
from typing import Any, cast

from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IMAGE = PROJECT_ROOT / "runs" / "screenshots" / "step_002_20260601_004433_755873.png"

sys.path.insert(0, str(PROJECT_ROOT))

from src.model_config import ModelCallConfig, load_model_config  # noqa: E402
from src.models import AgentState  # noqa: E402
from src.prompts import SYSTEM_PROMPT, build_user_prompt  # noqa: E402


def encode_image_to_base64(image_path: Path) -> str:
    with open(image_path, "rb") as file:
        return base64.b64encode(file.read()).decode("utf-8")


def usage_to_dict(usage: Any) -> dict[str, Any]:
    if usage is None:
        return {}
    if hasattr(usage, "model_dump"):
        return usage.model_dump()
    if isinstance(usage, dict):
        return usage
    return {}


def find_cache_fields(data: Any, prefix: str = "usage") -> dict[str, Any]:
    found: dict[str, Any] = {}
    if isinstance(data, dict):
        for key, value in data.items():
            path = f"{prefix}.{key}"
            if "cache" in key.lower():
                found[path] = value
            found.update(find_cache_fields(value, path))
    elif isinstance(data, list):
        for index, value in enumerate(data):
            found.update(find_cache_fields(value, f"{prefix}[{index}]"))
    return found


def percentile(values: list[float], ratio: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * ratio)))
    return ordered[index]


def build_messages(*, image_data_url: str, scenario: str, index: int) -> list[dict[str, Any]]:
    state_step = 1 if scenario == "same_request" else index
    state = AgentState(step=state_step, notes="Latency benchmark for Minecraft VLM agent.")
    system_prompt = SYSTEM_PROMPT
    user_prompt = build_user_prompt(state)

    if scenario == "cache_bust_prefix":
        nonce = uuid.uuid4().hex
        system_prompt = f"Request nonce: {nonce}\n{SYSTEM_PROMPT}"
        user_prompt = f"Request nonce: {nonce}\n{user_prompt}"

    return [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": image_data_url}},
                {"type": "text", "text": user_prompt},
            ],
        },
    ]


def call_once(
    *,
    client: OpenAI,
    model_config: ModelCallConfig,
    image_data_url: str,
    scenario: str,
    index: int,
    max_tokens_override: int | None,
) -> dict[str, Any]:
    messages = cast(list[ChatCompletionMessageParam], build_messages(image_data_url=image_data_url, scenario=scenario, index=index))
    max_tokens = max_tokens_override or model_config.max_output_tokens
    start = time.perf_counter()
    completion = client.chat.completions.create(
        model=model_config.model_name,
        messages=messages,
        temperature=model_config.temperature,
        max_tokens=max_tokens,
        extra_body=model_config.extra_body(),
    )
    elapsed_ms = (time.perf_counter() - start) * 1000
    content = completion.choices[0].message.content or ""
    usage = usage_to_dict(completion.usage)
    cache_fields = find_cache_fields(usage)
    return {
        "scenario": scenario,
        "index": index,
        "elapsed_ms": elapsed_ms,
        "content_chars": len(content),
        "usage": usage,
        "cache_fields": cache_fields,
    }


def summarize(name: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    latencies = [row["elapsed_ms"] for row in rows]
    return {
        "scenario": name,
        "count": len(rows),
        "min_ms": min(latencies) if latencies else 0.0,
        "avg_ms": statistics.mean(latencies) if latencies else 0.0,
        "median_ms": statistics.median(latencies) if latencies else 0.0,
        "p90_ms": percentile(latencies, 0.9),
        "max_ms": max(latencies) if latencies else 0.0,
    }


def print_row(row: dict[str, Any]) -> None:
    cache_fields = row["cache_fields"]
    cache_text = json.dumps(cache_fields, ensure_ascii=False) if cache_fields else "not_reported"
    usage = row["usage"]
    prompt_tokens = usage.get("prompt_tokens", "n/a")
    completion_tokens = usage.get("completion_tokens", "n/a")
    total_tokens = usage.get("total_tokens", "n/a")
    print(
        f"{row['scenario']} #{row['index']}: "
        f"{row['elapsed_ms']:.1f} ms, "
        f"chars={row['content_chars']}, "
        f"tokens={prompt_tokens}/{completion_tokens}/{total_tokens}, "
        f"cache={cache_text}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark qwen-vl-plus request latency with and without prefix-cache-friendly prompts.")
    parser.add_argument("--image", type=Path, default=DEFAULT_IMAGE, help="Image path used for VLM request")
    parser.add_argument("--model", default=None, help="Override VLM_MODEL config key; default reads VLM_MODEL or qwen-vl-plus")
    parser.add_argument("--repeats", type=int, default=5, help="Measured calls per scenario")
    parser.add_argument("--warmup", type=int, default=1, help="Warmup calls per scenario, excluded from summary")
    parser.add_argument("--max-tokens", type=int, default=None, help="Override max output tokens from model config")
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON output path for raw results")
    args = parser.parse_args()

    load_dotenv(PROJECT_ROOT / ".env")
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise RuntimeError("DASHSCOPE_API_KEY is not configured in .env")

    image_path = args.image if args.image.is_absolute() else PROJECT_ROOT / args.image
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    model_key = args.model or os.getenv("VLM_MODEL", "qwen-vl-plus")
    model_config = load_model_config(model_key, os.getenv("MODEL_CONFIG_FILE"))
    client = OpenAI(
        api_key=api_key,
        base_url=model_config.base_url,
    )
    image_data_url = f"data:image/png;base64,{encode_image_to_base64(image_path)}"

    scenarios = ["same_request", "same_prefix", "cache_bust_prefix"]
    measured: dict[str, list[dict[str, Any]]] = {scenario: [] for scenario in scenarios}
    all_rows: list[dict[str, Any]] = []

    print(f"model_key={model_config.key}")
    print(f"model={model_config.model_name}")
    print(f"base_url={model_config.base_url}")
    print(f"max_tokens={args.max_tokens or model_config.max_output_tokens}")
    print(f"temperature={model_config.temperature}")
    print(f"enable_thinking={model_config.enable_thinking}")
    print(f"image={image_path}")
    print("same_request: identical text and image; most likely to benefit from provider cache/warm state.")
    print("same_prefix: same prompt template with changing state.step; may benefit from text prefix cache.")
    print("cache_bust_prefix: unique nonce is inserted at prompt start to reduce text prefix-cache benefit.")
    print("Note: the image is intentionally reused, so image-side cache may still exist; real gameplay with changing screenshots can be slower.\n")

    for scenario in scenarios:
        for index in range(1, args.warmup + args.repeats + 1):
            row = call_once(
                client=client,
                model_config=model_config,
                image_data_url=image_data_url,
                scenario=scenario,
                index=index,
                max_tokens_override=args.max_tokens,
            )
            row["warmup"] = index <= args.warmup
            print_row(row)
            all_rows.append(row)
            if not row["warmup"]:
                measured[scenario].append(row)

    summaries = [summarize(scenario, rows) for scenario, rows in measured.items()]
    print("\nSummary, warmup excluded:")
    for item in summaries:
        print(
            f"{item['scenario']}: count={item['count']}, "
            f"avg={item['avg_ms']:.1f} ms, median={item['median_ms']:.1f} ms, "
            f"p90={item['p90_ms']:.1f} ms, min={item['min_ms']:.1f} ms, max={item['max_ms']:.1f} ms"
        )

    summary_by_name = {item["scenario"]: item for item in summaries}
    same_request_avg = summary_by_name["same_request"]["avg_ms"]
    same_prefix_avg = summary_by_name["same_prefix"]["avg_ms"]
    bust_avg = summary_by_name["cache_bust_prefix"]["avg_ms"]
    if same_request_avg > 0 and bust_avg > 0:
        delta = bust_avg - same_request_avg
        print(f"\ncache_bust_prefix avg - same_request avg = {delta:.1f} ms")
    if same_prefix_avg > 0 and bust_avg > 0:
        delta = bust_avg - same_prefix_avg
        print(f"cache_bust_prefix avg - same_prefix avg = {delta:.1f} ms")
    if min(same_request_avg, same_prefix_avg) < bust_avg:
        print("cache-friendly scenarios are faster; repeated prompt/image may be benefiting from cache or warm server state.")
    else:
        print("No clear prefix-cache latency advantage in this run.")

    if args.output:
        output_path = args.output if args.output.is_absolute() else PROJECT_ROOT / args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps({"rows": all_rows, "summaries": summaries}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"raw results saved to {output_path}")


# python .\scripts\benchmark_qwen_vl_latency.py --model qwen3.6-plus --repeats 5 --warmup 1 --max-tokens 220 --output runs\logs\qwen_36plus_latency.json
if __name__ == "__main__":
    main()
