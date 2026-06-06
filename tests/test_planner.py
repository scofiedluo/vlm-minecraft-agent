
from src.planner import DecisionPlanner, extract_json_object


def test_extract_json_object_from_markdown() -> None:
    raw = "```json\n{\"next_skill\": {\"name\": \"explore\", \"args\": {\"radius\": 8}, \"timeoutMs\": 15000}}\n```"
    assert extract_json_object(raw)["next_skill"]["name"] == "explore"


def test_parse_valid_plan_decision() -> None:
    raw = """
    {
      "scene": {"terrain": "forest", "visible_blocks": ["oak_log"], "mobs": [], "risk": "low", "summary": "tree ahead"},
      "plan_update": [{"id": "1", "status": "done"}],
      "next_skill": {"name": "collect_block", "args": {"block":"oak_log","count":3}, "timeoutMs": 30000},
      "reason": "collect wood first",
      "confidence": 0.8
    }
    """
    decision = DecisionPlanner().parse_decision(raw)
    assert decision.next_skill.name == "collect_block"
    assert decision.scene.terrain == "forest"


def test_fallback_without_vlm_client(tmp_path) -> None:
    image = tmp_path / "fake.png"
    image.write_bytes(b"fake")
    decision = DecisionPlanner(vlm_client=None).decide(image, {"goal": "test"})
    assert decision.next_skill.name == "explore"
