"""
PhysioGemma — AI Physiotherapy Agent powered by Gemma 4
========================================================
Kaggle Gemma 4 Good Hackathon | Health & Sciences Track

ReAct agent with tool-calling, structured reasoning, patient progress
tracking with recovery graph, and AI-powered recovery insights.

Run: python app.py
"""

import os
import json
import gradio as gr
from gemma_engine import process_message, get_client, MODEL_ID, AGENT_SYSTEM_PROMPT
from exercises import EXERCISES
from imaging_parser import parse_imaging_report, format_imaging_for_display
from progress import (
    create_empty_progress, log_session, generate_recovery_chart,
    tool_analyze_progress, serialize_progress, deserialize_progress,
    get_overall_stats,
)

# ── Theme ────────────────────────────────────────────────────────────────────

THEME = gr.themes.Base(
    primary_hue="red",
    neutral_hue="stone",
    font=gr.themes.GoogleFont("Archivo"),
)

CSS = """
/* ══════════════════════════════════════════════════════════════════════════
   PhysioGemma — Modernist design system
   #f3f2f2 page · #eae9e9 surface · #201e1d ink · #ec3013 accent · Archivo
   0px radius · 2px rules · flat, flush-left
   ══════════════════════════════════════════════════════════════════════════ */

@import url('https://fonts.googleapis.com/css2?family=Archivo:wght@400;600;800&display=swap');

/* ── Reset & Global ──────────────────────────────────────────────────────── */
.gradio-container {
    max-width: 1200px !important;
    background: #f3f2f2 !important;
    font-family: 'Archivo', system-ui, sans-serif !important;
}
* { border-radius: 0 !important; }
*:focus-visible { outline: 2px solid #ec3013 !important; outline-offset: 2px; }
::selection { background: rgba(236,48,19,0.3); }

/* ── Force ink text everywhere ───────────────────────────────────────────── */
body, .gradio-container, .gradio-container *,
.prose *, .markdown-text *, span, p, li, td, th,
label, h1, h2, h3, h4, h5, h6 {
    color: #201e1d !important;
    font-family: 'Archivo', system-ui, sans-serif !important;
}
.dark body, .dark .gradio-container * { color: #201e1d !important; }
code, pre, .reasoning-observation, .mono {
    font-family: ui-monospace, 'Cascadia Code', Consolas, monospace !important;
}

/* ── Typography ──────────────────────────────────────────────────────────── */
h1 { font-weight: 800 !important; letter-spacing: -0.015em !important; line-height: 1.12 !important; }
h2, h3 { font-weight: 800 !important; letter-spacing: -0.015em !important; }
h4, h5 { font-weight: 800 !important; }
label { color: rgba(32,30,29,0.7) !important; font-weight: 800 !important; font-size: 12px !important;
        text-transform: uppercase !important; letter-spacing: 0.08em !important; }

/* ── Chat bubbles ────────────────────────────────────────────────────────── */
.message-wrap .message {
    border-radius: 0 !important;
    padding: 14px 18px !important;
    font-size: 15px !important;
    line-height: 1.55 !important;
    max-width: 85% !important;
    box-shadow: none !important;
}
.message-wrap .bot,
.chatbot .message-wrap .bot {
    background: #eae9e9 !important;
    border: none !important;
    box-shadow: none !important;
}
.message-wrap .bot *, .message-wrap .bot p,
.message-wrap .bot span, .message-wrap .bot li,
.message-wrap .bot strong,
.chatbot .message-wrap .bot *,
.chatbot .message-wrap .bot p,
.chatbot .message-wrap .bot span {
    color: #201e1d !important;
}
.message-wrap .bot code {
    background: #ffe0d9 !important;
    color: #7c1405 !important;
    padding: 2px 8px !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
.message-wrap .user,
.chatbot .message-wrap .user {
    background: transparent !important;
    border: 2px solid #201e1d !important;
    box-shadow: none !important;
}
.message-wrap .user *, .message-wrap .user p,
.message-wrap .user span, .message-wrap .user li,
.chatbot .message-wrap .user *,
.chatbot .message-wrap .user p,
.chatbot .message-wrap .user span {
    color: #201e1d !important;
}
.chatbot { border: 2px solid rgba(32,30,29,0.4) !important; background: #f3f2f2 !important; box-shadow: none !important; }

/* ── Buttons ─────────────────────────────────────────────────────────────── */
button.primary {
    background: #ec3013 !important;
    border: none !important;
    font-weight: 800 !important;
    font-size: 14px !important;
    color: #f3f2f2 !important;
    box-shadow: none !important;
    padding: 12px 20px !important;
    justify-content: flex-start !important;
    text-align: left !important;
}
button.primary * { color: #f3f2f2 !important; }
button.primary:hover { background: #dd2b0f !important; transform: none; box-shadow: none !important; }
button.primary:active { background: #ae1800 !important; transform: none; }
button.secondary {
    border: 2px solid rgba(32,30,29,0.4) !important;
    background: transparent !important;
    font-weight: 600 !important;
    color: #201e1d !important;
    box-shadow: none !important;
}
button.secondary:hover {
    background: rgba(32,30,29,0.07) !important;
    border-color: #201e1d !important;
    color: #201e1d !important;
    box-shadow: none !important;
}

/* ── Tabs ────────────────────────────────────────────────────────────────── */
.tabs > .tab-nav {
    background: transparent !important;
    border-bottom: 2px solid rgba(32,30,29,0.4) !important;
    padding: 0 !important;
}
.tabs > .tab-nav > button {
    font-size: 14px !important;
    font-weight: 600 !important;
    padding: 12px 20px !important;
    color: #201e1d !important;
    border: none !important;
    background: transparent !important;
}
.tabs > .tab-nav > button.selected {
    background: transparent !important;
    border-bottom: 3px solid #ec3013 !important;
    color: #ec3013 !important;
    font-weight: 800 !important;
}
.tabs > .tab-nav > button:hover:not(.selected) {
    background: rgba(32,30,29,0.05) !important;
    color: #201e1d !important;
}

/* ── Assessment chips (progress pills) ───────────────────────────────────── */
.progress-bar {
    display: flex;
    gap: 10px;
    align-items: center;
    margin: 12px 0 20px 0;
    flex-wrap: wrap;
    border-bottom: 2px solid rgba(32,30,29,0.4);
    padding-bottom: 14px;
}
.progress-label {
    font-size: 11px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    font-weight: 800;
    margin-right: 8px;
    color: #201e1d !important;
}
.progress-pill {
    padding: 4px 12px;
    font-size: 12px;
}
.progress-done {
    background: #201e1d;
    color: #f3f2f2 !important;
    font-weight: 600;
    box-shadow: none;
}
.progress-done * { color: #f3f2f2 !important; }
.progress-pending {
    background: transparent;
    color: rgba(32,30,29,0.7) !important;
    border: 2px solid rgba(32,30,29,0.4);
}
.progress-pending * { color: rgba(32,30,29,0.7) !important; }

/* ── Stat strip ──────────────────────────────────────────────────────────── */
.stat-strip {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    border-bottom: 2px solid rgba(32,30,29,0.4);
    border-top: 2px solid rgba(32,30,29,0.4);
    margin: 16px 0;
}
.stat-cell { padding: 20px 24px; border-right: 1px solid rgba(32,30,29,0.15); }
.stat-cell:last-child { border-right: none; }
.stat-num { font-weight: 800; font-size: 34px; line-height: 1; color: #201e1d !important; }
.stat-num .unit { font-size: 16px; }
.stat-num.accent { color: #ae1800 !important; }
.stat-num.accent * { color: #ae1800 !important; }
.stat-label {
    font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase;
    color: rgba(32,30,29,0.6) !important; margin-top: 6px;
}

/* ── Exercise cards ──────────────────────────────────────────────────────── */
.exercise-card {
    background: #eae9e9;
    border: none;
    padding: 0;
    margin: 14px 0;
    box-shadow: none;
}
.exercise-card:hover { box-shadow: none; transform: none; }
.exercise-card h4 {
    color: #201e1d !important;
    margin: 0 0 4px 0;
    font-size: 15px;
    font-weight: 800;
    padding: 14px 16px 0 16px;
}
.exercise-card p {
    color: rgba(32,30,29,0.8) !important;
    margin: 6px 0;
    font-size: 14px;
    line-height: 1.55;
    padding: 0 16px;
}
.exercise-card .ex-meta {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin: 6px 0 8px 0;
    padding: 0 16px;
}
.exercise-card .ex-badge {
    display: inline-block;
    padding: 3px 10px;
    font-size: 11px;
    letter-spacing: 0.02em;
    font-weight: 400;
}
.ex-badge-sets { background: #f8f4f4; color: #444141 !important; border: none; }
.ex-badge-reps { background: #f8f4f4; color: #444141 !important; border: none; }
.ex-badge-type { background: #ffe0d9; color: #7c1405 !important; border: none; }
.exercise-card a {
    display: block;
    margin: 10px 16px 16px 16px;
    overflow: hidden;
    box-shadow: none;
}
.exercise-card a:hover { box-shadow: none; transform: none; }

/* ── Reasoning chain ─────────────────────────────────────────────────────── */
.reasoning-kicker {
    font-size: 10px; letter-spacing: 0.1em; text-transform: uppercase;
    font-weight: 800; color: #ae1800 !important; margin-bottom: 6px;
}
.reasoning-step {
    padding: 12px 16px;
    margin: 8px 0;
    font-size: 12px;
    line-height: 1.7;
    font-family: ui-monospace, Consolas, monospace !important;
}
.reasoning-step * { font-family: ui-monospace, Consolas, monospace !important; font-size: 12px !important; }
.reasoning-action {
    background: #eae9e9;
    border: none;
    border-left: 4px solid #ec3013;
}
.reasoning-observation {
    background: #eae9e9;
    border: none;
    border-left: 4px solid rgba(32,30,29,0.4);
}
.reasoning-warning {
    background: #ffe0d9;
    border: none;
    border-left: 4px solid #ae1800;
}
.reasoning-warning * { color: #7c1405 !important; }
.tool-badge {
    display: inline-block;
    background: #ffe0d9 !important;
    border: none;
    color: #7c1405 !important;
    padding: 2px 10px;
    font-size: 11px !important;
    font-weight: 600;
    margin: 2px 4px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    font-family: 'Archivo', sans-serif !important;
}

/* ── Milestone badges ────────────────────────────────────────────────────── */
.milestone-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #ffe0d9;
    border: none;
    padding: 4px 12px;
    font-size: 12px;
    margin: 4px;
    color: #7c1405 !important;
    font-weight: 600;
    box-shadow: none;
}
.milestone-badge:hover { box-shadow: none; transform: none; }

/* ── Insight rows ────────────────────────────────────────────────────────── */
.insight-card {
    padding: 14px 0;
    margin: 0;
    font-size: 14px;
    line-height: 1.55;
    box-shadow: none;
    border: none;
    border-bottom: 1px solid rgba(32,30,29,0.15);
    background: transparent;
    display: flex;
    gap: 16px;
    align-items: flex-start;
}
.insight-card:hover { transform: none; box-shadow: none; }
.insight-tag {
    flex: none;
    width: 90px;
    font-size: 11px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    font-weight: 800;
    color: #444141 !important;
}
.insight-concern .insight-tag { color: #ae1800 !important; }
.insight-improvement, .insight-suggestion, .insight-achievement,
.insight-info, .insight-milestone, .insight-ready_to_progress, .insight-concern {
    background: transparent;
    border-left: none;
}

/* ── Recommendation banner ───────────────────────────────────────────────── */
.recommendation-box {
    padding: 32px 28px;
    margin: 18px 0;
    font-size: 28px;
    font-weight: 800;
    line-height: 1.05;
    letter-spacing: -0.015em;
    text-align: left;
    box-shadow: none;
}
.rec-kicker {
    display: block;
    font-size: 11px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    font-weight: 400;
    opacity: 0.8;
    margin-bottom: 8px;
}

/* ── Section dividers ────────────────────────────────────────────────────── */
.section-divider {
    border: none;
    border-top: 2px solid rgba(32,30,29,0.4);
    margin: 28px 0;
}

/* ── Form elements ───────────────────────────────────────────────────────── */
input[type="range"] { accent-color: #ec3013 !important; height: 6px !important; }
input[type="checkbox"], input[type="radio"] { accent-color: #ec3013 !important; }
input, textarea {
    color: #201e1d !important;
    border: 2px solid rgba(32,30,29,0.4) !important;
    background: #f3f2f2 !important;
    caret-color: #ec3013 !important;
    box-shadow: none !important;
}
input:hover, textarea:hover { border-color: rgba(32,30,29,0.6) !important; }
input:focus, textarea:focus {
    border-color: #ec3013 !important;
    box-shadow: none !important;
}
.checkbox-group label {
    padding: 8px 16px !important;
    border: 2px solid rgba(32,30,29,0.4) !important;
    margin: 4px !important;
    font-weight: 600 !important;
    background: transparent !important;
    text-transform: none !important;
    letter-spacing: 0 !important;
    font-size: 14px !important;
}
.checkbox-group label:hover {
    border-color: #201e1d !important;
    background: rgba(32,30,29,0.07) !important;
}
.checkbox-group input:checked + label,
.checkbox-group label.selected {
    background: #ec3013 !important;
    border-color: #ec3013 !important;
    color: #f3f2f2 !important;
}
.checkbox-group label.selected * { color: #f3f2f2 !important; }

/* ── Blocks / panels: flatten Gradio chrome ──────────────────────────────── */
.block, .form, .panel, fieldset {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}
.accordion {
    border: 2px solid rgba(32,30,29,0.4) !important;
    background: transparent !important;
    box-shadow: none !important;
}
.accordion *, .accordion label, .accordion span { color: #201e1d !important; }

/* ── Misc ────────────────────────────────────────────────────────────────── */
footer { display: none !important; }
.markdown-text, .markdown-text *, .prose, .prose * { color: #201e1d !important; }
.dataframe { overflow: hidden; border: none !important; }
.dataframe th {
    background: transparent !important;
    color: rgba(32,30,29,0.6) !important;
    font-weight: 800 !important;
    font-size: 11px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    border-bottom: 2px solid rgba(32,30,29,0.4) !important;
}
.dataframe td {
    color: #201e1d !important;
    font-size: 14px !important;
    border-bottom: 1px solid rgba(32,30,29,0.15) !important;
}
"""

