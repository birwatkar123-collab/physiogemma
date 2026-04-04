"""
gemma_engine.py — Gemma 4 powered physiotherapy reasoning engine (v2)
======================================================================
Multi-step clinical assessment using SITCAR pain evaluation framework:
  S = Site of pain
  I = Intensity of pain (VAS 0-10)
  T = Tendency (getting worse / stable / improving)
  C = Characteristic (sharp / dull / burning / aching / throbbing / shooting)
  A = Aggravating factors
  R = Reducing factors

Plus: medical/surgical history, functional assessment, occupation.

Uses Google AI Studio API (free tier) with Gemma 4 for:
  1. Guided multi-turn clinical conversation
  2. SITCAR pain evaluation extraction
  3. Evidence-based exercise prescription with clinical reasoning
  4. Multilingual patient communication (English / Hindi)
"""

import os
import json
import re
from google import genai

from exercises import EXERCISES, get_exercise_plan, determine_level
from red_flags import check_red_flags, format_red_flag_warning

# ── Gemma 4 client setup ────────────────────────────────────────────────────

def get_client():
    """Get Google GenAI client with API key."""
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY environment variable not set. "
            "Get one free at https://aistudio.google.com/apikey"
        )
    return genai.Client(api_key=api_key)


MODEL_ID = "gemma-4-26b-a4b-it"

# ── Assessment stages ────────────────────────────────────────────────────────

STAGES = [
    "initial",        # Patient's first message
    "sitcar",         # SITCAR pain evaluation follow-up
    "medical_history", # Past medical/surgical history
    "functional",     # Functional & occupation assessment
    "prescription",   # Final prescription
]

# ── System prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are PhysioGemma, an AI physiotherapy assistant that conducts thorough
clinical assessments before prescribing exercises. You behave like a real physiotherapist
conducting a first consultation.

You follow the SITCAR framework for pain evaluation:
  S = Site (exact location, radiation pattern)
  I = Intensity (VAS 0-10)
  T = Tendency (getting worse, stable, or improving over time)
  C = Characteristic (sharp, dull, burning, aching, throbbing, shooting, stiffness)
  A = Aggravating factors (what makes pain worse)
  R = Reducing factors (what helps relieve pain)

You also gather:
  - Past medical history (chronic conditions, medications)
  - Surgical history (especially musculoskeletal surgeries)
  - Functional limitations (daily activities affected)
  - Occupation and physical demands
  - Previous physiotherapy or exercise experience

Clinical evidence you apply:
  - Boonstra 2014: VAS cutoffs for exercise intensity levels
  - NICE NG59: Low back pain management
  - ACSM: Age-adjusted exercise guidelines
  - ADA: Comorbidity-adjusted modifications
  - Cochrane Reviews: Knee OA, neck pain, frozen shoulder

IMPORTANT RULES:
1. Ask questions conversationally, like a caring physiotherapist
2. Ask 3-4 questions at a time, not all at once
3. Adapt your language to match the patient (Hindi if they write in Hindi)
4. Never diagnose - you provide exercise guidance only
5. Always include clinical disclaimer in final prescription
6. If patient mentions red flags (sudden weakness, bladder issues, unexplained weight loss,
   fever with pain, trauma), advise immediate medical consultation."""


# ── Extraction prompts for each stage ────────────────────────────────────────

INITIAL_EXTRACTION_PROMPT = """Analyze this patient's first message and extract what you can.

Patient says: "{message}"

Return ONLY a JSON object with these fields (use null for anything not mentioned):
{{
  "condition": "LBP or KNEE_OA or NECK or FROZEN_SHOULDER or SCIATICA or HIP_OA or PLANTAR_FASCIITIS or TENNIS_ELBOW or null",
  "pain_site_detail": "specific location description or null",
  "pain_vas": number or null,
  "age": number or null,
  "duration_months": number or null,
  "language": "hindi" or "english",
  "red_flags": ["list of any red flag symptoms"] or []
}}

