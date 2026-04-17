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

THEME = gr.themes.Soft(
    primary_hue="blue",
    secondary_hue="emerald",
    neutral_hue="slate",
    font=gr.themes.GoogleFont("Inter"),
)

CSS = """
/* ══════════════════════════════════════════════════════════════════════════
   PhysioGemma — Premium Healthcare Dashboard
   Design System: #F8FAFC bg · #2563EB primary · #10B981 accent · Inter font
   ══════════════════════════════════════════════════════════════════════════ */

/* ── Reset & Global ──────────────────────────────────────────────────────── */
.gradio-container {
    max-width: 1100px !important;
    background: #F8FAFC !important;
}
* { transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1); }

/* ── Force readable dark text everywhere ─────────────────────────────────── */
body, .gradio-container, .gradio-container *,
.prose *, .markdown-text *, span, p, li, td, th,
label, h1, h2, h3, h4, h5, h6 {
    color: #1e293b !important;
}
.dark body, .dark .gradio-container * { color: #1e293b !important; }

/* ── Typography ──────────────────────────────────────────────────────────── */
h1 { font-weight: 800 !important; letter-spacing: -0.03em !important; }
h2, h3 { font-weight: 700 !important; color: #0f172a !important; }
h4, h5 { font-weight: 600 !important; color: #1e293b !important; }
label { color: #475569 !important; font-weight: 600 !important; font-size: 13px !important; }

/* ── Card base ───────────────────────────────────────────────────────────── */
.card-base {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.03);
}
.card-base:hover {
    box-shadow: 0 4px 16px rgba(0,0,0,0.08), 0 8px 32px rgba(0,0,0,0.04);
    transform: translateY(-2px);
}

/* ── Chat bubbles ────────────────────────────────────────────────────────── */
.message-wrap .message {
    border-radius: 18px !important;
    padding: 14px 20px !important;
    font-size: 15px !important;
    line-height: 1.7 !important;
    max-width: 85% !important;
}
.message-wrap .bot,
.chatbot .message-wrap .bot {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
    border-radius: 18px 18px 18px 4px !important;
}
.message-wrap .bot *, .message-wrap .bot p,
.message-wrap .bot span, .message-wrap .bot li,
.message-wrap .bot strong, .message-wrap .bot code,
.chatbot .message-wrap .bot *,
.chatbot .message-wrap .bot p,
.chatbot .message-wrap .bot span {
    color: #1e293b !important;
}
.message-wrap .bot code {
    background: #f1f5f9 !important;
    color: #2563EB !important;
    padding: 2px 6px !important;
    border-radius: 6px !important;
    font-size: 13px !important;
}
.message-wrap .user,
.chatbot .message-wrap .user {
    background: linear-gradient(135deg, #2563EB 0%, #1d4ed8 100%) !important;
    color: #ffffff !important;
    border-radius: 18px 18px 4px 18px !important;
    box-shadow: 0 4px 14px rgba(37,99,235,0.35) !important;
}
.message-wrap .user *, .message-wrap .user p,
.message-wrap .user span, .message-wrap .user li,
.chatbot .message-wrap .user *,
.chatbot .message-wrap .user p,
.chatbot .message-wrap .user span {
    color: #ffffff !important;
}

/* ── Buttons ─────────────────────────────────────────────────────────────── */
button.primary {
    background: linear-gradient(135deg, #2563EB 0%, #1d4ed8 100%) !important;
    border: none !important;
    border-radius: 14px !important;
    font-weight: 700 !important;
    letter-spacing: 0.01em !important;
    box-shadow: 0 4px 14px rgba(37,99,235,0.3) !important;
    padding: 10px 24px !important;
}
button.primary:hover {
    box-shadow: 0 6px 20px rgba(37,99,235,0.45) !important;
    transform: translateY(-1px) scale(1.01);
}
button.primary:active {
    transform: translateY(0px) scale(0.99);
    box-shadow: 0 2px 8px rgba(37,99,235,0.3) !important;
}
button.secondary {
    border-radius: 14px !important;
    border: 1.5px solid #e2e8f0 !important;
    background: #ffffff !important;
    font-weight: 600 !important;
    color: #475569 !important;
}
button.secondary:hover {
    background: #f8fafc !important;
    border-color: #2563EB !important;
    color: #2563EB !important;
    box-shadow: 0 2px 8px rgba(37,99,235,0.1) !important;
}

/* ── Tabs ────────────────────────────────────────────────────────────────── */
.tabs > .tab-nav {
    background: #ffffff !important;
    border-radius: 14px 14px 0 0 !important;
    border-bottom: 2px solid #e2e8f0 !important;
    padding: 4px 4px 0 4px !important;
}
.tabs > .tab-nav > button {
    font-size: 14px !important;
    font-weight: 600 !important;
    padding: 12px 24px !important;
    border-radius: 10px 10px 0 0 !important;
    color: #64748b !important;
    border: none !important;
}
.tabs > .tab-nav > button.selected {
    background: #f0f7ff !important;
    border-bottom: 3px solid #2563EB !important;
    color: #2563EB !important;
    font-weight: 700 !important;
}
.tabs > .tab-nav > button:hover:not(.selected) {
    background: #f8fafc !important;
    color: #334155 !important;
}

/* ── Progress pills (consultation tracker) ───────────────────────────────── */
.progress-bar {
    display: flex;
    gap: 8px;
    justify-content: center;
    margin: 16px 0 28px 0;
    flex-wrap: wrap;
}
.progress-pill {
    padding: 7px 18px;
    border-radius: 24px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.03em;
}
.progress-done {
    background: linear-gradient(135deg, #10B981, #059669);
    color: #ffffff !important;
    box-shadow: 0 3px 10px rgba(16,185,129,0.35);
}
.progress-done * { color: #ffffff !important; }
.progress-pending {
    background: #f1f5f9;
    color: #64748b !important;
    border: 1.5px solid #e2e8f0;
}
.progress-pending * { color: #64748b !important; }

/* ── Stat cards ──────────────────────────────────────────────────────────── */
.stat-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 24px 16px 20px 16px;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.02);
    position: relative;
    overflow: hidden;
}
.stat-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, #2563EB, #10B981);
    opacity: 0;
    transition: opacity 0.3s ease;
}
.stat-card:hover {
    box-shadow: 0 8px 28px rgba(0,0,0,0.08);
    transform: translateY(-3px);
    border-color: #bfdbfe;
}
.stat-card:hover::before { opacity: 1; }
.stat-icon-wrap {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 48px; height: 48px;
    border-radius: 14px;
    font-size: 22px;
    margin-bottom: 8px;
}
.stat-card h3 {
    color: #0f172a !important;
    margin: 6px 0 2px 0 !important;
    font-size: 28px !important;
    font-weight: 800 !important;
}
.stat-card p {
    color: #64748b !important;
    margin: 0 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
}

/* ── Exercise cards ──────────────────────────────────────────────────────── */
.exercise-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 22px;
    margin: 14px 0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.02);
}
.exercise-card:hover {
    box-shadow: 0 8px 28px rgba(37,99,235,0.1);
    transform: translateY(-2px);
    border-color: #93c5fd;
}
.exercise-card h4 {
    color: #0f172a !important;
    margin: 0 0 10px 0;
    font-size: 17px;
    font-weight: 700;
}
.exercise-card p {
    color: #475569 !important;
    margin: 6px 0;
    font-size: 14px;
    line-height: 1.65;
}
.exercise-card .ex-meta {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin: 10px 0 12px 0;
}
.exercise-card .ex-badge {
    display: inline-block;
    padding: 5px 14px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.03em;
}
.ex-badge-sets { background: #eff6ff; color: #2563EB !important; border: 1px solid #bfdbfe; }
.ex-badge-reps { background: #ecfdf5; color: #059669 !important; border: 1px solid #a7f3d0; }
.ex-badge-type { background: #f5f3ff; color: #7c3aed !important; border: 1px solid #ddd6fe; }
.exercise-card a {
    display: block;
    margin-top: 14px;
    border-radius: 14px;
    overflow: hidden;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}
.exercise-card a:hover {
    box-shadow: 0 6px 24px rgba(37,99,235,0.15);
    transform: scale(1.01);
}

/* ── Reasoning chain ─────────────────────────────────────────────────────── */
.reasoning-step {
    border-radius: 12px;
    padding: 12px 16px;
    margin: 8px 0;
    font-size: 13px;
    line-height: 1.65;
}
.reasoning-action {
    background: #f0f7ff;
    border-left: 4px solid #2563EB;
    border: 1px solid #bfdbfe;
    border-left: 4px solid #2563EB;
}
.reasoning-observation {
    background: #ecfdf5;
    border: 1px solid #a7f3d0;
    border-left: 4px solid #10B981;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
}
.reasoning-warning {
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-left: 4px solid #ef4444;
}
.tool-badge {
    display: inline-block;
    background: linear-gradient(135deg, #eff6ff, #dbeafe);
    border: 1px solid #93c5fd;
    color: #1d4ed8 !important;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    margin: 2px 4px;
    letter-spacing: 0.03em;
    text-transform: uppercase;
}

/* ── Milestone badges ────────────────────────────────────────────────────── */
.milestone-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: linear-gradient(135deg, #fffbeb, #fef3c7);
    border: 1.5px solid #fbbf24;
    border-radius: 24px;
    padding: 8px 18px;
    font-size: 13px;
    margin: 4px;
    color: #b45309 !important;
    font-weight: 700;
    box-shadow: 0 2px 8px rgba(251,191,36,0.2);
}
.milestone-badge:hover {
    box-shadow: 0 4px 16px rgba(251,191,36,0.3);
    transform: translateY(-1px);
}

/* ── Insight cards ───────────────────────────────────────────────────────── */
.insight-card {
    border-radius: 14px;
    padding: 16px 20px;
    margin: 10px 0;
    font-size: 14px;
    line-height: 1.65;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    border: 1px solid transparent;
}
.insight-card:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(0,0,0,0.06);
}
.insight-improvement {
    background: #ecfdf5;
    border-left: 4px solid #10B981;
    border-color: #a7f3d0;
}
.insight-concern {
    background: #fef2f2;
    border-left: 4px solid #ef4444;
    border-color: #fecaca;
}
.insight-suggestion {
    background: #eff6ff;
    border-left: 4px solid #2563EB;
    border-color: #bfdbfe;
}
.insight-achievement {
    background: #fffbeb;
    border-left: 4px solid #f59e0b;
    border-color: #fde68a;
}
.insight-info {
    background: #f8fafc;
    border-left: 4px solid #64748b;
    border-color: #e2e8f0;
}
.insight-milestone {
    background: #faf5ff;
    border-left: 4px solid #8b5cf6;
    border-color: #ddd6fe;
}
.insight-ready_to_progress {
    background: #ecfdf5;
    border-left: 4px solid #059669;
    border-color: #a7f3d0;
}

/* ── Recommendation box ──────────────────────────────────────────────────── */
.recommendation-box {
    border-radius: 16px;
    padding: 22px 28px;
    margin: 18px 0;
    font-size: 16px;
    font-weight: 700;
    text-align: center;
    box-shadow: 0 2px 12px rgba(0,0,0,0.05);
}

/* ── Hero trust badges ───────────────────────────────────────────────────── */
.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 6px 16px;
    border-radius: 24px;
    font-size: 12px;
    font-weight: 700;
    margin: 4px;
    letter-spacing: 0.03em;
    backdrop-filter: blur(8px);
}
.badge-agent {
    background: rgba(134,239,172,0.18);
    color: #86efac !important;
    border: 1px solid rgba(134,239,172,0.38);
}
.badge-rag {
    background: rgba(52,211,153,0.15);
    color: #6ee7b7 !important;
    border: 1px solid rgba(52,211,153,0.32);
}
.badge-clinical {
    background: rgba(251,191,36,0.15);
    color: #fcd34d !important;
    border: 1px solid rgba(251,191,36,0.3);
}
.trust-item {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    background: rgba(255,255,255,0.07);
    border-radius: 24px;
    font-size: 12px;
    font-weight: 600;
    color: #bbf7d0 !important;
    margin: 3px;
    backdrop-filter: blur(8px);
    border: 1px solid rgba(134,239,172,0.2);
}

/* ── Section dividers ────────────────────────────────────────────────────── */
.section-divider {
    border: none;
    border-top: 1px solid #e2e8f0;
    margin: 28px 0;
}

/* ── Session card layout ─────────────────────────────────────────────────── */
.session-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 16px 20px;
    margin: 8px 0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    display: flex;
    align-items: center;
    gap: 16px;
}
.session-card:hover {
    box-shadow: 0 4px 16px rgba(0,0,0,0.06);
    border-color: #bfdbfe;
}
.pain-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 700;
}
.pain-low { background: #ecfdf5; color: #059669 !important; border: 1px solid #a7f3d0; }
.pain-mid { background: #fffbeb; color: #b45309 !important; border: 1px solid #fde68a; }
.pain-high { background: #fef2f2; color: #dc2626 !important; border: 1px solid #fecaca; }
.level-badge {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 700;
    background: #eff6ff;
    color: #2563EB !important;
    border: 1px solid #bfdbfe;
}

/* ── Form elements ───────────────────────────────────────────────────────── */
input[type="range"] {
    height: 8px !important;
    border-radius: 4px !important;
}
input, textarea {
    color: #1e293b !important;
    border-radius: 12px !important;
    border-color: #e2e8f0 !important;
}
input:focus, textarea:focus {
    border-color: #2563EB !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.1) !important;
}
.checkbox-group label {
    padding: 8px 16px !important;
    border-radius: 10px !important;
    border: 1.5px solid #e2e8f0 !important;
    margin: 4px !important;
    font-weight: 500 !important;
}
.checkbox-group label:hover {
    border-color: #93c5fd !important;
    background: #f0f7ff !important;
}
.checkbox-group input:checked + label,
.checkbox-group label.selected {
    background: #eff6ff !important;
    border-color: #2563EB !important;
    color: #2563EB !important;
}

/* ── Accordion ───────────────────────────────────────────────────────────── */
.accordion {
    border-radius: 14px !important;
    border: 1px solid #e2e8f0 !important;
    background: #ffffff !important;
}
.accordion *, .accordion label, .accordion span { color: #1e293b !important; }

/* ── Misc ────────────────────────────────────────────────────────────────── */
footer { display: none !important; }
.markdown-text, .markdown-text *, .prose, .prose * { color: #1e293b !important; }
.dataframe { border-radius: 12px !important; overflow: hidden; }
.dataframe th {
    background: #f8fafc !important;
    color: #475569 !important;
    font-weight: 700 !important;
    font-size: 12px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
}
.dataframe td {
    color: #1e293b !important;
    font-size: 14px !important;
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
        icon = "&#10003;" if has_data else "&#9679;"
        pills.append(f'<span class="progress-pill {cls}">{icon} {label}</span>')
    return f'<div class="progress-bar">{"".join(pills)}</div>'


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
    html += '<h4 style="color: #0f172a; margin-bottom: 10px; font-size: 15px; font-weight: 700;">Agent Reasoning Chain</h4>'
    for step in chain:
        if "action" in step:
            tool_label = TOOL_LABELS.get(step["action"], step["action"])
            args_str = ", ".join(f"{k}={v}" for k, v in step.get("args", {}).items()
                                if k not in ("patient_message", "progress_data_json"))
            if len(args_str) > 120:
                args_str = args_str[:120] + "..."
            html += (
                f'<div class="reasoning-step reasoning-action">'
                f'<strong>Action:</strong> <span class="tool-badge">{tool_label}</span>'
            )
            if args_str:
                html += f' <span style="color:#64748b; font-size:12px;">({args_str})</span>'
            html += '</div>'
        elif "observation" in step:
            tool_label = TOOL_LABELS.get(step["observation"], step["observation"])
            result_str = step.get("result", "")
            is_warning = "RED FLAG" in result_str.upper()
            cls = "reasoning-warning" if is_warning else "reasoning-observation"
            html += (
                f'<div class="reasoning-step {cls}">'
                f'<strong>Observation ({tool_label}):</strong> {result_str}'
                f'</div>'
            )
    html += '</div>'
    return html


# ── Format prescription exercises ───────────────────────────────────────────

def _format_prescription_html(result: dict) -> str:
    plan = result["plan"]
    exercises_html = ""
    type_icons = {
        "mobility": "&#128260;", "stretching": "&#129496;",
        "strengthening": "&#128170;", "stability": "&#9878;",
        "plyometric": "&#127939;", "posture": "&#129492;",
        "functional": "&#127947;"
    }
    for ex in plan["exercises"]:
        video_id = ex.get("video") or ex.get("video_id") or ""
        video_embed = ""
        if video_id:
            yt_url = f"https://www.youtube.com/watch?v={video_id}"
            thumb_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
            fallback_thumb = f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"
            video_embed = (
                f'<a href="{yt_url}" target="_top" '
                f'style="display:block; position:relative; margin-top:14px; '
                f'border-radius:14px; overflow:hidden; max-width:100%;">'
                f'<img src="{thumb_url}" '
                f'onerror="this.onerror=null;this.src=\'{fallback_thumb}\';" '
                f'style="width:100%; border-radius:14px; display:block;" '
                f'alt="Watch exercise video" />'
                f'<span style="position:absolute; top:50%; left:50%; '
                f'transform:translate(-50%,-50%); font-size:56px; '
                f'color:#fff; text-shadow:0 2px 16px rgba(0,0,0,0.5); '
                f'pointer-events:none;">&#9654;</span>'
                f'</a>'
            )
        icon = type_icons.get(ex.get("type", ""), "&#127947;")
        ex_type = ex.get("type", "general").title()
        exercises_html += (
            f'<div class="exercise-card">'
            f'<h4>{icon} {ex["name"]}</h4>'
            f'<div class="ex-meta">'
            f'<span class="ex-badge ex-badge-sets">Sets: {ex["sets"]}</span>'
            f'<span class="ex-badge ex-badge-reps">Reps: {ex["reps"]}</span>'
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
        <div style="text-align:center; padding:48px 24px; background:#ffffff;
                    border-radius:16px; border:1px solid #e2e8f0;
                    box-shadow:0 1px 3px rgba(0,0,0,0.04);">
            <div style="font-size:48px; margin-bottom:8px;">&#128203;</div>
            <p style="font-size:16px; color:#475569 !important; font-weight:600; margin:0 0 4px 0;">
                No sessions logged yet</p>
            <p style="font-size:14px; color:#94a3b8 !important; margin:0;">
                Complete a consultation and start tracking your recovery!</p>
        </div>"""

    pain_pct = stats.get("pain_change_pct", 0)
    pain_color = "#10B981" if pain_pct < 0 else "#ef4444" if pain_pct > 0 else "#64748b"
    pain_arrow = "&#8595;" if pain_pct < 0 else "&#8593;" if pain_pct > 0 else "&#8594;"

    cards = [
        ("&#128197;", "#eff6ff", "#2563EB", stats['total_sessions'], "Sessions", ""),
        ("&#128201;", "#ecfdf5" if pain_pct <= 0 else "#fef2f2",
         pain_color, f"{stats.get('current_pain', 'N/A')}/10",
         "Current Pain", f"{pain_arrow} {abs(pain_pct):.0f}%"),
        ("&#9989;", "#ecfdf5", "#10B981", f"{stats.get('avg_adherence', 0):.0f}%", "Adherence", ""),
        ("&#128293;", "#fff7ed", "#f97316", stats.get('current_streak', 0), "Day Streak", ""),
        ("&#127947;", "#f5f3ff", "#7c3aed", f"L{stats.get('current_level', '?')}", "Level", ""),
        ("&#127942;", "#fffbeb", "#f59e0b", stats.get('milestones_earned', 0), "Milestones", ""),
    ]

    html = '<div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(155px, 1fr)); gap:14px; margin:16px 0;">'
    for icon, bg, accent, value, label, sub in cards:
        sub_html = f'<p style="color:{accent} !important; font-size:12px; font-weight:600; margin:2px 0 0 0;">{sub}</p>' if sub else ''
        html += f"""
        <div class="stat-card">
            <div class="stat-icon-wrap" style="background:{bg};">
                <span style="font-size:22px;">{icon}</span>
            </div>
            <h3 style="color:{accent} !important;">{value}</h3>
            <p>{label}</p>
            {sub_html}
        </div>"""
    html += '</div>'

    # Recovery status bar
    if pain_pct < -15:
        status_label, status_color, status_bg, status_pct = "Improving", "#10B981", "#ecfdf5", min(90, 50 + abs(pain_pct))
    elif pain_pct > 10:
        status_label, status_color, status_bg, status_pct = "Needs Attention", "#ef4444", "#fef2f2", max(20, 50 - pain_pct)
    else:
        status_label, status_color, status_bg, status_pct = "Stable", "#f59e0b", "#fffbeb", 50

    html += f"""
    <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:16px;
                padding:20px 24px; margin-top:16px;
                box-shadow:0 1px 3px rgba(0,0,0,0.04);">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
            <span style="font-weight:700; font-size:15px; color:#0f172a !important;">Your Recovery Status</span>
            <span style="padding:5px 14px; border-radius:20px; font-size:12px; font-weight:700;
                         background:{status_bg}; color:{status_color} !important; border:1px solid {status_color}22;">
                {status_label}
            </span>
        </div>
        <div style="background:#f1f5f9; border-radius:8px; height:10px; overflow:hidden;">
            <div style="background:linear-gradient(90deg, {status_color}, {status_color}aa);
                        height:100%; width:{status_pct}%; border-radius:8px;
                        transition:width 0.5s ease;"></div>
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

INSIGHT_ICONS = {
    "improvement": "&#128200;",
    "concern": "&#9888;&#65039;",
    "suggestion": "&#128161;",
    "achievement": "&#127942;",
    "info": "&#8505;&#65039;",
    "milestone": "&#11088;",
    "ready_to_progress": "&#128640;",
}

RECOMMENDATION_STYLES = {
    "progress": ("background: linear-gradient(135deg, #ecfdf5, #d1fae5); color:#065f46 !important; border:2px solid #10B981;",
                 "&#128640; Ready to Progress to Next Level!"),
    "maintain": ("background: linear-gradient(135deg, #eff6ff, #dbeafe); color:#1e40af !important; border:2px solid #2563EB;",
                 "&#128170; Maintain Current Level — Keep Going!"),
    "regress": ("background: linear-gradient(135deg, #fef2f2, #fecaca); color:#991b1b !important; border:2px solid #ef4444;",
                "&#9888; Consider Stepping Back a Level for Safety"),
    "insufficient_data": ("background: linear-gradient(135deg, #f8fafc, #f1f5f9); color:#64748b !important; border:2px solid #cbd5e1;",
                          "&#128202; Log More Sessions for Personalized Insights"),
}


def _format_insights_html(analysis: dict) -> str:
    insights = analysis.get("insights", [])
    if not insights:
        return '<p style="color:#94a3b8 !important;">No insights yet. Log sessions to generate recovery insights.</p>'

    html = ""
    for ins in insights:
        itype = ins.get("type", "info")
        icon = INSIGHT_ICONS.get(itype, "&#8226;")
        cls = f"insight-{itype}"
        html += f'<div class="insight-card {cls}">{icon} {ins["text"]}</div>'
    return html


def _format_recommendation_html(analysis: dict) -> str:
    rec = analysis.get("recommendation", "insufficient_data")
    style, text = RECOMMENDATION_STYLES.get(rec, RECOMMENDATION_STYLES["insufficient_data"])
    return f'<div class="recommendation-box" style="{style}">{text}</div>'


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


def chat_loading(message: str, history: list, state: dict | None, progress_data: dict | None,
                 imaging_report: str = ""):
    """Phase 1: Show user message + loading indicator immediately."""
    if not message or not message.strip():
        return history, state, progress_data, message
    history = history + [{"role": "user", "content": message}]
    loading_text = "Analyzing your condition..."
    if imaging_report and imaging_report.strip():
        loading_text = "Parsing imaging report & analyzing your condition..."
    elif state and state.get("collected", {}).get("condition"):
        loading_text = "Generating your treatment plan..."
    history = history + [{"role": "assistant", "content": loading_text}]
    return history, state, progress_data, message


def chat(message: str, history: list, state: dict | None, progress_data: dict | None,
         imaging_report: str = ""):
    """Phase 2: Process with agent and replace loading message.

    Args:
        imaging_report: OPTIONAL radiology report text. If empty/whitespace,
                        no imaging processing occurs (zero overhead).
    """
    if not message or not message.strip():
        return history, state, "", "", "", "", "", progress_data, serialize_progress(progress_data or {})

    if state is None:
        state = {"collected": {}, "reasoning_chain": [], "prescription_generated": False}
    if progress_data is None:
        progress_data = create_empty_progress()

    # Remove the loading placeholder before processing
    if history and history[-1].get("content") in (
        "Analyzing your condition...",
        "Parsing imaging report & analyzing your condition...",
        "Generating your treatment plan...",
    ):
        history = history[:-1]

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

        return (history, state, progress, profile_md, exercises_html, explanation,
                full_reasoning, progress_data, serialize_progress(progress_data))
    else:
        bot_msg = result.get("text", str(result)) if isinstance(result, dict) else str(result)
        tool_names = [TOOL_LABELS.get(s["action"], s["action"]) for s in reasoning_chain if "action" in s]
        if tool_names:
            badge_str = " ".join(f"`{t}`" for t in tool_names)
            bot_msg = f"[{badge_str}]\n\n{bot_msg}"

        history = history + [{"role": "assistant", "content": bot_msg}]
        progress = _progress_html(state.get("collected", {}))
        full_reasoning = _format_reasoning_chain(state.get("all_reasoning", []))

        return (history, state, progress, "", "", "", full_reasoning,
                progress_data, serialize_progress(progress_data))


def reset():
    empty = create_empty_progress()
    return (
        None,                       # consultation_state
        _progress_html({}),         # progress_display
        "",                         # profile_display
        "",                         # exercises_display
        "",                         # reasoning_display
        "",                         # agent_chain_display
        empty,                      # progress_state
        serialize_progress(empty),  # progress_store
        "",                         # log_status
        gr.update(choices=[]),      # exercises_completed
        gr.update(visible=True),    # step1_group
        gr.update(visible=False),   # step2_group
        gr.update(visible=False),   # step3_group
        "",                         # complaint_box
        5,                          # pain_intake_slider
        None,                       # duration_radio
        [],                         # worse_when_cb
        None,                       # age_radio
        None,                       # occupation_radio
        [],                         # comorbidities_cb
        gr.update(value=None),      # cond_q1
        gr.update(value=None),      # cond_q2
        "",                         # imaging_report_box
    )


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


# ── Condition Detection ─────────────────────────────────────────────────────

CONDITION_KEYWORDS = {
    "lower_back_pain":    ["lower back", "lumbar", "back pain", "lumbago", "backache", "back ache"],
    "knee_oa":            ["knee pain", "knee arthritis", "knee oa", "knee replacement", " knee "],
    "neck_pain":          ["neck pain", "cervical", "stiff neck", "whiplash", "neck ache", "neck"],
    "frozen_shoulder":    ["frozen shoulder", "adhesive capsulitis", "shoulder stiff",
                           "can't raise arm", "cannot raise arm", "shoulder pain", "shoulder"],
    "sciatica":           ["sciatica", "sciatic", "shooting down leg", "radiating leg",
                           "pain down leg", "nerve pain leg", "down my leg"],
    "hip_oa":             ["hip pain", "hip arthritis", "hip oa", "groin pain", "hip replacement"],
    "plantar_fasciitis":  ["heel pain", "plantar fasciitis", "plantar", "heel", "foot pain",
                           "sole pain", "arch pain"],
    "tennis_elbow":       ["tennis elbow", "lateral epicondyl", "outer elbow",
                           "elbow pain", "elbow", "forearm pain"],
}

CONDITION_NAMES = {
    "lower_back_pain":   "Lower Back Pain",
    "knee_oa":           "Knee Osteoarthritis",
    "neck_pain":         "Neck Pain / Cervicalgia",
    "frozen_shoulder":   "Frozen Shoulder",
    "sciatica":          "Sciatica / Lumbar Radiculopathy",
    "hip_oa":            "Hip Osteoarthritis",
    "plantar_fasciitis": "Plantar Fasciitis",
    "tennis_elbow":      "Tennis Elbow (Lateral Epicondylitis)",
    "unknown":           "Musculoskeletal Pain",
}

CONDITION_COLORS = {
    "lower_back_pain":   ("#1e40af", "#eff6ff", "#bfdbfe"),
    "knee_oa":           ("#059669", "#ecfdf5", "#a7f3d0"),
    "neck_pain":         ("#7c3aed", "#f5f3ff", "#ddd6fe"),
    "frozen_shoulder":   ("#0891b2", "#ecfeff", "#a5f3fc"),
    "sciatica":          ("#dc2626", "#fef2f2", "#fecaca"),
    "hip_oa":            ("#d97706", "#fffbeb", "#fde68a"),
    "plantar_fasciitis": ("#0284c7", "#f0f9ff", "#bae6fd"),
    "tennis_elbow":      ("#65a30d", "#f7fee7", "#d9f99d"),
    "unknown":           ("#64748b", "#f8fafc", "#e2e8f0"),
}

CONDITION_SPECIFIC_Q = {
    "lower_back_pain": {
        "q1_label": "Does the pain radiate down to your leg(s)?",
        "q1_choices": ["Yes — below the knee", "Yes — above knee only", "No radiation", "Sometimes"],
        "q2_label": "Which position makes it worst?",
        "q2_choices": ["Sitting (prolonged)", "Bending forward", "Standing / Walking", "All positions"],
    },
    "knee_oa": {
        "q1_label": "Difficulty on stairs?",
        "q1_choices": ["Yes — significant", "Yes — mild", "Avoid stairs", "No difficulty"],
        "q2_label": "Knee swelling present?",
        "q2_choices": ["Yes — constant", "Yes — after activity", "Occasional", "No swelling"],
    },
    "neck_pain": {
        "q1_label": "Does the pain radiate to your arm or hand?",
        "q1_choices": ["Yes — with numbness / tingling", "Yes — pain only", "No radiation", "Sometimes"],
        "q2_label": "Daily screen / desk hours?",
        "q2_choices": ["< 4 hours", "4–8 hours", "> 8 hours", "Varies"],
    },
    "frozen_shoulder": {
        "q1_label": "Which shoulder is affected?",
        "q1_choices": ["Right shoulder", "Left shoulder", "Both shoulders"],
        "q2_label": "Which stage feels most accurate?",
        "q2_choices": ["Getting progressively stiffer", "Very stiff, pain reducing", "Slowly improving (thawing)"],
    },
    "sciatica": {
        "q1_label": "Which leg is affected?",
        "q1_choices": ["Right leg", "Left leg", "Both legs", "Alternating"],
        "q2_label": "Numbness or tingling in leg / foot?",
        "q2_choices": ["Yes — constant", "Yes — intermittent", "No — pain only", "Weakness present"],
    },
    "hip_oa": {
        "q1_label": "Do you have groin or inner thigh pain?",
        "q1_choices": ["Yes — significant", "Yes — mild", "Only outer hip pain", "No groin pain"],
        "q2_label": "Do you limp or use a walking aid?",
        "q2_choices": ["Yes — noticeable limp", "Slight limp when tired", "Use walking stick", "No limp"],
    },
    "plantar_fasciitis": {
        "q1_label": "First few morning steps — pain level?",
        "q1_choices": ["Very painful (worst of day)", "Mild–moderate", "Worse end of day instead", "Same all day"],
        "q2_label": "Your foot arch type?",
        "q2_choices": ["Flat / Low arch", "Normal arch", "High arch", "Not sure"],
    },
    "tennis_elbow": {
        "q1_label": "Is your dominant (writing) hand affected?",
        "q1_choices": ["Yes — dominant hand", "No — non-dominant hand", "Both hands"],
        "q2_label": "Grip weakness or dropping objects?",
        "q2_choices": ["Yes — significant weakness", "Mild weakness", "Dropping objects", "Pain only, no weakness"],
    },
}

DURATION_TENDENCY = {
    "< 6 weeks  (Acute)":              "acute",
    "6 weeks – 3 months  (Sub-acute)": "sub-acute",
    "> 3 months  (Chronic)":           "chronic",
}

OCCUPATION_MAP = {
    "Desk job / Sedentary":   ("desk worker",        "sedentary"),
    "Light physical":         ("light physical worker", "light"),
    "Manual labour":          ("manual labourer",    "heavy"),
    "Student":                ("student",             "sedentary"),
    "Retired / Homemaker":    ("retired/homemaker",  "light"),
}


def detect_condition(complaint: str) -> str:
    if not complaint:
        return "unknown"
    text = complaint.lower()
    for cond_key, keywords in CONDITION_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return cond_key
    return "unknown"


def pain_severity_html(pain_value) -> str:
    v = int(float(pain_value or 0))
    if v <= 3:
        color, label, bg, emoji = "#10B981", "Mild", "#ecfdf5", "🟢"
    elif v <= 7:
        color, label, bg, emoji = "#f59e0b", "Moderate", "#fffbeb", "🟡"
    else:
        color, label, bg, emoji = "#ef4444", "Severe", "#fef2f2", "🔴"
    return (
        f'<div style="background:{bg}; border:1px solid {color}55; border-radius:10px; '
        f'padding:10px 18px; text-align:center; margin:6px 0;">'
        f'<span style="color:{color} !important; font-weight:800; font-size:18px;">'
        f'{emoji}&nbsp; {label} &nbsp;·&nbsp; {v}/10</span>'
        f'<span style="color:#64748b !important; font-size:12px; margin-left:14px;">'
        f'Scale: 0–3 Mild &nbsp;·&nbsp; 4–7 Moderate &nbsp;·&nbsp; 8–10 Severe</span></div>'
    )


def build_condition_badge(condition_key: str) -> str:
    name = CONDITION_NAMES.get(condition_key, "Unknown")
    color, bg, border = CONDITION_COLORS.get(condition_key, ("#64748b", "#f8fafc", "#e2e8f0"))
    recognized = condition_key != "unknown"
    tag = (f'<span style="padding:4px 12px; border-radius:20px; font-size:11px; font-weight:700; '
           f'background:{color}18; color:{color} !important; border:1px solid {color}44;">'
           f'{"✓ Recognized" if recognized else "⚠ Not recognised — select condition below"}</span>')
    return (
        f'<div style="background:{bg}; border:1px solid {border}; border-radius:14px; '
        f'padding:14px 18px; margin:0 0 8px 0;">'
        f'<div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;">'
        f'<span style="font-size:22px;">🔍</span>'
        f'<div><p style="margin:0; font-size:11px; font-weight:600; color:#64748b !important; '
        f'text-transform:uppercase; letter-spacing:0.08em;">Detected Condition</p>'
        f'<p style="margin:0; font-size:18px; font-weight:800; color:{color} !important;">{name}</p></div>'
        f'{tag}</div></div>'
    )


# ── Intake Form Handlers ─────────────────────────────────────────────────────

def detect_and_show_form(complaint: str):
    """Step 1 → Step 2: detect condition, show assessment form."""
    if not complaint or not complaint.strip():
        return (gr.update(), gr.update(), gr.update(), "", gr.update(), gr.update(), gr.update())

    cond = detect_condition(complaint)
    badge = build_condition_badge(cond)
    cond_qs = CONDITION_SPECIFIC_Q.get(cond)
    if cond_qs:
        q1 = gr.update(choices=cond_qs["q1_choices"], label=cond_qs["q1_label"], visible=True, value=None)
        q2 = gr.update(choices=cond_qs["q2_choices"], label=cond_qs["q2_label"], visible=True, value=None)
        cg = gr.update(visible=True)
    else:
        q1 = gr.update(visible=False, value=None)
        q2 = gr.update(visible=False, value=None)
        cg = gr.update(visible=False)
    return (
        gr.update(visible=False),  # step1
        gr.update(visible=True),   # step2
        gr.update(visible=False),  # step3
        badge,                     # condition_badge_html
        cg,                        # cond_specific_group
        q1,                        # cond_q1
        q2,                        # cond_q2
    )


def process_intake_form(
    complaint: str,
    pain_value,
    duration: str,
    worse_when: list,
    age_group: str,
    occupation: str,
    comorbidities_val: list,
    cond_q1_val: str,
    cond_q2_val: str,
    imaging_report: str,
    state: dict | None,
    progress_data: dict | None,
):
    """Step 2 → Step 3: build state from form, call engine, return prescription."""
    if not complaint or not complaint.strip():
        return (gr.update(),) * 3 + ("", "", "", "", "", state, progress_data, serialize_progress({}))

    if state is None:
        state = {"collected": {}, "reasoning_chain": [], "prescription_generated": False}
    if progress_data is None:
        progress_data = create_empty_progress()

    pain_int = int(float(pain_value or 5))
    pain_label = "mild" if pain_int <= 3 else ("moderate" if pain_int <= 7 else "severe")

    tendency = DURATION_TENDENCY.get(duration or "", "unknown")
    age_mid  = {"18–30": "25", "31–45": "38", "46–60": "52", "60+": "65"}.get(age_group or "", "45")
    occ_label, phys_dem = OCCUPATION_MAP.get(occupation or "", ("unknown", "unknown"))
    comorbids = [c for c in (comorbidities_val or []) if c != "None"]
    aggrav    = list(worse_when or [])
    cond_key  = detect_condition(complaint)

    state["collected"] = {
        "condition":         cond_key if cond_key != "unknown" else None,
        "pain_vas":          pain_int,
        "intensity_vas":     pain_int,
        "tendency":          tendency,
        "characteristic":    "constant" if "At rest" in aggrav else "intermittent",
        "aggravating_factors": aggrav,
        "reducing_factors":  [],
        "age":               age_mid,
        "occupation":        occ_label,
        "physical_demands":  phys_dem,
        "comorbidities":     comorbids,
        "comorbidity_count": len(comorbids),
    }

    # Condition-specific context
    cond_ctx = ""
    qs = CONDITION_SPECIFIC_Q.get(cond_key, {})
    if qs and cond_q1_val:
        cond_ctx += f"\n- {qs.get('q1_label','')}: {cond_q1_val}"
    if qs and cond_q2_val:
        cond_ctx += f"\n- {qs.get('q2_label','')}: {cond_q2_val}"

    # Imaging
    if imaging_report and imaging_report.strip():
        try:
            parsed = parse_imaging_report(imaging_report)
            if parsed.get("findings") or parsed.get("red_flags"):
                state["collected"]["imaging"] = parsed
                if not state["collected"].get("condition") and parsed.get("condition_hints"):
                    state["collected"]["condition"] = parsed["condition_hints"][0]
                state.setdefault("all_reasoning", [])
                state["all_reasoning"] += [
                    {"action": "parse_imaging_report", "args": {"report_length": len(imaging_report)}},
                    {"observation": "parse_imaging_report", "result": parsed.get("summary", "Parsed")},
                ]
        except Exception as e:
            print(f"[imaging] {e}")

    # Build rich intake message
    cond_name   = CONDITION_NAMES.get(cond_key, "Unknown")
    worse_str   = ", ".join(aggrav) if aggrav else "Not specified"
    comorbid_str = ", ".join(comorbids) if comorbids else "None"
    message = (
        f"Patient intake:\n"
        f"Condition: {cond_name}\n"
        f"Pain: {pain_int}/10 ({pain_label})\n"
        f"Duration: {duration or 'not stated'} — tendency: {tendency}\n"
        f"Worse when: {worse_str}\n"
        f"Age: {age_group or 'not stated'}\n"
        f"Occupation: {occ_label} ({phys_dem} demands)\n"
        f"Medical history: {comorbid_str}"
        f"{cond_ctx}\n\n"
        f"Generate the complete personalized exercise prescription."
    )

    result, state = process_message(message, [{"role": "user", "content": message}], state)

    rc    = result.get("reasoning_chain", []) if isinstance(result, dict) else []
    state.setdefault("all_reasoning", [])
    state["all_reasoning"].extend(rc)

    if isinstance(result, dict) and "plan" in result:
        pt_info   = result.get("patient_info", {})
        ex_html   = _format_prescription_html(result)
        prof_md   = _format_patient_profile(pt_info)
        state["collected"].update(pt_info)
        plan      = result["plan"]
        state["last_prescription"] = {
            "exercise_names": [e["name"] for e in plan.get("exercises", [])],
            "level":          plan.get("level", 0),
            "condition":      plan.get("condition", ""),
        }
        progress_data["condition"]      = pt_info.get("condition", "")
        progress_data["exercise_level"] = plan.get("level", 0)
        prog_html  = _progress_html(state.get("collected", {}))
        full_chain = _format_reasoning_chain(state.get("all_reasoning", []))
        return (
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=True),
            prog_html, prof_md, ex_html,
            result.get("explanation", ""),
            full_chain,
            state, progress_data, serialize_progress(progress_data),
        )

    bot_msg    = result.get("text", str(result)) if isinstance(result, dict) else str(result)
    full_chain = _format_reasoning_chain(state.get("all_reasoning", []))
    return (
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=True),
        _progress_html(state.get("collected", {})),
        f"**Assessment note:**\n\n{bot_msg}",
        "", "", full_chain,
        state, progress_data, serialize_progress(progress_data),
    )


# ── Build Gradio app ────────────────────────────────────────────────────────

def build_app():
    with gr.Blocks(theme=THEME, css=CSS, title="PhysioGemma — AI Physiotherapy Agent") as app:

        # ── Hero Section ──
        gr.HTML("""
        <div style="text-align:center; padding:40px 28px 34px 28px;
                    background:linear-gradient(135deg, #0d2818 0%, #1a3c2a 45%, #1e5c3a 100%);
                    border-radius:20px; margin-bottom:20px;
                    box-shadow:0 8px 36px rgba(13,40,24,0.45);
                    position:relative; overflow:hidden;">

            <!-- Subtle background pattern -->
            <div style="position:absolute; top:0; left:0; right:0; bottom:0;
                        background:radial-gradient(circle at 15% 85%, rgba(52,211,153,0.12) 0%, transparent 52%),
                                   radial-gradient(circle at 85% 15%, rgba(16,185,129,0.10) 0%, transparent 52%),
                                   radial-gradient(circle at 50% 50%, rgba(134,239,172,0.04) 0%, transparent 70%);
                        pointer-events:none;"></div>

            <div style="position:relative; z-index:1;">
                <p style="font-size:11px; font-weight:700; letter-spacing:0.16em; text-transform:uppercase;
                          color:#86efac !important; margin:0 0 12px 0;">
                    AI-Powered Recovery Tracking
                </p>
                <h1 style="font-size:2.8em; margin:0; color:#ffffff !important;
                            font-weight:800; letter-spacing:-0.03em;">
                    &#129658; PhysioGemma
                </h1>
                <p style="font-size:1.1em; color:#a7f3d0 !important; margin:8px 0 20px 0; font-weight:400;">
                    AI Physiotherapy <strong style="color:#ffffff !important;">Agent</strong>
                    powered by <strong style="color:#4ade80 !important;">Gemma 4</strong>
                </p>

                <div style="margin:14px 0;">
                    <span class="hero-badge badge-agent">&#9889; ReAct Agent</span>
                    <span class="hero-badge badge-rag">&#128218; RAG-Enhanced</span>
                    <span class="hero-badge badge-clinical">&#127973; Clinical Decision Support</span>
                </div>

                <div style="margin:16px 0 8px 0;">
                    <span class="trust-item">&#9989; Evidence-Based</span>
                    <span class="trust-item">&#128737; Safe Recommendations</span>
                    <span class="trust-item">&#128200; Progress Tracking</span>
                    <span class="trust-item">&#127909; 183 Exercise Videos</span>
                </div>

                <p style="font-size:11px; color:#6ee7b7 !important; margin:16px 0 0 0; font-style:italic;">
                    Built with clinical reasoning + AI &bull; Not medical advice
                </p>
            </div>
        </div>
        """)

        # Hidden progress store for localStorage bridge
        progress_store = gr.Textbox(visible=False, elem_id="progress_store")
        progress_state = gr.State(None)
        consultation_state = gr.State(None)

        # ── TABS ────────────────────────────────────────────────────────
        with gr.Tabs() as tabs:

            # ════════════════════════════════════════════════════════════
            # TAB 1: CONSULTATION  (3-step intake flow)
            # ════════════════════════════════════════════════════════════
            with gr.TabItem("Consultation", id="consult"):

                # ── STEP 1 : Complaint ───────────────────────────────────
                with gr.Group(visible=True) as step1_group:
                    gr.HTML("""
                    <div style="text-align:center; padding:18px 8px 6px 8px;">
                        <p style="font-size:13px; font-weight:700; letter-spacing:0.12em;
                                  text-transform:uppercase; color:#1a3c2a !important; margin:0 0 6px 0;">
                            Step 1 of 2
                        </p>
                        <h2 style="font-size:1.5em; font-weight:800; color:#0f172a !important; margin:0 0 4px 0;">
                            What's bothering you today?
                        </h2>
                        <p style="font-size:14px; color:#64748b !important; margin:0;">
                            Describe your pain or condition in your own words
                        </p>
                    </div>""")

                    complaint_box = gr.Textbox(
                        label="",
                        placeholder=(
                            "Examples:\n"
                            "• My lower back has been aching for 3 months, worse when sitting...\n"
                            "• Knee pain when climbing stairs, 62 years old...\n"
                            "• Pain shooting down my left leg from lower back...\n"
                            "• Heel hurts every morning, stand all day at work..."
                        ),
                        lines=5,
                        show_label=False,
                    )

                    gr.Examples(
                        examples=[
                            ["My lower back has been hurting for 3 months. Pain is about 6 out of 10. I'm 45, desk job."],
                            ["I'm 62, knee pain for 6 months, worse going down stairs, some swelling."],
                            ["Shoulder is frozen, can't raise my arm above 90°. 55 years old, started 4 months ago."],
                            ["Pain shooting down my left leg from lower back, 7/10, age 38, IT job."],
                            ["My heel hurts every morning, been 2 months, I stand all day at work."],
                            ["Elbow pain on outer side, worse when gripping, I work in IT."],
                        ],
                        inputs=[complaint_box],
                        label="Quick examples — click to fill:",
                    )

                    with gr.Row():
                        detect_btn = gr.Button("Start Assessment  →", variant="primary", size="lg", scale=3)
                        gr.HTML('<div style="padding:6px 0; font-size:12px; color:#94a3b8 !important; '
                                'align-self:center;">Takes ~10 seconds</div>')

                # ── STEP 2 : Assessment Form ─────────────────────────────
                with gr.Group(visible=False) as step2_group:

                    condition_badge_html = gr.HTML("")

                    # ── Pain intensity ──
                    gr.HTML("""<div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:12px;
                                           padding:14px 18px; margin:4px 0 2px 0;">
                        <p style="margin:0 0 8px 0; font-size:13px; font-weight:700; color:#0f172a !important;">
                            ① Pain Intensity
                        </p>""")
                    pain_intake_slider = gr.Slider(
                        minimum=0, maximum=10, step=1, value=5,
                        label="Move slider to your current pain level (0 = none, 10 = worst imaginable)",
                    )
                    pain_severity_display = gr.HTML(value=pain_severity_html(5))
                    gr.HTML("</div>")

                    # ── Duration + Age ──
                    gr.HTML("""<div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:12px;
                                           padding:14px 18px; margin:8px 0 2px 0;">
                        <p style="margin:0 0 10px 0; font-size:13px; font-weight:700; color:#0f172a !important;">
                            ② Duration &amp; Age
                        </p>""")
                    with gr.Row():
                        duration_radio = gr.Radio(
                            choices=["< 6 weeks  (Acute)",
                                     "6 weeks – 3 months  (Sub-acute)",
                                     "> 3 months  (Chronic)"],
                            label="How long have you had this pain?",
                            value=None,
                        )
                        age_radio = gr.Radio(
                            choices=["18–30", "31–45", "46–60", "60+"],
                            label="Your age group",
                            value=None,
                        )
                    gr.HTML("</div>")

                    # ── Worse when ──
                    gr.HTML("""<div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:12px;
                                           padding:14px 18px; margin:8px 0 2px 0;">
                        <p style="margin:0 0 10px 0; font-size:13px; font-weight:700; color:#0f172a !important;">
                            ③ Pain is worse when... <span style="font-weight:400; color:#64748b !important;">(tick all that apply)</span>
                        </p>""")
                    worse_when_cb = gr.CheckboxGroup(
                        choices=["Sitting", "Standing", "Walking / Activity",
                                 "Morning stiffness", "Night pain", "Bending / Twisting", "At rest"],
                        label="",
                        value=[],
                        show_label=False,
                    )
                    gr.HTML("</div>")

                    # ── Occupation + Medical history ──
                    gr.HTML("""<div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:12px;
                                           padding:14px 18px; margin:8px 0 2px 0;">
                        <p style="margin:0 0 10px 0; font-size:13px; font-weight:700; color:#0f172a !important;">
                            ④ Occupation &amp; Medical History
                        </p>""")
                    with gr.Row():
                        occupation_radio = gr.Radio(
                            choices=["Desk job / Sedentary", "Light physical",
                                     "Manual labour", "Student", "Retired / Homemaker"],
                            label="Occupation type",
                            value=None,
                        )
                        comorbidities_cb = gr.CheckboxGroup(
                            choices=["Diabetes", "Hypertension", "Osteoporosis",
                                     "Previous surgery", "Obesity", "None"],
                            label="Medical history (tick all that apply)",
                            value=[],
                        )
                    gr.HTML("</div>")

                    # ── Condition-specific questions ──
                    with gr.Group(visible=False) as cond_specific_group:
                        gr.HTML("""<div style="background:#fffbeb; border:1px solid #fde68a; border-radius:12px;
                                               padding:14px 18px; margin:8px 0 2px 0;">
                            <p style="margin:0 0 10px 0; font-size:13px; font-weight:700; color:#92400e !important;">
                                ⑤ Condition-Specific Questions
                            </p>""")
                        with gr.Row():
                            cond_q1 = gr.Radio(choices=[], label="", visible=False)
                            cond_q2 = gr.Radio(choices=[], label="", visible=False)
                        gr.HTML("</div>")

                    # ── Optional imaging ──
                    gr.HTML("""<div style="background:#eff6ff; border:1px solid #bfdbfe; border-radius:12px;
                                           padding:14px 18px; margin:8px 0 2px 0;">
                        <p style="margin:0 0 4px 0; font-size:13px; font-weight:700; color:#1e40af !important;">
                            🩻 MRI / X-ray Report
                            <span style="font-weight:400; color:#64748b !important;">&nbsp;(optional)</span>
                        </p>
                        <p style="margin:0 0 8px 0; font-size:12px; color:#475569 !important;">
                            Paste your radiology report text. PhysioGemma will tailor recommendations to your findings.
                        </p>""")
                    imaging_report_box = gr.Textbox(
                        label="",
                        placeholder="Example: MRI Lumbar Spine — L4-L5 disc protrusion with mild lateral recess stenosis...",
                        lines=3,
                        show_label=False,
                    )
                    gr.HTML("</div>")

                    gr.HTML("<div style='height:8px;'></div>")
                    with gr.Row():
                        intake_back_btn  = gr.Button("← Edit Complaint",   variant="secondary", size="sm", scale=1)
                        intake_submit_btn = gr.Button("Get My Plan  →",    variant="primary",   size="lg", scale=3)

                # ── STEP 3 : Output ──────────────────────────────────────
                with gr.Group(visible=False) as step3_group:

                    progress_display = gr.HTML(value=_progress_html({}))

                    with gr.Row():
                        with gr.Column(scale=1):
                            profile_display = gr.Markdown(label="Clinical Assessment Summary")
                        with gr.Column(scale=1):
                            reasoning_display = gr.Markdown(label="Clinical Notes")

                    exercises_display = gr.HTML(label="Exercise Prescription")

                    with gr.Accordion("Agent Reasoning Chain", open=False):
                        agent_chain_display = gr.HTML(label="Reasoning Chain")

                    gr.HTML("<div style='height:8px;'></div>")
                    with gr.Row():
                        reset_btn = gr.Button("New Assessment", variant="primary", size="lg", scale=1)

            # ════════════════════════════════════════════════════════════
            # TAB 2: MY PROGRESS
            # ════════════════════════════════════════════════════════════
            with gr.TabItem("My Progress", id="progress"):

                gr.HTML("""
                <div style="margin-bottom:8px;">
                    <h3 style="color:#0f172a !important; font-size:20px; font-weight:800; margin:0 0 4px 0;">
                        Track Your Recovery</h3>
                    <p style="color:#64748b !important; font-size:14px; margin:0;">
                        Monitor pain levels, adherence, and recovery progress over time</p>
                </div>
                """)
                stats_display = gr.HTML(value=_stats_html({}))
                milestones_display = gr.HTML(value="")

                gr.HTML("<hr class='section-divider'>")
                gr.HTML("""
                <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:16px;
                            padding:24px; box-shadow:0 1px 3px rgba(0,0,0,0.04);">
                    <h3 style="color:#0f172a !important; font-size:18px; font-weight:700; margin:0 0 16px 0;">
                        &#128221; Log Today's Session</h3>
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

                gr.HTML("</div>")  # close session log card

                gr.HTML("<hr class='section-divider'>")
                gr.HTML("""
                <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:16px;
                            padding:24px; box-shadow:0 1px 3px rgba(0,0,0,0.04);">
                    <h3 style="color:#0f172a !important; font-size:18px; font-weight:700; margin:0 0 4px 0;">
                        &#128200; Recovery Trend</h3>
                    <p style="color:#64748b !important; font-size:13px; margin:0 0 16px 0;">
                        Pain and adherence over time</p>
                """)
                recovery_plot = gr.Plot(label="Recovery Progress")
                gr.HTML("</div>")

                gr.HTML("<hr class='section-divider'>")
                gr.HTML("""
                <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:16px;
                            padding:24px; box-shadow:0 1px 3px rgba(0,0,0,0.04);">
                    <h3 style="color:#0f172a !important; font-size:18px; font-weight:700; margin:0 0 16px 0;">
                        &#128203; Session History</h3>
                """)
                session_history = gr.Dataframe(
                    headers=["Date", "Pain", "Adherence", "Difficulty", "Level", "Notes"],
                    label="Past Sessions",
                    interactive=False,
                )
                gr.HTML("</div>")

            # ════════════════════════════════════════════════════════════
            # TAB 3: AI INSIGHTS
            # ════════════════════════════════════════════════════════════
            with gr.TabItem("AI Insights", id="insights"):

                gr.HTML("""
                <div style="margin-bottom:16px;">
                    <h3 style="color:#0f172a !important; font-size:20px; font-weight:800; margin:0 0 4px 0;">
                        Recovery Insights powered by Gemma 4</h3>
                    <p style="color:#64748b !important; font-size:14px; margin:0;">
                        Combines rule-based analysis with AI-generated narrative</p>
                </div>
                """)

                refresh_insights_btn = gr.Button("Generate Recovery Insights", variant="primary", size="lg")

                recommendation_display = gr.HTML("")
                insights_display = gr.HTML("")

                gr.HTML("<hr class='section-divider'>")
                gr.HTML("""
                <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:16px;
                            padding:24px; box-shadow:0 1px 3px rgba(0,0,0,0.04);">
                    <h3 style="color:#0f172a !important; font-size:18px; font-weight:700; margin:0 0 16px 0;">
                        &#129302; AI Recovery Report</h3>
                """)
                ai_narrative_display = gr.Markdown("")
                gr.HTML("</div>")

        # Footer
        gr.HTML("""
        <div style="text-align:center; padding:28px 24px;
                    background:linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
                    border-radius:16px; margin-top:24px;
                    border:1px solid #e2e8f0;
                    box-shadow:0 1px 3px rgba(0,0,0,0.03);">
            <p style="color:#1e293b !important; font-size:14px; font-weight:700; margin:0 0 6px 0;">
                PhysioGemma Agent
            </p>
            <p style="color:#64748b !important; font-size:12px; margin:4px 0;">
                Kaggle Gemma 4 Good Hackathon &bull; Health &amp; Sciences Track
            </p>
            <div style="margin:10px 0 6px 0; display:flex; gap:8px; justify-content:center; flex-wrap:wrap;">
                <span style="padding:4px 12px; border-radius:20px; font-size:11px; font-weight:600;
                             background:#eff6ff; color:#2563EB !important; border:1px solid #bfdbfe;">
                    ReAct Agent</span>
                <span style="padding:4px 12px; border-radius:20px; font-size:11px; font-weight:600;
                             background:#ecfdf5; color:#059669 !important; border:1px solid #a7f3d0;">
                    RAG-Enhanced</span>
                <span style="padding:4px 12px; border-radius:20px; font-size:11px; font-weight:600;
                             background:#f5f3ff; color:#7c3aed !important; border:1px solid #ddd6fe;">
                    183 Exercises</span>
                <span style="padding:4px 12px; border-radius:20px; font-size:11px; font-weight:600;
                             background:#fef2f2; color:#dc2626 !important; border:1px solid #fecaca;">
                    Not Medical Advice</span>
            </div>
            <p style="color:#94a3b8 !important; font-size:11px; margin:8px 0 0 0;">
                Created by Gaurav Birwatkar &bull; CC-BY 4.0 License
            </p>
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

        # Step 1 → 2: detect condition & show form
        detect_outputs = [
            step1_group, step2_group, step3_group,
            condition_badge_html, cond_specific_group,
            cond_q1, cond_q2,
        ]
        detect_btn.click(
            fn=detect_and_show_form,
            inputs=[complaint_box],
            outputs=detect_outputs,
        )
        complaint_box.submit(
            fn=detect_and_show_form,
            inputs=[complaint_box],
            outputs=detect_outputs,
        )

        # Step 2 → 1: back button
        intake_back_btn.click(
            fn=lambda: (gr.update(visible=True), gr.update(visible=False), gr.update(visible=False)),
            outputs=[step1_group, step2_group, step3_group],
        )

        # Pain slider live label
        pain_intake_slider.change(
            fn=pain_severity_html,
            inputs=[pain_intake_slider],
            outputs=[pain_severity_display],
        )

        # Step 2 → 3: submit intake form
        intake_inputs = [
            complaint_box, pain_intake_slider,
            duration_radio, worse_when_cb,
            age_radio, occupation_radio, comorbidities_cb,
            cond_q1, cond_q2,
            imaging_report_box,
            consultation_state, progress_state,
        ]
        intake_outputs = [
            step1_group, step2_group, step3_group,
            progress_display, profile_display,
            exercises_display, reasoning_display, agent_chain_display,
            consultation_state, progress_state, progress_store,
        ]
        intake_submit_btn.click(
            fn=process_intake_form,
            inputs=intake_inputs,
            outputs=intake_outputs,
        ).then(fn=None, js=JS_SAVE_PROGRESS, inputs=[progress_store])

        # Reset — go back to Step 1
        reset_outputs = [
            consultation_state, progress_display, profile_display,
            exercises_display, reasoning_display, agent_chain_display,
            progress_state, progress_store, log_status, exercises_completed,
            step1_group, step2_group, step3_group,
            complaint_box, pain_intake_slider,
            duration_radio, worse_when_cb,
            age_radio, occupation_radio, comorbidities_cb,
            cond_q1, cond_q2,
            imaging_report_box,
        ]
        reset_btn.click(fn=reset, outputs=reset_outputs)

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
    )