# ── localStorage JS bridge ──────────────────────────────────────────────────

JS_LOAD_PROGRESS = """
() => {
    const data = localStorage.getItem('physiogemma_progress');
    return data || '{}';
}
"""

JS_SAVE_PROGRESS = """
(data) => {
    if (data && data !== '{}') {
        localStorage.setItem('physiogemma_progress', data);
    }
    return data;
}
"""

# ── Progress indicator ──────────────────────────────────────────────────────

DATA_FIELDS = {
    "Condition": "condition",
    "Pain (VAS)": "pain_vas",
    "Age": "age",
    "Tendency": "tendency",
    "Characteristic": "characteristic",
    "Occupation": "occupation",
    "Medical Hx": "comorbidities",
    "Exercise Recommendations": "level",
}


def _progress_html(collected: dict) -> str:
    pills = []
    for label, key in DATA_FIELDS.items():
        has_data = bool(collected.get(key))
        if key == "pain_vas":
            has_data = bool(collected.get("pain_vas") or collected.get("intensity_vas"))
        if key == "comorbidities":
            has_data = collected.get("comorbidities") is not None or collected.get("comorbidity_count") is not None
        if key == "occupation":
            has_data = bool(collected.get("occupation") or collected.get("physical_demands"))
        cls = "progress-done" if has_data else "progress-pending"
        text = f"&#10003; {label}" if has_data else label
        pills.append(f'<span class="progress-pill {cls}">{text}</span>')
    return (f'<div class="progress-bar"><span class="progress-label">Assessment</span>'
            f'{"".join(pills)}</div>')


