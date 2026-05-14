#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

DEFAULT_TASKS = Path("benchmarks/tasks")
DEFAULT_OUTPUT = Path("benchmarks/index.html")


LOCALES: dict[str, dict[str, Any]] = {
    "en": {
        "lang": "en",
        "title": "Benchmark Task Registry",
        "brand": "Benchmark Registry",
        "readme": "../README.md",
        "switch_href": "index.zh-CN.html",
        "switch_label": "中文",
        "source": "Task source",
        "eyebrow": "benchmarks/tasks snapshot",
        "hero_title": "Executable benchmark tasks, one screen.",
        "hero_copy": (
            "A static registry for public benchmark tasks: type, complexity, context maturity, "
            "budget, scope, checks, and the exact evaluation command."
        ),
        "summary_aria": "Benchmark summary",
        "task_total": "Executable tasks",
        "task_total_note": "Every task has task.json and executable tests.sh.",
        "type_total": "Task types",
        "type_total_note": "Bugfix, feature, refactor, test.",
        "matrix_total": "Complexity cells",
        "matrix_total_note": "L1-L3 crossed with C1-C3.",
        "median_budget": "Median budget",
        "budget_range": "Budget range:",
        "budget_unit": "minutes",
        "filters": "Filters",
        "search_tasks": "Search tasks",
        "search_placeholder": "Search by title, id, scope, scenario...",
        "type": "Type",
        "effort": "Effort",
        "complexity": "Complexity",
        "sort": "Sort",
        "type_aria": "Task type",
        "effort_aria": "Effort size",
        "complexity_aria": "Business complexity",
        "sort_aria": "Sort tasks",
        "sort_id": "Sort by id",
        "sort_time": "Sort by time budget",
        "sort_cost": "Sort by cost budget",
        "sort_type": "Sort by type",
        "registry_title": "Merged Tasks",
        "showing": "Showing {shown} of {total}",
        "empty_title": "No matching tasks",
        "empty_copy": "Tighten the question less: remove a filter or use a broader keyword.",
        "all_types": "All types",
        "all_efforts": "All efforts",
        "all_complexity": "All complexity",
        "metric_budget": "budget",
        "metric_cost": "max cost",
        "metric_interventions": "interventions",
        "hidden_checks": "{count} hidden checks",
        "context_sources": "{count} context sources",
        "more_paths": "+{count} paths",
        "task_link": "Task",
        "json_link": "JSON",
        "tests_link": "Tests",
        "labels": {
            "all": "All",
            "bugfix": "Bugfix",
            "feature": "Feature",
            "refactor": "Refactor",
            "test": "Test",
            "small": "Small",
            "medium": "Medium",
            "large": "Large",
            "L1_standardized": "L1 standardized",
            "L2_linked": "L2 linked",
            "L3_complex": "L3 complex",
            "C1_complete": "C1 complete",
            "C2_partial": "C2 partial",
            "C3_missing": "C3 missing",
        },
    },
    "zh-CN": {
        "lang": "zh-CN",
        "title": "Benchmark 任务索引",
        "brand": "Benchmark 任务索引",
        "readme": "../README.zh-CN.md",
        "switch_href": "index.html",
        "switch_label": "English",
        "source": "任务源码",
        "eyebrow": "benchmarks/tasks 快照",
        "hero_title": "可执行 Benchmark 任务，一屏掌握。",
        "hero_copy": (
            "一个静态任务索引，展示公开测评任务矩阵的类型、复杂度、上下文成熟度、"
            "预算、范围、检查项和精确复现命令。"
        ),
        "summary_aria": "Benchmark 摘要",
        "task_total": "可执行任务",
        "task_total_note": "每个任务都有 task.json 和可执行 tests.sh。",
        "type_total": "任务类型",
        "type_total_note": "修复、功能、重构、测试。",
        "matrix_total": "复杂度单元",
        "matrix_total_note": "L1-L3 与 C1-C3 交叉。",
        "median_budget": "预算中位数",
        "budget_range": "预算范围：",
        "budget_unit": "分钟",
        "filters": "筛选器",
        "search_tasks": "搜索任务",
        "search_placeholder": "按标题、ID、范围、场景搜索...",
        "type": "类型",
        "effort": "规模",
        "complexity": "复杂度",
        "sort": "排序",
        "type_aria": "任务类型",
        "effort_aria": "任务规模",
        "complexity_aria": "业务复杂度",
        "sort_aria": "任务排序",
        "sort_id": "按 ID 排序",
        "sort_time": "按时间预算排序",
        "sort_cost": "按成本预算排序",
        "sort_type": "按类型排序",
        "registry_title": "任务清单",
        "showing": "显示 {shown} / {total}",
        "empty_title": "没有匹配任务",
        "empty_copy": "问题别收得太窄：移除一个筛选条件，或换一个更宽的关键词。",
        "all_types": "全部类型",
        "all_efforts": "全部规模",
        "all_complexity": "全部复杂度",
        "metric_budget": "预算",
        "metric_cost": "最高成本",
        "metric_interventions": "人工介入",
        "hidden_checks": "{count} 个隐藏检查",
        "context_sources": "{count} 类上下文源",
        "more_paths": "+{count} 个路径",
        "task_link": "任务",
        "json_link": "JSON",
        "tests_link": "测试",
        "labels": {
            "all": "全部",
            "bugfix": "修复",
            "feature": "功能",
            "refactor": "重构",
            "test": "测试",
            "small": "小",
            "medium": "中",
            "large": "大",
            "L1_standardized": "L1 标准化",
            "L2_linked": "L2 联动",
            "L3_complex": "L3 复杂",
            "C1_complete": "C1 完整",
            "C2_partial": "C2 部分",
            "C3_missing": "C3 缺失",
        },
    },
}


