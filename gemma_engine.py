"""
gemma_engine.py — Gemma 4 Agent with Tool-Calling & Structured Reasoning
==========================================================================
Converts PhysioGemma from a linear chatbot into a ReAct agent that:
  1. Decides what information to gather (no fixed stages)
  2. Calls clinical tools (red flags, exercise level, prescription)
  3. Shows structured reasoning chain (Thought → Action → Observation)
  4. Uses SITCAR framework through autonomous conversation

Uses Google AI Studio API with Gemma 4 function calling.
"""

import os
import json
import re
import functools
from google import genai
from google.genai import types

from exercises import (
    EXERCISES, tool_classify_occupation, tool_determine_exercise_level,
    tool_get_exercise_prescription,
)
from red_flags import tool_check_red_flags, format_red_flag_warning
from progress import tool_analyze_progress

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

# ── Tool Declarations for Gemma Function Calling ────────────────────────────

TOOL_DECLARATIONS = [
    types.FunctionDeclaration(
        name="check_red_flags",
        description=(
            "MANDATORY: Call this on EVERY patient message to scan for clinical red flags "
            "(cauda equina, fractures, cardiac, infections, etc.) before any other action. "
            "Returns detected flags with severity and recommended actions."
        ),
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "patient_message": types.Schema(
                    type="STRING",
                    description="The patient's latest message text to scan for red flags"
                ),
                "condition": types.Schema(
                    type="STRING",
                    description="Condition code (LBP, KNEE_OA, NECK, FROZEN_SHOULDER, SCIATICA, HIP_OA, PLANTAR_FASCIITIS, TENNIS_ELBOW) or empty string if unknown",
                ),
            },
            required=["patient_message"],
        ),
    ),
    types.FunctionDeclaration(
        name="classify_occupation",
        description=(
            "Classify patient's occupation/job into physical demand category "
            "(sedentary/light/moderate/heavy). Call when patient describes their work."
        ),
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "occupation_description": types.Schema(
                    type="STRING",
                    description="Patient's job/role description"
                ),
            },
            required=["occupation_description"],
        ),
    ),
    types.FunctionDeclaration(
        name="determine_exercise_level",
        description=(
            "Calculate evidence-based exercise level (1-5) using Boonstra 2014 VAS cutoffs, "
            "ACSM age guidelines, SITCAR modifiers, and surgical history. "
            "Call when you have: pain_vas, age, duration, tendency, characteristic, and surgery info."
        ),
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "pain_vas": types.Schema(type="NUMBER", description="Pain VAS score 0-10"),
                "age": types.Schema(type="INTEGER", description="Patient age in years"),
                "is_chronic": types.Schema(type="BOOLEAN", description="True if pain duration >= 3 months"),
                "comorbidity_count": types.Schema(type="INTEGER", description="Number of comorbidities (0 if none)"),
                "tendency": types.Schema(type="STRING", description="worsening, stable, or improving"),
                "characteristic": types.Schema(type="STRING", description="sharp, dull, burning, aching, throbbing, shooting, stiffness, or mixed"),
                "has_relevant_surgery": types.Schema(type="BOOLEAN", description="True if patient has relevant MSK surgical history"),
            },
            required=["pain_vas", "age", "is_chronic", "comorbidity_count",
                       "tendency", "characteristic", "has_relevant_surgery"],
        ),
    ),
    types.FunctionDeclaration(
        name="get_exercise_prescription",
        description=(
            "Get the full personalized exercise prescription with occupation and BMI modifiers. "
            "Call AFTER determine_exercise_level returns a level. Returns exercises with video IDs, "
            "modifier notes, and BMI info."
        ),
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "condition": types.Schema(
                    type="STRING",
                    description="Condition code: LBP, KNEE_OA, NECK, FROZEN_SHOULDER, SCIATICA, HIP_OA, PLANTAR_FASCIITIS, TENNIS_ELBOW"
                ),
                "level": types.Schema(type="INTEGER", description="Exercise level 1-5 from determine_exercise_level"),
                "occupation_category": types.Schema(type="STRING", description="sedentary, light, moderate, heavy, or unknown"),
                "aggravating_factors": types.Schema(
                    type="ARRAY",
                    items=types.Schema(type="STRING"),
                    description="List of aggravating activities (sitting, bending, walking, standing, lifting, stairs, overhead, driving)"
                ),
                "height_cm": types.Schema(type="NUMBER", description="Height in cm (0 if unknown)"),
                "weight_kg": types.Schema(type="NUMBER", description="Weight in kg (0 if unknown)"),
            },
            required=["condition", "level", "occupation_category", "aggravating_factors"],
        ),
    ),
    types.FunctionDeclaration(
        name="analyze_progress",
        description=(
            "Analyze patient's progress tracking data to generate recovery insights, "
            "pain trends, adherence stats, and level progression recommendations. "
            "Call when the patient asks about their progress, recovery, or whether to change levels."
        ),
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "progress_data_json": types.Schema(
                    type="STRING",
                    description="JSON string of the patient's progress data with sessions array"
                ),
            },
            required=["progress_data_json"],
        ),
    ),
]

