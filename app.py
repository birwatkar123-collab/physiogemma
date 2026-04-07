"""
PhysioGemma — AI Physiotherapy Agent powered by Gemma 4
========================================================
Kaggle Gemma 4 Good Hackathon | Health & Sciences Track

ReAct agent architecture with tool-calling, structured reasoning chain,
SITCAR pain evaluation, and evidence-based exercise prescription.

Run: python app.py
"""

import os
import json
import gradio as gr
from gemma_engine import process_message
from exercises import EXERCISES

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
.disclaimer {
    background: #fffbeb;
    border: 1px solid #fde68a;
    border-radius: 8px;
    padding: 12px;
    margin-top: 16px;
    font-size: 13px;
    color: #92400e;
}
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
footer { display: none !important; }
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
        # Check both direct key and alternatives
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
}


def _format_reasoning_chain(chain: list) -> str:
    """Format the agent's reasoning chain as styled HTML."""
    if not chain:
        return ""

    html = '<div style="margin-top: 8px;">'
    html += '<h4 style="color: #475569; margin-bottom: 8px;">Agent Reasoning Chain</h4>'

    for step in chain:
        if "action" in step:
            tool_label = TOOL_LABELS.get(step["action"], step["action"])
            args_str = ", ".join(f"{k}={v}" for k, v in step.get("args", {}).items()
                                if k != "patient_message")
            if len(args_str) > 120:
                args_str = args_str[:120] + "..."
            html += (
                f'<div class="reasoning-step reasoning-action">'
                f'<strong>Action:</strong> <span class="tool-badge">{tool_label}</span>'
            )
            if args_str:
                html += f' <span style="color:#64748b;">({args_str})</span>'
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
    """Format exercise cards with clickable YouTube thumbnails."""
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
                f'pointer-events:none;">&#9654;</span>'
                f'</a>'
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
    """Format patient profile as markdown table."""
    condition = info.get("condition", "Unknown")
    condition_name = EXERCISES.get(condition, {}).get("name", condition)
    comorbidities = ", ".join(info.get("comorbidities", [])) if isinstance(info.get("comorbidities"), list) else "N/A"
    surgeries = ", ".join(info.get("surgical_history", [])) if isinstance(info.get("surgical_history"), list) else "None"
    aggravating = ", ".join(info.get("aggravating_factors", [])) if isinstance(info.get("aggravating_factors"), list) else "N/A"
    reducing = ", ".join(info.get("reducing_factors", [])) if isinstance(info.get("reducing_factors"), list) else "N/A"
    limited = ", ".join(info.get("limited_activities", [])) if isinstance(info.get("limited_activities"), list) else "N/A"

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
    is_chronic = info.get('is_chronic')
    duration = info.get('duration_months', 'N/A')
    chronicity = ""
    if is_chronic is not None:
        chronicity = f" ({'Chronic' if is_chronic else 'Acute'})"

    return f"""### Clinical Assessment Summary

| Category | Detail |
|----------|--------|
| **Condition** | {condition_name} |
| **Intensity (VAS)** | {vas}/10 |
| **Tendency** | {info.get('tendency', 'N/A')} |
| **Characteristic** | {info.get('characteristic', 'N/A')} |
| **Duration** | {duration} months{chronicity} |
| **Aggravating** | {aggravating} |
| **Reducing** | {reducing} |
| **Age** | {info.get('age', 'N/A')} |
| **Height / Weight** | {body_info} |
| **Comorbidities** | {comorbidities} |
| **Surgical History** | {surgeries} |
| **Occupation** | {info.get('occupation', 'N/A')} ({info.get('physical_demands', 'N/A')} demands) |
| **Prescription** | {plan_label} |
"""


# ── Main chat function ──────────────────────────────────────────────────────

def chat(message: str, history: list, state: dict | None):
    """Handle chat messages through agent-based assessment."""
    if not message or not message.strip():
        return history, state, "", "", "", "", ""

    if state is None:
        state = {"collected": {}, "reasoning_chain": [], "prescription_generated": False}

    # Add user message to chat
    history = history + [{"role": "user", "content": message}]

    # Process through agent engine
    result, state = process_message(message, history, state)

    # Extract reasoning chain
    reasoning_chain = result.get("reasoning_chain", []) if isinstance(result, dict) else []
    reasoning_html = _format_reasoning_chain(reasoning_chain)

    # Accumulate reasoning chains across turns
    state.setdefault("all_reasoning", [])
    state["all_reasoning"].extend(reasoning_chain)

    # Check if result contains a prescription
    if isinstance(result, dict) and "plan" in result:
        explanation = result.get("explanation", "")
        patient_info = result.get("patient_info", {})
        exercises_html = _format_prescription_html(result)
        profile_md = _format_patient_profile(patient_info)

        # Merge patient info into collected
        state["collected"].update(patient_info)

        # Build tool badges for chat display
        tool_names = [TOOL_LABELS.get(s["action"], s["action"])
                      for s in reasoning_chain if "action" in s]
        badge_html = " ".join(f"`{t}`" for t in tool_names)
        bot_msg = (f"**Assessment complete! Your personalized exercise plan is ready.**\n\n"
                   f"Tools used: {badge_html}\n\n"
                   "Scroll down to see your prescription with video demonstrations, "
                   "clinical reasoning, and safety guidelines.\n\n"
                   "Feel free to ask any follow-up questions!")
        history = history + [{"role": "assistant", "content": bot_msg}]

        progress = _progress_html(state.get("collected", {}))
        full_reasoning = _format_reasoning_chain(state.get("all_reasoning", []))

        return history, state, progress, profile_md, exercises_html, explanation, full_reasoning

    else:
        # Conversational response
        bot_msg = result.get("text", str(result)) if isinstance(result, dict) else str(result)

        # Add tool badges if tools were called
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
    """Reset the conversation."""
    return [], None, _progress_html({}), "", "", "", "", ""