# ── Format reasoning chain ──────────────────────────────────────────────────

TOOL_LABELS = {
    "check_red_flags": "Safety Check",
    "classify_occupation": "Classify Occupation",
    "determine_exercise_level": "Determine Level",
    "get_exercise_prescription": "Generate Prescription",
    "analyze_progress": "Progress Analysis",
    "parse_imaging_report": "Imaging Analysis",
}


def _format_reasoning_chain(chain: list) -> str:
    if not chain:
        return ""
    html = '<div style="margin-top: 8px;">'
    html += '<div class="reasoning-kicker">Reasoning chain</div>'
    for step in chain:
        if "action" in step:
            tool_label = TOOL_LABELS.get(step["action"], step["action"])
            args_str = ", ".join(f"{k}={v}" for k, v in step.get("args", {}).items()
                                if k not in ("patient_message", "progress_data_json"))
            if len(args_str) > 120:
                args_str = args_str[:120] + "..."
            html += (
                f'<div class="reasoning-step reasoning-action">'
                f'ACTION&nbsp;&nbsp;[{tool_label}]'
            )
            if args_str:
                html += f' &mdash; {args_str}'
            html += '</div>'
        elif "observation" in step:
            tool_label = TOOL_LABELS.get(step["observation"], step["observation"])
            result_str = step.get("result", "")
            is_warning = "RED FLAG" in result_str.upper()
            cls = "reasoning-warning" if is_warning else "reasoning-observation"
            html += (
                f'<div class="reasoning-step {cls}">'
                f'RESULT&nbsp;&nbsp;[{tool_label}] &mdash; {result_str}'
                f'</div>'
            )
    html += '</div>'
    return html


# ── Format prescription exercises ───────────────────────────────────────────

def _format_prescription_html(result: dict) -> str:
    plan = result["plan"]
    exercises_html = ""
    for ex in plan["exercises"]:
        video_id = ex.get("video") or ex.get("video_id") or ""
        video_embed = ""
        if video_id:
            embed_url = f"https://www.youtube.com/embed/{video_id}?rel=0"
            video_embed = (
                f'<div style="margin:10px 16px 16px 16px; overflow:hidden; '
                f'border:2px solid rgba(32,30,29,0.4); background:#201e1d;">'
                f'<iframe src="{embed_url}" '
                f'title="Exercise video" '
                f'style="width:100%; aspect-ratio:16/9; border:0; display:block;" '
                f'allow="accelerometer; autoplay; clipboard-write; encrypted-media; '
                f'gyroscope; picture-in-picture; web-share" '
                f'referrerpolicy="strict-origin-when-cross-origin" '
                f'allowfullscreen></iframe>'
                f'</div>'
            )
        ex_type = ex.get("type", "general").title()
        exercises_html += (
            f'<div class="exercise-card">'
            f'<h4>{ex["name"]}</h4>'
            f'<div class="ex-meta">'
            f'<span class="ex-badge ex-badge-sets">{ex["sets"]} sets &times; {ex["reps"]}</span>'
            f'<span class="ex-badge ex-badge-type">{ex_type}</span>'
            f'</div>'
            f'<p>{ex.get("instruction", "")}</p>'
            f'{video_embed}</div>'
        )
    return exercises_html


