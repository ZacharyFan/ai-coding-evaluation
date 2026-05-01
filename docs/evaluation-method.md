# Evaluation Method

[Chinese version](evaluation-method.zh-CN.md)

## Fixed Question

The useful question is:

```text
On my real task distribution, which workflow produces acceptable code at the lowest total cost?
```

## Primary Metric

```text
attention_adjusted_score = final_score / max(1, human_interventions)
```

This is blunt on purpose. A workflow that needs constant steering is not cheap, even if the model cost is low.

## Score Formula

```text
final_score =
  0.35 * correctness
+ 0.15 * regression_safety
+ 0.15 * maintainability
+ 0.10 * test_quality
+ 0.10 * security
+ 0.05 * process_compliance
+ 0.10 * efficiency
```

Each component is normalized to `0.0-1.0`, then converted to `0-100`.

## Three-Layer Evidence Model

The benchmark should not stop at "the code looked good in the assistant session." A useful AI coding evaluation keeps three layers separate:

```text
quality   Offline task performance: did the run solve the task safely?
process   Execution evidence: did the agent use the right project context?
outcome   Delivery evidence: did generated code survive into the accepted change?
```

Quality is the default benchmark layer in this repository. Process evidence is captured through `process_compliance` and supporting run metadata. Outcome evidence is represented by optional adoption fields; calculating production adoption rates is intentionally out of scope for v0.2.

## Complexity Matrix

Task `effort_size` and task complexity are orthogonal:

```text
effort_size          How large is the work and budget pressure?
business_complexity  How hard is the business/state/interaction reasoning?
context_maturity     How complete is the docs/API/examples/knowledge context?
```

Examples:

```text
small + L3_complex   Small change, sharp reasoning risk
large + L1_standardized  Lots of work, mostly mechanical
medium + L2_linked   Typical real engineering task
```

Use the matrix to aggregate score heatmaps and locate AI capability boundaries:

```text
L1_standardized  Standard CRUD, simple form, direct bug fix, simple config
L2_linked        Cross-field state, multi-step flow, multi-table logic, integration
L3_complex       Deep custom UI, architecture-level change, complex data flow

C1_complete      Docs, APIs, examples, and project knowledge are enough
C2_partial       Context exists but is incomplete, stale, or scattered
C3_missing       The agent must infer or create missing context
```

High scores in `L1_standardized + C1_complete` prove basic competence. The interesting signal is where a workflow remains reliable as tasks move toward `L2/L3` and `C2/C3`.

## Hard Gates

Hard gates clamp the final score after the weighted score is calculated.

| Gate | Max Score |
| --- | ---: |
| `task_not_solved` | 40 |
| `security_issue` | 50 |
| `public_api_break` | 55 |
| `required_tests_failed` | 60 |
| `unrelated_changes` | 65 |
| `hidden_tests_failed` | 70 |

## What Counts As Evidence

Each run should preserve:

```text
transcript.md   AI/user interaction notes or summarized transcript
diff.patch      final code diff
test.log        required and optional test output
run.json        pre-scoring facts and coding-process evidence
score.json      review scores, hard gates, and final score
```

`prepare_run.py` creates this evidence scaffold and clones the target repo into an isolated run worktree. `execute_run.py` runs target setup/test commands, writes `test.log`, writes `diff.patch`, and updates `run.json`. Human reviewers fill `score.json` directly, or `llm_review_run.py` can ask an OpenAI-compatible LLM to fill the review dimensions. `score_run.py` calculates final score fields.

Extra long-form review notes may be added as custom files in the run directory. They are not part of the standard protocol; structured review notes belong in `score.json.review_notes`.

For v0.2, `run.json` may also preserve optional diagnostic evidence:

```text
process_evidence  Docs, tools, knowledge sources, and self-review trail used during coding
adoption          AI-generated lines, accepted lines, and adoption rate when available
context_metrics   Context call, hit, and adoption rates for knowledge/SPEC/skills analysis
```

## Minimum Valid Comparison

Use the same task set, same model budget, and same run count per workflow.

Probabilities:

```text
5 tasks     80% useful for debugging the benchmark, 30% useful for choosing a workflow
10-15 tasks 60% useful for eliminating weak workflows
30 tasks    75% useful for selecting a main workflow
50+ tasks   80-85% useful for optimizing workflow details
```