# ── Build Gradio app ────────────────────────────────────────────────────────

def build_app():
    with gr.Blocks(title="PhysioGemma — AI Physiotherapy Agent") as app:

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
                ReAct Agent &bull; Tool-Calling &bull; Structured Reasoning &bull;
                SITCAR Evaluation &bull; 8 Conditions &bull; English &amp; Hindi
            </p>
        </div>
        """)

        # How it works
        with gr.Accordion("How does the PhysioGemma Agent work?", open=False):
            gr.Markdown("""
**PhysioGemma** is a **ReAct Agent** (not just a chatbot) that autonomously conducts clinical assessments:

**Agent Architecture:**
- **Thinks** — Decides what information is needed next
- **Acts** — Calls clinical tools (red flag scanner, level calculator, prescription generator)
- **Observes** — Processes tool results and decides next action
- **Explains** — Provides clinical reasoning for every decision

**4 Agent Tools:**
1. **Safety Check** — Scans every message for clinical red flags (cauda equina, fractures, cardiac, infections)
2. **Classify Occupation** — Categorizes work demands (sedentary/light/moderate/heavy)
3. **Determine Level** — Evidence-based exercise level using Boonstra VAS cutoffs + ACSM + ADA modifiers
4. **Generate Prescription** — Personalized exercises with occupation, aggravation, and BMI adaptations

**Structured Reasoning Chain:** Every tool call and observation is logged and displayed transparently.

**8 Conditions:** Lower Back Pain, Knee OA, Neck Pain, Frozen Shoulder, Sciatica, Hip OA, Plantar Fasciitis, Tennis Elbow

**Clinical references:** Boonstra 2014, NICE NG59, ACSM, ADA, Cochrane Reviews, Canadian C-Spine Rules, McKenzie Method
            """)

        # Progress indicator
        progress_display = gr.HTML(value=_progress_html({}))

        # State
        state = gr.State(None)

        # Chat
        chatbot = gr.Chatbot(
            label="PhysioGemma Agent Consultation",
            height=420,
            placeholder="Describe your pain or condition to begin the agent assessment...",
        )

        with gr.Row():
            msg = gr.Textbox(
                label="Your message",
                placeholder="Example: My lower back has been hurting for 3 months, pain is 6/10, I'm 45...",
                lines=2, scale=4,
            )
            with gr.Column(scale=1, min_width=120):
                send_btn = gr.Button("Send", variant="primary", size="lg")
                reset_btn = gr.Button("New Assessment", variant="secondary", size="sm")

        # Examples
        gr.Examples(
            examples=[
                "My lower back has been hurting for 3 months. Pain is about 6 out of 10. I'm 45 years old.",
                "I'm 62, knee pain for 6 months, getting worse lately",
                "Shoulder is frozen, can't raise my arm. 55 years old, pain started 4 months ago",
                "Pain shooting down my left leg from lower back, 7/10, age 38",
                "My heel hurts every morning when I step out of bed, been 2 months",
                "Elbow pain on outer side, worse when gripping or typing, I work in IT",
            ],
            inputs=msg,
            label="Try these examples:",
        )

        # Results section
        gr.HTML("<hr style='margin: 20px 0; border-color: #e2e8f0;'>")

        with gr.Row():
            with gr.Column(scale=1):
                profile_display = gr.Markdown(label="Clinical Assessment Summary")
            with gr.Column(scale=1):
                reasoning_display = gr.Markdown(label="Clinical Reasoning")

        exercises_display = gr.HTML(label="Exercise Prescription")

        # Agent reasoning chain (collapsible)
        with gr.Accordion("Agent Reasoning Chain (Tool Calls & Observations)", open=False):
            agent_chain_display = gr.HTML(label="Reasoning Chain")

        # Wire up events
        outputs = [chatbot, state, progress_display, profile_display,
                   exercises_display, reasoning_display, agent_chain_display]

        send_btn.click(
            fn=chat,
            inputs=[msg, chatbot, state],
            outputs=outputs,
        ).then(lambda: "", outputs=msg)

        msg.submit(
            fn=chat,
            inputs=[msg, chatbot, state],
            outputs=outputs,
        ).then(lambda: "", outputs=msg)

        reset_btn.click(
            fn=reset,
            outputs=[chatbot, state, progress_display, profile_display,
                     exercises_display, reasoning_display, agent_chain_display, msg],
        )

        # Footer
        gr.HTML("""
        <div style="text-align: center; padding: 20px; color: #94a3b8; font-size: 12px;
                    border-top: 1px solid #e2e8f0; margin-top: 30px;">
            <p><strong>PhysioGemma Agent</strong> &mdash; Built for the Gemma 4 Good Hackathon
               (Health &amp; Sciences Track)</p>
            <p>ReAct Agent &bull; Tool-Calling &bull; Gemma 4 &bull; Evidence-based guidelines &bull;
               Not medical advice</p>
            <p>Created by Gaurav Birwatkar &bull; CC-BY 4.0 License</p>
        </div>
        """)

    return app


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = build_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", 7860)),
        share=False,
        theme=THEME,
        css=CSS,
    )