# ── Format patient profile ──────────────────────────────────────────────────

def _format_patient_profile(info: dict) -> str:
    condition = info.get("condition", "Unknown")
    condition_name = EXERCISES.get(condition, {}).get("name", condition)
    comorbidities = ", ".join(info.get("comorbidities", [])) if isinstance(info.get("comorbidities"), list) else "N/A"
    aggravating = ", ".join(info.get("aggravating_factors", [])) if isinstance(info.get("aggravating_factors"), list) else "N/A"
    reducing = ", ".join(info.get("reducing_factors", [])) if isinstance(info.get("reducing_factors"), list) else "N/A"

    plan_label = ""
    level = info.get("level")
    if level:
        cond = EXERCISES.get(condition, {})
        lvl = cond.get("levels", {}).get(level, {})
        plan_label = f"Level {level} — {lvl.get('label', info.get('level_label', ''))}"

    height = info.get('height_cm')
    weight = info.get('weight_kg')
    body_info = f"{height} cm / {weight} kg" if height and weight else "N/A"
    vas = info.get('intensity_vas', info.get('pain_vas', 'N/A'))

    profile = f"""### Clinical Assessment Summary

| Category | Detail |
|----------|--------|
| **Condition** | {condition_name} |
| **Intensity (VAS)** | {vas}/10 |
| **Tendency** | {info.get('tendency', 'N/A')} |
| **Characteristic** | {info.get('characteristic', 'N/A')} |
| **Aggravating** | {aggravating} |
| **Reducing** | {reducing} |
| **Age** | {info.get('age', 'N/A')} |
| **Height / Weight** | {body_info} |
| **Comorbidities** | {comorbidities} |
| **Occupation** | {info.get('occupation', 'N/A')} ({info.get('physical_demands', 'N/A')}) |
| **Prescription** | {plan_label} |
"""

    # Append imaging findings if present (optional — only shown if patient provided a report)
    imaging = info.get("imaging")
    if imaging and imaging.get("findings"):
        imaging_md = format_imaging_for_display(imaging)
        if imaging_md:
            profile += "\n\n---\n\n" + imaging_md

    return profile


# ── Stats cards HTML ────────────────────────────────────────────────────────

def _stats_html(progress_data: dict) -> str:
    stats = get_overall_stats(progress_data)
    if stats["total_sessions"] == 0:
        return """
        <div style="padding:32px 24px; background:#eae9e9; margin:16px 0;">
            <p style="font-size:16px; font-weight:800; color:#201e1d !important; margin:0 0 4px 0;">
                No sessions logged yet</p>
            <p style="font-size:13px; color:rgba(32,30,29,0.6) !important; margin:0;">
                Complete a consultation and start tracking your recovery.</p>
        </div>"""

    pain_pct = stats.get("pain_change_pct", 0)
    if pain_pct < 0:
        pain_sub = f"Pain &middot; down {abs(pain_pct):.0f}%"
    elif pain_pct > 0:
        pain_sub = f"Pain &middot; up {pain_pct:.0f}%"
    else:
        pain_sub = "Pain"

    cells = [
        (str(stats['total_sessions']), "", "Sessions", False),
        (f"{stats.get('current_pain', 'N/A')}", "/10", pain_sub, True),
        (f"{stats.get('avg_adherence', 0):.0f}", "%", "Adherence", False),
        (str(stats.get('current_streak', 0)), "", "Day streak", False),
        (f"L{stats.get('current_level', '?')}", "", "Level", False),
        (str(stats.get('milestones_earned', 0)), "", "Milestones", False),
    ]

    html = '<div class="stat-strip">'
    for value, unit, label, accent in cells:
        num_cls = "stat-num accent" if accent else "stat-num"
        unit_html = f'<span class="unit">{unit}</span>' if unit else ''
        html += (
            f'<div class="stat-cell">'
            f'<div class="{num_cls}">{value}{unit_html}</div>'
            f'<div class="stat-label">{label}</div>'
            f'</div>'
        )
    html += '</div>'

    # Recovery status line (flat, modernist)
    if pain_pct < -15:
        status_label, status_pct = "Improving", min(90, 50 + abs(pain_pct))
    elif pain_pct > 10:
        status_label, status_pct = "Needs attention", max(20, 50 - pain_pct)
    else:
        status_label, status_pct = "Stable", 50

    html += f"""
    <div style="margin-top:4px;">
        <div style="display:flex; justify-content:space-between; align-items:baseline; margin-bottom:8px;">
            <span style="font-size:12px; letter-spacing:0.08em; text-transform:uppercase;
                         font-weight:800; color:#201e1d !important;">Recovery status</span>
            <span style="font-size:13px; color:rgba(32,30,29,0.6) !important;">{status_label}</span>
        </div>
        <div style="background:#eae9e9; height:10px; border:none;">
            <div style="background:#ec3013; height:100%; width:{status_pct}%;"></div>
        </div>
    </div>"""

    return html


def _milestones_html(progress_data: dict) -> str:
    milestones = progress_data.get("milestones", [])
    if not milestones:
        return ""
    badges = "".join(f'<span class="milestone-badge">&#127942; {m["label"]}</span>' for m in milestones)
    return f'<div style="margin:14px 0; text-align:center;">{badges}</div>'


# ── Format insights ─────────────────────────────────────────────────────────

INSIGHT_TAGS = {
    "improvement": "Positive",
    "concern": "Warning",
    "suggestion": "Tip",
    "achievement": "Milestone",
    "info": "Info",
    "milestone": "Milestone",
    "ready_to_progress": "Positive",
}

RECOMMENDATION_STYLES = {
    "progress": ("background:#ec3013; color:#f3f2f2 !important;",
                 "Ready to progress<br>to the next level"),
    "maintain": ("background:#201e1d; color:#f3f2f2 !important;",
                 "Maintain current level<br>&mdash; keep going"),
    "regress": ("background:#ae1800; color:#f3f2f2 !important;",
                "Consider stepping back<br>a level for safety"),
    "insufficient_data": ("background:#eae9e9; color:#201e1d !important;",
                          "Log more sessions for<br>personalized insights"),
}


