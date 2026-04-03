"""
PhysioGemma — AI Physiotherapy Assistant powered by Gemma 4
============================================================
Kaggle Gemma 4 Good Hackathon | Health & Sciences Track

Natural language patient intake → Evidence-based exercise prescription
with clinical reasoning, YouTube video demos, and multilingual support.

Run: python app.py
Demo: https://huggingface.co/spaces/YOUR_USERNAME/physiogemma
"""

import os
import gradio as gr
from gemma_engine import chat_with_patient
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
.patient-info-card {
    background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
    border: 1px solid #86efac;
    border-radius: 12px;
    padding: 16px;
    margin: 10px 0;
}
.disclaimer {
    background: #fffbeb;
    border: 1px solid #fde68a;
    border-radius: 8px;
    padding: 12px;
    margin-top: 16px;
    font-size: 13px;
    color: #92400e;
}
.hero-section {
    text-align: center;
    padding: 20px;
    background: linear-gradient(135deg, #eff6ff 0%, #f0fdf4 100%);
    border-radius: 16px;
    margin-bottom: 20px;
}
.video-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 12px;
    margin-top: 10px;
}
footer { display: none !important; }
"""


# ── Helper: format prescription as Markdown + HTML ───────────────────────────

def format_prescription(result: dict) -> tuple:
    """Format the prescription result into display components."""
    if result["type"] == "clarification":
        return result["message"], "", "", ""

    if result["type"] == "error":
        return f"**Error:** {result['message']}", "", "", ""

    info = result["patient_info"]
    plan = result["plan"]
    explanation = result["explanation"]

    # Patient info card
    condition_name = EXERCISES.get(info["condition"], {}).get("name", info["condition"])
    comorbidities = ", ".join(info.get("comorbidities", [])) or "None reported"
    chronicity = "Chronic (3+ months)" if info.get("is_chronic") else "Acute (< 3 months)"

    info_md = f"""### Patient Profile
| Parameter | Value |
|-----------|-------|
| **Condition** | {condition_name} |
| **Pain Level** | {info['pain_vas']}/10 (VAS) |
| **Age** | {info['age']} years |
| **Duration** | {info.get('duration_months', 'N/A')} months ({chronicity}) |
| **Comorbidities** | {comorbidities} |
| **Exercise Level** | Level {info['level']} — {plan['label']} |
| **Goal** | {plan['goal']} |
"""

    # Exercise cards with video embeds
    exercises_html = ""
    for ex in plan["exercises"]:
        video_id = ex.get("video", "")
        video_embed = ""
        if video_id:
            video_embed = f"""<iframe width="100%" height="200"
                src="https://www.youtube-nocookie.com/embed/{video_id}"
                frameborder="0" allowfullscreen
                style="border-radius: 8px; margin-top: 8px;"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture">
            </iframe>"""

        type_icons = {
            "mobility": "🔄", "stretching": "🧘", "strengthening": "💪",
            "stability": "⚖️", "plyometric": "🏃"
        }
        icon = type_icons.get(ex.get("type", ""), "🏋️")

        exercises_html += f"""
        <div class="exercise-card">
            <h4>{icon} {ex['name']}</h4>
            <p><strong>Sets:</strong> {ex['sets']} | <strong>Reps:</strong> {ex['reps']} | <strong>Type:</strong> {ex.get('type', 'general').title()}</p>
            <p>{ex.get('instruction', '')}</p>
            {video_embed}
        </div>
        """

    # Clinical reasoning from Gemma 4
    reasoning_md = f"""### Clinical Reasoning (Gemma 4)

{explanation}