TOOLS = [types.Tool(function_declarations=TOOL_DECLARATIONS)]

# ── Tool Dispatch ───────────────────────────────────────────────────────────

TOOL_DISPATCH = {
    "check_red_flags": tool_check_red_flags,
    "classify_occupation": tool_classify_occupation,
    "determine_exercise_level": tool_determine_exercise_level,
    "get_exercise_prescription": tool_get_exercise_prescription,
    "analyze_progress": tool_analyze_progress,
}

# ── Agent System Prompt ─────────────────────────────────────────────────────

AGENT_SYSTEM_PROMPT = """You are PhysioGemma, an AI physiotherapy AGENT that autonomously conducts
clinical assessments and prescribes evidence-based exercises.

=== YOUR ROLE ===
YOU are the clinical reasoner. You drive the assessment, make decisions, and communicate with patients.
TOOLS assist and validate your decisions — they handle deterministic calculations (exercise levels,
red flags, prescriptions). You are responsible for reasoning and final decisions.

You decide when to call tools. Avoid unnecessary tool calls — only invoke tools when you have
actionable data or need to verify safety. Be concise unless detailed explanation is needed.

=== AGENT PROTOCOL ===

STEP 1 — SAFETY (EVERY message):
  Call check_red_flags on every patient message. This is non-negotiable.
  If flags found → STOP and warn. Do NOT proceed to exercises.

STEP 2 — GATHER CLINICAL DATA:
  Through warm, conversational questions, collect:
  REQUIRED: condition, pain_vas (0-10), age, duration_months, tendency, characteristic
  IMPORTANT: aggravating_factors, reducing_factors, occupation, comorbidities, surgical_history
  HELPFUL: height_cm, weight_kg, limited_activities, exercise_history, goals

  Ask 3-4 questions at a time. Acknowledge previous answers. Be empathetic.
  You decide the flow. If patient gives rich info, skip ahead — don't over-ask.

STEP 3 — PRESCRIBE (when you have enough data):
  Minimum needed: condition, pain_vas, age, duration, tendency, characteristic, occupation.
  Call tools: classify_occupation → determine_exercise_level → get_exercise_prescription

STEP 4 — EXPLAIN:
  After prescription, provide a focused clinical explanation:
  1. Personal summary — acknowledge their situation (2-3 sentences)
  2. Clinical reasoning — WHY this level, key modifiers applied
  3. Exercise guide — for each exercise: purpose, one key form cue, what to watch
  4. Occupation guidance — workplace modifications
  5. Safety precautions — personalized to their profile
  6. Daily schedule and progression criteria
  7. Clinical disclaimer

  Keep it actionable. Avoid repeating information the patient already provided.

STEP 5 — PROGRESS ANALYSIS (when asked about recovery):
  Call analyze_progress if patient has progress data.
  Narrate insights warmly with specific numbers. Suggest level changes when appropriate.

=== SITCAR FRAMEWORK ===
  S = Site | I = Intensity (VAS 0-10) | T = Tendency | C = Characteristic
  A = Aggravating factors | R = Reducing factors

=== CONDITION PROBES ===
LBP: leg radiation, sitting tolerance | KNEE_OA: morning stiffness, stairs, crepitus
NECK: arm radiation, headaches, dizziness | FROZEN_SHOULDER: active vs passive range, night pain
SCIATICA: dermatome, cough aggravation | HIP_OA: groin vs lateral, walking distance
PLANTAR_FASCIITIS: first-step morning pain, footwear | TENNIS_ELBOW: grip weakness, triggers

=== CONDITION MAPPING ===
lower back/lumbar = LBP | knee/osteoarthritis = KNEE_OA | neck/cervical = NECK
shoulder/frozen = FROZEN_SHOULDER | sciatica/radiating leg = SCIATICA | hip/groin = HIP_OA
heel/plantar/sole = PLANTAR_FASCIITIS | elbow/tennis elbow = TENNIS_ELBOW

=== RULES ===
1. ALWAYS call check_red_flags first on every patient message
2. Be conversational, warm, empathetic — like a real physiotherapist
3. Match patient language (Hindi if they write in Hindi)
4. Never diagnose — exercise guidance only
5. Never fabricate exercises — ALWAYS use get_exercise_prescription tool
6. Be concise. Don't over-explain. Let the exercises and reasoning speak.

=== EVIDENCE BASE ===
Boonstra 2014, NICE NG59, ACSM, ADA, Cochrane Reviews, McKenzie Method, Canadian C-Spine Rules"""