Condition mapping:
- lower back / lumbar / back pain = LBP
- knee / osteoarthritis / joint stiffness in knee = KNEE_OA
- neck / cervical / stiff neck = NECK
- shoulder / frozen shoulder / shoulder stiffness = FROZEN_SHOULDER
- sciatica / leg pain from back / radiating leg pain / shooting down leg = SCIATICA
- hip / hip joint / groin pain / hip arthritis = HIP_OA
- heel pain / plantar fasciitis / foot pain bottom / sole pain = PLANTAR_FASCIITIS
- elbow pain / tennis elbow / lateral epicondylitis / outer elbow = TENNIS_ELBOW"""


SITCAR_EXTRACTION_PROMPT = """Extract SITCAR pain evaluation details from the conversation.

Conversation so far:
{conversation}

Return ONLY a JSON object:
{{
  "site_detail": "exact pain location and radiation pattern",
  "intensity_vas": number (0-10),
  "tendency": "worsening" or "stable" or "improving",
  "characteristic": "sharp" or "dull" or "burning" or "aching" or "throbbing" or "shooting" or "stiffness" or "mixed",
  "aggravating_factors": ["list of things that make pain worse"],
  "reducing_factors": ["list of things that help"],
  "duration_months": number,
  "is_constant": true or false
}}

Use null for any field not yet discussed."""


MEDICAL_EXTRACTION_PROMPT = """Extract medical and surgical history from the conversation.

Conversation so far:
{conversation}

Return ONLY a JSON object:
{{
  "age": number,
  "comorbidities": ["list: diabetes, hypertension, heart disease, obesity, etc."],
  "surgical_history": ["list of past surgeries, especially musculoskeletal"],
  "medications": ["current medications"],
  "previous_physio": true or false or null,
  "allergies": ["list"] or []
}}

Use null for any field not discussed."""


FUNCTIONAL_EXTRACTION_PROMPT = """Extract functional assessment from the conversation.

Conversation so far:
{conversation}

Return ONLY a JSON object:
{{
  "occupation": "description of job/daily role",
  "physical_demands": "sedentary" or "light" or "moderate" or "heavy",
  "limited_activities": ["list of activities affected by pain"],
  "exercise_history": "none" or "occasional" or "regular" or "athletic",
  "goals": "what the patient wants to achieve"
}}

Use null for any field not discussed."""


# ── Stage question generators ────────────────────────────────────────────────

def _generate_sitcar_questions(initial_info: dict) -> str:
    """Generate SITCAR follow-up questions based on initial info."""
    client = get_client()
    known = json.dumps(initial_info, indent=2)

    prompt = f"""Based on this initial information from the patient:
{known}

Generate SITCAR follow-up questions. Ask about the parameters we DON'T have yet from:
S - Site: Exact location? Does pain radiate anywhere?
I - Intensity: Pain level 0-10? (skip if already known)
T - Tendency: Is pain getting worse, staying same, or improving over time?
C - Characteristic: Is the pain sharp, dull, burning, aching, shooting?
A - Aggravating: What activities or positions make it worse?
R - Reducing: What helps? Rest, heat, ice, medication, position?

Also ask about duration if not known.

Rules:
- Ask 3-4 questions maximum (skip what we already know)
- Be warm and conversational like a real physiotherapist
- Match the patient's language ({initial_info.get('language', 'english')})
- Number each question for clarity
- Start with a brief acknowledgment of their pain"""

    response = client.models.generate_content(
        model=MODEL_ID, contents=prompt,
        config={"system_instruction": SYSTEM_PROMPT}
    )
    return response.text


def _generate_medical_questions(collected: dict) -> str:
    """Generate medical history questions."""
    client = get_client()
    lang = collected.get("language", "english")

    prompt = f"""Now ask the patient about their medical and surgical history.
We already know about their pain from SITCAR evaluation.