def _format_insights_html(analysis: dict) -> str:
    insights = analysis.get("insights", [])
    if not insights:
        return ('<p style="color:rgba(32,30,29,0.55) !important; font-size:14px;">'
                'No insights yet. Log sessions to generate recovery insights.</p>')

    html = ""
    for ins in insights:
        itype = ins.get("type", "info")
        tag = INSIGHT_TAGS.get(itype, "Info")
        cls = f"insight-{itype}"
        html += (
            f'<div class="insight-card {cls}">'
            f'<span class="insight-tag">{tag}</span>'
            f'<span style="font-size:14px;">{ins["text"]}</span>'
            f'</div>'
        )
    return html


def _format_recommendation_html(analysis: dict) -> str:
    rec = analysis.get("recommendation", "insufficient_data")
    style, text = RECOMMENDATION_STYLES.get(rec, RECOMMENDATION_STYLES["insufficient_data"])
    fg = "#f3f2f2" if rec != "insufficient_data" else "#201e1d"
    return (
        f'<div class="recommendation-box" style="{style}">'
        f'<span class="rec-kicker" style="color:{fg} !important;">Recommendation</span>'
        f'<span style="color:{fg} !important;">{text}</span>'
        f'</div>'
    )


# ── Progress table ──────────────────────────────────────────────────────────

def _progress_to_dataframe(progress_data: dict) -> list:
    sessions = progress_data.get("sessions", [])
    if not sessions:
        return []
    rows = []
    for s in reversed(sessions):  # newest first
        rows.append([
            s.get("date", ""),
            s.get("pain_vas", ""),
            f"{s.get('adherence_pct', 0):.0f}%",
            s.get("difficulty_rating", ""),
            f"L{s.get('exercise_level', '?')}",
            s.get("notes", "")[:60],
        ])
    return rows


# ── Chat handler ────────────────────────────────────────────────────────────

LOADING_MESSAGES = [
    "Analyzing your condition...",
    "Running safety checks...",
]


def chat(message: str, history: list, state: dict | None, progress_data: dict | None,
         imaging_report: str = ""):
    """Single-event generator: yields loading state immediately, then the
    final result. Replaces the old two-phase chat_loading/chat chain, whose
    .then() steps raced on input snapshots in Gradio 5.50.

    Yields 10 outputs: chatbot, state, progress_display, profile, exercises,
    reasoning, agent_chain, progress_state, progress_store, msg (cleared).
    """
    if not message or not message.strip():
        yield (history, state, gr.update(), gr.update(), gr.update(), gr.update(),
               gr.update(), progress_data, serialize_progress(progress_data or {}), gr.update())
        return

    if state is None:
        state = {"collected": {}, "reasoning_chain": [], "prescription_generated": False}
    if progress_data is None:
        progress_data = create_empty_progress()

    history = history + [{"role": "user", "content": message}]

    loading_text = "Analyzing your condition..."
    if imaging_report and imaging_report.strip():
        loading_text = "Parsing imaging report & analyzing your condition..."
    elif state.get("collected", {}).get("condition"):
        loading_text = "Generating your treatment plan..."

    # Immediate feedback: user message + loading bubble, clear the input box
    yield (history + [{"role": "assistant", "content": loading_text}], state,
           gr.update(), gr.update(), gr.update(), gr.update(), gr.update(),
           progress_data, serialize_progress(progress_data), "")

    # ── OPTIONAL: Parse imaging report if provided ──────────────────────────
    # This is Mode 1 of imaging integration (text-only, no scan plates).
    # Completely skipped when field is empty — zero cost for non-users.
    if imaging_report and imaging_report.strip():
        try:
            parsed = parse_imaging_report(imaging_report)
            if parsed.get("findings") or parsed.get("red_flags"):
                state["collected"]["imaging"] = parsed
                # Auto-fill condition if not yet set and imaging gives a strong hint
                if not state["collected"].get("condition") and parsed.get("condition_hints"):
                    state["collected"]["condition"] = parsed["condition_hints"][0]
                # Log a synthetic reasoning step for transparency in the UI
                state.setdefault("all_reasoning", [])
                state["all_reasoning"].append({
                    "action": "parse_imaging_report",
                    "args": {"report_length": len(imaging_report)},
                })
                state["all_reasoning"].append({
                    "observation": "parse_imaging_report",
                    "result": parsed.get("summary", "Parsed imaging report"),
                })
        except Exception as e:
            print(f"[imaging] parse error: {e}")

    result, state = process_message(message, history, state)

    reasoning_chain = result.get("reasoning_chain", []) if isinstance(result, dict) else []
    reasoning_html = _format_reasoning_chain(reasoning_chain)
    state.setdefault("all_reasoning", [])
    state["all_reasoning"].extend(reasoning_chain)

    if isinstance(result, dict) and "plan" in result:
        explanation = result.get("explanation", "")
        patient_info = result.get("patient_info", {})
        exercises_html = _format_prescription_html(result)
        profile_md = _format_patient_profile(patient_info)
        state["collected"].update(patient_info)

        # Store prescription in progress data
        plan = result["plan"]
        exercise_names = [ex["name"] for ex in plan.get("exercises", [])]
        state["last_prescription"] = {
            "exercise_names": exercise_names,
            "level": plan.get("level", 0),
            "condition": plan.get("condition", ""),
        }

        # Update progress data with condition and level
        progress_data["condition"] = patient_info.get("condition", progress_data.get("condition", ""))
        progress_data["exercise_level"] = plan.get("level", 0)

        tool_names = [TOOL_LABELS.get(s["action"], s["action"]) for s in reasoning_chain if "action" in s]
        badge_html = " ".join(f"`{t}`" for t in tool_names)
        bot_msg = (f"**Assessment complete! Your personalized exercise plan is ready.**\n\n"
                   f"Tools used: {badge_html}\n\n"
                   "Scroll down for your prescription with videos.\n"
                   "Go to **My Progress** tab to start tracking your recovery!")
        history = history + [{"role": "assistant", "content": bot_msg}]

        progress = _progress_html(state.get("collected", {}))
        full_reasoning = _format_reasoning_chain(state.get("all_reasoning", []))

        yield (history, state, progress, profile_md, exercises_html, explanation,
               full_reasoning, progress_data, serialize_progress(progress_data), "")
    else:
        bot_msg = result.get("text", str(result)) if isinstance(result, dict) else str(result)
        tool_names = [TOOL_LABELS.get(s["action"], s["action"]) for s in reasoning_chain if "action" in s]
        if tool_names:
            badge_str = " ".join(f"`{t}`" for t in tool_names)
            bot_msg = f"[{badge_str}]\n\n{bot_msg}"

        history = history + [{"role": "assistant", "content": bot_msg}]
        progress = _progress_html(state.get("collected", {}))
        full_reasoning = _format_reasoning_chain(state.get("all_reasoning", []))

        yield (history, state, progress, gr.update(), gr.update(), gr.update(), full_reasoning,
               progress_data, serialize_progress(progress_data), "")


