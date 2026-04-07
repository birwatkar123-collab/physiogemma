"""
PhysioGemma — AI Physiotherapy Agent powered by Gemma 4
========================================================
Kaggle Gemma 4 Good Hackathon | Health & Sciences Track

ReAct agent with tool-calling, structured reasoning, patient progress
tracking, recovery graph, and AI-powered insights.

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
from google.genai import types

# ── Theme ────────────────────────────────────────────────────────────────────

THEME = gr.themes.Soft(
    primary_hue="blue",
    secondary_hue="emerald",
    neutral_hue="slate",
    font=gr.themes.GoogleFont("Inter"),
)

CSS = """
.exercise-card {
    background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
    border: 1px solid #bae6fd;
    border-radius: 12px;
    padding: 16px;
    margin: 8px 0;
}
.exercise-card h4 { color: #0369a1; margin: 0 0 8px 0; }
.exercise-card p { color: #475569; margin: 4px 0; font-size: 14px; }
.reasoning-step {
    border-radius: 8px;
    padding: 10px 14px;
    margin: 6px 0;
    font-size: 13px;
    line-height: 1.5;
}
.reasoning-action {
    background: #dbeafe;
    border-left: 4px solid #3b82f6;
}
.reasoning-observation {
    background: #d1fae5;
    border-left: 4px solid #10b981;
    font-family: monospace;
    font-size: 12px;
}
.reasoning-warning {
    background: #fef2f2;
    border-left: 4px solid #ef4444;
}
.tool-badge {
    display: inline-block;
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    color: #1d4ed8;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
    margin: 2px 4px;
}
.progress-bar {
    display: flex; gap: 6px; justify-content: center;
    margin: 10px 0 20px 0; flex-wrap: wrap;
}
.progress-pill {
    padding: 5px 14px; border-radius: 20px; font-size: 12px; font-weight: 600;
}
.progress-done { background: #10b981; color: white; }
.progress-pending { background: #e2e8f0; color: #94a3b8; }
.stat-card {
    background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
    border: 1px solid #bae6fd;
    border-radius: 12px;
    padding: 16px;
    text-align: center;
}
.stat-card h3 { color: #3b82f6; margin: 0; font-size: 28px; }
.stat-card p { color: #64748b; margin: 4px 0 0 0; font-size: 13px; }
.milestone-badge {
    display: inline-block;
    background: linear-gradient(135deg, #fef3c7, #fde68a);
    border: 1px solid #f59e0b;
    border-radius: 20px;
    padding: 6px 14px;
    margin: 4px;
    font-size: 13px;
    font-weight: 600;
    color: #92400e;
}
.insight-card {
    border-radius: 10px;
    padding: 12px 16px;
    margin: 8px 0;
    font-size: 14px;
}
.insight-improvement { background: #d1fae5; border-left: 4px solid #10b981; }
.insight-achievement { background: #dbeafe; border-left: 4px solid #3b82f6; }
.insight-concern { background: #fef2f2; border-left: 4px solid #ef4444; }
.insight-suggestion { background: #fef3c7; border-left: 4px solid #f59e0b; }
.insight-info { background: #f1f5f9; border-left: 4px solid #94a3b8; }
.insight-milestone { background: #f5f3ff; border-left: 4px solid #8b5cf6; }
.insight-ready_to_progress { background: #d1fae5; border-left: 4px solid #059669; }
footer { display: none !important; }
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
    "Prescription": "level",
}


def _progress_html(collected: dict) -> str:
    """Dynamic progress based on what data the agent has collected."""
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
    html += '<h4 style="color: #475569; margin-bottom: 8px;">Agent Reasoning Chain</h4>'
    for step in chain:
        if "action" in step:
            tool_label = TOOL_LABELS.get(step["action"], step["action"])
            args_str = ", ".join(f"{k}={v}" for k, v in step.get("args", {}).items()
                                if k != "patient_message" and k != "progress_data_json")
            if len(args_str) > 120:
                args_str = args_str[:120] + "..."
            html += (f'<div class="reasoning-step reasoning-action">'
                     f'<strong>Action:</strong> <span class="tool-badge">{tool_label}</span>')
            if args_str:
                html += f' <span style="color:#64748b;">({args_str})</span>'
            html += '</div>'
        elif "observation" in step:
            tool_label = TOOL_LABELS.get(step["observation"], step["observation"])
            result_str = step.get("result", "")
            is_warning = "RED FLAG" in result_str.upper()
            cls = "reasoning-warning" if is_warning else "reasoning-observation"
            html += (f'<div class="reasoning-step {cls}">'
                     f'<strong>Observation ({tool_label}):</strong> {result_str}</div>')
    html += '</div>'
    return html


# ── Format prescription exercises ───────────────────────────────────────────

def _format_prescription_html(result: dict) -> str:
    plan = result["plan"]
    exercises_html = ""
    type_icons = {
        "mobility": "&#128260;", "stretching": "&#129496;",
        "strengthening": "&#128170;", "stability": "&#9878;",
        "plyometric": "&#127939;"
    }
    for ex in plan["exercises"]:
        video_id = ex.get("video", "")
        video_embed = ""
        if video_id:
            yt_url = f"https://www.youtube.com/watch?v={video_id}"
            thumb_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
            video_embed = (
                f'<a href="{yt_url}" target="_blank" '
                f'style="display:block; position:relative; margin-top:8px; '
                f'border-radius:8px; overflow:hidden; max-width:100%;">'
                f'<img src="{thumb_url}" '
                f'style="width:100%; border-radius:8px; display:block;" '
                f'alt="Watch exercise video" />'
                f'<span style="position:absolute; top:50%; left:50%; '
                f'transform:translate(-50%,-50%); font-size:48px; '
                f'color:#fff; text-shadow:0 0 10px rgba(0,0,0,0.7); '
                f'pointer-events:none;">&#9654;</span></a>'
            )
        icon = type_icons.get(ex.get("type", ""), "&#127947;")
        exercises_html += (
            f'<div class="exercise-card">'
            f'<h4>{icon} {ex["name"]}</h4>'
            f'<p><strong>Sets:</strong> {ex["sets"]} | '
            f'<strong>Reps:</strong> {ex["reps"]} | '
            f'<strong>Type:</strong> {ex.get("type", "general").title()}</p>'
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
    level = info.get("level")
    plan_label = ""
    if level:
        cond = EXERCISES.get(condition, {})
        lvl = cond.get("levels", {}).get(level, {})
        plan_label = f"Level {level} — {lvl.get('label', info.get('level_label', ''))}"
    vas = info.get('intensity_vas', info.get('pain_vas', 'N/A'))

    return f"""### Clinical Assessment Summary

| Category | Detail |
|----------|--------|
| **Condition** | {condition_name} |
| **Intensity (VAS)** | {vas}/10 |
| **Tendency** | {info.get('tendency', 'N/A')} |
| **Characteristic** | {info.get('characteristic', 'N/A')} |
| **Aggravating** | {aggravating} |
| **Age** | {info.get('age', 'N/A')} |
| **Occupation** | {info.get('occupation', 'N/A')} ({info.get('physical_demands', 'N/A')}) |
| **Prescription** | {plan_label} |
"""


# ── Progress tracking helpers ───────────────────────────────────────────────

def _stats_html(progress_data: dict) -> str:
    """Generate stats cards HTML."""
    stats = get_overall_stats(progress_data)
    if stats["total_sessions"] == 0:
        return '<p style="color: #94a3b8; text-align: center;">No sessions logged yet. Complete a consultation and start tracking!</p>'

    pain_color = "#10b981" if stats.get("pain_change_pct", 0) < 0 else "#ef4444"
    pain_arrow = "&#8595;" if stats.get("pain_change_pct", 0) < 0 else "&#8593;"

    return f"""
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px;">
        <div class="stat-card">
            <h3>{stats['total_sessions']}</h3>
            <p>Sessions</p>
        </div>
        <div class="stat-card">
            <h3 style="color: {pain_color};">{stats.get('current_pain', 'N/A')}</h3>
            <p>Current Pain {pain_arrow} {abs(stats.get('pain_change_pct', 0)):.0f}%</p>
        </div>
        <div class="stat-card">
            <h3>{stats.get('avg_adherence', 0):.0f}%</h3>
            <p>Avg Adherence</p>
        </div>
        <div class="stat-card">
            <h3>{stats.get('current_streak', 0)}</h3>
            <p>Day Streak</p>
        </div>
        <div class="stat-card">
            <h3>L{stats.get('current_level', '?')}</h3>
            <p>Current Level</p>
        </div>
        <div class="stat-card">
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
    return f'<div style="margin-top: 12px;">{badges}</div>'


def _sessions_table(progress_data: dict) -> list:
    sessions = progress_data.get("sessions", [])
    rows = []
    for s in reversed(sessions):
        rows.append([
            s.get("date", ""),
            f"{s.get('pain_vas', '')}/10",
            f"{s.get('adherence_pct', 0):.0f}%",
            f"{s.get('difficulty_rating', '')}/5",
            s.get("notes", "")[:60],
        ])
    return rows


def _format_insights(analysis: dict) -> str:
    insights = analysis.get("insights", [])
    if not insights:
        return "No insights available yet."
    html = ""
    type_icons = {
        "improvement": "&#128994;", "achievement": "&#11088;",
        "concern": "&#128308;", "suggestion": "&#128161;",
        "info": "&#8505;", "milestone": "&#127942;",
        "ready_to_progress": "&#128640;",
    }
    for ins in insights:
        itype = ins.get("type", "info")
        icon = type_icons.get(itype, "&#8505;")
        html += f'<div class="insight-card insight-{itype}">{icon} {ins["text"]}</div>'

    rec = analysis.get("recommendation", "maintain")
    rec_labels = {
        "progress": ("&#128640; Ready to Progress", "#059669", "Your data suggests you can move to the next exercise level!"),
        "maintain": ("&#9989; Maintain Current Level", "#3b82f6", "Keep up your current routine — you're on track."),
        "regress": ("&#9888; Consider Easier Level", "#ef4444", "Pain is increasing — a gentler level may help."),
        "insufficient_data": ("&#8505; Need More Data", "#94a3b8", "Log at least 3 sessions for meaningful insights."),
    }
    label, color, desc = rec_labels.get(rec, rec_labels["maintain"])
    html += f"""
    <div style="margin-top: 16px; padding: 16px; border-radius: 12px;
                background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
                border: 2px solid {color};">
        <h4 style="color: {color}; margin: 0 0 6px 0;">{label}</h4>
        <p style="color: #475569; margin: 0;">{desc}</p>
    </div>
    """
    return html


# ── Chat handler ────────────────────────────────────────────────────────────

# Store last prescription exercises globally for checkbox population
_last_prescribed_exercises = []


def chat(message: str, history: list, state: dict | None):
    global _last_prescribed_exercises

    if not message or not message.strip():
        return history, state, "", "", "", "", ""

    if state is None:
        state = {"collected": {}, "reasoning_chain": [], "prescription_generated": False}

    history = history + [{"role": "user", "content": message}]
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

        # Save exercise names for progress tracking
        plan = result["plan"]
        _last_prescribed_exercises = [ex["name"] for ex in plan.get("exercises", [])]
        state["prescribed_exercises"] = _last_prescribed_exercises
        state["exercise_level"] = plan.get("level", 0)
        state["condition"] = plan.get("condition", patient_info.get("condition", ""))

        tool_names = [TOOL_LABELS.get(s["action"], s["action"])
                      for s in reasoning_chain if "action" in s]
        badge_html = " ".join(f"`{t}`" for t in tool_names)
        bot_msg = (f"**Assessment complete! Your personalized exercise plan is ready.**\n\n"
                   f"Tools used: {badge_html}\n\n"
                   "Scroll down for your prescription with video demos.\n"
                   "**Go to the 'My Progress' tab to start tracking your recovery!**")
        history = history + [{"role": "assistant", "content": bot_msg}]

        progress = _progress_html(state.get("collected", {}))
        full_reasoning = _format_reasoning_chain(state.get("all_reasoning", []))
        return history, state, progress, profile_md, exercises_html, explanation, full_reasoning
    else:
        bot_msg = result.get("text", str(result)) if isinstance(result, dict) else str(result)
        tool_names = [TOOL_LABELS.get(s["action"], s["action"])
                      for s in reasoning_chain if "action" in s]
        if tool_names:
            badge_str = " ".join(f"`{t}`" for t in tool_names)
            bot_msg = f"[{badge_str}]\n\n{bot_msg}"
        history = history + [{"role": "assistant", "content": bot_msg}]

        progress = _progress_html(state.get("collected", {}))
        full_reasoning = _format_reasoning_chain(state.get("all_reasoning", []))
        return history, state, progress, "", "", "", full_reasoning


def reset():
    return [], None, _progress_html({}), "", "", "", "", ""


# ── Progress tab handlers ───────────────────────────────────────────────────

def load_progress_from_store(json_str):
    """Load progress from localStorage JSON string."""
    progress = deserialize_progress(json_str)
    chart = generate_recovery_chart(progress)
    table = _sessions_table(progress)
    stats = _stats_html(progress)
    milestones = _milestones_html(progress)
    return progress, chart, table, stats, milestones


def log_session_handler(progress_data, pain_vas, exercises_done, difficulty, notes, consult_state):
    """Log a session and update all displays."""
    if not progress_data or not isinstance(progress_data, dict) or "sessions" not in progress_data:
        condition = ""
        level = 0
        if consult_state and isinstance(consult_state, dict):
            condition = consult_state.get("condition", "")
            level = consult_state.get("exercise_level", 0)
        progress_data = create_empty_progress(condition, level)

    # Get prescribed exercises from consultation state
    prescribed = []
    level = 0
    condition = progress_data.get("condition", "")
    if consult_state and isinstance(consult_state, dict):
        prescribed = consult_state.get("prescribed_exercises", [])
        level = consult_state.get("exercise_level", 0)
        if not condition:
            condition = consult_state.get("condition", "")
            progress_data["condition"] = condition

    if not exercises_done:
        exercises_done = []

    progress_data = log_session(
        progress_data=progress_data,
        pain_vas=pain_vas,
        exercises_completed=exercises_done,
        exercises_prescribed=prescribed or exercises_done,
        difficulty_rating=difficulty,
        notes=notes,
        exercise_level=level,
    )

    # Regenerate displays
    chart = generate_recovery_chart(progress_data)
    table = _sessions_table(progress_data)
    stats = _stats_html(progress_data)
    milestones = _milestones_html(progress_data)
    serialized = serialize_progress(progress_data)

    # New milestones notification
    recent_milestones = progress_data.get("milestones", [])
    if recent_milestones:
        latest = recent_milestones[-1]
        status = f"**Session logged!** &#127942; New milestone: {latest['label']}"
    else:
        status = "**Session logged!** Keep up the great work."

    return progress_data, serialized, chart, table, stats, milestones, status


def generate_insights_handler(progress_data, consult_state):
    """Generate AI insights from progress data."""
    if not progress_data or not isinstance(progress_data, dict):
        return "No progress data available. Log some sessions first!", ""

    sessions = progress_data.get("sessions", [])
    if not sessions:
        return "No sessions logged yet. Complete some exercise sessions and log them to see insights!", ""

    # Rule-based analysis
    analysis = tool_analyze_progress(json.dumps(progress_data, default=str))
    insights_html = _format_insights(analysis)

    # AI narration via Gemma
    ai_narrative = ""
    try:
        client = get_client()
        stats = analysis.get("summary", {})
        pain_trend = analysis.get("pain_trend", {})
        insights_text = "\n".join(f"- [{i['type']}] {i['text']}" for i in analysis.get("insights", []))

        prompt = f"""You are PhysioGemma. Analyze this patient's recovery progress and write a warm,
encouraging progress report (3-5 paragraphs). Reference specific numbers.

Patient condition: {progress_data.get('condition', 'Unknown')}
Total sessions: {stats.get('total_sessions', 0)}
Pain change: {stats.get('first_pain', '?')}/10 → {stats.get('current_pain', '?')}/10 ({stats.get('pain_change_pct', 0):.0f}%)
Average adherence: {stats.get('avg_adherence', 0):.0f}%
Current streak: {stats.get('current_streak', 0)} days
Current level: {stats.get('current_level', '?')}
Recommendation: {analysis.get('recommendation', 'maintain')}

Insights:
{insights_text}

Write directly to the patient using "you/your". Be specific, warm, and motivating.
Include one concrete suggestion for improvement. End with encouragement."""

        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(system_instruction=AGENT_SYSTEM_PROMPT),
        )
        ai_narrative = response.text if response.text else ""
    except Exception:
        ai_narrative = ""

    return insights_html, ai_narrative


# ── Build Gradio app ────────────────────────────────────────────────────────

def build_app():
    with gr.Blocks(theme=THEME, css=CSS, title="PhysioGemma — AI Physiotherapy Agent") as app:

        # Hero
        gr.HTML("""
        <div style="text-align: center; padding: 20px;
                    background: linear-gradient(135deg, #eff6ff 0%, #f0fdf4 100%);
                    border-radius: 16px; margin-bottom: 10px;">
            <h1 style="font-size: 2.2em; margin: 0; color: #1e40af;">
                &#129658; PhysioGemma
            </h1>
            <p style="font-size: 1.1em; color: #475569; margin: 8px 0 0 0;">
                AI Physiotherapy <strong>Agent</strong> powered by <strong>Gemma 4</strong>
            </p>
            <p style="font-size: 0.85em; color: #64748b; margin: 4px 0 0 0;">
                ReAct Agent &bull; Tool-Calling &bull; Progress Tracking &bull;
                Recovery Graph &bull; AI Insights &bull; 8 Conditions
            </p>
        </div>
        """)

        # Hidden localStorage bridge
        progress_store = gr.Textbox(visible=False, elem_id="progress_store")
        progress_state = gr.State({})
        consult_state = gr.State(None)

        with gr.Tabs() as tabs:

            # ═══════════════════════════════════════════════════════════════
            # TAB 1: Consultation
            # ═══════════════════════════════════════════════════════════════
            with gr.TabItem("Consultation", id="consult"):

                with gr.Accordion("How does the PhysioGemma Agent work?", open=False):
                    gr.Markdown("""
**PhysioGemma** is a **ReAct Agent** that autonomously conducts clinical assessments:

**Agent Tools:** Safety Check | Classify Occupation | Determine Exercise Level | Generate Prescription | Progress Analysis

**Flow:** Thinks → Calls Tools → Observes Results → Decides Next Step

**8 Conditions:** LBP, Knee OA, Neck Pain, Frozen Shoulder, Sciatica, Hip OA, Plantar Fasciitis, Tennis Elbow
                    """)

                progress_display = gr.HTML(value=_progress_html({}))

                chatbot_kwargs = dict(
                    label="PhysioGemma Agent",
                    height=400,
                    placeholder="Describe your pain or condition...",
                )
                try:
                    chatbot = gr.Chatbot(type="messages", **chatbot_kwargs)
                except TypeError:
                    chatbot = gr.Chatbot(**chatbot_kwargs)

                with gr.Row():
                    msg = gr.Textbox(
                        label="Your message",
                        placeholder="Example: My lower back hurts for 3 months, pain 6/10, I'm 45...",
                        lines=2, scale=4,
                    )
                    with gr.Column(scale=1, min_width=120):
                        send_btn = gr.Button("Send", variant="primary", size="lg")
                        reset_btn = gr.Button("New Assessment", variant="secondary", size="sm")

                gr.Examples(
                    examples=[
                        "My lower back has been hurting for 3 months. Pain is about 6 out of 10. I'm 45 years old.",
                        "I'm 62, knee pain for 6 months, getting worse lately",
                        "Shoulder is frozen, can't raise my arm. 55 years old, pain started 4 months ago",
                        "Elbow pain on outer side, worse when gripping, I work in IT",
                    ],
                    inputs=msg,
                    label="Try these examples:",
                )

                gr.HTML("<hr style='margin: 20px 0; border-color: #e2e8f0;'>")

                with gr.Row():
                    with gr.Column(scale=1):
                        profile_display = gr.Markdown(label="Clinical Assessment")
                    with gr.Column(scale=1):
                        reasoning_display = gr.Markdown(label="Clinical Reasoning")

                exercises_display = gr.HTML(label="Exercise Prescription")

                with gr.Accordion("Agent Reasoning Chain", open=False):
                    agent_chain_display = gr.HTML()

            # ═══════════════════════════════════════════════════════════════
            # TAB 2: Progress Tracking
            # ═══════════════════════════════════════════════════════════════
            with gr.TabItem("My Progress", id="progress"):

                gr.Markdown("### Track Your Recovery")
                stats_display = gr.HTML(value=_stats_html({}))
                milestones_display = gr.HTML(value="")

                gr.Markdown("---")
                gr.Markdown("### Log Today's Session")

                with gr.Row():
                    with gr.Column(scale=1):
                        pain_slider = gr.Slider(
                            minimum=0, maximum=10, step=0.5, value=5,
                            label="Pain Level (VAS 0-10)"
                        )
                        difficulty_slider = gr.Slider(
                            minimum=1, maximum=5, step=1, value=3,
                            label="Difficulty (1=Easy, 5=Very Hard)"
                        )
                    with gr.Column(scale=1):
                        exercises_checklist = gr.CheckboxGroup(
                            choices=[],
                            label="Exercises Completed",
                            info="Complete a consultation first to see your exercises"
                        )

                session_notes = gr.Textbox(
                    label="Session Notes",
                    placeholder="How did you feel? Any issues?",
                    lines=2,
                )
                log_btn = gr.Button("Log Session", variant="primary")
                log_status = gr.Markdown("")

                gr.Markdown("---")
                gr.Markdown("### Recovery Graph")
                recovery_plot = gr.Plot(label="Recovery Progress")

                gr.Markdown("---")
                gr.Markdown("### Session History")
                session_table = gr.Dataframe(
                    headers=["Date", "Pain", "Adherence", "Difficulty", "Notes"],
                    label="Past Sessions",
                    interactive=False,
                )

            # ═══════════════════════════════════════════════════════════════
            # TAB 3: AI Insights
            # ═══════════════════════════════════════════════════════════════
            with gr.TabItem("AI Insights", id="insights"):

                gr.Markdown("### Recovery Insights powered by Gemma 4")
                gr.Markdown("*Analyzes your progress data to provide personalized recovery insights, "
                            "trend analysis, and level progression recommendations.*")

                refresh_btn = gr.Button("Generate Insights", variant="primary", size="lg")

                insights_display = gr.HTML("")
                ai_narrative_display = gr.Markdown("")

        # Footer
        gr.HTML("""
        <div style="text-align: center; padding: 20px; color: #94a3b8; font-size: 12px;
                    border-top: 1px solid #e2e8f0; margin-top: 30px;">
            <p><strong>PhysioGemma Agent</strong> &mdash; Gemma 4 Good Hackathon (Health &amp; Sciences)</p>
            <p>ReAct Agent &bull; Tool-Calling &bull; Progress Tracking &bull; Not medical advice</p>
            <p>Created by Gaurav Birwatkar &bull; CC-BY 4.0</p>
        </div>
        """)

        # ═══════════════════════════════════════════════════════════════════
        # EVENT WIRING
        # ═══════════════════════════════════════════════════════════════════

        # Consultation tab events
        consult_outputs = [chatbot, consult_state, progress_display, profile_display,
                          exercises_display, reasoning_display, agent_chain_display]

        send_btn.click(
            fn=chat,
            inputs=[msg, chatbot, consult_state],
            outputs=consult_outputs,
        ).then(lambda: "", outputs=msg
        ).then(
            fn=lambda s: gr.update(choices=s.get("prescribed_exercises", []) if s and isinstance(s, dict) else []),
            inputs=[consult_state],
            outputs=[exercises_checklist],
        )

        msg.submit(
            fn=chat,
            inputs=[msg, chatbot, consult_state],
            outputs=consult_outputs,
        ).then(lambda: "", outputs=msg
        ).then(
            fn=lambda s: gr.update(choices=s.get("prescribed_exercises", []) if s and isinstance(s, dict) else []),
            inputs=[consult_state],
            outputs=[exercises_checklist],
        )

        reset_btn.click(
            fn=reset,
            outputs=[chatbot, consult_state, progress_display, profile_display,
                     exercises_display, reasoning_display, agent_chain_display, msg],
        )

        # Progress tab: load from localStorage on app start
        app.load(
            fn=load_progress_from_store,
            inputs=[progress_store],
            outputs=[progress_state, recovery_plot, session_table, stats_display, milestones_display],
            js=JS_LOAD_PROGRESS,
        )

        # Progress tab: log session
        log_btn.click(
            fn=log_session_handler,
            inputs=[progress_state, pain_slider, exercises_checklist,
                    difficulty_slider, session_notes, consult_state],
            outputs=[progress_state, progress_store, recovery_plot, session_table,
                     stats_display, milestones_display, log_status],
        ).then(fn=None, js=JS_SAVE_PROGRESS, inputs=[progress_store])

        # Insights tab: generate insights
        refresh_btn.click(
            fn=generate_insights_handler,
            inputs=[progress_state, consult_state],
            outputs=[insights_display, ai_narrative_display],
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