Ask about (3-4 questions max):
1. Age (if not already known)
2. Any chronic conditions (diabetes, blood pressure, heart problems, thyroid, etc.)
3. Any past surgeries (especially related to spine, joints, or muscles)
4. Current medications they take regularly

Language: {'Hindi (Devanagari)' if lang == 'hindi' else 'English'}
Be warm, reassuring. Explain why you're asking (to ensure safe exercises)."""

    response = client.models.generate_content(
        model=MODEL_ID, contents=prompt,
        config={"system_instruction": SYSTEM_PROMPT}
    )
    return response.text


def _generate_functional_questions(collected: dict) -> str:
    """Generate functional assessment questions."""
    client = get_client()
    lang = collected.get("language", "english")
    condition = collected.get("condition", "pain")

    prompt = f"""Final assessment step. Ask the patient about their daily function and goals.
Their condition: {condition}

Ask about (3-4 questions max):
1. What is their occupation / daily routine? (desk job, manual work, homemaker, retired)
2. Which daily activities are most affected by the pain?
3. Do they currently exercise or have they done physiotherapy before?
4. What is their main goal? (pain relief, return to work, return to sport, daily function)

Language: {'Hindi (Devanagari)' if lang == 'hindi' else 'English'}
Almost done — be encouraging. Tell them you have almost all the information needed."""

    response = client.models.generate_content(
        model=MODEL_ID, contents=prompt,
        config={"system_instruction": SYSTEM_PROMPT}
    )
    return response.text


# ── Prescription generator with full clinical context ────────────────────────

