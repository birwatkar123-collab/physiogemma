"""
gemma_engine.py — Gemma 4 powered physiotherapy reasoning engine
=================================================================
Uses Google AI Studio API (free tier) with Gemma 4 for:
  1. Natural language patient intake → structured JSON extraction
  2. Evidence-based exercise level assignment
  3. Exercise prescription with clinical reasoning
  4. Multilingual patient communication (English / Hindi)

References:
  - Boonstra 2014, NICE NG59, ACSM, ADA guidelines
"""

import os
import json
import re
from google import genai

from exercises import EXERCISES, get_exercise_plan, determine_level

# ── Gemma 4 client setup ────────────────────────────────────────────────────

def get_client():
    """Get Google GenAI client with API key."""
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set. Get one free at https://aistudio.google.com/apikey")
    return genai.Client(api_key=api_key)


MODEL_ID = "gemma-4-26b-a4b-it"  # Gemma 4 26B MoE via Google AI Studio


# ── System prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are PhysioGemma, an AI physiotherapy assistant built to help patients
understand their condition and receive evidence-based exercise prescriptions.

Your role:
1. Extract clinical information from patient descriptions (condition, pain level, age, duration, comorbidities)
2. Provide evidence-based exercise prescriptions using established clinical guidelines
3. Explain the reasoning behind each prescription in simple, compassionate language
4. Communicate in the patient's preferred language (English or Hindi)

Clinical knowledge you apply:
- Boonstra 2014: VAS pain cutoffs for exercise intensity levels
- NICE NG59: Low back pain management guidelines
- ACSM: Exercise guidelines for older adults and those with comorbidities
- ADA: Comorbidity-adjusted exercise modifications
- Cochrane Reviews: Evidence for knee OA, neck pain, frozen shoulder interventions

Exercise level assignment (Boonstra 2014):
- Level 1 (VAS 7.5-10): Acute/severe - gentle mobility and pain relief
- Level 2 (VAS 5.0-7.4): Moderate - stability and gentle strengthening
- Level 3 (VAS 3.5-4.9): Mild - core/functional strengthening
- Level 4 (VAS 1.0-3.4): Low pain - advanced strengthening
- Level 5 (VAS 0-0.9): Minimal - performance and prevention

Modifiers:
- Age >= 65: drop one level (ACSM)
- Age 50-64 with 2+ comorbidities: drop one level
- 3+ comorbidities: drop one additional level (ADA)
- Chronic (>3 months) with low pain: can advance one level
- Acute with moderate pain: be more conservative (drop one level)
- Level 5 restricted to patients under 50

Supported conditions: Lower Back Pain, Knee Pain/OA, Neck Pain, Frozen Shoulder

IMPORTANT: Always provide a clinical disclaimer that this is guidance only and patients should
consult a qualified physiotherapist for proper diagnosis and treatment."""


# ── Core engine functions ────────────────────────────────────────────────────

def extract_patient_info(description: str) -> dict | None:
    """
    Use Gemma 4 to extract structured clinical parameters from natural language.
    Returns dict with condition, pain_vas, age, duration_months, comorbidities, language.
    """
    client = get_client()

    prompt = f"""Extract clinical parameters from this patient description as JSON.

Patient says: "{description}"

Rules:
- condition must be one of: LBP, KNEE_OA, NECK, FROZEN_SHOULDER
  (LBP = lower back pain, KNEE_OA = knee pain/osteoarthritis, NECK = neck pain/stiffness, FROZEN_SHOULDER = shoulder pain/frozen shoulder)
- pain_vas: pain intensity 0-10. If not mentioned, use -1.
- age: patient age in years. If not mentioned, use 40.
- duration_months: how long they've had pain in months. If "weeks" convert to fraction. If not mentioned, use 1.
- comorbidities: list of conditions like diabetes, hypertension, obesity, heart disease. Empty list if none.
- language: "hindi" if patient wrote in Hindi/Devanagari, otherwise "english"

