"""
PhysioGemma — AI Physiotherapy Assistant powered by Gemma 4 (v2)
=================================================================
Kaggle Gemma 4 Good Hackathon | Health & Sciences Track

Multi-step clinical assessment using SITCAR pain evaluation framework,
medical/surgical history, and functional assessment before prescribing
personalized, evidence-based exercise plans.

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
.stage-indicator {
    display: flex; gap: 8px; justify-content: center;
    margin: 10px 0 20px 0;
}
.stage-pill {
    padding: 6px 16px; border-radius: 20px; font-size: 13px; font-weight: 600;
}
.stage-active { background: #3b82f6; color: white; }
.stage-done { background: #10b981; color: white; }
.stage-pending { background: #e2e8f0; color: #94a3b8; }
footer { display: none !important; }
"""

# ── Stage indicator HTML ─────────────────────────────────────────────────────

STAGE_LABELS = {
    "initial": "Pain Description",
    "sitcar": "SITCAR Evaluation",
    "medical_history": "Medical History",
    "functional": "Functional Assessment",
    "prescription": "Your Exercise Plan",
}

def _stage_html(current_stage: str) -> str:
    stages = list(STAGE_LABELS.items())
    current_idx = next((i for i, (k, _) in enumerate(stages) if k == current_stage), 0)

    pills = []
    for i, (key, label) in enumerate(stages):
        if i < current_idx:
            cls = "stage-done"
            icon = "&#10003;"
        elif i == current_idx:
            cls = "stage-active"
            icon = str(i + 1)
        else:
            cls = "stage-pending"
            icon = str(i + 1)
        pills.append(f'<span class="stage-pill {cls}">{icon}. {label}</span>')

    return f'<div class="stage-indicator">{"".join(pills)}</div>'


# ── Format prescription result ───────────────────────────────────────────────