def _generate_full_prescription(collected: dict) -> dict:
    """Generate prescription using all collected clinical data."""

    # Determine exercise level
    pain_vas = collected.get("intensity_vas") or collected.get("pain_vas") or 5.0
    age = collected.get("age") or 40
    duration = collected.get("duration_months") or 1
    is_chronic = duration >= 3
    comorbidities = collected.get("comorbidities") or []
    surgical_history = collected.get("surgical_history") or []
    tendency = collected.get("tendency", "stable")
    characteristic = collected.get("characteristic", "aching")
    condition = collected.get("condition", "LBP")

    # Base level from Boonstra
    level = determine_level(
        pain_vas=float(pain_vas),
        age=int(age),
        is_chronic=is_chronic,
        comorbidity_count=len(comorbidities)
    )

    # Additional modifiers from SITCAR
    # Worsening tendency: be more conservative
    if tendency == "worsening":
        level = max(level - 1, 1)

    # Sharp/shooting pain: be more conservative (possible nerve involvement)
    if characteristic in ("sharp", "shooting"):
        level = max(level - 1, 1)

    # Relevant surgical history: be more conservative
    spine_surgery = any(
        kw in s.lower() for s in surgical_history
        for kw in ["spine", "disc", "laminectomy", "fusion", "back", "knee replacement",
                    "shoulder", "rotator", "acl", "meniscus"]
    )
    if spine_surgery:
        level = max(level - 1, 1)

    # Get exercise plan
    plan = get_exercise_plan(condition, level)
    if "error" in plan:
        return {"error": plan["error"]}

    # Build comprehensive context for Gemma 4 reasoning
    client = get_client()
    lang = collected.get("language", "english")
    lang_instruction = "in Hindi (Devanagari script)" if lang == "hindi" else "in English"

    exercises_json = json.dumps(
        [{"name": ex["name"], "sets": ex["sets"], "reps": ex["reps"],
          "type": ex["type"], "instruction": ex.get("instruction", "")}
         for ex in plan["exercises"]],
        indent=2
    )

    aggravating = ", ".join(collected.get("aggravating_factors", [])) or "Not specified"
    reducing = ", ".join(collected.get("reducing_factors", [])) or "Not specified"
    limited = ", ".join(collected.get("limited_activities", [])) or "Not specified"
    surgeries = ", ".join(surgical_history) or "None"
    meds = ", ".join(collected.get("medications", [])) or "None"
    comorbidities_str = ", ".join(comorbidities) or "None"
    chronicity = "Chronic" if is_chronic else "Acute"
    occupation = collected.get("occupation", "Not specified")
    physical_demands = collected.get("physical_demands", "unknown")
    exercise_history = collected.get("exercise_history", "unknown")
    goals = collected.get("goals", "Pain relief and improved function")

    prompt = f"""You completed a full physiotherapy assessment. Now provide the prescription and clinical reasoning.

=== COMPLETE CLINICAL PROFILE ===

SITCAR Pain Evaluation:
- Site: {collected.get('site_detail', condition)} ({plan['condition']})
- Intensity: {pain_vas}/10 (VAS)
- Tendency: {tendency}
- Characteristic: {characteristic}
- Aggravating factors: {aggravating}
- Reducing factors: {reducing}
- Duration: {duration} months ({chronicity})
- Constant: {collected.get('is_constant', 'unknown')}

Medical History:
- Age: {age} years
- Comorbidities: {comorbidities_str}
- Surgical history: {surgeries}
- Medications: {meds}
- Previous physiotherapy: {collected.get('previous_physio', 'unknown')}

Functional Assessment:
- Occupation: {occupation} ({physical_demands} demands)
- Limited activities: {limited}
- Exercise history: {exercise_history}
- Patient goals: {goals}

=== PRESCRIPTION ===
- Level: {level} — {plan['label']}
- Goal: {plan['goal']}
- Exercises:
{exercises_json}

=== MODIFIERS APPLIED ===
- Boonstra 2014 VAS cutoff: VAS {pain_vas} -> base level
- Age modifier (ACSM): {'Applied (-1)' if age >= 65 else 'Not needed'}
- Comorbidity modifier (ADA): {'Applied (-1)' if len(comorbidities) >= 3 else ('Applied (-1) age 50-64 with 2+ comorbidities' if age >= 50 and len(comorbidities) >= 2 else 'Not needed')}
- Tendency modifier: {'Applied (-1) - pain worsening' if tendency == 'worsening' else 'Not needed'}
- Pain character modifier: {'Applied (-1) - sharp/shooting suggests neural involvement' if characteristic in ('sharp', 'shooting') else 'Not needed'}
- Surgical history modifier: {'Applied (-1) - post-surgical caution' if spine_surgery else 'Not needed'}
- Chronicity modifier: {'Applied (+1) - chronic with lower pain can progress' if is_chronic and pain_vas < 5 else 'Not needed'}

Provide your response {lang_instruction} with:

1. **Summary of findings** from the assessment (2-3 sentences)
2. **Clinical reasoning** — explain WHY this exercise level was chosen, citing each modifier applied
3. **For each exercise**: one line on why it specifically helps this patient's profile
4. **Safety precautions** tailored to their specific profile:
   - Based on surgical history: what to avoid
   - Based on aggravating factors: modifications
   - Based on medications/comorbidities: monitoring needed
   - Based on pain characteristic: warning signs
5. **Activity modifications** for their occupation and daily tasks
6. **Progression criteria** — when they can move to the next level
7. **Home advice** based on reducing factors
8. **Encouragement** with realistic timeline
9. **When to seek immediate help** (red flags)
10. **Clinical disclaimer**

Be thorough but compassionate. This should read like a professional physiotherapy report written for the patient."""

    response = client.models.generate_content(
        model=MODEL_ID, contents=prompt,
        config={"system_instruction": SYSTEM_PROMPT}
    )

    explanation = response.text if response.text else "Unable to generate explanation."

    collected["level"] = level
    collected["is_chronic"] = is_chronic

    return {
        "patient_info": collected,
        "plan": plan,
        "explanation": explanation,
        "modifiers_applied": {
            "boonstra_vas": f"VAS {pain_vas}",
            "age_acsm": age >= 65,
            "comorbidity_ada": len(comorbidities) >= 3 or (age >= 50 and len(comorbidities) >= 2),
            "tendency_worsening": tendency == "worsening",
            "sharp_shooting": characteristic in ("sharp", "shooting"),
            "post_surgical": spine_surgery,
        }
    }


