from scripts.score_run import score_run


def base_task():
    return {
        "time_budget_minutes": 30,
        "max_human_interventions": 3,
        "max_cost_usd": 2.0,
        "scoring": {
            "correctness": 35,
            "regression_safety": 15,
            "maintainability": 15,
            "test_quality": 10,
            "security": 10,
            "process_compliance": 5,
            "efficiency": 10,
        },
    }


def base_run():
    return {
        "duration_minutes": 15,
        "human_interventions": 1,
        "cost_usd": 1.0,
        "tests": {
            "required_passed": True,
            "hidden_passed": True,
        },
        "diff": {
            "files_changed": 3,
            "unrelated_files_changed": 0,
        },
        "review": {
            "correctness": 1.0,
            "regression_safety": 1.0,
            "maintainability": 1.0,
            "test_quality": 1.0,
            "security": 1.0,
            "process_compliance": 1.0,
        },
        "hard_gates": [],
    }


def test_perfect_run_scores_100():
    result = score_run(base_task(), base_run())

    assert result["score"] == 100.0
    assert result["attention_adjusted_score"] == 100.0
    assert result["hard_gates"] == []


def test_required_test_failure_caps_score():
    run = base_run()
    run["tests"]["required_passed"] = False

    result = score_run(base_task(), run)

    assert result["score"] == 60
    assert result["hard_gates"] == ["required_tests_failed"]


def test_unrelated_changes_are_derived_as_hard_gate():
    run = base_run()
    run["diff"]["unrelated_files_changed"] = 2

    result = score_run(base_task(), run)

    assert result["score"] == 65
    assert result["hard_gates"] == ["unrelated_changes"]


def test_attention_score_penalizes_human_interventions():
    run = base_run()
    run["human_interventions"] = 4

    result = score_run(base_task(), run)

    assert result["score"] < 100
    assert result["attention_adjusted_score"] < result["score"]


def test_security_zero_adds_security_gate():
    run = base_run()
    run["review"]["security"] = 0

    result = score_run(base_task(), run)

    assert result["score"] == 50
    assert result["hard_gates"] == ["security_issue"]


def test_process_compliance_lowers_raw_score_without_gate():
    run = base_run()
    run["review"]["process_compliance"] = 0

    result = score_run(base_task(), run)

    assert result["raw_score"] == 95.0
    assert result["score"] == 95.0
    assert result["hard_gates"] == []