STYLE = """
    :root {
      --bg: #f6f7f2;
      --surface: #ffffff;
      --ink: #172033;
      --muted: #607085;
      --line: #d9dfda;
      --line-strong: #c3ccc5;
      --green: #147a4b;
      --green-soft: #e6f4ec;
      --blue: #2857a4;
      --blue-soft: #e7eefb;
      --rose: #a8374f;
      --rose-soft: #fae8ed;
      --violet: #6846a3;
      --violet-soft: #efe9fb;
      --shadow: 0 18px 45px rgba(23, 32, 51, 0.08);
      color-scheme: light;
    }

    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }

    body {
      margin: 0;
      background:
        linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(246, 247, 242, 0.96) 320px),
        var(--bg);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 16px;
      line-height: 1.55;
    }

    a { color: inherit; text-decoration: none; }
    button, input, select { font: inherit; }
    button, select { cursor: pointer; }

    :focus-visible {
      outline: 3px solid rgba(20, 122, 75, 0.42);
      outline-offset: 3px;
    }

    .visually-hidden {
      position: absolute;
      width: 1px;
      height: 1px;
      margin: -1px;
      border: 0;
      padding: 0;
      clip: rect(0 0 0 0);
      overflow: hidden;
      white-space: nowrap;
    }

    .page { min-height: 100vh; }

    .topbar {
      position: sticky;
      top: 0;
      z-index: 20;
      border-bottom: 1px solid rgba(217, 223, 218, 0.82);
      background: rgba(246, 247, 242, 0.9);
      backdrop-filter: blur(14px);
    }

    .nav {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 18px;
      width: min(1180px, calc(100% - 32px));
      margin: 0 auto;
      padding: 14px 0;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 10px;
      min-width: 0;
      font-weight: 750;
      letter-spacing: 0;
    }

    .brand-mark {
      display: grid;
      width: 34px;
      height: 34px;
      border: 1px solid #111827;
      background: #111827;
      color: #ffffff;
      place-items: center;
    }

    .brand small {
      display: block;
      color: var(--muted);
      font-size: 12px;
      font-weight: 650;
      line-height: 1.1;
    }

    .nav-actions {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      justify-content: flex-end;
    }

    .link-button {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      min-height: 40px;
      border: 1px solid var(--line-strong);
      border-radius: 8px;
      background: var(--surface);
      padding: 8px 12px;
      color: var(--ink);
      font-size: 14px;
      font-weight: 700;
      transition: border-color 180ms ease, transform 180ms ease, box-shadow 180ms ease;
    }

    .link-button:hover {
      border-color: #111827;
      box-shadow: 0 10px 24px rgba(23, 32, 51, 0.08);
      transform: translateY(-1px);
    }

    .link-button.primary {
      border-color: #111827;
      background: #111827;
      color: #ffffff;
    }

    .icon {
      width: 16px;
      height: 16px;
      flex: 0 0 auto;
      stroke: currentColor;
      stroke-width: 2;
      stroke-linecap: round;
      stroke-linejoin: round;
      fill: none;
    }

    .hero {
      width: min(1180px, calc(100% - 32px));
      margin: 0 auto;
      padding: 54px 0 28px;
    }

    .eyebrow {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      border: 1px solid var(--line-strong);
      border-radius: 999px;
      background: var(--surface);
      padding: 6px 10px;
      color: var(--green);
      font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
      font-size: 12px;
      font-weight: 750;
      text-transform: uppercase;
    }

    h1 {
      max-width: 980px;
      margin: 18px 0 14px;
      font-size: 48px;
      line-height: 1.04;
      letter-spacing: 0;
    }

    .locale-zh h1 {
      max-width: none;
      font-size: 42px;
      white-space: nowrap;
    }

    .hero-copy {
      max-width: 780px;
      margin: 0;
      color: var(--muted);
      font-size: 18px;
    }

    .summary-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      width: min(1180px, calc(100% - 32px));
      margin: 0 auto;
      padding: 14px 0 22px;
    }

    .summary-card {
      min-height: 120px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--surface);
      padding: 18px;
      box-shadow: 0 8px 20px rgba(23, 32, 51, 0.04);
    }

    .summary-label {
      color: var(--muted);
      font-size: 12px;
      font-weight: 800;
      letter-spacing: 0;
      text-transform: uppercase;
    }

    .summary-value {
      margin-top: 8px;
      color: var(--ink);
      font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
      font-size: 34px;
      font-weight: 800;
      line-height: 1;
    }

    .summary-note {
      margin-top: 8px;
      color: var(--muted);
      font-size: 13px;
    }

    .controls-band {
      border-block: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.72);
    }

    .controls {
      display: grid;
      grid-template-columns: minmax(220px, 1fr) repeat(4, minmax(132px, 170px));
      gap: 10px;
      width: min(1180px, calc(100% - 32px));
      margin: 0 auto;
      padding: 16px 0;
    }

    .field {
      position: relative;
      min-width: 0;
    }

    .field svg {
      position: absolute;
      left: 12px;
      top: 50%;
      color: var(--muted);
      transform: translateY(-50%);
      pointer-events: none;
    }

    .search-input,
    .select-input {
      width: 100%;
      min-height: 44px;
      border: 1px solid var(--line-strong);
      border-radius: 8px;
      background: var(--surface);
      color: var(--ink);
      padding: 10px 12px;
    }

    .search-input { padding-left: 40px; }

    .select-input {
      appearance: none;
      padding-right: 34px;
      background-image:
        linear-gradient(45deg, transparent 50%, var(--muted) 50%),
        linear-gradient(135deg, var(--muted) 50%, transparent 50%);
      background-position:
        calc(100% - 17px) 19px,
        calc(100% - 11px) 19px;
      background-size: 6px 6px, 6px 6px;
      background-repeat: no-repeat;
    }

    .registry {
      width: min(1180px, calc(100% - 32px));
      margin: 0 auto;
      padding: 24px 0 56px;
    }

    .registry-head {
      display: flex;
      align-items: end;
      justify-content: space-between;
      gap: 18px;
      margin-bottom: 14px;
    }

    .registry-title {
      margin: 0;
      font-size: 22px;
      line-height: 1.15;
    }

    .result-count {
      color: var(--muted);
      font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
      font-size: 13px;
      white-space: nowrap;
    }

    .task-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      grid-auto-rows: 1fr;
      gap: 14px;
      align-items: stretch;
    }

    .task-card {
      display: flex;
      height: 100%;
      min-height: 360px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--surface);
      box-shadow: 0 10px 26px rgba(23, 32, 51, 0.055);
      flex-direction: column;
      overflow: hidden;
      transition: border-color 180ms ease, box-shadow 180ms ease, transform 180ms ease;
    }

    .task-card:hover {
      border-color: #9ca7a1;
      box-shadow: var(--shadow);
      transform: translateY(-2px);
    }

    .card-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      border-bottom: 1px solid var(--line);
      padding: 14px 16px 12px;
    }

    .task-id {
      color: var(--muted);
      font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
      font-size: 12px;
      font-weight: 700;
      overflow-wrap: anywhere;
    }

    .pill {
      display: inline-flex;
      align-items: center;
      border-radius: 999px;
      padding: 5px 8px;
      font-size: 12px;
      font-weight: 800;
      line-height: 1;
      text-transform: capitalize;
      white-space: nowrap;
    }

    .pill.bugfix { background: var(--rose-soft); color: var(--rose); }
    .pill.feature { background: var(--green-soft); color: var(--green); }
    .pill.refactor { background: var(--violet-soft); color: var(--violet); }
    .pill.test { background: var(--blue-soft); color: var(--blue); }

    .card-body {
      display: flex;
      padding: 16px;
      flex: 1;
      flex-direction: column;
    }

    .task-title {
      margin: 0;
      min-height: 46px;
      font-size: 19px;
      line-height: 1.22;
      display: -webkit-box;
      overflow: hidden;
      -webkit-box-orient: vertical;
      -webkit-line-clamp: 2;
    }

    .scenario {
      margin-top: 7px;
      min-height: 40px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
      display: -webkit-box;
      overflow: hidden;
      -webkit-box-orient: vertical;
      -webkit-line-clamp: 2;
    }

    .summary {
      margin: 14px 0 0;
      min-height: 63px;
      color: #2a3547;
      font-size: 14px;
      line-height: 1.5;
      display: -webkit-box;
      overflow: hidden;
      -webkit-box-orient: vertical;
      -webkit-line-clamp: 3;
    }

    .metric-row {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 8px;
      margin-top: 16px;
    }

    .metric {
      min-width: 0;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fbfcf8;
      padding: 8px;
    }

    .metric b {
      display: block;
      color: var(--ink);
      font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
      font-size: 16px;
      line-height: 1.1;
    }

    .metric span {
      display: block;
      margin-top: 4px;
      color: var(--muted);
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
    }

    .chips {
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
      align-content: flex-start;
      height: 60px;
      margin-top: 14px;
      overflow: hidden;
    }

    .chip {
      border: 1px solid var(--line);
      border-radius: 999px;
      background: #fbfcf8;
      padding: 5px 8px;
      color: #405067;
      font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
      font-size: 11px;
      font-weight: 700;
    }

    .command {
      display: block;
      width: 100%;
      height: 54px;
      margin-top: 14px;
      border: 1px solid #d7ded6;
      border-radius: 6px;
      background: #111827;
      color: #e5e7eb;
      padding: 10px;
      font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
      font-size: 12px;
      line-height: 1.35;
      overflow-x: auto;
      white-space: nowrap;
    }

    .card-actions {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 8px;
      margin-top: auto;
      padding-top: 16px;
    }

    .card-action {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 38px;
      border: 1px solid var(--line-strong);
      border-radius: 7px;
      background: #fbfcf8;
      color: var(--ink);
      font-size: 13px;
      font-weight: 750;
      transition: background 180ms ease, border-color 180ms ease;
    }

    .card-action:hover {
      border-color: #111827;
      background: #f0f4ef;
    }

    .empty-state {
      display: none;
      border: 1px dashed var(--line-strong);
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.72);
      padding: 28px;
      color: var(--muted);
      text-align: center;
    }

    .empty-state strong {
      display: block;
      margin-bottom: 4px;
      color: var(--ink);
      font-size: 18px;
    }

    @media (max-width: 980px) {
      .summary-grid, .task-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .controls { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .controls .field:first-child { grid-column: 1 / -1; }
    }

    @media (max-width: 640px) {
      .nav, .registry-head {
        align-items: stretch;
        flex-direction: column;
      }

      .nav-actions { justify-content: stretch; }
      .link-button { justify-content: center; }
      .summary-grid, .controls, .task-grid, .metric-row { grid-template-columns: 1fr; }
      .hero { padding-top: 36px; }
      h1 { font-size: 30px; }
      .locale-zh h1 { font-size: 28px; }
      .hero-copy { font-size: 16px; }
      .result-count { white-space: normal; }
    }

    @media (max-width: 390px) {
      .locale-zh h1 { font-size: 24px; }
    }

    @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after {
        scroll-behavior: auto !important;
        transition: none !important;
      }
    }
"""