# ── Main multi-step chat function ────────────────────────────────────────────

def process_message(message: str, history: list, state: dict) -> tuple:
    """
    Process a message in the multi-step assessment flow.
    Returns: (bot_response, updated_state)

    State tracks:
      - stage: current assessment stage
      - collected: all extracted clinical data
      - conversation: full conversation text
    """
    if not state:
        state = {"stage": "initial", "collected": {}, "conversation": ""}

    stage = state["stage"]
    state["conversation"] += f"\nPatient: {message}\n"

    try:
        client = get_client()

        # ── STAGE: Initial ───────────────────────────────────────────────
        if stage == "initial":
            # Extract what we can from first message
            prompt = INITIAL_EXTRACTION_PROMPT.format(message=message)
            response = client.models.generate_content(
                model=MODEL_ID, contents=prompt,
                config={"system_instruction": SYSTEM_PROMPT}
            )
            initial_info = _parse_json(response.text) or {}
            state["collected"].update({k: v for k, v in initial_info.items() if v is not None})

            # Check for red flags using comprehensive detection engine
            condition = state["collected"].get("condition")
            detected_flags = check_red_flags(message, condition)

            # Also check any LLM-detected red flags
            llm_flags = initial_info.get("red_flags", [])
            if llm_flags:
                # Run LLM-detected flag text through our engine too
                for flag_text in llm_flags:
                    extra_flags = check_red_flags(flag_text, condition)
                    detected_flags.extend(extra_flags)

            if detected_flags:
                warning = format_red_flag_warning(detected_flags)
                state["red_flags_detected"] = detected_flags
                state["stage"] = "initial"  # Don't proceed to exercises
                return warning, state

            # Check if we have enough to identify condition
            if not state["collected"].get("condition"):
                # Ask for basic info
                bot_reply = _generate_initial_clarification(message, initial_info.get("language", "english"))
                state["conversation"] += f"PhysioGemma: {bot_reply}\n"
                return bot_reply, state

            # Move to SITCAR
            state["stage"] = "sitcar"
            bot_reply = _generate_sitcar_questions(state["collected"])
            state["conversation"] += f"PhysioGemma: {bot_reply}\n"
            return bot_reply, state

        # ── STAGE: SITCAR ────────────────────────────────────────────────
        elif stage == "sitcar":
            # Red flag check on every message
            condition = state["collected"].get("condition")
            detected_flags = check_red_flags(message, condition)
            if detected_flags:
                warning = format_red_flag_warning(detected_flags)
                state["red_flags_detected"] = detected_flags
                return warning, state

            prompt = SITCAR_EXTRACTION_PROMPT.format(conversation=state["conversation"])
            response = client.models.generate_content(
                model=MODEL_ID, contents=prompt,
                config={"system_instruction": SYSTEM_PROMPT}
            )
            sitcar_info = _parse_json(response.text) or {}
            state["collected"].update({k: v for k, v in sitcar_info.items() if v is not None})

            # Move to medical history
            state["stage"] = "medical_history"
            bot_reply = _generate_medical_questions(state["collected"])
            state["conversation"] += f"PhysioGemma: {bot_reply}\n"
            return bot_reply, state

        # ── STAGE: Medical History ───────────────────────────────────────
        elif stage == "medical_history":
            # Red flag check (cancer history, etc.)
            detected_flags = check_red_flags(message, state["collected"].get("condition"))
            if detected_flags:
                warning = format_red_flag_warning(detected_flags)
                state["red_flags_detected"] = detected_flags
                return warning, state

            prompt = MEDICAL_EXTRACTION_PROMPT.format(conversation=state["conversation"])
            response = client.models.generate_content(
                model=MODEL_ID, contents=prompt,
                config={"system_instruction": SYSTEM_PROMPT}
            )
            med_info = _parse_json(response.text) or {}
            state["collected"].update({k: v for k, v in med_info.items() if v is not None})

            # Move to functional assessment
            state["stage"] = "functional"
            bot_reply = _generate_functional_questions(state["collected"])
            state["conversation"] += f"PhysioGemma: {bot_reply}\n"
            return bot_reply, state

        # ── STAGE: Functional Assessment ─────────────────────────────────
        elif stage == "functional":
            prompt = FUNCTIONAL_EXTRACTION_PROMPT.format(conversation=state["conversation"])
            response = client.models.generate_content(
                model=MODEL_ID, contents=prompt,
                config={"system_instruction": SYSTEM_PROMPT}
            )
            func_info = _parse_json(response.text) or {}
            state["collected"].update({k: v for k, v in func_info.items() if v is not None})

            # Generate full prescription
            state["stage"] = "prescription"
            result = _generate_full_prescription(state["collected"])

            if "error" in result:
                return f"**Error:** {result['error']}", state

            state["result"] = result
            return result, state

        # ── STAGE: Prescription (follow-up questions) ────────────────────
        elif stage == "prescription":
            # Patient asking follow-up after getting prescription
            context = state["conversation"]
            prompt = f"""The patient received their exercise prescription and is asking a follow-up question.

Conversation context:
{context}

Patient asks: "{message}"

Answer their question helpfully based on the prescription and clinical assessment.
Be specific to their condition and profile. Keep the clinical disclaimer."""

            response = client.models.generate_content(
                model=MODEL_ID, contents=prompt,
                config={"system_instruction": SYSTEM_PROMPT}
            )
            bot_reply = response.text
            state["conversation"] += f"PhysioGemma: {bot_reply}\n"
            return bot_reply, state

    except ValueError as e:
        return str(e), state
    except Exception as e:
        return f"An error occurred: {str(e)}", state


