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

from exercises import (EXERCISES, get_exercise_plan, determine_level, apply_modifiers,
                       apply_bmi_modifiers, calculate_bmi, OCCUPATION_ADDONS, AGGRAVATION_MODIFIERS)
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

=== YOUR HYBRID ARCHITECTURE ===
You work within a hybrid system where:
- A RULE ENGINE handles: exercise level assignment (Boonstra VAS cutoffs), red flag detection,
  occupation/aggravation modifiers, and safety constraints. These are deterministic and evidence-based.
- YOU (Gemma 4) handle: conversational assessment, clinical reasoning, exercise adaptation
  explanations, patient education, progression guidance, and empathetic communication.

Your job is NOT to pick exercise levels — the rule engine does that correctly every time.
Your job IS to:
1. Conduct a thorough, empathetic clinical interview
2. Extract precise clinical parameters through conversation
3. Explain WHY the chosen exercises and level are right for THIS specific patient
4. Provide intelligent adaptations, warnings, and encouragement
5. Answer follow-up questions with clinical depth

=== SITCAR FRAMEWORK ===
  S = Site (exact location, radiation pattern, bilateral/unilateral)
  I = Intensity (VAS 0-10, at rest vs. during activity)
  T = Tendency (getting worse, stable, or improving — and over what timeframe)
  C = Characteristic (sharp, dull, burning, aching, throbbing, shooting, stiffness, mixed)
  A = Aggravating factors (specific activities, positions, times of day)
  R = Reducing factors (rest, heat, ice, medication, positions, activity)

=== CONDITION-SPECIFIC KNOWLEDGE ===
Use this to ask smarter questions for each condition:
- LBP: Ask about leg radiation (sciatica screen), morning stiffness vs activity pain, sitting tolerance
- KNEE_OA: Ask about morning stiffness duration (<30min = OA), crepitus, stair difficulty, locking
- NECK: Ask about arm radiation (radiculopathy screen), headaches, dizziness, hand numbness
- FROZEN_SHOULDER: Ask about active vs passive range, night pain, which movements lost first
- SCIATICA: Ask about distribution (L4/L5/S1 dermatome), cough/sneeze aggravation, foot weakness
- HIP_OA: Ask about groin vs lateral pain, morning stiffness, walking distance limitation
- PLANTAR_FASCIITIS: Ask about first-step morning pain, prolonged standing, footwear
- TENNIS_ELBOW: Ask about grip weakness, specific aggravating grips, work/sport triggers

=== CLINICAL EVIDENCE ===
  - Boonstra 2014: VAS cutoffs for exercise intensity levels
  - NICE NG59: Low back pain management
  - ACSM: Age-adjusted exercise guidelines, workplace ergonomics
  - ADA: Comorbidity-adjusted modifications
  - Cochrane Reviews: Knee OA, neck pain, frozen shoulder
  - McKenzie Method: Directional preference for spinal pain
  - Canadian C-Spine Rules: Neck injury screening