SCRIPT = """
    const TASKS = %%TASKS%%;
    const labels = %%LABELS%%;
    const copy = %%COPY%%;

    const $ = (selector) => document.querySelector(selector);
    const grid = $("#taskGrid");
    const resultCount = $("#resultCount");
    const emptyState = $("#emptyState");
    const searchInput = $("#searchInput");
    const typeFilter = $("#typeFilter");
    const effortFilter = $("#effortFilter");
    const complexityFilter = $("#complexityFilter");
    const sortSelect = $("#sortSelect");

    function uniqueBy(key) {
      return [...new Set(TASKS.map((task) => task[key]))].sort();
    }

    function option(select, value, text) {
      const node = document.createElement("option");
      node.value = value;
      node.textContent = text;
      select.append(node);
    }

    function seedFilter(select, allLabel, values) {
      option(select, "all", allLabel);
      values.forEach((value) => option(select, value, labels[value] || value));
    }

    function median(values) {
      const sorted = [...values].sort((a, b) => a - b);
      const middle = Math.floor(sorted.length / 2);
      return sorted.length % 2 ? sorted[middle] : Math.round((sorted[middle - 1] + sorted[middle]) / 2);
    }

    function setSummary() {
      const budgets = TASKS.map((task) => task.minutes);
      $("#taskTotal").textContent = TASKS.length;
      $("#typeTotal").textContent = uniqueBy("type").length;
      $("#matrixTotal").textContent = new Set(TASKS.map((task) => `${task.b}:${task.c}`)).size;
      $("#medianBudget").textContent = `${median(budgets)}m`;
      $("#budgetRange").textContent = budgets.length
        ? `${Math.min(...budgets)}-${Math.max(...budgets)} ${copy.budgetUnit}`
        : `0 ${copy.budgetUnit}`;
    }

    function searchable(task) {
      return [
        task.id,
        task.title,
        task.type,
        task.effort,
        task.b,
        task.c,
        task.scenario,
        task.summary,
        task.scope.join(" "),
        task.cmd
      ].join(" ").toLowerCase();
    }

    function matches(task) {
      const query = searchInput.value.trim().toLowerCase();
      const type = typeFilter.value;
      const effort = effortFilter.value;
      const complexity = complexityFilter.value;
      return (!query || searchable(task).includes(query))
        && (type === "all" || task.type === type)
        && (effort === "all" || task.effort === effort)
        && (complexity === "all" || task.b === complexity || task.c === complexity);
    }

    function sorted(tasks) {
      const sort = sortSelect.value;
      return [...tasks].sort((a, b) => {
        if (sort === "time") {
          return a.minutes - b.minutes || a.id.localeCompare(b.id);
        }
        if (sort === "cost") {
          return a.cost - b.cost || a.id.localeCompare(b.id);
        }
        if (sort === "type") {
          return a.type.localeCompare(b.type) || a.id.localeCompare(b.id);
        }
        return a.id.localeCompare(b.id);
      });
    }

    function format(template, count) {
      return template.replace("{count}", count);
    }

    function el(tag, className, text) {
      const node = document.createElement(tag);
      if (className) {
        node.className = className;
      }
      if (text !== undefined) {
        node.textContent = text;
      }
      return node;
    }

    function link(text, href) {
      const node = el("a", "card-action", text);
      node.href = href;
      return node;
    }

    function renderTask(task) {
      const card = el("article", "task-card");
      const top = el("div", "card-top");
      top.append(el("div", "task-id", task.id), el("span", `pill ${task.type}`, labels[task.type]));

      const body = el("div", "card-body");
      body.append(el("h3", "task-title", task.title));
      body.append(el("div", "scenario", `${task.scenario} / ${labels[task.b]} / ${labels[task.c]}`));
      body.append(el("p", "summary", task.summary));

      const metrics = el("div", "metric-row");
      [
        [`${task.minutes}m`, copy.metricBudget],
        [`$${task.cost.toFixed(1)}`, copy.metricCost],
        [`${task.interventions}`, copy.metricInterventions]
      ].forEach(([value, label]) => {
        const metric = el("div", "metric");
        metric.append(el("b", "", value), el("span", "", label));
        metrics.append(metric);
      });
      body.append(metrics);

      const chips = el("div", "chips");
      [
        labels[task.effort],
        format(copy.hiddenChecks, task.hidden),
        format(copy.contextSources, task.contexts),
        ...task.scope,
        task.scopeMore ? format(copy.morePaths, task.scopeMore) : null
      ].filter(Boolean).forEach((text) => chips.append(el("span", "chip", text)));
      body.append(chips);

      body.append(el("code", "command", task.cmd));

      const actions = el("div", "card-actions");
      actions.append(
        link(copy.taskLink, task.taskHref),
        link(copy.jsonLink, task.jsonHref),
        link(copy.testsLink, task.testsHref)
      );
      body.append(actions);

      card.append(top, body);
      return card;
    }

    function showingText(shown) {
      return copy.showing.replace("{shown}", shown).replace("{total}", TASKS.length);
    }

    function render() {
      const tasks = sorted(TASKS.filter(matches));
      grid.replaceChildren(...tasks.map(renderTask));
      resultCount.textContent = showingText(tasks.length);
      emptyState.style.display = tasks.length ? "none" : "block";
    }

    setSummary();
    seedFilter(typeFilter, copy.allTypes, uniqueBy("type"));
    seedFilter(effortFilter, copy.allEfforts, uniqueBy("effort"));
    seedFilter(complexityFilter, copy.allComplexity, [...uniqueBy("b"), ...uniqueBy("c")]);
    [searchInput, typeFilter, effortFilter, complexityFilter, sortSelect].forEach((input) => {
      input.addEventListener("input", render);
      input.addEventListener("change", render);
    });
    render();
"""


