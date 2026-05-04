#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.dashboard_i18n import LOCALES
from scripts.report_data import collect_runs, is_number, is_scored


def esc(value: Any) -> str:
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def json_for_script(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=True, sort_keys=True)
    return payload.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")


def unique_values(records: list[dict[str, Any]], key: str) -> list[str]:
    values = {str(record.get(key)) for record in records if record.get(key) not in (None, "")}
    return sorted(values)


def option_tags(values: list[str]) -> str:
    return "".join(f'<option value="{esc(value)}">{esc(value)}</option>' for value in values)


def sample_size_note(records: list[dict[str, Any]], locale: str) -> str:
    tasks = {record.get("task_id") for record in records if record.get("task_id")}
    count = len(tasks)
    if locale == "zh-CN":
        if count < 5:
            return f"{count} 个任务：只适合调试 benchmark。"
        if count < 10:
            return f"{count} 个任务：主要仍是 benchmark 调试信号。"
        if count <= 15:
            return f"{count} 个任务：适合淘汰较弱工作流。"
        if count < 30:
            return f"{count} 个任务：已有价值，但选择主力工作流仍偏轻。"
        return f"{count} 个任务：适合选择主力工作流。"
    if count < 5:
        return f"{count} task{'s' if count != 1 else ''}: debugging signal only."
    if count < 10:
        return f"{count} tasks: still mostly benchmark-debugging signal."
    if count <= 15:
        return f"{count} tasks: useful for eliminating weak workflows."
    if count < 30:
        return f"{count} tasks: useful, but still light for choosing a primary workflow."
    return f"{count} tasks: useful for choosing a primary workflow."