=== RULES ===
1. Ask questions conversationally, like a caring physiotherapist who genuinely listens
2. Ask 3-4 questions at a time, not all at once — and acknowledge their previous answers first
3. Adapt your language to match the patient (Hindi if they write in Hindi, simple if they seem anxious)
4. Never diagnose — you provide exercise guidance only
5. Always include clinical disclaimer in final prescription
6. If patient mentions red flags, advise immediate medical consultation
7. When explaining exercises, relate them to the patient's specific daily activities and goals
8. Use analogies patients can understand (e.g., "core muscles are like a corset supporting your spine")
9. Acknowledge pain and frustration — patients need to feel heard before they trust your plan"""


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
  "height_cm": number or null,
  "weight_kg": number or null,
  "comorbidities": ["list: diabetes, hypertension, heart disease, obesity, etc."],
  "surgical_history": ["list of past surgeries, especially musculoskeletal"],
  "medications": ["current medications"],
  "previous_physio": true or false or null,
  "allergies": ["list"] or []
}}

Height/weight conversion rules:
- If height given in feet/inches, convert to cm (e.g., 5'6" = 167.6 cm, 5 feet 10 = 177.8 cm)
- If weight given in pounds/lbs, convert to kg (divide by 2.205)
- If height given in meters, convert to cm (multiply by 100)
- Round to nearest whole number

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

CONDITION_SPECIFIC_PROBES = {
    "LBP": "Also screen: Does pain go down into the leg? Is it worse in the morning or after activity? How long can you sit comfortably?",
    "KNEE_OA": "Also screen: How long is morning stiffness? (<30min suggests OA). Any grinding/crepitus? Difficulty with stairs? Any locking or giving way?",
    "NECK": "Also screen: Does pain go into the arm or hand? Any headaches or dizziness? Numbness or tingling in fingers?",
    "FROZEN_SHOULDER": "Also screen: Can someone else move your arm further than you can? Does it wake you at night? Which movement did you lose first — reaching up, behind back, or to the side?",
    "SCIATICA": "Also screen: Where exactly does the leg pain go (back of thigh, calf, foot)? Does coughing or sneezing make it worse? Any weakness in foot or toes?",
    "HIP_OA": "Also screen: Is the pain in the groin or on the outside of the hip? How far can you walk before needing to stop? Morning stiffness duration?",
    "PLANTAR_FASCIITIS": "Also screen: Is the first step in the morning the worst? Does it ease after walking for a few minutes? What footwear do you usually wear?",
    "TENNIS_ELBOW": "Also screen: Is grip strength affected? Which grips hurt most (turning doorknob, lifting cup, wringing)? Related to work, sport, or both?",
}


def _generate_sitcar_questions(initial_info: dict) -> str:
    """Generate SITCAR follow-up questions based on initial info."""
    client = get_client()
    known = json.dumps(initial_info, indent=2)
    condition = initial_info.get("condition", "")
    condition_probe = CONDITION_SPECIFIC_PROBES.get(condition, "")

    prompt = f"""Based on this initial information from the patient:
{known}

Generate SITCAR follow-up questions. Ask about the parameters we DON'T have yet from:
S - Site: Exact location? Does pain radiate anywhere?
I - Intensity: Pain level 0-10 at rest AND during aggravating activity? (skip if already known)
T - Tendency: Is pain getting worse, staying same, or improving? Over what timeframe?
C - Characteristic: Is the pain sharp, dull, burning, aching, shooting, or stiffness?
A - Aggravating: What SPECIFIC activities, positions, or times of day make it worse?
R - Reducing: What helps? Rest, heat, ice, medication, specific positions?

{f"CONDITION-SPECIFIC SCREENING ({condition}):" + chr(10) + condition_probe if condition_probe else ""}

Also ask about duration if not known.

Rules:
- Ask 3-4 questions maximum (skip what we already know)
- Be warm and conversational — acknowledge their pain first, show you're listening
- Weave condition-specific screening questions naturally into SITCAR questions
- Match the patient's language ({initial_info.get('language', 'english')})
- Number each question for clarity
- If they seem anxious, reassure them that understanding their pain helps create the safest plan"""

    response = client.models.generate_content(
        model=MODEL_ID, contents=prompt,
        config={"system_instruction": SYSTEM_PROMPT}
    )
    return response.text


def _generate_medical_questions(collected: dict) -> str:
    """Generate medical history questions."""
    client = get_client()
    lang = collected.get("language", "english")
    condition = collected.get("condition", "")
    characteristic = collected.get("characteristic", "")

    # Condition-specific medical concerns to probe
    med_concerns = {
        "LBP": "Especially ask about osteoporosis (affects exercise choice) and any spinal surgeries.",
        "KNEE_OA": "Especially ask about rheumatoid arthritis, gout, and any knee surgeries or injections.",
        "NECK": "Especially ask about headache history, blood pressure (affects manual therapy), and any neck trauma.",
        "FROZEN_SHOULDER": "Especially ask about diabetes (strong link to frozen shoulder), thyroid, and any shoulder surgeries.",
        "SCIATICA": "Especially ask about any spinal surgeries, injections, and bladder/bowel function (cauda equina screen).",
        "HIP_OA": "Especially ask about hip/knee replacements, osteoporosis, and use of walking aids.",
        "PLANTAR_FASCIITIS": "Especially ask about diabetes (affects healing), weight changes, and any steroid injections in the heel.",
        "TENNIS_ELBOW": "Especially ask about repetitive work tasks, previous elbow treatments, and any nerve symptoms.",
    }

    prompt = f"""Now ask the patient about their medical and surgical history.