# ── Agent Loop ──────────────────────────────────────────────────────────────

def _build_contents(history: list, new_message: str) -> list:
    """Convert Gradio chat history to Google AI Content objects."""
    contents = []
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))
    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=new_message)]))
    return contents


@functools.lru_cache(maxsize=64)
def _cached_tool_call(name: str, args_json: str) -> str:
    """Cached tool execution. Returns JSON string."""
    fn = TOOL_DISPATCH.get(name)
    if not fn:
        return json.dumps({"error": f"Unknown tool: {name}"})
    try:
        args = json.loads(args_json)
        result = fn(**args)
        return json.dumps(result, default=str)
    except Exception as e:
        return json.dumps({"error": f"Tool {name} failed: {str(e)}"})


def _execute_tool(name: str, args: dict) -> dict:
    """Execute a tool by name with caching."""
    args_json = json.dumps(args, sort_keys=True, default=str)
    result_json = _cached_tool_call(name, args_json)
    return json.loads(result_json)


def process_message(message: str, history: list, state: dict) -> tuple:
    """
    Agent-based message processing with ReAct tool-calling loop.

    Returns: (response_dict_or_str, updated_state)
    response_dict keys:
      - text: agent's reply to patient
      - reasoning_chain: list of {thought, action, args, observation} dicts
      - plan: exercise plan dict (only when prescription generated)
      - patient_info: collected clinical data
    """
    if not state:
        state = {"collected": {}, "reasoning_chain": [], "prescription_generated": False}

    reasoning_chain = []
    prescription_data = None

    try:
        client = get_client()

        # Trim history to last 6 messages for speed (keep context manageable)
        trimmed_history = history[-6:] if len(history) > 6 else history

        contents = []
        for msg in trimmed_history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(types.Content(
                role=role,
                parts=[types.Part.from_text(text=msg["content"])]
            ))

        # Optimized config: lower tokens + temperature for speed
        config = types.GenerateContentConfig(
            system_instruction=AGENT_SYSTEM_PROMPT,
            tools=TOOLS,
            tool_config=types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(mode="AUTO")
            ),
            max_output_tokens=400,
            temperature=0.3,
        )

        response = client.models.generate_content(
            model=MODEL_ID,
            contents=contents,
            config=config,
        )

        # ReAct loop: max 3 iterations, early exit on prescription
        max_iterations = 3
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            if not response.candidates or not response.candidates[0].content.parts:
                break

            has_function_call = False
            function_responses = []

            for part in response.candidates[0].content.parts:
                if part.function_call:
                    has_function_call = True
                    fc = part.function_call
                    tool_name = fc.name
                    tool_args = dict(fc.args) if fc.args else {}

                    # Record reasoning: Action
                    reasoning_chain.append({
                        "action": tool_name,
                        "args": tool_args,
                    })

                    # Execute tool (cached)
                    result = _execute_tool(tool_name, tool_args)

                    # Record reasoning: Observation
                    reasoning_chain.append({
                        "observation": tool_name,
                        "result": _summarize_result(result),
                    })

                    # Track prescription data
                    if tool_name == "get_exercise_prescription" and "exercises" in result:
                        prescription_data = result

                    # Track collected data from tool calls
                    if tool_name == "determine_exercise_level" and "level" in result:
                        state["collected"]["level"] = result["level"]
                        state["collected"]["level_label"] = result.get("label", "")
                        state["collected"]["level_reasoning"] = result.get("reasoning", "")

                    if tool_name == "classify_occupation" and "category" in result:
                        state["collected"]["physical_demands"] = result["category"]

                    if tool_name == "check_red_flags" and result.get("flags_found"):
                        state["collected"]["red_flags_detected"] = result["flags"]

                    function_responses.append(types.Part.from_function_response(
                        name=tool_name,
                        response=result,
                    ))

            if not has_function_call:
                break

            # EARLY EXIT: prescription generated, get final explanation
            if prescription_data:
                contents.append(response.candidates[0].content)
                contents.append(types.Content(role="user", parts=function_responses))
                response = client.models.generate_content(
                    model=MODEL_ID, contents=contents, config=config,
                )
                break

            # Continue loop with tool results
            contents.append(response.candidates[0].content)
            contents.append(types.Content(role="user", parts=function_responses))

            response = client.models.generate_content(
                model=MODEL_ID, contents=contents, config=config,
            )

        # Extract final text response
        final_text = ""
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.text:
                    final_text += part.text

        if not final_text:
            final_text = "I'm processing your information. Could you tell me more about your condition?"

        # If prescription was generated, return structured result
        if prescription_data:
            state["prescription_generated"] = True
            patient_info = _extract_patient_info(state, reasoning_chain)

            return {
                "text": final_text,
                "plan": prescription_data,
                "explanation": final_text,
                "patient_info": patient_info,
                "reasoning_chain": reasoning_chain,
            }, state
        else:
            return {
                "text": final_text,
                "reasoning_chain": reasoning_chain,
            }, state

    except Exception as e:
        error_msg = str(e)
        if "tool" in error_msg.lower() or "function" in error_msg.lower():
            return _fallback_process(message, history, state)
        return {"text": f"An error occurred: {error_msg}", "reasoning_chain": []}, state