<div class="disclaimer">
<strong>Disclaimer:</strong> This is AI-generated exercise guidance based on clinical guidelines (NICE NG59, ACSM, Boonstra 2014).
It does not replace professional medical advice. Always consult a qualified physiotherapist for proper diagnosis and treatment.
</div>
"""

    return info_md, exercises_html, reasoning_md, ""


# ── Main processing function ─────────────────────────────────────────────────

def process_input(message: str, history: list) -> tuple:
    """Process patient message and return formatted prescription."""
    if not message or not message.strip():
        return "", "", "", "Please describe your pain or condition."

    result = chat_with_patient(message)

    if result["type"] == "clarification":
        return "", "", "", result["message"]

    if result["type"] == "error":
        return "", "", "", f"**Error:** {result['message']}"

    info_md, exercises_html, reasoning_md, _ = format_prescription(result)
    return info_md, exercises_html, reasoning_md, ""


# ── Example inputs ───────────────────────────────────────────────────────────

EXAMPLES = [
    "My lower back has been hurting for 3 months. Pain is about 6 out of 10. I'm 45 years old.",
    "I'm 62 years old with knee pain and diabetes. It's been bothering me for 6 months. Pain is 7/10.",
    "मेरी गर्दन में 2 हफ्ते से दर्द है, दर्द 5/10 है, उम्र 35 साल",
    "I'm 28, my shoulder has been frozen for 4 months. Pain is about 8 out of 10. Very stiff.",
    "Neck pain for 1 week, pain level 4, age 50, I have hypertension and high cholesterol",
    "मेरे घुटने में दर्द है, 55 साल, दर्द 6/10, diabetes और BP है, 1 साल से है",
]


# ── Gradio UI ────────────────────────────────────────────────────────────────

def build_app():
    with gr.Blocks(theme=THEME, css=CSS, title="PhysioGemma — AI Physiotherapy Assistant") as app:

        # Hero
        gr.HTML("""
        <div class="hero-section">
            <h1 style="font-size: 2.2em; margin: 0; color: #1e40af;">🩺 PhysioGemma</h1>
            <p style="font-size: 1.1em; color: #475569; margin: 8px 0 0 0;">
                AI Physiotherapy Assistant powered by <strong>Gemma 4</strong>
            </p>
            <p style="font-size: 0.9em; color: #64748b; margin: 4px 0 0 0;">
                Evidence-based exercise prescriptions • Clinical reasoning • English & Hindi
            </p>
        </div>
        """)

        # How it works
        with gr.Accordion("How does PhysioGemma work?", open=False):
            gr.Markdown("""
**PhysioGemma** uses Google's **Gemma 4** open model with native function calling to:

1. **Understand** your pain description in natural language (English or Hindi)
2. **Extract** clinical parameters (condition, pain level, age, duration, comorbidities)
3. **Determine** the right exercise level using evidence-based cutoffs (Boonstra 2014, ACSM, ADA)
4. **Prescribe** a personalized exercise plan with video demonstrations
5. **Explain** the clinical reasoning behind every recommendation

**Supported conditions:** Lower Back Pain, Knee Pain/OA, Neck Pain, Frozen Shoulder

**Clinical references:** NICE NG59, Cochrane Reviews, ACSM Guidelines, Boonstra 2014 VAS cutoffs
            """)

        # Input section
        with gr.Row():
            with gr.Column(scale=3):
                user_input = gr.Textbox(
                    label="Describe your pain or condition",
                    placeholder="Example: My lower back has been hurting for 3 months. Pain is 6/10. I'm 45 years old with diabetes.",
                    lines=3,
                    max_lines=5,
                )
            with gr.Column(scale=1):
                submit_btn = gr.Button("Get Exercise Plan 🏋️", variant="primary", size="lg")

        # Examples
        gr.Examples(
            examples=EXAMPLES,
            inputs=user_input,
            label="Try these examples (click to load):",
        )

        # Status/clarification
        status_output = gr.Markdown(label="Status", visible=True)

        # Results
        with gr.Row():
            with gr.Column(scale=1):
                patient_info = gr.Markdown(label="Patient Profile")
            with gr.Column(scale=1):
                clinical_reasoning = gr.Markdown(label="Clinical Reasoning")

        exercises_display = gr.HTML(label="Exercise Prescription")

        # Wire up
        submit_btn.click(
            fn=process_input,
            inputs=[user_input, gr.State([])],
            outputs=[patient_info, exercises_display, clinical_reasoning, status_output],
        )
        user_input.submit(
            fn=process_input,
            inputs=[user_input, gr.State([])],
            outputs=[patient_info, exercises_display, clinical_reasoning, status_output],
        )

        # Footer
        gr.HTML("""
        <div style="text-align: center; padding: 20px; color: #94a3b8; font-size: 12px; border-top: 1px solid #e2e8f0; margin-top: 30px;">
            <p><strong>PhysioGemma</strong> — Built for the Gemma 4 Good Hackathon (Health & Sciences Track)</p>
            <p>Powered by Gemma 4 26B • Evidence-based clinical guidelines • Not medical advice</p>
            <p>Created by Gaurav Birwatkar • CC-BY 4.0 License</p>
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