We've completed the SITCAR pain evaluation. This is the next step.

Briefly acknowledge what you've learned so far about their pain (1 sentence summary), then ask about:
1. Age (if not already known: {collected.get('age', 'NOT KNOWN')})
2. Height and weight (frame it naturally: "Could you share your height and approximate weight?
   This helps me choose exercises that are safe for your joints." — never mention BMI)
3. Any chronic conditions (diabetes, blood pressure, heart problems, thyroid, osteoporosis, etc.)
4. Any past surgeries (especially related to spine, joints, or muscles)
5. Current medications they take regularly

{med_concerns.get(condition, "")}

{"Note: patient reports " + characteristic + " pain — probe for any nerve-related conditions if relevant." if characteristic in ("shooting", "sharp", "burning") else ""}

Language: {'Hindi (Devanagari)' if lang == 'hindi' else 'English'}
Be warm, reassuring. Briefly explain why you're asking (to ensure safe, personalized exercises).
Keep it to 3-4 questions max. Don't repeat questions already answered."""

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
    aggravating = collected.get("aggravating_factors", [])

    # Condition-specific functional probes
    func_probes = {
        "LBP": "Ask specifically: how long can you sit/stand/walk before pain starts? Can you bend to tie shoes?",
        "KNEE_OA": "Ask specifically: can you climb stairs? Squat? Get up from a low chair? Walk for 30 minutes?",
        "NECK": "Ask specifically: can you turn head fully both ways? Can you work at a computer? Drive comfortably?",
        "FROZEN_SHOULDER": "Ask specifically: can you reach behind your back? Wash your hair? Reach a high shelf?",
        "SCIATICA": "Ask specifically: how long can you sit? Can you walk without limping? Any difficulty with shoes/socks?",
        "HIP_OA": "Ask specifically: can you walk 500m? Climb stairs? Get in/out of car? Cut toenails?",
        "PLANTAR_FASCIITIS": "Ask specifically: how many steps before pain starts? Can you stand for 30 minutes? Exercise/run?",
        "TENNIS_ELBOW": "Ask specifically: can you grip a cup of tea? Turn a doorknob? Type without pain? Carry a bag?",
    }

    prompt = f"""Final assessment step — we're almost done! Ask the patient about their daily function and goals.
Their condition: {condition}
Their aggravating factors: {', '.join(aggravating) if aggravating else 'Not yet specified'}

Ask about (3-4 questions max):
1. What is their occupation / daily routine? Be specific — ask about physical demands
   (desk job, standing all day, manual lifting, homemaker, retired, student)
2. Which daily activities are MOST affected by the pain? (this helps personalize the plan)
3. Do they currently exercise or have they done physiotherapy before? What kind?
4. What is their MAIN goal? (pain relief, return to specific activity, return to work/sport, sleep better)

{func_probes.get(condition, "")}

Language: {'Hindi (Devanagari)' if lang == 'hindi' else 'English'}
Almost done — be encouraging. Tell them you have almost all the information needed and
you'll be creating their personalized exercise plan shortly. Make them feel this is worth the time."""

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

    # Apply occupation-based and aggravation-based modifiers
    aggravating_factors = collected.get("aggravating_factors") or []
    occupation = collected.get("occupation", "")
    physical_demands = collected.get("physical_demands", "")

    # Map occupation description to demand category if physical_demands not set
    occ_category = physical_demands if physical_demands in ("sedentary", "light", "moderate", "heavy") else ""
    if not occ_category and occupation:
        occ_lower = occupation.lower()
        if any(kw in occ_lower for kw in ["desk", "office", "computer", "software", "it ", "bank", "account"]):
            occ_category = "sedentary"
        elif any(kw in occ_lower for kw in ["teacher", "retail", "shop", "cook", "homemaker", "housewife"]):
            occ_category = "light"
        elif any(kw in occ_lower for kw in ["nurse", "warehouse", "factory", "delivery", "kitchen"]):
            occ_category = "moderate"
        elif any(kw in occ_lower for kw in ["construction", "farm", "labour", "labor", "loading", "mining"]):
            occ_category = "heavy"

    plan = apply_modifiers(plan, occ_category, aggravating_factors, level)

    # Apply BMI-based modifiers
    height_cm = collected.get("height_cm")
    weight_kg = collected.get("weight_kg")
    bmi_info = calculate_bmi(height_cm or 0, weight_kg or 0)
    if bmi_info["bmi"] and bmi_info["modifier_key"]:
        plan = apply_bmi_modifiers(plan, bmi_info, condition, level)

    modifier_notes = plan.get("modifier_notes", [])

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

    aggravating = ", ".join(aggravating_factors) or "Not specified"
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
- Height: {height_cm or 'Not provided'} cm | Weight: {weight_kg or 'Not provided'} kg | BMI: {bmi_info['bmi'] or 'Not calculated'} ({bmi_info['category']})
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
- BMI modifier: {f'BMI {bmi_info["bmi"]} ({bmi_info["category"]}) - joint-protective modifications applied' if bmi_info.get('modifier_key') else 'Not needed (normal BMI or not provided)'}

=== OCCUPATION & AGGRAVATION MODIFIERS ===
{chr(10).join(modifier_notes) if modifier_notes else "No specific modifiers applied."}

YOUR ROLE: The rule engine selected the exercises and level. Your job is to EXPLAIN and ADAPT.
Do NOT second-guess the exercise selection — instead, explain WHY each exercise is right for this
specific patient and how to do them safely given their profile.

Provide your response {lang_instruction} with:

1. **Personal summary** (2-3 sentences) — Address the patient by acknowledging their specific
   situation. Connect their pain story to the plan. Make them feel heard.

2. **Clinical reasoning** — Explain in patient-friendly language WHY this exercise level was chosen.
   For each modifier applied, explain the reasoning:
   - "Because your pain is [VAS], we're starting at a [gentle/moderate/active] level"
   - "Since your pain is [worsening/sharp], we're being more conservative to protect you"
   - "Your [occupation] means we've added specific exercises to help you at work"
   Use analogies: "Think of these exercises as building a support system for your [body part]"

3. **Exercise guide** — For EACH exercise, provide:
   - Why THIS exercise helps YOUR specific condition and profile
   - One key form cue to get right
   - What to watch out for (specific to their aggravating factors)
   - How it connects to their daily function goals

4. **Occupation-specific guidance** — Concrete workplace/daily modifications:
   - Specific ergonomic changes for their job
   - When to do exercises relative to work (before shift, lunch break, after work)
   - How to modify aggravating work tasks

5. **Safety precautions** — Personalized to THIS patient:
   - Surgical history: specific movements to avoid or modify
   - Comorbidities: monitoring needs (e.g., "check blood sugar before exercise if diabetic")
   - Medications: interaction warnings (e.g., "blood thinners mean report any unusual bruising")
   - Pain boundaries: "Stop if pain goes above [VAS+2] or changes character"

6. **Daily schedule** — Suggest a realistic exercise schedule:
   - How many times per day/week
   - How long each session
   - Best time of day for their pattern (morning stiffness → gentle AM, activity pain → PM)

7. **Progression pathway** — Clear criteria for moving to next level:
   - "When you can do all exercises without pain increase for 1 week..."
   - "When your VAS drops below [threshold]..."
   - What the next level looks like (preview)

8. **Home management** — Based on their reducing factors:
   - Specific ice/heat protocols
   - Sleep position recommendations for their condition
   - Activity pacing strategies

9. **Motivation** — Realistic timeline with milestones:
   - Week 1-2: what to expect
   - Week 3-4: typical improvements
   - "Most patients with your profile see [specific improvement] by [timeframe]"

10. **Red flags to watch** — Condition-specific warning signs requiring immediate medical attention

11. **Clinical disclaimer** — Standard but compassionate

Write as a caring physiotherapist speaking directly to the patient. Use "you" and "your".
Avoid medical jargon unless you explain it immediately. Be specific — never generic."""

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
            "occupation_category": occ_category,
            "aggravation_modifiers": [a for a in aggravating_factors if any(k in a.lower() for k in AGGRAVATION_MODIFIERS)],
            "bmi": bmi_info.get("bmi"),
            "bmi_category": bmi_info.get("category"),
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
            collected = state.get("collected", {})
            result = state.get("result", {})
            plan_info = result.get("plan", {}) if isinstance(result, dict) else {}

            prompt = f"""The patient received their exercise prescription and is asking a follow-up question.

=== PATIENT PROFILE ===
Condition: {collected.get('condition', 'Unknown')}
Pain level: {collected.get('intensity_vas', collected.get('pain_vas', 'N/A'))}/10
Exercise level: {collected.get('level', 'N/A')}
Occupation: {collected.get('occupation', 'N/A')} ({collected.get('physical_demands', 'N/A')})
Aggravating factors: {', '.join(collected.get('aggravating_factors', [])) or 'N/A'}
Comorbidities: {', '.join(collected.get('comorbidities', [])) or 'None'}
Goals: {collected.get('goals', 'N/A')}

=== CONVERSATION ===
{context}

=== PATIENT ASKS ===
"{message}"

Answer their question with clinical depth. Common follow-up topics and how to handle them:

1. **Exercise technique questions** — Give detailed form cues, common mistakes, and modifications
   for their specific profile (age, condition, limitations)

2. **Pain during exercise** — Explain the difference between therapeutic discomfort (mild, eases
   after) and harmful pain (sharp, increasing, persists). Give the "traffic light" system:
   Green = mild discomfort OK, Yellow = stop if pain increases by 2+ on VAS, Red = stop immediately
   if sharp/shooting or new symptoms

3. **Progression questions** — Explain when they can progress: typically when current exercises are
   pain-free for 5-7 consecutive days. Preview what the next level includes.

4. **Lifestyle/work questions** — Give specific, practical advice for their occupation and daily tasks

5. **Alternative exercise questions** — Suggest modifications if an exercise is too difficult,
   always within their prescribed level

6. **Timeline/prognosis** — Give realistic expectations based on their specific profile
   (condition, chronicity, age, compliance)

Be specific to THEIR profile — never give generic answers. Maintain the warm, professional tone.
End with brief clinical disclaimer if giving new exercise advice."""

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
1. Where exactly is the pain? (lower back, knee, neck, shoulder, hip, heel, elbow, or leg pain from back)
2. How long have they had this pain?
3. How would they rate the pain from 0 to 10?

Respond {lang_inst}. Be warm and professional — show empathy for their pain. Keep it to one short paragraph + 3 numbered questions."""

        response = client.models.generate_content(
            model=MODEL_ID, contents=prompt,
            config={"system_instruction": SYSTEM_PROMPT}
        )
        return response.text
    except Exception:
        return ("Welcome! I'm PhysioGemma, your AI physiotherapy assistant. "
                "I'm here to help create a safe, personalized exercise plan for you.\n\n"
                "Could you please tell me:\n"
                "1. Where is your pain? (lower back, knee, neck, shoulder, hip, heel, elbow, or leg pain from back)\n"
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