def dashboard_records(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records = []
    for run in runs:
        tests = run.get("tests", {})
        diff = run.get("diff", {})
        hard_gates = run.get("hard_gates") if isinstance(run.get("hard_gates"), list) else []
        records.append(
            {
                "workflow_id": run.get("workflow_id") or "",
                "model": run.get("model_label") or "unknown",
                "task_id": run.get("task_id") or "",
                "run_id": run.get("run_id") or "",
                "task_type": run.get("task_type") or "unknown",
                "effort_size": run.get("effort_size") or "unknown",
                "business_complexity": run.get("business_complexity") or "unknown",
                "context_maturity": run.get("context_maturity") or "unknown",
                "score": run.get("score") if is_number(run.get("score")) else None,
                "raw_score": run.get("raw_score") if is_number(run.get("raw_score")) else None,
                "attention_adjusted_score": run.get("attention_adjusted_score")
                if is_number(run.get("attention_adjusted_score"))
                else None,
                "duration_minutes": run.get("duration_minutes") if is_number(run.get("duration_minutes")) else None,
                "human_interventions": run.get("human_interventions")
                if is_number(run.get("human_interventions"))
                else None,
                "required_passed": tests.get("required_passed") if isinstance(tests.get("required_passed"), bool) else None,
                "hidden_passed": tests.get("hidden_passed") if isinstance(tests.get("hidden_passed"), bool) else None,
                "unrelated_files_changed": diff.get("unrelated_files_changed")
                if is_number(diff.get("unrelated_files_changed"))
                else None,
                "hard_gates": hard_gates,
                "path": run.get("_path") or "",
                "scored": is_scored(run),
            }
        )
    return records


def filters(records: list[dict[str, Any]], labels: dict[str, Any]) -> str:
    filter_labels = labels["filters"]
    fields = [
        ("taskFilter", filter_labels["task"], "task_id"),
        ("workflowFilter", filter_labels["workflow"], "workflow_id"),
        ("modelFilter", filter_labels["model"], "model"),
        ("typeFilter", filter_labels["type"], "task_type"),
        ("effortFilter", filter_labels["effort"], "effort_size"),
        ("businessFilter", filter_labels["business"], "business_complexity"),
        ("contextFilter", filter_labels["context"], "context_maturity"),
    ]
    controls = []
    for element_id, label, key in fields:
        controls.append(
            f'<label>{esc(label)}<select id="{element_id}"><option value="">{esc(filter_labels["all"])}</option>{option_tags(unique_values(records, key))}</select></label>'
        )
    controls.append(
        f'<label class="check"><input id="scoredOnly" type="checkbox"> {esc(filter_labels["scored_only"])}</label>'
    )
    return (
        '<section class="filter-panel">'
        f'<div class="section-head"><h2>{esc(filter_labels["title"])}</h2></div>'
        f'<div class="filters">{"".join(controls)}</div>'
        "</section>"
    )


HTML_TEMPLATE = """<!doctype html>
<html lang="%%LANG%%">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>%%TITLE%%</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f8fafc;
      --panel: #ffffff;
      --panel-soft: #f1f5f9;
      --text: #0f172a;
      --muted: #64748b;
      --faint: #94a3b8;
      --line: #d7dee8;
      --line-strong: #cbd5e1;
      --blue: #1e40af;
      --blue-soft: #dbeafe;
      --blue-text: #1e3a8a;
      --green-bg: #dcfce7;
      --green-text: #166534;
      --amber-bg: #fef3c7;
      --amber-text: #92400e;
      --red-bg: #fee2e2;
      --red-text: #991b1b;
      --gray-bg: #e2e8f0;
      --shadow: 0 1px 2px rgba(15, 23, 42, 0.06), 0 10px 24px rgba(15, 23, 42, 0.04);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font: 14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    main { max-width: 1520px; margin: 0 auto; padding: 28px; }
    header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 24px;
      margin-bottom: 16px;
      padding: 22px 24px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 10px;
      box-shadow: var(--shadow);
    }
    h1 { font-size: 28px; line-height: 1.15; margin: 0 0 8px; letter-spacing: 0; }
    h2 { font-size: 15px; line-height: 1.2; margin: 0; letter-spacing: 0; }
    p { margin: 0; color: var(--muted); }
    .eyebrow {
      color: var(--blue);
      font-size: 12px;
      font-weight: 700;
      letter-spacing: .08em;
      margin-bottom: 8px;
      text-transform: uppercase;
    }
    section, .metric-card {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 10px;
      box-shadow: var(--shadow);
    }
    section { padding: 16px; margin-top: 14px; }
    .section-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 12px;
    }
    .sample-note {
      color: var(--amber-text);
      background: var(--amber-bg);
      border: 1px solid #f2d48b;
      border-radius: 999px;
      padding: 8px 12px;
      white-space: nowrap;
      font-weight: 650;
      box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.45);
    }
    .metrics { display: grid; grid-template-columns: repeat(6, minmax(128px, 1fr)); gap: 12px; }
    .metric-card {
      position: relative;
      overflow: hidden;
      min-height: 92px;
      padding: 16px 16px 14px;
      transition: border-color 160ms ease, box-shadow 160ms ease;
    }
    .metric-card::before {
      content: "";
      position: absolute;
      inset: 0 auto 0 0;
      width: 4px;
      background: var(--blue);
    }
    .metric-card:hover { border-color: var(--line-strong); box-shadow: 0 8px 22px rgba(15, 23, 42, 0.08); }
    .metric-card span { display: block; color: var(--muted); font-size: 12px; font-weight: 650; margin-bottom: 8px; text-transform: uppercase; }
    .metric-card strong { font-size: 30px; line-height: 1; letter-spacing: 0; }
    .filter-panel { padding: 14px 16px 16px; }
    .filters { display: flex; flex-wrap: wrap; gap: 10px; align-items: end; }
    label { display: grid; gap: 6px; color: var(--muted); font-size: 12px; font-weight: 650; }
    select, input[type="checkbox"] { accent-color: var(--blue); }
    select {
      min-width: 150px;
      height: 38px;
      border: 1px solid var(--line);
      border-radius: 7px;
      background: white;
      padding: 0 34px 0 10px;
      color: var(--text);
      cursor: pointer;
    }
    select:hover { border-color: var(--line-strong); }
    select:focus-visible, input:focus-visible, th:focus-visible {
      outline: 3px solid rgba(59, 130, 246, 0.28);
      outline-offset: 2px;
    }
    label.check {
      display: flex;
      align-items: center;
      gap: 8px;
      height: 38px;
      padding: 0 10px;
      color: var(--text);
      background: var(--panel-soft);
      border: 1px solid var(--line);
      border-radius: 7px;
      cursor: pointer;
    }
    table { width: 100%; border-collapse: collapse; }
    th, td { border-bottom: 1px solid var(--line); padding: 9px 10px; text-align: left; vertical-align: top; }
    th {
      color: #475569;
      font-weight: 750;
      font-size: 12px;
      background: #f8fafc;
      position: sticky;
      top: 0;
      z-index: 1;
      text-transform: uppercase;
    }
    tbody tr:nth-child(even) { background: #fbfdff; }
    tbody tr:hover { background: #eff6ff; }
    .compact td, .compact th { white-space: nowrap; }
    .table-scroll { overflow-x: auto; }
    .section-note { margin: -4px 0 12px; }
    .heatmap th:first-child { min-width: 180px; }
    .heat { min-width: 158px; border-left: 4px solid transparent; }
    .heat strong, .heat span { display: block; }
    .heat strong { font-size: 20px; line-height: 1.05; }
    .heat span { color: var(--muted); font-size: 12px; margin-top: 4px; }
    .score-high { background: var(--green-bg); color: var(--green-text); border-left-color: #2c9f5b; }
    .score-good { background: var(--blue-soft); color: var(--blue-text); border-left-color: #4285d9; }
    .score-mid { background: var(--amber-bg); color: var(--amber-text); border-left-color: #d6981b; }
    .score-low { background: var(--red-bg); color: var(--red-text); border-left-color: #cc3b2f; }
    .score-empty { background: var(--gray-bg); color: var(--muted); }
    .score-cell { font-weight: 750; }
    code { font-size: 12px; color: #334155; white-space: nowrap; }
    .details-wrap { max-height: 640px; overflow: auto; border: 1px solid var(--line); border-radius: 8px; }
    .bool-pill, .gate-pill {
      display: inline-flex;
      align-items: center;
      min-height: 22px;
      border-radius: 999px;
      padding: 2px 8px;
      font-size: 12px;
      font-weight: 700;
      white-space: nowrap;
    }
    .pill-pass { background: var(--green-bg); color: var(--green-text); }
    .pill-fail { background: var(--red-bg); color: var(--red-text); }
    .pill-empty { background: var(--gray-bg); color: #475569; }
    .gate-pill { background: var(--red-bg); color: var(--red-text); margin: 0 4px 4px 0; }
    #emptyState { display: none; color: var(--muted); padding: 12px 0 0; }
    @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after { transition: none !important; scroll-behavior: auto !important; }
    }
    @media (max-width: 900px) {
      main { padding: 18px; }
      header { display: block; }
      .sample-note { margin-top: 12px; white-space: normal; }
      .metrics { grid-template-columns: repeat(2, minmax(120px, 1fr)); }
    }
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <div class="eyebrow">%%EYEBROW%%</div>
        <h1>%%TITLE%%</h1>
        <p>%%SUBTITLE%%</p>
      </div>
      <div class="sample-note">%%NOTE%%</div>
    </header>

    <div id="metrics" class="metrics"></div>
    %%FILTERS%%

    <section>
      <div class="section-head">
        <h2>%%HEATMAP_TITLE%%</h2>
      </div>
      <p class="section-note">%%HEATMAP_NOTE%%</p>
      <div class="table-scroll">
        <table id="heatmap" class="heatmap"></table>
      </div>
    </section>

    <section>
      <div class="section-head">
        <h2>%%WORKFLOW_TITLE%%</h2>
      </div>
      <table id="workflowComparison" class="compact"></table>
    </section>

    <section>
      <div class="section-head">
        <h2>%%MODEL_TITLE%%</h2>
      </div>
      <table id="modelComparison" class="compact"></table>
    </section>

    <section>
      <div class="section-head">
        <h2>%%DETAILS_TITLE%%</h2>
      </div>
      <div class="details-wrap">
        <table id="runsTable">
          <thead>
            <tr>
              %%RUN_HEADERS%%
            </tr>
          </thead>
          <tbody id="runsBody"></tbody>
        </table>
      </div>
      <p id="emptyState">%%EMPTY_STATE%%</p>
    </section>
  </main>

  <script id="runs-data" type="application/json">%%DATA%%</script>
  <script id="dashboard-labels" type="application/json">%%LABELS%%</script>
  <script>
    const allRuns = JSON.parse(document.getElementById("runs-data").textContent);
    const labels = JSON.parse(document.getElementById("dashboard-labels").textContent);
    const filters = [
      ["taskFilter", "task_id"],
      ["workflowFilter", "workflow_id"],
      ["modelFilter", "model"],
      ["typeFilter", "task_type"],
      ["effortFilter", "effort_size"],
      ["businessFilter", "business_complexity"],
      ["contextFilter", "context_maturity"]
    ];

    function isNumber(value) {
      return typeof value === "number" && Number.isFinite(value);
    }

    function scored(run) {
      return isNumber(run.score);
    }

    function escapeHtml(value) {
      return String(value ?? "").replace(/[&<>"']/g, (char) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
      })[char]);
    }

    function fmtNumber(value, digits = 2) {
      return isNumber(value) ? value.toFixed(digits) : "-";
    }

    function fmtRate(value) {
      return isNumber(value) ? Math.round(value * 100) + "%" : "-";
    }

    function fmtBool(value) {
      if (value === true) return labels.js.pass;
      if (value === false) return labels.js.fail;
      return "-";
    }

    function boolPill(value) {
      const klass = value === true ? "pill-pass" : value === false ? "pill-fail" : "pill-empty";
      return '<span class="bool-pill ' + klass + '">' + escapeHtml(fmtBool(value)) + '</span>';
    }

    function scoreCell(value) {
      return '<td class="score-cell ' + scoreClass(value) + '">' + fmtNumber(value) + '</td>';
    }

    function gatePills(gates) {
      if (!gates || !gates.length) return '<span class="bool-pill pill-empty">-</span>';
      return gates.map((gate) => '<span class="gate-pill">' + escapeHtml(gate) + '</span>').join("");
    }

    function mean(values) {
      const numeric = values.filter(isNumber);
      if (!numeric.length) return null;
      return numeric.reduce((sum, value) => sum + value, 0) / numeric.length;
    }

    function firstPass(run) {
      return run.required_passed === true && (!run.hard_gates || run.hard_gates.length === 0);
    }

    function summarize(runs) {
      const scoredRuns = runs.filter(scored);
      const gated = scoredRuns.filter((run) => run.hard_gates && run.hard_gates.length > 0);
      const firstPasses = scoredRuns.filter(firstPass);
      return {
        runs: runs.length,
        scored_runs: scoredRuns.length,
        avg_score: mean(scoredRuns.map((run) => run.score)),
        avg_attention_score: mean(scoredRuns.map((run) => run.attention_adjusted_score)),
        avg_duration_minutes: mean(scoredRuns.map((run) => run.duration_minutes)),
        avg_human_interventions: mean(scoredRuns.map((run) => run.human_interventions)),
        first_pass_rate: scoredRuns.length ? firstPasses.length / scoredRuns.length : null,
        gate_rate: scoredRuns.length ? gated.length / scoredRuns.length : null
      };
    }

    function groupBy(runs, key) {
      return runs.reduce((groups, run) => {
        const label = run[key] || labels.js.unknown;
        if (!groups[label]) groups[label] = [];
        groups[label].push(run);
        return groups;
      }, {});
    }

    function scoreClass(value) {
      if (!isNumber(value)) return "score-empty";
      if (value >= 90) return "score-high";
      if (value >= 75) return "score-good";
      if (value >= 60) return "score-mid";
      return "score-low";
    }

    function renderMetrics(runs) {
      const summary = summarize(runs);
      const cards = [
        [labels.metrics.runs, String(summary.runs)],
        [labels.metrics.scored, String(summary.scored_runs)],
        [labels.metrics.avg_final, fmtNumber(summary.avg_score)],
        [labels.metrics.avg_attention, fmtNumber(summary.avg_attention_score)],
        [labels.metrics.first_pass, fmtRate(summary.first_pass_rate)],
        [labels.metrics.gate_rate, fmtRate(summary.gate_rate)]
      ];
      document.getElementById("metrics").innerHTML = cards.map(([label, value]) =>
        '<div class="metric-card"><span>' + escapeHtml(label) + '</span><strong>' + escapeHtml(value) + '</strong></div>'
      ).join("");
    }

    function renderHeatmap(runs) {
      const tasks = Array.from(new Set(runs.map((run) => run.task_id).filter(Boolean))).sort();
      const workflows = Array.from(new Set(runs.map((run) => run.workflow_id).filter(Boolean))).sort();
      const header = '<thead><tr><th>' + escapeHtml(labels.filters.task) + '</th>' + workflows.map((workflow) => '<th>' + escapeHtml(workflow) + '</th>').join("") + '</tr></thead>';
      const body = tasks.map((task) => {
        const cells = workflows.map((workflow) => {
          const items = runs.filter((run) => run.task_id === task && run.workflow_id === workflow && scored(run));
          if (!items.length) return '<td class="heat score-empty"><span>' + escapeHtml(labels.js.unscored) + '</span></td>';
          const summary = summarize(items);
          const gated = items.filter((run) => run.hard_gates && run.hard_gates.length > 0).length;
          return '<td class="heat ' + scoreClass(summary.avg_score) + '">' +
            '<strong>' + fmtNumber(summary.avg_score) + '</strong>' +
            '<span>' + escapeHtml(labels.js.attention_prefix) + ' ' + fmtNumber(summary.avg_attention_score) + '</span>' +
            '<span>' + items.length + ' ' + escapeHtml(items.length === 1 ? labels.js.run_one : labels.js.run_many) + ', ' + gated + ' ' + escapeHtml(labels.js.gated) + '</span>' +
            '</td>';
        }).join("");
        return '<tr><th>' + escapeHtml(task) + '</th>' + cells + '</tr>';
      }).join("");
      document.getElementById("heatmap").innerHTML = header + '<tbody>' + body + '</tbody>';
    }

    function renderComparison(elementId, runs, key) {
      const groups = groupBy(runs, key);
      const rows = Object.keys(groups).sort().map((label) => {
        const summary = summarize(groups[label]);
        return '<tr>' +
          '<td>' + escapeHtml(label) + '</td>' +
          '<td>' + summary.runs + '</td>' +
          '<td>' + summary.scored_runs + '</td>' +
          '<td class="score-cell ' + scoreClass(summary.avg_score) + '">' + fmtNumber(summary.avg_score) + '</td>' +
          '<td>' + fmtNumber(summary.avg_attention_score) + '</td>' +
          '<td>' + fmtRate(summary.first_pass_rate) + '</td>' +
          '<td>' + fmtRate(summary.gate_rate) + '</td>' +
          '<td>' + fmtNumber(summary.avg_duration_minutes) + '</td>' +
          '<td>' + fmtNumber(summary.avg_human_interventions) + '</td>' +
          '</tr>';
      }).join("");
      document.getElementById(elementId).innerHTML =
        '<thead><tr>' + labels.comparison_headers.map((header) => '<th>' + escapeHtml(header) + '</th>').join("") + '</tr></thead>' +
        '<tbody>' + rows + '</tbody>';
    }

    function renderRows(runs) {
      document.getElementById("runsBody").innerHTML = runs.map((run) => {
        return '<tr>' +
          '<td>' + escapeHtml(run.workflow_id) + '</td>' +
          '<td>' + escapeHtml(run.model) + '</td>' +
          '<td>' + escapeHtml(run.task_id) + '</td>' +
          '<td>' + escapeHtml(run.run_id) + '</td>' +
          '<td>' + escapeHtml(run.task_type) + '</td>' +
          '<td>' + escapeHtml(run.effort_size) + '</td>' +
          '<td>' + escapeHtml(run.business_complexity) + '</td>' +
          '<td>' + escapeHtml(run.context_maturity) + '</td>' +
          scoreCell(run.score) +
          '<td>' + fmtNumber(run.raw_score) + '</td>' +
          '<td>' + fmtNumber(run.attention_adjusted_score) + '</td>' +
          '<td>' + fmtNumber(run.duration_minutes) + '</td>' +
          '<td>' + fmtNumber(run.human_interventions, 0) + '</td>' +
          '<td>' + boolPill(run.required_passed) + '</td>' +
          '<td>' + boolPill(run.hidden_passed) + '</td>' +
          '<td>' + fmtNumber(run.unrelated_files_changed, 0) + '</td>' +
          '<td>' + gatePills(run.hard_gates) + '</td>' +
          '<td><code>' + escapeHtml(run.path) + '</code></td>' +
          '</tr>';
      }).join("");
      document.getElementById("emptyState").style.display = runs.length ? "none" : "block";
    }

    function currentRuns() {
      const scoredOnly = document.getElementById("scoredOnly").checked;
      return allRuns.filter((run) => {
        const matchesSelects = filters.every(([id, key]) => {
          const selected = document.getElementById(id).value;
          return !selected || run[key] === selected;
        });
        return matchesSelects && (!scoredOnly || scored(run));
      });
    }

    function renderAll() {
      const runs = currentRuns();
      renderMetrics(runs);
      renderHeatmap(runs);
      renderComparison("workflowComparison", runs, "workflow_id");
      renderComparison("modelComparison", runs, "model");
      renderRows(runs);
    }

    function sortTable(column) {
      const tbody = document.getElementById("runsBody");
      const rows = Array.from(tbody.querySelectorAll("tr"));
      const current = Number(tbody.dataset.sortColumn || -1);
      const direction = current === column && tbody.dataset.sortDirection !== "desc" ? "desc" : "asc";
      rows.sort((a, b) => {
        const left = a.children[column].innerText.trim();
        const right = b.children[column].innerText.trim();
        const leftNum = Number(left);
        const rightNum = Number(right);
        const bothNumeric = !Number.isNaN(leftNum) && !Number.isNaN(rightNum);
        const result = bothNumeric ? leftNum - rightNum : left.localeCompare(right);
        return direction === "asc" ? result : -result;
      });
      tbody.dataset.sortColumn = String(column);
      tbody.dataset.sortDirection = direction;
      rows.forEach((row) => tbody.appendChild(row));
    }

    filters.forEach(([id]) => document.getElementById(id).addEventListener("change", renderAll));
    document.getElementById("scoredOnly").addEventListener("change", renderAll);
    document.querySelectorAll("#runsTable th").forEach((header, index) => {
      header.tabIndex = 0;
      header.addEventListener("click", () => sortTable(index));
      header.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          sortTable(index);
        }
      });
      header.style.cursor = "pointer";
    });
    renderAll();
  </script>
</body>
</html>
"""


def run_header_html(labels: dict[str, Any]) -> str:
    return "\n              ".join(f"<th>{esc(header)}</th>" for header in labels["run_headers"])


def zh_output_path(output: Path) -> Path:
    return output.with_name(f"{output.stem}.zh-CN{output.suffix or '.html'}")


def dashboard_html(runs: list[dict[str, Any]], locale: str = "en") -> str:
    if locale not in LOCALES:
        raise ValueError(f"unsupported dashboard locale: {locale}")
    labels = LOCALES[locale]
    sections = labels["sections"]
    records = dashboard_records(runs)
    return (
        HTML_TEMPLATE.replace("%%LANG%%", esc(labels["html_lang"]))
        .replace("%%EYEBROW%%", esc(labels["eyebrow"]))
        .replace("%%TITLE%%", esc(labels["title"]))
        .replace("%%SUBTITLE%%", esc(labels["subtitle"]))
        .replace("%%NOTE%%", esc(sample_size_note(records, locale)))
        .replace("%%FILTERS%%", filters(records, labels))
        .replace("%%HEATMAP_TITLE%%", esc(sections["heatmap"]))
        .replace("%%HEATMAP_NOTE%%", esc(sections["heatmap_note"]))
        .replace("%%WORKFLOW_TITLE%%", esc(sections["workflow"]))
        .replace("%%MODEL_TITLE%%", esc(sections["model"]))
        .replace("%%DETAILS_TITLE%%", esc(sections["details"]))
        .replace("%%RUN_HEADERS%%", run_header_html(labels))
        .replace("%%EMPTY_STATE%%", esc(labels["js"]["empty_state"]))
        .replace("%%LABELS%%", json_for_script(labels))
        .replace("%%DATA%%", json_for_script(records))
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a static HTML comparison dashboard.")
    parser.add_argument("--runs", type=Path, default=Path("runs"), help="Runs root directory")
    parser.add_argument("--tasks", type=Path, default=Path("benchmarks/tasks"), help="Benchmark tasks root directory")
    parser.add_argument("--output", type=Path, default=Path("reports/dashboard.html"), help="Output HTML path")
    parser.add_argument("--zh-output", type=Path, default=None, help="Chinese dashboard output path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    runs = collect_runs(args.runs, args.tasks)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    zh_path = args.zh_output or zh_output_path(args.output)
    zh_path.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(dashboard_html(runs, "en"), encoding="utf-8")
    zh_path.write_text(dashboard_html(runs, "zh-CN"), encoding="utf-8")
    print(args.output)
    print(zh_path)


if __name__ == "__main__":
    main()
