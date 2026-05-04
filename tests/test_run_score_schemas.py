import json
from pathlib import Path


def load_schema(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def test_run_schema_is_facts_only():
    schema = load_schema("schemas/run.schema.json")

    assert schema["additionalProperties"] is False
    assert "review" not in schema["properties"]
    assert "score" not in schema["properties"]
    assert "raw_score" not in schema["properties"]
    assert "hard_gates" not in schema["properties"]
    assert schema["properties"]["workflow_id"]["pattern"] == "^(?!.*\\.\\.)[A-Za-z0-9][A-Za-z0-9._-]*$"
    assert schema["properties"]["model"]["type"] == ["string", "null"]
    assert schema["properties"]["cost_usd"]["type"] == ["number", "null"]
    assert schema["properties"]["tests"]["properties"]["hidden_passed"]["type"] == ["boolean", "null"]
    assert schema["properties"]["diff"]["properties"]["unrelated_files_changed"]["type"] == ["integer", "null"]
    assert schema["properties"]["diff"]["properties"]["unrelated_files"]["type"] == ["array", "null"]
    assert schema["properties"]["adoption"]["properties"]["adoption_rate"]["type"] == ["number", "null"]
    assert schema["properties"]["context_metrics"]["properties"]["call_rate"]["type"] == ["number", "null"]
    assert "event_collection" in schema["properties"]
    assert "models_used" in schema["properties"]
    assert "self_review_performed" in schema["properties"]["process_evidence"]["properties"]
    assert "review_performed" not in schema["properties"]["process_evidence"]["properties"]


def test_score_schema_contains_review_and_results():
    schema = load_schema("schemas/score.schema.json")

    assert schema["additionalProperties"] is False
    assert "review" in schema["required"]
    assert "score" not in schema["required"]
    assert "raw_score" not in schema["required"]
    assert schema["properties"]["workflow_id"]["pattern"] == "^(?!.*\\.\\.)[A-Za-z0-9][A-Za-z0-9._-]*$"
    assert schema["properties"]["review"]["properties"]["correctness"]["type"] == ["number", "null"]
    assert "manual_hard_gates" in schema["properties"]
    assert "derived_hard_gates" in schema["properties"]
    assert "derived_hard_gates" not in schema["required"]
    assert "hard_gates" not in schema["required"]