def reset():
    empty = create_empty_progress()
    return ([], None, _progress_html({}), "", "", "", "", empty,
            serialize_progress(empty), "", gr.update(choices=[]), "")


# ── Progress tab handlers ───────────────────────────────────────────────────

def load_progress_from_store(json_str: str):
    """Load progress from localStorage on app start."""
    progress_data = deserialize_progress(json_str)
    chart = generate_recovery_chart(progress_data)
    table = _progress_to_dataframe(progress_data)
    stats = _stats_html(progress_data)
    milestones = _milestones_html(progress_data)

    # Get exercise choices from progress data
    exercise_choices = []
    sessions = progress_data.get("sessions", [])
    if sessions:
        last = sessions[-1]
        exercise_choices = last.get("exercises_prescribed", [])

    return progress_data, chart, table, stats, milestones, gr.update(choices=exercise_choices)


def log_session_handler(
    progress_data: dict, pain_vas: float, exercises_done: list,
    difficulty: int, notes: str, consultation_state: dict | None
):
    """Log a session and update all displays."""
    if progress_data is None:
        progress_data = create_empty_progress()

    # Get prescribed exercises from consultation state
    prescribed = []
    level = progress_data.get("exercise_level", 0)
    if consultation_state and "last_prescription" in consultation_state:
        rx = consultation_state["last_prescription"]
        prescribed = rx.get("exercise_names", [])
        level = rx.get("level", level)

    if not prescribed and exercises_done:
        prescribed = list(exercises_done)

    progress_data = log_session(
        progress_data=progress_data,
        pain_vas=pain_vas,
        exercises_completed=exercises_done or [],
        exercises_prescribed=prescribed,
        difficulty_rating=difficulty,
        notes=notes,
        exercise_level=level,
    )

    chart = generate_recovery_chart(progress_data)
    table = _progress_to_dataframe(progress_data)
    stats = _stats_html(progress_data)
    milestones = _milestones_html(progress_data)
    serialized = serialize_progress(progress_data)

    # Check for new milestones in last entry
    new_ms = progress_data.get("milestones", [])
    status = "**Session logged!**"
    if new_ms:
        latest = new_ms[-1]
        status += f" &#127942; **{latest['label']}**"

    return progress_data, chart, table, stats, milestones, serialized, status


def get_exercise_choices(consultation_state: dict | None, progress_data: dict | None):
    """Get exercise names for the checkbox group."""
    choices = []
    if consultation_state and "last_prescription" in consultation_state:
        choices = consultation_state["last_prescription"].get("exercise_names", [])
    elif progress_data:
        sessions = progress_data.get("sessions", [])
        if sessions:
            choices = sessions[-1].get("exercises_prescribed", [])
    return gr.update(choices=choices, value=[])


# ── AI Insights handler ────────────────────────────────────────────────────

def generate_insights_handler(progress_data: dict, consultation_state: dict | None):
    """Run rule-based analysis, then optionally narrate with Gemma."""
    if not progress_data or not progress_data.get("sessions"):
        return (
            '<p style="color:#94a3b8 !important;">No sessions logged yet. Start tracking your progress to get AI insights!</p>',
            _format_recommendation_html({"recommendation": "insufficient_data"}),
            "",
        )

    # Rule-based analysis
    analysis = tool_analyze_progress(progress_data)
    insights_html = _format_insights_html(analysis)
    rec_html = _format_recommendation_html(analysis)

    # Generate AI narrative with Gemma
    ai_narrative = ""
    try:
        client = get_client()
        condition = progress_data.get("condition", "")
        stats = analysis.get("summary", {})
        pain_trend = analysis.get("pain_trend", {})
        insights_text = "\n".join(f"- [{i['type']}] {i['text']}" for i in analysis.get("insights", []))

        prompt = f"""You are PhysioGemma. Write a brief, warm, encouraging progress report (4-6 sentences)
for this patient based on their recovery data.

Condition: {condition}
Total sessions: {stats.get('total_sessions', 0)}
Pain: {stats.get('first_pain', '?')} -> {stats.get('current_pain', '?')} ({stats.get('pain_change_pct', 0):+.0f}%)
Adherence: {stats.get('avg_adherence', 0):.0f}%
Current level: {stats.get('current_level', '?')}
Streak: {stats.get('current_streak', 0)} days
Pain trend: {pain_trend.get('trend', 'unknown')}
Recommendation: {analysis.get('recommendation', 'maintain')}

Key insights:
{insights_text}

Be specific with numbers. Be encouraging but honest. If there are concerns, address them gently.
End with one actionable tip for their next session."""

        from google.genai import types
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(system_instruction=AGENT_SYSTEM_PROMPT),
        )
        ai_narrative = response.text if response.text else ""
    except Exception:
        ai_narrative = ""

    return insights_html, rec_html, ai_narrative


# ── Build Gradio app ────────────────────────────────────────────────────────