def _format_prescription_html(result: dict) -> str:
    """Format exercise cards with video embeds."""
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
            video_embed = (
                f'<iframe width="100%" height="200" '
                f'src="https://www.youtube-nocookie.com/embed/{video_id}" '
                f'frameborder="0" allowfullscreen '
                f'style="border-radius: 8px; margin-top: 8px;" '
                f'allow="accelerometer; autoplay; clipboard-write; encrypted-media; '
                f'gyroscope; picture-in-picture"></iframe>'
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


def _format_patient_profile(info: dict) -> str:
    """Format patient profile as markdown table."""
    condition_name = EXERCISES.get(info.get("condition", ""), {}).get("name", info.get("condition", "Unknown"))
    comorbidities = ", ".join(info.get("comorbidities", [])) or "None"
    surgeries = ", ".join(info.get("surgical_history", [])) or "None"
    aggravating = ", ".join(info.get("aggravating_factors", [])) or "Not specified"
    reducing = ", ".join(info.get("reducing_factors", [])) or "Not specified"
    limited = ", ".join(info.get("limited_activities", [])) or "Not specified"

    plan_label = ""
    if "level" in info:
        cond = EXERCISES.get(info.get("condition", ""), {})
        lvl = cond.get("levels", {}).get(info["level"], {})
        plan_label = f"Level {info['level']} — {lvl.get('label', '')}"

    return f"""### Clinical Assessment Summary

| Category | Detail |
|----------|--------|
| **Condition** | {condition_name} |
| **Pain Site** | {info.get('site_detail', 'N/A')} |
| **Intensity (VAS)** | {info.get('intensity_vas', info.get('pain_vas', 'N/A'))}/10 |
| **Tendency** | {info.get('tendency', 'N/A')} |
| **Characteristic** | {info.get('characteristic', 'N/A')} |
| **Duration** | {info.get('duration_months', 'N/A')} months ({'Chronic' if info.get('is_chronic') else 'Acute'}) |
| **Aggravating** | {aggravating} |
| **Reducing** | {reducing} |
| **Age** | {info.get('age', 'N/A')} |
| **Comorbidities** | {comorbidities} |
| **Surgical History** | {surgeries} |
| **Occupation** | {info.get('occupation', 'N/A')} ({info.get('physical_demands', 'N/A')} demands) |
| **Limited Activities** | {limited} |
| **Exercise History** | {info.get('exercise_history', 'N/A')} |
| **Goals** | {info.get('goals', 'N/A')} |
| **Prescription** | {plan_label} |
"""


# ── Main chat function ───────────────────────────────────────────────────────

def chat(message: str, history: list, state: dict | None):
    """Handle chat messages through multi-step assessment."""
    if not message or not message.strip():
        return history, state, "", "", "", ""

    if state is None:
        state = {"stage": "initial", "collected": {}, "conversation": ""}

    # Add user message to chat
    history = history + [{"role": "user", "content": message}]

    # Process through engine
    result, state = process_message(message, history, state)

    # Check if result is a prescription (dict) or text response (str)
    if isinstance(result, dict) and "plan" in result:
        # Prescription received — format all outputs
        explanation = result.get("explanation", "")
        patient_info = result.get("patient_info", {})
        exercises_html = _format_prescription_html(result)
        profile_md = _format_patient_profile(patient_info)

        # Add summary to chat
        bot_msg = ("**Assessment complete! Your personalized exercise plan is ready.**\n\n"
                   "Scroll down to see your prescription with video demonstrations, "
                   "clinical reasoning, and safety guidelines.\n\n"
                   "Feel free to ask any follow-up questions!")
        history = history + [{"role": "assistant", "content": bot_msg}]

        stage_html = _stage_html("prescription")

        return history, state, stage_html, profile_md, exercises_html, explanation
    else:
        # Conversational response
        bot_msg = result if isinstance(result, str) else str(result)
        history = history + [{"role": "assistant", "content": bot_msg}]

        stage_html = _stage_html(state.get("stage", "initial"))

        return history, state, stage_html, "", "", ""


def reset():
    """Reset the conversation."""
    return [], None, _stage_html("initial"), "", "", "", ""


# ── Build Gradio app ─────────────────────────────────────────────────────────

def build_app():
    with gr.Blocks(theme=THEME, css=CSS, title="PhysioGemma — AI Physiotherapy Assistant") as app:

        # Hero
        gr.HTML("""
        <div style="text-align: center; padding: 20px;
                    background: linear-gradient(135deg, #eff6ff 0%, #f0fdf4 100%);
                    border-radius: 16px; margin-bottom: 10px;">
            <h1 style="font-size: 2.2em; margin: 0; color: #1e40af;">
                &#129658; PhysioGemma
            </h1>
            <p style="font-size: 1.1em; color: #475569; margin: 8px 0 0 0;">
                AI Physiotherapy Assistant powered by <strong>Gemma 4</strong>
            </p>
            <p style="font-size: 0.85em; color: #64748b; margin: 4px 0 0 0;">
                SITCAR Pain Evaluation &bull; Evidence-Based Prescriptions &bull;
                Clinical Reasoning &bull; English &amp; Hindi
            </p>
        </div>
        """)

        # How it works
        with gr.Accordion("How does PhysioGemma work?", open=False):
            gr.Markdown("""
**PhysioGemma** conducts a **4-step clinical assessment** like a real physiotherapist:

1. **Pain Description** — Tell us about your pain in your own words
2. **SITCAR Evaluation** — We assess Site, Intensity, Tendency, Characteristic, Aggravating & Reducing factors
3. **Medical History** — Past conditions, surgeries, medications
4. **Functional Assessment** — Occupation, daily limitations, goals

Then **Gemma 4** synthesizes everything into an evidence-based exercise prescription with full clinical reasoning.

**Red Flag Detection:** PhysioGemma screens for serious warning signs (cauda equina, fractures, infections, cardiac symptoms) and advises immediate medical consultation when detected.

**8 Conditions:** Lower Back Pain, Knee OA, Neck Pain, Frozen Shoulder, Sciatica, Hip OA, Plantar Fasciitis, Tennis Elbow

**Clinical references:** Boonstra 2014, NICE NG59, ACSM, ADA, Cochrane Reviews, Canadian C-Spine Rules
            """)

        # Stage indicator
        stage_display = gr.HTML(value=_stage_html("initial"))

        # State
        state = gr.State(None)

        # Chat
        chatbot = gr.Chatbot(
            label="PhysioGemma Consultation",
            height=400,
            type="messages",
            placeholder="Describe your pain or condition to begin your assessment...",
            avatar_images=(None, "https://em-content.zobj.net/source/twitter/376/stethoscope_1fa7a.png"),
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
                "मेरी गर्दन में 2 हफ्ते से दर्द है, बहुत तेज़ दर्द है",
                "Shoulder is frozen, can't raise my arm. 55 years old, pain started 4 months ago",
                "Pain shooting down my left leg from lower back, 7/10, age 38",
                "My heel hurts every morning when I step out of bed, been 2 months",
                "Hip pain for 1 year, 65 years old, hard to walk and climb stairs",
                "Elbow pain on outer side, worse when gripping or typing, I work in IT",
            ],
            inputs=msg,
            label="Try these examples:",
        )

        # Results section (hidden until prescription)
        gr.HTML("<hr style='margin: 20px 0; border-color: #e2e8f0;'>")

        with gr.Row():
            with gr.Column(scale=1):
                profile_display = gr.Markdown(label="Clinical Assessment Summary")
            with gr.Column(scale=1):
                reasoning_display = gr.Markdown(label="Clinical Reasoning")

        exercises_display = gr.HTML(label="Exercise Prescription")

        # Wire up events
        outputs = [chatbot, state, stage_display, profile_display, exercises_display, reasoning_display]

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
            outputs=[chatbot, state, stage_display, profile_display, exercises_display, reasoning_display, msg],
        )

        # Footer
        gr.HTML("""
        <div style="text-align: center; padding: 20px; color: #94a3b8; font-size: 12px;
                    border-top: 1px solid #e2e8f0; margin-top: 30px;">
            <p><strong>PhysioGemma</strong> &mdash; Built for the Gemma 4 Good Hackathon
               (Health &amp; Sciences Track)</p>
            <p>SITCAR Assessment &bull; Gemma 4 26B &bull; Evidence-based guidelines &bull;
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
    )