TEMPLATE = """<!doctype html>
<html lang="%%LANG%%">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>%%TITLE%%</title>
  <style>
%%STYLE%%
  </style>
</head>
<body class="%%BODY_CLASS%%">
  <div class="page">
    <header class="topbar">
      <nav class="nav" aria-label="Primary">
        <a class="brand" href="#">
          <span class="brand-mark" aria-hidden="true">B</span>
          <span>
            %%BRAND%%
            <small>ai-coding-evaluation</small>
          </span>
        </a>
        <div class="nav-actions">
          <a class="link-button" href="%%README%%">
            <svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M4 4.5A2.5 2.5 0 0 1 6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5z"></path></svg>
            README
          </a>
          <a class="link-button" href="%%SWITCH_HREF%%">%%SWITCH_LABEL%%</a>
          <a class="link-button primary" href="tasks/">
            <svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14"></path><path d="m12 5 7 7-7 7"></path></svg>
            %%SOURCE%%
          </a>
        </div>
      </nav>
    </header>

    <main>
      <section class="hero" aria-labelledby="page-title">
        <span class="eyebrow">%%EYEBROW%%</span>
        <h1 id="page-title">%%HERO_TITLE%%</h1>
        <p class="hero-copy">%%HERO_COPY%%</p>
      </section>

      <section class="summary-grid" aria-label="%%SUMMARY_ARIA%%">
        <article class="summary-card">
          <div class="summary-label">%%TASK_TOTAL%%</div>
          <div class="summary-value" id="taskTotal">%%TASK_COUNT%%</div>
          <div class="summary-note">%%TASK_TOTAL_NOTE%%</div>
        </article>
        <article class="summary-card">
          <div class="summary-label">%%TYPE_TOTAL%%</div>
          <div class="summary-value" id="typeTotal">%%TYPE_COUNT%%</div>
          <div class="summary-note">%%TYPE_TOTAL_NOTE%%</div>
        </article>
        <article class="summary-card">
          <div class="summary-label">%%MATRIX_TOTAL%%</div>
          <div class="summary-value" id="matrixTotal">%%MATRIX_COUNT%%</div>
          <div class="summary-note">%%MATRIX_TOTAL_NOTE%%</div>
        </article>
        <article class="summary-card">
          <div class="summary-label">%%MEDIAN_BUDGET%%</div>
          <div class="summary-value" id="medianBudget">%%MEDIAN_BUDGET_VALUE%%m</div>
          <div class="summary-note">%%BUDGET_RANGE%%<span id="budgetRange">%%BUDGET_RANGE_VALUE%% %%BUDGET_UNIT%%</span>.</div>
        </article>
      </section>

      <section class="controls-band" aria-label="%%FILTERS%%">
        <div class="controls">
          <label class="field">
            <svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="8"></circle><path d="m21 21-4.3-4.3"></path></svg>
            <span class="visually-hidden">%%SEARCH_TASKS%%</span>
            <input id="searchInput" class="search-input" type="search" placeholder="%%SEARCH_PLACEHOLDER%%" autocomplete="off">
          </label>
          <label class="field">
            <span class="visually-hidden">%%TYPE%%</span>
            <select id="typeFilter" class="select-input" aria-label="%%TYPE_ARIA%%"></select>
          </label>
          <label class="field">
            <span class="visually-hidden">%%EFFORT%%</span>
            <select id="effortFilter" class="select-input" aria-label="%%EFFORT_ARIA%%"></select>
          </label>
          <label class="field">
            <span class="visually-hidden">%%COMPLEXITY%%</span>
            <select id="complexityFilter" class="select-input" aria-label="%%COMPLEXITY_ARIA%%"></select>
          </label>
          <label class="field">
            <span class="visually-hidden">%%SORT%%</span>
            <select id="sortSelect" class="select-input" aria-label="%%SORT_ARIA%%">
              <option value="id">%%SORT_ID%%</option>
              <option value="time">%%SORT_TIME%%</option>
              <option value="cost">%%SORT_COST%%</option>
              <option value="type">%%SORT_TYPE%%</option>
            </select>
          </label>
        </div>
      </section>

      <section class="registry" aria-labelledby="registry-title">
        <div class="registry-head">
          <h2 class="registry-title" id="registry-title">%%REGISTRY_TITLE%%</h2>
          <div class="result-count" id="resultCount">%%RESULT_COUNT%%</div>
        </div>
        <div class="empty-state" id="emptyState" role="status">
          <strong>%%EMPTY_TITLE%%</strong>
          %%EMPTY_COPY%%
        </div>
        <div class="task-grid" id="taskGrid"></div>
      </section>
    </main>
  </div>

  <script>
%%SCRIPT%%
  </script>
</body>
</html>
"""


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_text_if_exists(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def json_for_script(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, indent=6, sort_keys=True)
    return payload.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")


def zh_output_path(output: Path) -> Path:
    if output.suffix:
        return output.with_name(f"{output.stem}.zh-CN{output.suffix}")
    return output.with_name(f"{output.name}.zh-CN.html")


def first_match(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, re.MULTILINE)
    if not match:
        return None
    return match.group(1).strip()


def extract_expected_behavior(text: str, locale: str) -> list[str]:
    heading = "期望行为" if locale == "zh-CN" else "Expected behavior"
    items: list[str] = []
    capture = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith(heading.lower()):
            capture = True
            continue
        if capture and re.match(r"^[A-Za-z][A-Za-z ]+:\s*$", stripped):
            break
        if capture and locale == "zh-CN" and re.match(r"^[^\s`]+[：:]\s*$", stripped):
            break
        if capture and stripped.startswith("- "):
            items.append(stripped[2:].rstrip(".。"))
    return items


def fallback_summary(text: str) -> str:
    for paragraph in re.split(r"\n\s*\n", text):
        cleaned = re.sub(r"\s+", " ", paragraph.strip())
        if cleaned and not cleaned.startswith("#"):
            return cleaned[:167].rstrip() + "..." if len(cleaned) > 170 else cleaned
    return ""


def task_markdown(task_dir: Path, locale: str) -> tuple[str, Path]:
    if locale == "zh-CN":
        zh_path = task_dir / "task.zh-CN.md"
        if zh_path.exists():
            return zh_path.read_text(encoding="utf-8"), zh_path
    path = task_dir / "task.md"
    return read_text_if_exists(path), path


def task_title(markdown: str, task_id: str, locale: str) -> str:
    if locale == "zh-CN":
        return first_match(r"^#\s*任务[：:]\s*(.+)$", markdown) or task_id
    return first_match(r"^#\s*Task:\s*(.+)$", markdown) or task_id


def task_scenario(markdown: str, locale: str) -> str:
    if locale == "zh-CN":
        return first_match(r"^场景[：:]\s*(.+?)。?$", markdown) or ""
    return first_match(r"^Scenario:\s*(.+?)\.?$", markdown) or ""


def task_record(task_dir: Path, locale: str) -> dict[str, Any]:
    task = load_json(task_dir / "task.json")
    markdown, markdown_path = task_markdown(task_dir, locale)
    complexity = task.get("complexity") if isinstance(task.get("complexity"), dict) else {}
    scope = task.get("scope") if isinstance(task.get("scope"), dict) else {}
    target = task.get("target") if isinstance(task.get("target"), dict) else {}
    scope_paths = scope.get("allowed_paths") if isinstance(scope.get("allowed_paths"), list) else []
    expected = extract_expected_behavior(markdown, locale)
    summary = "；".join(expected[:3]) if locale == "zh-CN" else "; ".join(expected[:3])
    if not summary:
        summary = fallback_summary(markdown)

    return {
        "id": task.get("id") or task_dir.name,
        "title": task_title(markdown, str(task.get("id") or task_dir.name), locale),
        "type": task.get("type") or "unknown",
        "effort": task.get("effort_size") or "unknown",
        "b": complexity.get("business_complexity") or "unknown",
        "c": complexity.get("context_maturity") or "unknown",
        "minutes": task.get("time_budget_minutes") or 0,
        "interventions": task.get("max_human_interventions") or 0,
        "cost": task.get("max_cost_usd") or 0,
        "scenario": task_scenario(markdown, locale),
        "summary": summary,
        "scope": [str(path) for path in scope_paths[:3]],
        "scopeMore": max(0, len(scope_paths) - 3),
        "hidden": len(
            task.get("hidden_checks") if isinstance(task.get("hidden_checks"), list) else []
        ),
        "contexts": len(
            task.get("context_sources") if isinstance(task.get("context_sources"), list) else []
        ),
        "cmd": (target.get("test_commands") or [""])[0],
        "taskHref": f"tasks/{task_dir.name}/{markdown_path.name}",
        "jsonHref": f"tasks/{task_dir.name}/task.json",
        "testsHref": f"tasks/{task_dir.name}/tests.sh",
    }


def collect_tasks(tasks_root: Path, locale: str) -> list[dict[str, Any]]:
    return [task_record(path.parent, locale) for path in sorted(tasks_root.glob("*/task.json"))]


def median(values: list[float]) -> float:
    if not values:
        return 0
    sorted_values = sorted(values)
    middle = len(sorted_values) // 2
    if len(sorted_values) % 2:
        return sorted_values[middle]
    return round((sorted_values[middle - 1] + sorted_values[middle]) / 2)


def page_html(tasks: list[dict[str, Any]], locale: str) -> str:
    labels = LOCALES[locale]
    budgets = [float(task["minutes"]) for task in tasks]
    copy = {
        "allTypes": labels["all_types"],
        "allEfforts": labels["all_efforts"],
        "allComplexity": labels["all_complexity"],
        "budgetUnit": labels["budget_unit"],
        "metricBudget": labels["metric_budget"],
        "metricCost": labels["metric_cost"],
        "metricInterventions": labels["metric_interventions"],
        "hiddenChecks": labels["hidden_checks"],
        "contextSources": labels["context_sources"],
        "morePaths": labels["more_paths"],
        "taskLink": labels["task_link"],
        "jsonLink": labels["json_link"],
        "testsLink": labels["tests_link"],
        "showing": labels["showing"],
    }
    script = SCRIPT.replace("%%TASKS%%", json_for_script(tasks))
    script = script.replace("%%LABELS%%", json_for_script(labels["labels"]))
    script = script.replace("%%COPY%%", json_for_script(copy))

    replacements = {
        "%%LANG%%": labels["lang"],
        "%%TITLE%%": labels["title"],
        "%%BODY_CLASS%%": "locale-zh" if locale == "zh-CN" else "locale-en",
        "%%STYLE%%": STYLE,
        "%%BRAND%%": labels["brand"],
        "%%README%%": labels["readme"],
        "%%SWITCH_HREF%%": labels["switch_href"],
        "%%SWITCH_LABEL%%": labels["switch_label"],
        "%%SOURCE%%": labels["source"],
        "%%EYEBROW%%": labels["eyebrow"],
        "%%HERO_TITLE%%": labels["hero_title"],
        "%%HERO_COPY%%": labels["hero_copy"],
        "%%SUMMARY_ARIA%%": labels["summary_aria"],
        "%%TASK_TOTAL%%": labels["task_total"],
        "%%TASK_COUNT%%": str(len(tasks)),
        "%%TASK_TOTAL_NOTE%%": labels["task_total_note"],
        "%%TYPE_TOTAL%%": labels["type_total"],
        "%%TYPE_COUNT%%": str(len({task["type"] for task in tasks})),
        "%%TYPE_TOTAL_NOTE%%": labels["type_total_note"],
        "%%MATRIX_TOTAL%%": labels["matrix_total"],
        "%%MATRIX_COUNT%%": str(len({(task["b"], task["c"]) for task in tasks})),
        "%%MATRIX_TOTAL_NOTE%%": labels["matrix_total_note"],
        "%%MEDIAN_BUDGET%%": labels["median_budget"],
        "%%MEDIAN_BUDGET_VALUE%%": f"{median(budgets):g}",
        "%%BUDGET_RANGE%%": labels["budget_range"],
        "%%BUDGET_RANGE_VALUE%%": f"{min(budgets or [0]):g}-{max(budgets or [0]):g}",
        "%%BUDGET_UNIT%%": labels["budget_unit"],
        "%%FILTERS%%": labels["filters"],
        "%%SEARCH_TASKS%%": labels["search_tasks"],
        "%%SEARCH_PLACEHOLDER%%": labels["search_placeholder"],
        "%%TYPE%%": labels["type"],
        "%%EFFORT%%": labels["effort"],
        "%%COMPLEXITY%%": labels["complexity"],
        "%%SORT%%": labels["sort"],
        "%%TYPE_ARIA%%": labels["type_aria"],
        "%%EFFORT_ARIA%%": labels["effort_aria"],
        "%%COMPLEXITY_ARIA%%": labels["complexity_aria"],
        "%%SORT_ARIA%%": labels["sort_aria"],
        "%%SORT_ID%%": labels["sort_id"],
        "%%SORT_TIME%%": labels["sort_time"],
        "%%SORT_COST%%": labels["sort_cost"],
        "%%SORT_TYPE%%": labels["sort_type"],
        "%%REGISTRY_TITLE%%": labels["registry_title"],
        "%%RESULT_COUNT%%": labels["showing"].format(shown=len(tasks), total=len(tasks)),
        "%%EMPTY_TITLE%%": labels["empty_title"],
        "%%EMPTY_COPY%%": labels["empty_copy"],
        "%%SCRIPT%%": script,
    }
    html = TEMPLATE
    for key, value in replacements.items():
        html = html.replace(key, str(value))
    if locale == "zh-CN":
        html = html.replace(
            f'<span id="budgetRange">{replacements["%%BUDGET_RANGE_VALUE%%"]} {labels["budget_unit"]}</span>.',
            f'<span id="budgetRange">{replacements["%%BUDGET_RANGE_VALUE%%"]} {labels["budget_unit"]}</span>。',
        )
    return html


def write_registry(tasks_root: Path, output: Path, zh_output: Path | None = None) -> list[Path]:
    output.parent.mkdir(parents=True, exist_ok=True)
    zh_path = zh_output or zh_output_path(output)
    zh_path.parent.mkdir(parents=True, exist_ok=True)

    en_tasks = collect_tasks(tasks_root, "en")
    zh_tasks = collect_tasks(tasks_root, "zh-CN")
    output.write_text(page_html(en_tasks, "en"), encoding="utf-8")
    zh_path.write_text(page_html(zh_tasks, "zh-CN"), encoding="utf-8")
    return [output, zh_path]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate static benchmark task registry pages.")
    parser.add_argument("--tasks", type=Path, default=DEFAULT_TASKS, help="Benchmark tasks root")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="English HTML output")
    parser.add_argument("--zh-output", type=Path, default=None, help="Chinese HTML output")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    for path in write_registry(args.tasks, args.output, args.zh_output):
        print(path)


if __name__ == "__main__":
    main()
