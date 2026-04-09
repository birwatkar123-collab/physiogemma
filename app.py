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
/* ── Global — Gemma brand palette ─────────────────────────────────────── */
/* Primary: #4285F4 (Gemma Blue)  Accent: #8ab4f8 (Light Gemma)
   Deep: #1a237e (Navy)  Surface: #e8eaf6 (Indigo tint)
   Success: #34a853  Warning: #fbbc04  Error: #ea4335              */
.gradio-container { max-width: 1100px !important; }
* { transition: box-shadow 0.2s ease, transform 0.2s ease; }

/* ── Force readable text everywhere ───────────────────────────────────── */
.gradio-container, .gradio-container *, .prose *, .markdown-text *,
.chatbot *, .message *, span, p, li, td, th, label, h1, h2, h3, h4, h5, h6 {
    color: #1e293b;
}
.dark .gradio-container * { color: #1e293b; }
.chatbot .message-wrap .bot, .chatbot .message-wrap .bot *,
.chatbot .message-wrap .bot p, .chatbot .message-wrap .bot span,
.chatbot .message-wrap .bot li, .chatbot .message-wrap .bot strong {
    color: #1e293b !important;
}
.chatbot .message-wrap .user, .chatbot .message-wrap .user *,
.chatbot .message-wrap .user p, .chatbot .message-wrap .user span {
    color: #ffffff !important;
}

/* ── Chat bubbles ──────────────────────────────────────────────────────── */
.message-wrap .message {
    border-radius: 16px !important;
    padding: 14px 18px !important;
    font-size: 15px !important;
    line-height: 1.65 !important;
    max-width: 88% !important;
}
.message-wrap .bot {
    background: #ffffff !important;
    border: 1px solid #c5cae9 !important;
    box-shadow: 0 2px 8px rgba(26,35,126,0.06) !important;
    border-radius: 16px 16px 16px 4px !important;
    color: #1e293b !important;
}
.message-wrap .bot * {
    color: #1e293b !important;
}
.message-wrap .bot code {
    color: #1a237e !important;
    background: #e8eaf6 !important;
}
.message-wrap .user {
    background: linear-gradient(135deg, #4285F4 0%, #1a73e8 100%) !important;
    color: #ffffff !important;
    border-radius: 16px 16px 4px 16px !important;
    box-shadow: 0 2px 10px rgba(66,133,244,0.3) !important;
}
.message-wrap .user * {
    color: #ffffff !important;
}

/* ── Buttons ───────────────────────────────────────────────────────────── */
button.primary {
    background: linear-gradient(135deg, #4285F4, #1a73e8) !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    letter-spacing: 0.02em !important;
    box-shadow: 0 2px 8px rgba(66,133,244,0.25) !important;
}
button.primary:hover {
    box-shadow: 0 4px 16px rgba(66,133,244,0.4) !important;
    transform: translateY(-1px);
}
button.secondary {
    border-radius: 12px !important;
    border-color: #c5cae9 !important;
}

/* ── Tabs ──────────────────────────────────────────────────────────────── */
.tabs > .tab-nav > button {
    font-size: 15px !important;
    font-weight: 600 !important;
    padding: 12px 22px !important;
    border-radius: 12px 12px 0 0 !important;
}
.tabs > .tab-nav > button.selected {
    background: linear-gradient(135deg, #e8eaf6 0%, #c5cae9 100%) !important;
    border-bottom: 3px solid #4285F4 !important;
    color: #1a237e !important;
}

/* ── Exercise cards ────────────────────────────────────────────────────── */
.exercise-card {
    background: linear-gradient(145deg, #f5f7ff 0%, #e8eaf6 50%, #f0f4ff 100%);
    border: 1px solid #c5cae9;
    border-radius: 16px;
    padding: 20px;
    margin: 12px 0;
    box-shadow: 0 2px 12px rgba(26,35,126,0.04);
}
.exercise-card:hover {
    box-shadow: 0 6px 24px rgba(66,133,244,0.12);
    transform: translateY(-2px);
    border-color: #8ab4f8;
}
.exercise-card h4 {
    color: #1a237e;
    margin: 0 0 10px 0;
    font-size: 17px;
    font-weight: 700;
}
.exercise-card p {
    color: #475569;
    margin: 5px 0;
    font-size: 14px;
    line-height: 1.6;
}
.exercise-card .ex-meta {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin: 8px 0 10px 0;
}
.exercise-card .ex-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.03em;
}
.ex-badge-sets { background: #e3f2fd; color: #1565c0; }
.ex-badge-reps { background: #e8f5e9; color: #2e7d32; }
.ex-badge-type { background: #ede7f6; color: #6a1b9a; }
.exercise-card a {
    display: block;
    margin-top: 12px;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 2px 10px rgba(0,0,0,0.08);
}
.exercise-card a:hover {
    box-shadow: 0 4px 20px rgba(66,133,244,0.2);
    transform: scale(1.01);
}

/* ── Reasoning chain ───────────────────────────────────────────────────── */
.reasoning-step {
    border-radius: 10px;
    padding: 12px 16px;
    margin: 8px 0;
    font-size: 13px;
    line-height: 1.6;
}
.reasoning-action {
    background: linear-gradient(135deg, #e8eaf6, #c5cae9);
    border-left: 4px solid #4285F4;
}
.reasoning-observation {
    background: linear-gradient(135deg, #e8f5e9, #c8e6c9);
    border-left: 4px solid #34a853;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
}
.reasoning-warning {
    background: linear-gradient(135deg, #fce4ec, #ffcdd2);
    border-left: 4px solid #ea4335;
}
.tool-badge {
    display: inline-block;
    background: linear-gradient(135deg, #e3f2fd, #bbdefb);
    border: 1px solid #8ab4f8;
    color: #1a237e;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    margin: 2px 4px;
    letter-spacing: 0.03em;
    text-transform: uppercase;
}

/* ── Progress pills ────────────────────────────────────────────────────── */
.progress-bar {
    display: flex;
    gap: 8px;
    justify-content: center;
    margin: 12px 0 24px 0;
    flex-wrap: wrap;
}
.progress-pill {
    padding: 6px 16px;
    border-radius: 24px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.02em;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.progress-done {
    background: linear-gradient(135deg, #4285F4, #1a73e8);
    color: white;
    box-shadow: 0 2px 8px rgba(66,133,244,0.3);
}
.progress-pending { background: #e8eaf6; color: #3949ab; border: 1px solid #c5cae9; }

/* ── Stat cards ────────────────────────────────────────────────────────── */
.stat-card {
    background: linear-gradient(145deg, #ffffff 0%, #f5f7ff 100%);
    border: 1px solid #c5cae9;
    border-radius: 16px;
    padding: 20px 16px;
    text-align: center;
    box-shadow: 0 2px 12px rgba(26,35,126,0.04);
}
.stat-card:hover {
    box-shadow: 0 6px 20px rgba(66,133,244,0.1);
    transform: translateY(-2px);
    border-color: #8ab4f8;
}
.stat-card .stat-icon { font-size: 28px; margin-bottom: 4px; }
.stat-card h3 { color: #1a237e; margin: 4px 0 2px 0; font-size: 30px; font-weight: 800; }
.stat-card p { color: #5c6bc0; margin: 0; font-size: 13px; font-weight: 500; }

/* ── Milestones ────────────────────────────────────────────────────────── */
.milestone-badge {
    display: inline-block;
    background: linear-gradient(135deg, #fff8e1, #ffecb3);
    border: 1px solid #fbbc04;
    border-radius: 24px;
    padding: 8px 16px;
    font-size: 13px;
    margin: 4px;
    color: #e65100;
    font-weight: 700;
    box-shadow: 0 2px 8px rgba(251,188,4,0.2);
}

/* ── Insight cards ─────────────────────────────────────────────────────── */
.insight-card {
    border-radius: 12px;
    padding: 14px 18px;
    margin: 10px 0;
    font-size: 14px;
    line-height: 1.6;
    box-shadow: 0 1px 6px rgba(0,0,0,0.04);
}
.insight-improvement { background: linear-gradient(135deg, #e8f5e9, #c8e6c9); border-left: 4px solid #34a853; }
.insight-concern { background: linear-gradient(135deg, #fce4ec, #ffcdd2); border-left: 4px solid #ea4335; }
.insight-suggestion { background: linear-gradient(135deg, #e3f2fd, #bbdefb); border-left: 4px solid #4285F4; }
.insight-achievement { background: linear-gradient(135deg, #fff8e1, #ffecb3); border-left: 4px solid #fbbc04; }
.insight-info { background: linear-gradient(135deg, #f5f7ff, #e8eaf6); border-left: 4px solid #7986cb; }
.insight-milestone { background: linear-gradient(135deg, #f3e5f5, #e1bee7); border-left: 4px solid #9c27b0; }
.insight-ready_to_progress { background: linear-gradient(135deg, #e8f5e9, #c8e6c9); border-left: 4px solid #2e7d32; }

/* ── Recommendation box ────────────────────────────────────────────────── */
.recommendation-box {
    border-radius: 16px;
    padding: 20px 24px;
    margin: 16px 0;
    font-size: 16px;
    font-weight: 700;
    text-align: center;
    box-shadow: 0 2px 12px rgba(26,35,126,0.06);
}

/* ── Hero trust badges ─────────────────────────────────────────────────── */
.hero-badge {
    display: inline-block;
    padding: 6px 16px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 700;
    margin: 3px;
    letter-spacing: 0.03em;
}
.badge-agent { background: rgba(138,180,248,0.2); color: #8ab4f8 !important; border: 1px solid rgba(138,180,248,0.4); }
.badge-rag { background: rgba(52,168,83,0.15); color: #81c995 !important; border: 1px solid rgba(52,168,83,0.3); }
.badge-clinical { background: rgba(251,188,4,0.15); color: #fdd663 !important; border: 1px solid rgba(251,188,4,0.3); }
.trust-item {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    background: rgba(255,255,255,0.08);
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    color: #c5cae9 !important;
    margin: 3px;
    backdrop-filter: blur(4px);
    border: 1px solid rgba(255,255,255,0.1);
}

/* ── Hero section — override global dark-text rule for white-on-dark card ── */
.physio-hero h1 { color: #ffffff !important; }
.physio-hero p  { color: #c5cae9 !important; }
.physio-hero p .hero-strong  { color: #ffffff !important; }
.physio-hero p .hero-accent  { color: #8ab4f8 !important; }

/* ── Misc ──────────────────────────────────────────────────────────────── */
footer { display: none !important; }
.accordion { border-radius: 12px !important; }
.accordion *, .accordion label, .accordion span { color: #1e293b !important; }
.markdown-text, .markdown-text *, .prose, .prose * { color: #1e293b !important; }
input, textarea { color: #1e293b !important; }
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
}


def _format_reasoning_chain(chain: list) -> str:
    if not chain:
        return ""
    html = '<div style="margin-top: 8px;">'
    html += '<h4 style="color: #334155; margin-bottom: 10px; font-size: 15px;">Agent Reasoning Chain</h4>'
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
            video_embed = (
                f'<a href="{yt_url}" target="_blank" '
                f'style="display:block; position:relative; margin-top:12px; '
                f'border-radius:12px; overflow:hidden; max-width:100%;">'
                f'<img src="{thumb_url}" '
                f'style="width:100%; border-radius:12px; display:block;" '
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

    return f"""### Clinical Assessment Summary

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


# ── Stats cards HTML ────────────────────────────────────────────────────────

def _stats_html(progress_data: dict) -> str:
    stats = get_overall_stats(progress_data)
    if stats["total_sessions"] == 0:
        return """<div style="text-align:center; padding:40px 20px; color:#94a3b8;">
            <p style="font-size:40px; margin:0;">&#128203;</p>
            <p style="font-size:15px; margin:8px 0 0 0;">No sessions logged yet. Complete a consultation and start tracking!</p>
        </div>"""

    pain_pct = stats.get("pain_change_pct", 0)
    pain_color = "#10b981" if pain_pct < 0 else "#ef4444" if pain_pct > 0 else "#64748b"
    pain_arrow = "&#8595;" if pain_pct < 0 else "&#8593;" if pain_pct > 0 else "&#8594;"

    return f"""
    <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap:14px; margin:16px 0;">
        <div class="stat-card">
            <div class="stat-icon">&#128197;</div>
            <h3>{stats['total_sessions']}</h3>
            <p>Sessions</p>
        </div>
        <div class="stat-card">
            <div class="stat-icon">&#128201;</div>
            <h3 style="color:{pain_color}">{stats.get('current_pain', 'N/A')}/10</h3>
            <p>Pain {pain_arrow} {abs(pain_pct):.0f}%</p>
        </div>
        <div class="stat-card">
            <div class="stat-icon">&#9989;</div>
            <h3>{stats.get('avg_adherence', 0):.0f}%</h3>
            <p>Adherence</p>
        </div>
        <div class="stat-card">
            <div class="stat-icon">&#128293;</div>
            <h3>{stats.get('current_streak', 0)}</h3>
            <p>Day Streak</p>
        </div>
        <div class="stat-card">
            <div class="stat-icon">&#127947;</div>
            <h3>L{stats.get('current_level', '?')}</h3>
            <p>Level</p>
        </div>
        <div class="stat-card">
            <div class="stat-icon">&#127942;</div>
            <h3>{stats.get('milestones_earned', 0)}</h3>
            <p>Milestones</p>
        </div>
    </div>
    """


def _milestones_html(progress_data: dict) -> str:
    milestones = progress_data.get("milestones", [])
    if not milestones:
        return ""
    badges = "".join(f'<span class="milestone-badge">&#127942; {m["label"]}</span>' for m in milestones)
    return f'<div style="margin:12px 0; text-align:center;">{badges}</div>'


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
    "progress": ("background: linear-gradient(135deg, #d1fae5, #a7f3d0); color:#065f46; border:2px solid #10b981;",
                 "&#128640; Ready to Progress to Next Level!"),
    "maintain": ("background: linear-gradient(135deg, #dbeafe, #bfdbfe); color:#1e40af; border:2px solid #3b82f6;",
                 "&#128170; Maintain Current Level — Keep Going!"),
    "regress": ("background: linear-gradient(135deg, #fef2f2, #fecaca); color:#991b1b; border:2px solid #ef4444;",
                "&#9888; Consider Stepping Back a Level for Safety"),
    "insufficient_data": ("background: linear-gradient(135deg, #f8fafc, #f1f5f9); color:#64748b; border:2px solid #cbd5e1;",
                          "&#128202; Log More Sessions for Personalized Insights"),
}


def _format_insights_html(analysis: dict) -> str:
    insights = analysis.get("insights", [])
    if not insights:
        return '<p style="color:#94a3b8;">No insights yet. Log sessions to generate recovery insights.</p>'

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


def chat_loading(message: str, history: list, state: dict | None, progress_data: dict | None):
    """Phase 1: Show user message + loading indicator immediately."""
    if not message or not message.strip():
        return history, state, progress_data, message
    history = history + [{"role": "user", "content": message}]
    loading_text = "Analyzing your condition..."
    if state and state.get("collected", {}).get("condition"):
        loading_text = "Generating your treatment plan..."
    history = history + [{"role": "assistant", "content": loading_text}]
    return history, state, progress_data, message


def chat(message: str, history: list, state: dict | None, progress_data: dict | None):
    """Phase 2: Process with agent and replace loading message."""
    if not message or not message.strip():
        return history, state, "", "", "", "", "", progress_data, serialize_progress(progress_data or {})

    if state is None:
        state = {"collected": {}, "reasoning_chain": [], "prescription_generated": False}
    if progress_data is None:
        progress_data = create_empty_progress()

    # Remove the loading placeholder before processing
    if history and history[-1].get("content") in (
        "Analyzing your condition...",
        "Generating your treatment plan...",
    ):
        history = history[:-1]

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
    return ([], None, _progress_html({}), "", "", "", "", empty,
            serialize_progress(empty), "", gr.update(choices=[]))


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
            '<p style="color:#94a3b8;">No sessions logged yet. Start tracking your progress to get AI insights!</p>',
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

        # ── Hero Section ──
        gr.HTML("""
        <div class="physio-hero" style="text-align: center; padding: 32px 24px 28px 24px;
                    background: linear-gradient(135deg, #1a237e 0%, #283593 40%, #1565c0 100%);
                    border-radius: 20px; margin-bottom: 16px;
                    box-shadow: 0 4px 24px rgba(26,35,126,0.25);">

            <h1 style="font-size: 2.6em; margin: 0;
                        font-weight: 800; letter-spacing: -0.02em;">
                &#129658; PhysioGemma
            </h1>
            <p style="font-size: 1.15em; margin: 8px 0 16px 0; font-weight: 400;">
                AI Physiotherapy <span class="hero-strong">Agent</span>
                powered by <span class="hero-accent">Gemma 4</span>
            </p>

            <div style="margin: 12px 0;">
                <span class="hero-badge badge-agent">&#9889; ReAct Agent</span>
                <span class="hero-badge badge-rag">&#128218; RAG-Enhanced</span>
                <span class="hero-badge badge-clinical">&#127973; Clinical Decision Support</span>
            </div>

            <div style="margin: 14px 0 4px 0;">
                <span class="trust-item">&#9989; Evidence-Based</span>
                <span class="trust-item">&#128737; Safe Recommendations</span>
                <span class="trust-item">&#128200; Progress Tracking</span>
                <span class="trust-item">&#127909; 183 Exercise Videos</span>
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
            # TAB 1: CONSULTATION
            # ════════════════════════════════════════════════════════════
            with gr.TabItem("Consultation", id="consult"):

                with gr.Accordion("How does the PhysioGemma Agent work?", open=False):
                    gr.Markdown("""
**PhysioGemma** is a **ReAct Agent** that autonomously conducts clinical assessments:

**5 Agent Tools:** Safety Check, Classify Occupation, Determine Exercise Level, Generate Prescription, Progress Analysis
**+ RAG-Enhanced** clinical reasoning with condition-specific evidence injection

Every tool call is logged in the **Reasoning Chain** for full transparency.

**8 Conditions:** Lower Back Pain, Knee OA, Neck Pain, Frozen Shoulder, Sciatica, Hip OA, Plantar Fasciitis, Tennis Elbow
                    """)

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

                gr.HTML("<hr style='margin: 24px 0; border: none; border-top: 1px solid #e2e8f0;'>")

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

                gr.Markdown("### Track Your Recovery")
                stats_display = gr.HTML(value=_stats_html({}))
                milestones_display = gr.HTML(value="")

                gr.HTML("<hr style='margin: 20px 0; border: none; border-top: 1px solid #e2e8f0;'>")
                gr.Markdown("### Log Today's Session")

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

                gr.HTML("<hr style='margin: 20px 0; border: none; border-top: 1px solid #e2e8f0;'>")
                gr.Markdown("### Recovery Graph")
                recovery_plot = gr.Plot(label="Recovery Progress")

                gr.HTML("<hr style='margin: 20px 0; border: none; border-top: 1px solid #e2e8f0;'>")
                gr.Markdown("### Session History")
                session_history = gr.Dataframe(
                    headers=["Date", "Pain", "Adherence", "Difficulty", "Level", "Notes"],
                    label="Past Sessions",
                    interactive=False,
                )

            # ════════════════════════════════════════════════════════════
            # TAB 3: AI INSIGHTS
            # ════════════════════════════════════════════════════════════
            with gr.TabItem("AI Insights", id="insights"):

                gr.Markdown("### Recovery Insights powered by Gemma 4")
                gr.Markdown("*Combines rule-based analysis with AI-generated narrative*")

                refresh_insights_btn = gr.Button("Generate Recovery Insights", variant="primary", size="lg")

                recommendation_display = gr.HTML("")
                insights_display = gr.HTML("")

                gr.HTML("<hr style='margin: 20px 0; border: none; border-top: 1px solid #e2e8f0;'>")
                gr.Markdown("### AI Recovery Report")
                ai_narrative_display = gr.Markdown("")

        # Footer
        gr.HTML("""
        <div style="text-align: center; padding: 24px 20px;
                    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
                    border-radius: 16px; margin-top: 24px;
                    border: 1px solid #e2e8f0;">
            <p style="color: #475569; font-size: 13px; font-weight: 600; margin: 0 0 4px 0;">
                <strong>PhysioGemma Agent</strong> &mdash; Gemma 4 Good Hackathon
                (Health &amp; Sciences Track)
            </p>
            <p style="color: #94a3b8; font-size: 12px; margin: 4px 0;">
                ReAct Agent &bull; Tool-Calling &bull; RAG-Enhanced &bull;
                183 Exercises &bull; Not medical advice
            </p>
            <p style="color: #94a3b8; font-size: 12px; margin: 4px 0 0 0;">
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

        # Hidden textbox to hold message during two-phase chat
        msg_holder = gr.Textbox(visible=False)

        # Consultation chat — two-phase: loading → process
        loading_outputs = [chatbot, consultation_state, progress_state, msg_holder]
        chat_outputs = [chatbot, consultation_state, progress_display, profile_display,
                        exercises_display, reasoning_display, agent_chain_display,
                        progress_state, progress_store]

        send_btn.click(
            fn=chat_loading,
            inputs=[msg, chatbot, consultation_state, progress_state],
            outputs=loading_outputs,
        ).then(lambda: "", outputs=msg).then(
            fn=chat,
            inputs=[msg_holder, chatbot, consultation_state, progress_state],
            outputs=chat_outputs,
        ).then(fn=None, js=JS_SAVE_PROGRESS, inputs=[progress_store])

        msg.submit(
            fn=chat_loading,
            inputs=[msg, chatbot, consultation_state, progress_state],
            outputs=loading_outputs,
        ).then(lambda: "", outputs=msg).then(
            fn=chat,
            inputs=[msg_holder, chatbot, consultation_state, progress_state],
            outputs=chat_outputs,
        ).then(fn=None, js=JS_SAVE_PROGRESS, inputs=[progress_store])

        reset_btn.click(
            fn=reset,
            outputs=[chatbot, consultation_state, progress_display, profile_display,
                     exercises_display, reasoning_display, agent_chain_display,
                     progress_state, progress_store, log_status, exercises_completed],
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
    )