Return ONLY a JSON object, no other text:
{{"condition": "...", "pain_vas": number, "age": number, "duration_months": number, "comorbidities": [...], "language": "..."}}"""

    response = client.models.generate_content(
        model=MODEL_ID,
        contents=prompt,
        config={"system_instruction": SYSTEM_PROMPT}
    )

    patient_info = _parse_json(response.text)

    if not patient_info or "condition" not in patient_info:
        return None

    # Validate condition
    valid_conditions = {"LBP", "KNEE_OA", "NECK", "FROZEN_SHOULDER"}
    if patient_info["condition"] not in valid_conditions:
        return None

    # Check if pain was not mentioned (need to ask)
    if patient_info.get("pain_vas", -1) < 0:
        return None

    # Set defaults
    patient_info.setdefault("age", 40)
    patient_info.setdefault("duration_months", 1)
    patient_info.setdefault("comorbidities", [])
    patient_info.setdefault("language", "english")

    # Calculate level using evidence-based logic
    is_chronic = patient_info.get("duration_months", 1) >= 3
    level = determine_level(
        pain_vas=float(patient_info["pain_vas"]),
        age=int(patient_info["age"]),
        is_chronic=is_chronic,
        comorbidity_count=len(patient_info.get("comorbidities", []))
    )
    patient_info["level"] = level
    patient_info["is_chronic"] = is_chronic

    return patient_info


def generate_prescription(patient_info: dict) -> dict:
    """Generate exercise prescription with Gemma 4 clinical reasoning."""
    plan = get_exercise_plan(patient_info["condition"], patient_info["level"])
    if "error" in plan:
        return plan

    client = get_client()
    lang = patient_info.get("language", "english")
    chronicity = "Chronic" if patient_info.get("is_chronic") else "Acute"
    comorbidities_str = ", ".join(patient_info.get("comorbidities", [])) or "None reported"
    lang_instruction = "in Hindi (Devanagari script)" if lang == "hindi" else "in English"
    exercises_json = json.dumps(
        [{"name": ex["name"], "sets": ex["sets"], "reps": ex["reps"], "type": ex["type"]} for ex in plan["exercises"]],
        indent=2
    )

    prompt = f"""Based on these clinical parameters, explain this exercise prescription to the patient.

Patient Profile:
- Condition: {plan['condition']}
- Pain Level: {patient_info['pain_vas']}/10 (VAS)
- Age: {patient_info['age']} years
- Duration: {patient_info.get('duration_months', 'unknown')} months ({chronicity})
- Comorbidities: {comorbidities_str}
- Assigned Level: {plan['level']} - {plan['label']}
- Goal: {plan['goal']}

Prescribed Exercises:
{exercises_json}

Provide your response {lang_instruction} with:
1. A warm, reassuring greeting
2. Brief explanation of their condition and why this exercise level was chosen (cite Boonstra 2014 VAS cutoffs and any applicable ACSM/ADA modifiers)
3. For each exercise: one sentence on why it helps their specific condition
4. Safety tips and when to stop
5. Encouragement and expected timeline for improvement
6. Clinical disclaimer

Keep it conversational and compassionate — this is a patient, not a medical professional."""

    response = client.models.generate_content(
        model=MODEL_ID,
        contents=prompt,
        config={"system_instruction": SYSTEM_PROMPT}
    )

    explanation = response.text if response.text else "Unable to generate explanation."

    return {
        "patient_info": patient_info,
        "plan": plan,
        "explanation": explanation,
    }


def chat_with_patient(message: str, history: list = None) -> dict:
    """
    Main entry point: patient sends a message, gets back a complete prescription.
    Handles the full flow: extract → determine level → prescribe → explain.
    """
    if history is None:
        history = []

    try:
        # Step 1: Extract patient info using Gemma 4
        patient_info = extract_patient_info(message)

        if not patient_info:
            return {
                "type": "clarification",
                "message": _get_clarification(message),
            }

        # Step 2: Generate prescription with clinical reasoning
        result = generate_prescription(patient_info)

        if "error" in result:
            return {"type": "error", "message": result["error"]}

        return {
            "type": "prescription",
            **result,
        }

    except ValueError as e:
        return {"type": "error", "message": str(e)}
    except Exception as e:
        return {"type": "error", "message": f"An error occurred: {str(e)}"}


def _parse_json(text: str) -> dict | None:
    """Extract JSON object from Gemma 4 response text."""
    if not text:
        return None
    try:
        # Try direct parse first (if response is pure JSON)
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    try:
        # Extract from markdown code block
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
    except json.JSONDecodeError:
        pass

    try:
        # Find any JSON object in the text
        match = re.search(r'\{[^{}]*"condition"[^{}]*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except json.JSONDecodeError:
        pass

    return None


def _get_clarification(message: str) -> str:
    """Generate a clarification request when we can't extract enough info."""
    try:
        client = get_client()
        prompt = f"""The patient said: "{message}"

I couldn't extract enough clinical information to create an exercise plan. Ask them a friendly follow-up question to get:
1. Where is the pain? (lower back, knee, neck, or shoulder)
2. How bad is the pain on a scale of 0-10?
3. Their age
4. How long they've had the pain

Keep it warm, short, and conversational. One short paragraph."""

        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config={"system_instruction": SYSTEM_PROMPT}
        )
        return response.text
    except Exception:
        return ("I'd love to help you with your exercise plan! Could you tell me:\n"
                "1. Where is your pain? (lower back, knee, neck, or shoulder)\n"
                "2. How bad is the pain from 0-10?\n"
                "3. Your age\n"
                "4. How long you've had this pain?\n\n"
                "For example: 'My lower back has been hurting for 2 months, pain is 6/10, I'm 45 years old'")