def build_app():
    with gr.Blocks(theme=THEME, css=CSS, title="PhysioGemma — AI Physiotherapy Agent") as app:

        # ── Top nav (Modernist) ──
        gr.HTML("""
        <div style="display:flex; align-items:center; gap:16px; padding:18px 8px 16px 8px;
                    border-bottom:2px solid rgba(32,30,29,0.4); flex-wrap:wrap;">
            <div style="display:flex; align-items:center; gap:10px; margin-right:auto;">
                <span style="display:inline-block; width:14px; height:14px; background:#ec3013;"></span>
                <span style="font-size:19px; font-weight:800; color:#201e1d !important;
                             letter-spacing:-0.015em; font-family:'Archivo',sans-serif;">PhysioGemma</span>
            </div>
            <span style="font-size:12px; letter-spacing:0.08em; text-transform:uppercase;
                         padding:4px 12px; border:2px solid rgba(32,30,29,0.4);
                         color:#201e1d !important;">
                Gemma 4 26B &middot; no login &middot; data stays in your browser
            </span>
        </div>
        """)

        # Hidden progress store for localStorage bridge
        progress_store = gr.Textbox(visible=False, elem_id="progress_store")
        progress_state = gr.State(None)
        consultation_state = gr.State(None)

        # ── TABS ────────────────────────────────────────────────────────
        with gr.Tabs() as tabs:

            # ════════════════════════════════════════════════════════════
            # TAB 1: CONSULTATION
            # ════════════════════════════════════════════════════════════
            with gr.TabItem("Consultation", id="consult"):

                gr.HTML("""
                <div style="border:2px solid #201e1d; padding:16px 18px; margin:12px 0 4px 0;">
                    <div style="font-size:11px; letter-spacing:0.1em; text-transform:uppercase;
                                font-weight:800; color:#ae1800 !important; margin-bottom:6px;">
                        How decisions are made</div>
                    <p style="margin:0; font-size:13px; line-height:1.6; color:#201e1d !important;">
                        Every exercise comes from a deterministic rule engine &mdash; Gemma 4 reasons
                        and explains, but can never invent an unsafe exercise. Red flags are checked
                        on every message. Every tool call is logged in the reasoning chain.</p>
                </div>
                """)

                # ── OPTIONAL: Radiology report (Mode 1 imaging) ──────────────
                gr.HTML("""
                <div style="background:#eae9e9; padding:18px 20px 6px 20px; margin:8px 0 0 0;">
                    <h4 style="font-weight:800; font-size:16px; margin:0 0 4px 0; color:#201e1d !important;">
                        Imaging report <span style="font-weight:400; color:rgba(32,30,29,0.6) !important;">(optional)</span></h4>
                    <p style="margin:0; font-size:13px; color:rgba(32,30,29,0.6) !important;">
                        Paste your MRI / X-ray report text. Findings are parsed locally and bias
                        your plan &mdash; 45+ patterns, red flags included.</p>
                </div>
                """)
                imaging_report_box = gr.Textbox(
                    label="Radiology report text (leave empty to skip)",
                    placeholder="e.g. MRI Lumbar Spine — L4-L5 disc protrusion with mild left lateral recess stenosis. No nerve root impingement.",
                    lines=3,
                )

                progress_display = gr.HTML(value=_progress_html({}))

                try:
                    chatbot = gr.Chatbot(
                        label="PhysioGemma Agent",
                        height=420,
                        type="messages",
                        placeholder="Describe your pain or condition to begin...",
                    )
                except TypeError:
                    chatbot = gr.Chatbot(
                        label="PhysioGemma Agent",
                        height=420,
                        placeholder="Describe your pain or condition to begin...",
                    )

                with gr.Row():
                    msg = gr.Textbox(
                        label="Your message",
                        placeholder="Example: My lower back hurts for 3 months, pain 6/10, I'm 45, desk worker...",
                        lines=2, scale=4,
                    )
                    with gr.Column(scale=1, min_width=120):
                        send_btn = gr.Button("Send", variant="primary", size="lg")
                        reset_btn = gr.Button("New Assessment", variant="secondary", size="sm")

                gr.Examples(
                    examples=[
                        "My lower back has been hurting for 3 months. Pain is about 6 out of 10. I'm 45 years old.",
                        "I'm 62, knee pain for 6 months, getting worse lately",
                        "Shoulder is frozen, can't raise my arm. 55 years old, 4 months ago",
                        "Pain shooting down my left leg from lower back, 7/10, age 38",
                        "My heel hurts every morning, been 2 months, I stand all day at work",
                        "Elbow pain on outer side, worse when gripping, I work in IT",
                    ],
                    inputs=msg,
                    label="Try these examples:",
                )

                gr.HTML("<hr class='section-divider'>")

                with gr.Row():
                    with gr.Column(scale=1):
                        profile_display = gr.Markdown(label="Clinical Assessment Summary")
                    with gr.Column(scale=1):
                        reasoning_display = gr.Markdown(label="Clinical Reasoning")

                exercises_display = gr.HTML(label="Exercise Prescription")

                with gr.Accordion("Agent Reasoning Chain", open=False):
                    agent_chain_display = gr.HTML(label="Reasoning Chain")

            # ════════════════════════════════════════════════════════════
            # TAB 2: MY PROGRESS
            # ════════════════════════════════════════════════════════════
            with gr.TabItem("My Progress", id="progress"):

                gr.HTML("""
                <div style="display:flex; align-items:baseline; justify-content:space-between;
                            border-bottom:2px solid rgba(32,30,29,0.4); padding-bottom:10px; margin:8px 0 4px 0;">
                    <h3 style="color:#201e1d !important; font-size:22px; font-weight:800; margin:0;">
                        Track your recovery</h3>
                    <span style="color:rgba(32,30,29,0.55) !important; font-size:13px;">
                        pain &middot; adherence &middot; streak &middot; milestones</span>
                </div>
                """)
                stats_display = gr.HTML(value=_stats_html({}))
                milestones_display = gr.HTML(value="")

                gr.HTML("<hr class='section-divider'>")
                gr.HTML("""
                <div style="border-bottom:2px solid rgba(32,30,29,0.4); padding-bottom:10px; margin-bottom:16px;">
                    <h3 style="color:#201e1d !important; font-size:22px; font-weight:800; margin:0;">
                        Log today's session</h3>
                </div>
                """)

                with gr.Row():
                    with gr.Column(scale=1):
                        pain_slider = gr.Slider(
                            minimum=0, maximum=10, step=0.5, value=5,
                            label="Pain Level Today (VAS 0-10)"
                        )
                        difficulty_slider = gr.Slider(
                            minimum=1, maximum=5, step=1, value=3,
                            label="Difficulty (1=Easy, 5=Very Hard)"
                        )
                    with gr.Column(scale=1):
                        exercises_completed = gr.CheckboxGroup(
                            choices=[],
                            label="Exercises Completed",
                        )

                session_notes = gr.Textbox(
                    label="Session Notes (optional)",
                    placeholder="How did you feel? Any issues? What felt easier?",
                    lines=2,
                )

                with gr.Row():
                    log_btn = gr.Button("Log Session", variant="primary", size="lg")
                    refresh_exercises_btn = gr.Button("Load My Exercises", variant="secondary", size="sm")

                log_status = gr.Markdown("")

                gr.HTML("<hr class='section-divider'>")
                gr.HTML("""
                <div style="display:flex; align-items:baseline; justify-content:space-between;
                            border-bottom:2px solid rgba(32,30,29,0.4); padding-bottom:10px; margin-bottom:16px;">
                    <h3 style="color:#201e1d !important; font-size:22px; font-weight:800; margin:0;">
                        Recovery graph</h3>
                    <span style="color:rgba(32,30,29,0.55) !important; font-size:13px;">
                        Pain (VAS) &middot; adherence over time</span>
                </div>
                """)
                recovery_plot = gr.Plot(label="Recovery Progress")

                gr.HTML("<hr class='section-divider'>")
                gr.HTML("""
                <div style="border-bottom:2px solid rgba(32,30,29,0.4); padding-bottom:10px; margin-bottom:4px;">
                    <h3 style="color:#201e1d !important; font-size:17px; font-weight:800; margin:0;">
                        Session history</h3>
                </div>
                """)
                session_history = gr.Dataframe(
                    headers=["Date", "Pain", "Adherence", "Difficulty", "Level", "Notes"],
                    label="Past Sessions",
                    interactive=False,
                )

            # ════════════════════════════════════════════════════════════
            # TAB 3: AI INSIGHTS
            # ════════════════════════════════════════════════════════════
            with gr.TabItem("AI Insights", id="insights"):

                gr.HTML("""
                <div style="border-bottom:2px solid rgba(32,30,29,0.4); padding-bottom:12px; margin-bottom:16px;">
                    <h3 style="color:#201e1d !important; font-size:25px; font-weight:800; margin:0;">
                        Recovery insights</h3>
                    <p style="color:rgba(32,30,29,0.55) !important; font-size:13px; margin:4px 0 0 0;">
                        Rule-based analysis of your sessions, narrated by Gemma 4</p>
                </div>
                """)

                refresh_insights_btn = gr.Button("Generate insights", variant="primary", size="lg")

                recommendation_display = gr.HTML("")
                insights_display = gr.HTML("")

                gr.HTML("<hr class='section-divider'>")
                gr.HTML("""
                <div style="background:#eae9e9; padding:20px 22px;">
                    <div style="font-size:10px; letter-spacing:0.1em; text-transform:uppercase;
                                color:#ae1800 !important; font-weight:800; margin-bottom:8px;">
                        Gemma 4 &middot; your recovery report</div>
                """)
                ai_narrative_display = gr.Markdown("")
                gr.HTML("""</div>
                <div style="border:2px solid #201e1d; padding:16px 18px; margin-top:24px;">
                    <div style="font-size:11px; letter-spacing:0.1em; text-transform:uppercase;
                                font-weight:800; margin-bottom:6px; color:#201e1d !important;">
                        How this works</div>
                    <p style="margin:0; font-size:13px; line-height:1.6; color:#201e1d !important;">
                        Trends, adherence and level-readiness are computed by deterministic rules
                        on your logged sessions. Gemma 4 only narrates &mdash; it never decides
                        your exercise level.</p>
                </div>
                <p style="margin:16px 0 0 0; font-size:12px; color:rgba(32,30,29,0.55) !important;">
                    PhysioGemma supplements, and does not replace, professional physiotherapy care.
                    If pain worsens sharply or new symptoms appear, consult a clinician.</p>
                """)

        # Footer
        gr.HTML("""
        <div style="margin-top:28px; padding:16px 8px 8px 8px;
                    border-top:2px solid rgba(32,30,29,0.4);
                    display:flex; align-items:baseline; gap:16px; flex-wrap:wrap;">
            <span style="font-size:14px; font-weight:800; color:#201e1d !important;">PhysioGemma</span>
            <span style="font-size:12px; color:rgba(32,30,29,0.55) !important;">
                Kaggle Gemma 4 Good Hackathon &middot; Health &amp; Sciences Track</span>
            <span style="margin-left:auto; font-size:11px; letter-spacing:0.08em; text-transform:uppercase;
                         color:rgba(32,30,29,0.55) !important;">
                ReAct agent &middot; 183 exercises &middot; not medical advice &middot; CC-BY 4.0</span>
        </div>
        """)

        # ── Event Wiring ────────────────────────────────────────────────

        # Load progress from localStorage on app start
        app.load(
            fn=load_progress_from_store,
            inputs=[progress_store],
            outputs=[progress_state, recovery_plot, session_history,
                     stats_display, milestones_display, exercises_completed],
            js=JS_LOAD_PROGRESS,
        )

        # Consultation chat — single generator event: yields loading state
        # first, then the final result (no .then() chain, no input races)
        chat_inputs = [msg, chatbot, consultation_state, progress_state, imaging_report_box]
        chat_outputs = [chatbot, consultation_state, progress_display, profile_display,
                        exercises_display, reasoning_display, agent_chain_display,
                        progress_state, progress_store, msg]

        send_btn.click(
            fn=chat, inputs=chat_inputs, outputs=chat_outputs,
        ).then(fn=None, js=JS_SAVE_PROGRESS, inputs=[progress_store])

        msg.submit(
            fn=chat, inputs=chat_inputs, outputs=chat_outputs,
        ).then(fn=None, js=JS_SAVE_PROGRESS, inputs=[progress_store])

        reset_btn.click(
            fn=reset,
            outputs=[chatbot, consultation_state, progress_display, profile_display,
                     exercises_display, reasoning_display, agent_chain_display,
                     progress_state, progress_store, log_status, exercises_completed,
                     imaging_report_box],
        )

        # Log session
        log_btn.click(
            fn=log_session_handler,
            inputs=[progress_state, pain_slider, exercises_completed,
                    difficulty_slider, session_notes, consultation_state],
            outputs=[progress_state, recovery_plot, session_history,
                     stats_display, milestones_display, progress_store, log_status],
        ).then(fn=None, js=JS_SAVE_PROGRESS, inputs=[progress_store])

        # Refresh exercises from prescription
        refresh_exercises_btn.click(
            fn=get_exercise_choices,
            inputs=[consultation_state, progress_state],
            outputs=[exercises_completed],
        )

        # AI Insights
        refresh_insights_btn.click(
            fn=generate_insights_handler,
            inputs=[progress_state, consultation_state],
            outputs=[insights_display, recommendation_display, ai_narrative_display],
        )

    return app


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = build_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", 7860)),
        share=False,
        ssr_mode=False,
    )