def _summarize_result(result: dict) -> str:
    """Create a concise summary of tool result for display."""
    if "error" in result:
        return f"Error: {result['error']}"
    if "flags_found" in result:
        if result["flags_found"]:
            return f"RED FLAGS DETECTED ({result['count']}): {', '.join(f['flag'] for f in result['flags'])}"
        return "No red flags detected"
    if "level" in result and "reasoning" in result:
        return f"Level {result['level']} ({result['label']}) — {result['reasoning']}"
    if "category" in result:
        return f"{result['category'].title()} — {result['description']}"
    if "exercises" in result:
        return f"Prescription: {result['total_exercises']} exercises at Level {result['level']} ({result['label']})"
    return json.dumps(result, default=str)[:200]


def _extract_patient_info(state: dict, chain: list) -> dict:
    """Extract patient info from tool call arguments in reasoning chain."""
    info = dict(state.get("collected", {}))
    for step in chain:
        if "args" in step:
            args = step["args"]
            if "pain_vas" in args:
                info["pain_vas"] = args["pain_vas"]
                info["intensity_vas"] = args["pain_vas"]
            if "age" in args:
                info["age"] = args["age"]
            if "is_chronic" in args:
                info["is_chronic"] = args["is_chronic"]
            if "tendency" in args:
                info["tendency"] = args["tendency"]
            if "characteristic" in args:
                info["characteristic"] = args["characteristic"]
            if "condition" in args:
                info["condition"] = args["condition"]
            if "aggravating_factors" in args:
                info["aggravating_factors"] = args["aggravating_factors"]
            if "occupation_description" in args:
                info["occupation"] = args["occupation_description"]
            if "height_cm" in args:
                info["height_cm"] = args["height_cm"]
            if "weight_kg" in args:
                info["weight_kg"] = args["weight_kg"]
            if "comorbidity_count" in args:
                info["comorbidity_count"] = args["comorbidity_count"]
    return info