def _generate_initial_clarification(message: str, language: str) -> str:
    """When we can't identify the condition from the first message."""
    try:
        client = get_client()
        lang_inst = "in Hindi (Devanagari)" if language == "hindi" else "in English"

        prompt = f"""The patient said: "{message}"

I couldn't identify their specific condition. As a physiotherapist, greet them warmly and ask:
1. Where exactly is the pain? (lower back, knee, neck, or shoulder)
2. How long have they had this pain?
3. How would they rate the pain from 0 to 10?

Respond {lang_inst}. Be warm and professional. Keep it to one short paragraph + 3 numbered questions."""

        response = client.models.generate_content(
            model=MODEL_ID, contents=prompt,
            config={"system_instruction": SYSTEM_PROMPT}
        )
        return response.text
    except Exception:
        return ("Welcome! I'm PhysioGemma, your AI physiotherapy assistant. "
                "To create the best exercise plan for you, I need to understand your condition.\n\n"
                "Could you please tell me:\n"
                "1. Where is your pain? (lower back, knee, neck, or shoulder)\n"
                "2. How long have you had this pain?\n"
                "3. How would you rate your pain from 0-10?")


# ── JSON parser ──────────────────────────────────────────────────────────────

def _parse_json(text: str) -> dict | None:
    """Extract JSON object from Gemma 4 response text."""
    if not text:
        return None
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    try:
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
    except json.JSONDecodeError:
        pass
    try:
        # Find the largest JSON object in text
        matches = re.findall(r'\{[^{}]*\}', text, re.DOTALL)
        for m in reversed(matches):  # try largest first
            try:
                parsed = json.loads(m)
                if isinstance(parsed, dict) and len(parsed) > 1:
                    return parsed
            except json.JSONDecodeError:
                continue
    except Exception:
        pass
    return None