# ── Fallback: Non-tool mode for models without function calling ─────────────

def _fallback_process(message: str, history: list, state: dict) -> tuple:
    """Fallback when function calling is not supported by the model."""
    from exercises import (get_exercise_plan, determine_level, apply_modifiers,
                           apply_bmi_modifiers, calculate_bmi)
    from red_flags import check_red_flags, format_red_flag_warning

    if not state:
        state = {"collected": {}, "reasoning_chain": [], "prescription_generated": False}

    try:
        client = get_client()

        # Build simple prompt with tool awareness
        conversation = "\n".join(
            f"{'Patient' if m['role'] == 'user' else 'PhysioGemma'}: {m['content']}"
            for m in history
        )

        prompt = f"""You are PhysioGemma, an AI physiotherapy agent. Conduct a clinical assessment.

Conversation so far:
{conversation}

Based on the conversation, respond as a physiotherapist. If you have enough information
(condition, pain level, age, duration, tendency, characteristic, occupation), say
"READY_TO_PRESCRIBE" followed by a JSON block with the collected data.

Otherwise, ask 3-4 questions to gather missing SITCAR data. Be warm and empathetic.

If the patient mentions emergency symptoms (bladder/bowel issues, bilateral weakness,
fever with severe pain), warn them to seek immediate medical care."""

        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(system_instruction=AGENT_SYSTEM_PROMPT),
        )

        text = response.text or "Could you tell me more about your condition?"

        # Check if ready to prescribe
        if "READY_TO_PRESCRIBE" in text:
            json_match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group())
                    state["collected"].update(data)
                except json.JSONDecodeError:
                    pass

            collected = state["collected"]
            condition = collected.get("condition", "LBP")
            pain_vas = float(collected.get("pain_vas", 5))
            age = int(collected.get("age", 40))
            duration = int(collected.get("duration_months", 1))
            tendency = collected.get("tendency", "stable")
            characteristic = collected.get("characteristic", "aching")

            level_result = tool_determine_exercise_level(
                pain_vas=pain_vas, age=age, is_chronic=duration >= 3,
                comorbidity_count=len(collected.get("comorbidities", [])),
                tendency=tendency, characteristic=characteristic,
                has_relevant_surgery=bool(collected.get("surgical_history"))
            )

            occ = tool_classify_occupation(collected.get("occupation", "unknown"))

            prescription = tool_get_exercise_prescription(
                condition=condition, level=level_result["level"],
                occupation_category=occ["category"],
                aggravating_factors=collected.get("aggravating_factors", []),
                height_cm=float(collected.get("height_cm", 0)),
                weight_kg=float(collected.get("weight_kg", 0))
            )

            if "exercises" in prescription:
                state["prescription_generated"] = True
                # Remove READY_TO_PRESCRIBE and JSON from displayed text
                clean_text = text.split("READY_TO_PRESCRIBE")[0].strip()
                if not clean_text:
                    clean_text = "Your personalized exercise plan is ready!"

                return {
                    "text": clean_text,
                    "plan": prescription,
                    "explanation": clean_text,
                    "patient_info": collected,
                    "reasoning_chain": [
                        {"action": "determine_exercise_level", "args": {"pain_vas": pain_vas, "age": age}},
                        {"observation": "determine_exercise_level", "result": f"Level {level_result['level']}"},
                        {"action": "get_exercise_prescription", "args": {"condition": condition}},
                        {"observation": "get_exercise_prescription", "result": f"{prescription['total_exercises']} exercises"},
                    ],
                }, state

        return {"text": text, "reasoning_chain": []}, state

    except Exception as e:
        return {"text": f"An error occurred: {str(e)}", "reasoning_chain": []}, state
