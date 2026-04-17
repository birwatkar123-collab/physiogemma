# PhysioGemma: AI Physiotherapy Agent Powered by Gemma 4

**Track: Health & Sciences**
**Subtitle: A ReAct agent with tool-calling, RAG-enhanced clinical reasoning, imaging report parsing, structured reasoning, patient progress tracking, recovery graphs, and AI-powered recovery insights — autonomous clinical assessment, red flag detection, BMI-aware joint protection, and occupation-adapted exercise prescriptions powered by Gemma 4**

---

## The Problem

Musculoskeletal conditions affect 1.71 billion people globally, making them the leading contributor to disability worldwide (WHO, 2023). In India, there is only 1 physiotherapist per 19,000 people. Most patients never receive proper exercise guidance, leading to chronic pain, disability, and reduced quality of life.

Even when patients access physiotherapy, only 35% complete home exercise programs — often because instructions lack personalization, clinical context, or are delivered in a language patients struggle with.

## The Solution

PhysioGemma is an AI physiotherapy **agent** (not a chatbot) that autonomously conducts complete clinical consultations using a **ReAct architecture** — Gemma 4 reasons about what to do next, calls clinical tools, observes results, and decides the next step. A deterministic rule engine handles safety-critical decisions through tool interfaces, while Gemma 4 drives intelligent conversation, clinical reasoning, and patient education.

Unlike simple symptom-checkers or linear chatbots, PhysioGemma operates as a **tool-calling agent** enhanced with **condition-specific RAG (Retrieval-Augmented Generation)** and **optional imaging report parsing** that follows real physiotherapy methodology — the **SITCAR pain evaluation framework** — gathering comprehensive clinical data through autonomous conversation, detecting red flags via tool calls, and generating personalized prescriptions across **8 musculoskeletal conditions** with **183 exercises** (all with verified YouTube video demonstrations).

> **PhysioGemma is the first AI physiotherapy agent where the LLM can never hallucinate an unsafe exercise — because every clinical decision passes through a deterministic evidence-based tool before reaching the patient.**

### What Makes This Different

| | Generic Health Chatbots | PhysioGemma |
|--|------------------------|-------------|
| **Exercise safety** | LLM generates exercises (hallucination risk) | Every exercise comes from a deterministic rule engine tool (zero hallucination) |
| **Clinical transparency** | Black box responses | Full reasoning chain: every tool call, every decision visible |
| **Evidence grounding** | Generic LLM knowledge | RAG-injected evidence from Boonstra 2014, NICE NG59, Cochrane, ACSM, OARSI |
| **Red flag detection** | Basic symptom matching | 40+ red flag patterns across 8 conditions in English AND Hindi |
| **Imaging integration** | None | Paste MRI/X-ray report text → 45+ finding patterns extract findings, bias prescriptions, catch imaging red flags |
| **Patient data privacy** | Server-stored data, logins required | Zero server storage — all progress data in browser localStorage |
| **Clinical coverage** | — | 183 exercises across 8 conditions, 5 severity levels, with occupation, aggravation, and BMI modifiers |

---

## Agent Architecture: Why It Matters

**Problem with chatbots:** Linear chatbots follow fixed scripts. They can't adapt when a patient provides rich information upfront, can't handle unexpected inputs, and can't show their reasoning.

**Problem with pure LLMs:** LLMs can hallucinate exercise recommendations or miss safety-critical red flags. Clinical decisions must be deterministic and evidence-based.

**PhysioGemma's solution: ReAct Agent + Tool-Calling**

The agent follows the **Thought -> Action -> Observation** loop:

1. **Thinks** — Decides what clinical information is still needed
2. **Acts** — Calls the appropriate clinical tool
3. **Observes** — Processes tool results and updates its reasoning
4. **Decides** — Asks follow-up questions or generates the prescription

This means the agent can handle a patient who provides everything in one message just as well as one who needs 4 rounds of questions.

---

## 5 Agent Tools

PhysioGemma uses **Gemma 4 function calling** to invoke 5 clinical tools:

| Tool | Purpose | When Called |
|------|---------|------------|
| **check_red_flags** | Scans for serious pathology (cauda equina, fractures, cardiac, infections) | EVERY patient message — mandatory safety gate |
| **classify_occupation** | Categorizes work into sedentary/light/moderate/heavy demands | When patient describes their job |
| **determine_exercise_level** | Evidence-based level (1-5) using Boonstra VAS + ACSM + SITCAR modifiers | When sufficient clinical data collected |
| **get_exercise_prescription** | Full prescription with occupation, aggravation, and BMI modifications | After level is determined |
| **analyze_progress** | Analyzes recovery trends, adherence, pain trajectories, and level readiness | When patient asks about their progress |

Each tool wraps deterministic rule engine logic — **no hallucination risk** for clinical decisions. The agent decides **when** to call each tool based on what information it has gathered.

---

## Lightweight RAG: Condition-Specific Knowledge Injection

A core challenge with LLM-driven clinical agents is **accuracy drift** — the model may generate plausible-sounding but clinically imprecise guidance. PhysioGemma addresses this with a **lightweight Retrieval-Augmented Generation (RAG)** system that injects condition-specific clinical knowledge directly into the system prompt.

### How It Works

1. **Knowledge Base** — `knowledge_base.py` contains 12 curated clinical entries spanning all 8 conditions, each citing specific evidence (Cochrane reviews, NICE guidelines, ACSM, OARSI, etc.)
2. **Condition Tracking** — As the agent identifies the patient's condition through tool calls, the condition code is stored in session state
3. **Dynamic Prompt Augmentation** — On every subsequent turn, the system prompt is augmented with relevant clinical knowledge:

```
AGENT_SYSTEM_PROMPT
+
=== RELEVANT CLINICAL KNOWLEDGE (use to improve accuracy) ===
For chronic low back pain, core stabilization exercises like McGill Big 3
(curl-up, side plank, bird dog) are first-line. Avoid prolonged sitting >30 min...
```

4. **Conditional Injection** — Knowledge is only injected when a condition is identified, adding **zero overhead** to early assessment turns where no condition is known yet

### Why Not Vector DB / Embeddings?

| Approach | Latency | Complexity | Accuracy for 8 conditions |
|----------|---------|------------|--------------------------|
| FAISS + embeddings | +200-500ms per query | High (model loading, index) | Overkill — 12 entries |
| ChromaDB / Pinecone | +300ms+ (API call) | High (external service) | Unnecessary |
| **PhysioGemma's approach** | **<1ms** (in-memory list scan) | **Minimal** (single function) | **Perfect** (exact condition match) |

With only 8 conditions and 12 knowledge entries, a simple keyword match achieves **100% retrieval precision** with negligible latency. This is a deliberate architectural choice — complexity is only added where it improves patient outcomes.

> **The RAG system achieves 100% retrieval precision with <1ms latency by design — because with 8 conditions, a simple exact-match lookup outperforms any vector database.**

### Clinical Knowledge Coverage

| Condition | Entries | Key Evidence Injected |
|-----------|---------|----------------------|
| LBP | 2 | McGill Big 3, graded activity, cauda equina red flags (NICE NG59, Hayden 2021) |
| Knee OA | 2 | Quad strengthening first-line, BMI joint load impact (Fransen 2015, OARSI) |
| Sciatica | 2 | McKenzie extensions, centralization signs, SLR diagnostics (Albert 2012, Cochrane 2023) |
| Neck | 2 | Deep neck flexors, C-Spine rules, vertebral artery screening (Gross 2015, Blanpied 2017) |
| Frozen Shoulder | 1 | Phase-specific ROM (freezing/frozen/thawing), aggressive stretch contraindication (Kelley 2009) |
| Hip OA | 1 | Abductor strengthening, aquatic therapy, walking aid guidance (Bennell 2014, EULAR) |
| Plantar Fasciitis | 1 | High-load heel raises > stretching alone, night splints (Rathleff 2015, APTA CPG) |
| Tennis Elbow | 1 | Tyler twist, eccentric wrist extension gold standard, isometric analgesia (Coombes 2015) |

---

## Imaging Report Integration (Mode 1)

A key differentiator of PhysioGemma is its ability to accept and parse **written radiology reports** from MRI, X-ray, or CT scans — giving the prescription engine objective anatomical grounding that no other AI physio tool currently offers.

### Why Text-Only (Mode 1)?

We deliberately chose **not** to analyse raw scan images (Mode 2). Scan image interpretation requires specialized models trained on DICOM/grayscale medical imaging, and automated image diagnosis crosses into **Software as a Medical Device (SaMD)** territory — requiring FDA Class II / CE Mark MDR Class IIa regulatory approval and validated clinical studies. By parsing the radiologist's *written* report instead, we capture most of the clinical value with none of the medicolegal risk. This is a deliberate, informed architectural boundary — not a limitation.

### How It Works

`imaging_parser.py` is a **deterministic regex-based parser** (no LLM call — instant, zero cost, 100% reliable) that extracts structured clinical findings from report text:

1. Patient optionally pastes their radiology report into the Consultation tab
2. Parser scans for **45+ finding patterns** across spine, knee, shoulder, hip, cervical, foot, and elbow
3. **Negation handling** correctly ignores "No compression fracture", "No nerve root impingement" etc.
4. Structured findings are injected into Gemma's system prompt before assessment begins
5. Findings, contraindications, and exercise bias appear in the Clinical Assessment Summary

### Finding Patterns Covered

| Region | Findings Detected |
|--------|-------------------|
| **Lumbar spine** | Disc herniation/protrusion/bulge, stenosis (central/lateral/foraminal), spondylolisthesis (with grade), facet arthropathy, annular tear, Modic changes, nerve root compression |
| **Cervical spine** | Disc herniation, stenosis, myelopathy, spondylosis |
| **Knee** | Meniscus tear (medial/lateral/bucket-handle), ACL/PCL/MCL tear, K-L graded OA, chondromalacia, Baker's cyst, effusion |
| **Shoulder** | Full/partial rotator cuff tear, subacromial impingement, adhesive capsulitis, labral tear, AC joint OA, biceps tendon pathology |
| **Hip** | FAI (cam/pincer), labral tear, OA, trochanteric bursitis |
| **Foot** | Plantar fasciopathy, calcaneal spur, Achilles tendinopathy |
| **Elbow** | Lateral/medial epicondylopathy |
| **General** | Osteoporosis, AVN (imaging red flag), inflammatory arthritis |

### Imaging Red Flags

When serious findings are detected, the parser raises red flags that instruct Gemma to **defer exercise and refer** instead of prescribing:

| Finding | Action |
|---------|--------|
| Cauda equina compression | SURGICAL EMERGENCY — defer, refer immediately |
| Spinal cord compression / myelopathy | Defer — neurosurgical consultation required |
| Vertebral compression fracture | Physician clearance required before loading |
| Possible malignancy / lytic lesion | Defer — oncology/spine specialist referral |
| Spinal infection (osteomyelitis/discitis) | Defer — immediate medical referral |
| Full-thickness rotator cuff tear | Surgical consultation before loading program |
| AVN / osteonecrosis | Orthopaedic management — defer loading |
| Complete ACL tear | Surgical consultation before high-demand program |

### Exercise Bias Logic

Imaging findings vote on the appropriate exercise direction, resolving prescription conflicts:

| Finding | Exercise Bias | Clinical Basis |
|---------|--------------|----------------|
| Disc herniation / nerve root compression | **Extension-biased** | McKenzie press-ups reduce disc pressure and centralize symptoms |
| Spinal stenosis / facet arthropathy / spondylolisthesis | **Flexion-biased** | Flexion opens the spinal canal and reduces facet loading |
| Most other findings | **Neutral** | Standard evidence-based protocol |

The bias is injected into the system prompt so Gemma selects appropriately from the exercise library — a patient with both disc protrusion (extension vote) and stenosis (flexion vote) gets the dominant directional recommendation.

### Integration Flow

```
Patient pastes report (optional)
    |
    v
imaging_parser.parse_imaging_report(text)    ← deterministic regex, <1ms
    |
    |-- Extract: findings, severity, vertebral levels, OA grades
    |-- Check: negation ("no compression fracture" → ignored)
    |-- Detect: imaging red flags
    |-- Vote: exercise bias (extension/flexion/neutral)
    |-- Generate: contraindication list (plain English)
    |
    v
state["collected"]["imaging"] = parsed_findings
    |
    v
gemma_engine.py: format_imaging_for_prompt() → injected into system prompt
    |
    v
Gemma sees: "[MODERATE] Disc herniation at L4-L5 | contraindications: avoid
             forward bending | exercise bias: extension-biased | ..."
    |
    v
Prescription respects imaging findings + contraindications
    |
    v
Assessment Summary shows findings with severity icons (🔴 severe / 🟡 moderate / 🔵 mild)
```

If the imaging textbox is left empty, **nothing changes** — zero overhead, zero behavior difference for patients who don't have reports.

---

## Structured Reasoning Chain

Every tool call and observation is logged and displayed transparently in the UI:

```
Action: [Safety Check] patient_message="My back hurts for 3 months..."
Observation: No red flags detected

Action: [Imaging Analysis] report_length=312
Observation: Detected: Disc herniation at L4-L5; Facet arthropathy — extension-biased

Action: [Classify Occupation] occupation="software developer"
Observation: Sedentary — Desk/office worker

Action: [Determine Level] pain_vas=6, age=45, is_chronic=true, tendency=worsening
Observation: Level 1 (Gentle Mobility) — VAS 6 -> Level 2, worsening -1

Action: [Generate Prescription] condition=LBP, level=1, occupation=sedentary
Observation: Prescription: 9 exercises at Level 1
```

This transparency lets patients (and clinicians reviewing output) understand exactly how decisions were made.

---

## How the Agent Works: Clinical Flow

### Autonomous Assessment (No Fixed Stages)

Unlike a linear chatbot which forces patients through fixed stages, the agent **decides its own flow**:

- If a patient says "I'm 45, lower back pain 6/10, desk worker, 3 months, getting worse, dull ache, sitting makes it worse" — the agent has enough to prescribe in 1-2 turns
- If a patient says "my back hurts" — the agent conducts thorough SITCAR questioning over 3-4 turns
- The agent uses **condition-specific probes** (e.g., dermatome mapping for sciatica, morning stiffness for OA)

### SITCAR Pain Evaluation Framework

| Parameter | Assessment | Clinical Significance |
|-----------|-----------|----------------------|
| **S** - Site | Exact location, radiation, bilateral/unilateral | Identifies structures, screens for radiculopathy |
| **I** - Intensity | VAS 0-10 at rest AND during activity | Determines exercise level (Boonstra 2014) |
| **T** - Tendency | Worsening / stable / improving | Worsening = -1 level (conservative) |
| **C** - Characteristic | Sharp / dull / burning / shooting / stiffness | Sharp/shooting = -1 level (neural caution) |
| **A** - Aggravating | Specific activities, positions, times | Triggers aggravation-based exercise swaps |
| **R** - Reducing | Rest, heat, ice, medication, positions | Informs home advice and exercise timing |

---

## Red Flag Detection (Safety Tool)

The `check_red_flags` tool is called on **every patient message** — this is enforced in the agent protocol. It scans for:

| Condition | Example Red Flags | Severity |
|-----------|------------------|----------|
| LBP | Bladder dysfunction, saddle anesthesia (cauda equina) | Emergency |
| Knee OA | Hot, red, swollen joint with fever (septic arthritis) | Emergency |
| Neck | Progressive arm weakness, gait disturbance (myelopathy) | Emergency |
| Sciatica | Bilateral leg symptoms, foot drop | Emergency |
| All | Unexplained weight loss, night sweats, cancer history | Urgent |

When flags are detected, the agent **stops the exercise pathway** and advises immediate medical consultation. This is handled deterministically by the rule engine tool — never left to LLM judgment.

> **PhysioGemma detects clinical emergencies (cauda equina, septic arthritis, cardiac events) in both English and Hindi, serving 1.4 billion people who lack physiotherapy access.**

The red flag engine includes **40+ patterns** across all 8 conditions plus 6 general flags, with Hindi keyword support (`peshab`, `bukhar`, `gir gaya`, `sujan`, etc.) — critical for India where 80% of the population lacks access to physiotherapy.

---

## Occupation-Based Exercise Modifications

The `classify_occupation` tool categorizes work demands, then `get_exercise_prescription` adds tailored exercises:

| Category | Example Jobs | Added Exercises | Workplace Advice |
|----------|-------------|-----------------|------------------|
| **Sedentary** | Office, IT, banking | Chin tucks, thoracic extension, hip flexor stretch | 2-min breaks every 30 min |
| **Light** | Teacher, retail, homemaker | Scapular squeezes, calf raises | Supportive footwear |
| **Moderate** | Nursing, warehouse, delivery | McGill curl-up, farmer's walk | Proper body mechanics |
| **Heavy** | Construction, farming, loading | Hip hinge drill, anti-rotation press | Warm up before shifts |

---

## Aggravation-Based Exercise Swaps

When specific activities worsen pain, the prescription automatically adapts:

| Aggravator | Modification | Clinical Basis |
|-----------|-------------|----------------|
| Sitting | McKenzie press-ups, remove flexion exercises | Counteracts sustained flexion |
| Bending | Hip hinge retraining, remove knee-to-chest | Teaches hip hinge over spinal flexion |
| Lifting | Dead bug, defer loaded exercises | Build stability before loading |
| Standing | Supine core activation, lying exercises | Reduce weight-bearing |
| Stairs | Graded step-up retraining | Retrain mechanics at lower load |

---

## BMI-Aware Exercise Modifications

Height and weight are collected naturally ("helps me choose exercises safe for your joints"). BMI is calculated silently — **never displayed to the patient** — and used as an exercise modifier:

| BMI Range | Modifications |
|-----------|--------------|
| 25.0-29.9 | Good form emphasis, low-impact preference |
| 30.0-34.9 | Seated marching added, seated/lying priorities |
| 35.0-39.9 | Wall push-ups, avoid floor-to-standing transitions |
| 40.0+ | Ankle pumps, rest breaks, breathing monitoring |

---

## Evidence-Based Prescription Logic

The `determine_exercise_level` tool stacks published clinical modifiers:

**Base Level** (Boonstra 2014 VAS cutoffs):
- Level 1 (VAS 7.5-10): Gentle mobility and pain relief
- Level 2 (VAS 5.0-7.4): Stability and gentle strengthening
- Level 3 (VAS 3.5-4.9): Core/functional strengthening
- Level 4 (VAS 1.0-3.4): Advanced strengthening
- Level 5 (VAS 0-0.9): Performance and prevention

**Modifiers applied by the tool:**
- Worsening tendency: -1 level
- Sharp/shooting pain: -1 level (neural caution)
- Post-surgical history: -1 level
- Age 65+: -1 level (ACSM)
- Age 50-64 with 2+ comorbidities: -1 level (ADA)
- 3+ comorbidities: -1 additional level

**Example:** 52-year-old desk worker (92kg, 170cm) with LBP, VAS 5/10, shooting pain worsening over 4 months, diabetes + hypertension, aggravated by sitting. MRI report: L4-L5 disc protrusion, no stenosis.
- Imaging parser: extension-biased, avoid heavy lifting
- Tool: `determine_exercise_level(5.0, 52, true, 2, "worsening", "shooting", false)` → Level 1
- Tool: `classify_occupation("desk worker")` → Sedentary
- Tool: `get_exercise_prescription("LBP", 1, "sedentary", ["sitting"], 170, 92)` → 9 exercises + modifiers
- Result: Level 1 + extension-biased McKenzie exercises + seated marching + diabetes monitoring + sitting management

---

## 8 Conditions Covered

| Condition | Exercises | Key Evidence |
|-----------|-----------|-------------|
| Lower Back Pain | 20+ across 5 levels | NICE NG59, McKenzie |
| Knee Osteoarthritis | 20+ across 5 levels | Cochrane Review |
| Neck Pain | 20+ across 5 levels | Canadian C-Spine Rules |
| Frozen Shoulder | 20+ across 5 levels | Cochrane Review |
| Sciatica | 20+ across 5 levels | McKenzie, nerve glides |
| Hip Osteoarthritis | 20+ across 5 levels | OARSI Guidelines |
| Plantar Fasciitis | 20+ across 5 levels | Eccentric loading evidence |
| Tennis Elbow | 20+ across 5 levels | Tyler Twist, eccentric evidence |

Total: **183 exercises** — 160 core exercises across 8 conditions × 5 levels, plus 23 supplementary exercises from occupation, aggravation, and BMI modifiers — **every single exercise has a YouTube video demonstration** with clickable thumbnail cards. All **120 unique video IDs are verified working** — scanned programmatically and dead links replaced.

---

## Patient Progress Tracking (Memory System)

Physiotherapy outcomes depend on **adherence over weeks**, not a single session. PhysioGemma includes a full progress tracking system that turns one-time prescriptions into ongoing recovery journeys.

### Session Logging

After each exercise session, patients log:

| Data Point | Input | Purpose |
|-----------|-------|---------|
| **Pain VAS** | Slider 0-10 (0.5 step) | Tracks pain trajectory over time |
| **Exercises Completed** | Checkboxes (auto-populated from prescription) | Calculates adherence percentage |
| **Difficulty Rating** | Slider 1-5 | Detects when exercises are too hard or too easy |
| **Session Notes** | Free text | Captures subjective feedback for AI analysis |

Data persists across browser sessions via **localStorage** — no login required, no server storage, fully private.

### Recovery Dashboard (Stats Cards)

Six real-time metrics displayed at a glance:
- **Total Sessions** logged
- **Current Pain** with percentage change from first session (color-coded: green = improving, red = worsening)
- **Average Adherence** across all sessions
- **Day Streak** — consecutive days with logged sessions
- **Current Level** — exercise progression level
- **Milestones Earned** — achievement count

### Milestone System

Auto-detected achievements that encourage adherence:

| Milestone | Trigger | Purpose |
|-----------|---------|---------|
| First Session | 1 session logged | Celebrate starting |
| 7 Sessions | 7 sessions completed | One-week consistency |
| 14 Sessions | 14 sessions completed | Two-week warrior |
| Pain Below Moderate | VAS drops below 3.5 | Clinical threshold (Boonstra) |
| 50% Pain Reduction | Last 3 avg ≤ 50% of first 3 avg | Meaningful recovery |
| Perfect Streak | 3 consecutive 100% adherence | Exercise commitment |

---

## Recovery Graph

A **dual-axis matplotlib chart** visualizes the patient's recovery journey:

**Top Panel — Pain VAS Over Time:**
- Line chart with data points and fill gradient
- **Boonstra zone coloring**: green (mild 0-3.5), amber (moderate 3.5-7.5), red (severe 7.5-10)
- Milestone markers as vertical dashed lines with labels
- Threshold lines at VAS 3.5 and 7.5

**Bottom Panel — Exercise Adherence:**
- Bar chart per session, color-coded: green (≥80%), yellow (50-80%), red (<50%)
- 80% target line (evidence-based adherence threshold)

---

## AI-Powered Recovery Insights

The `analyze_progress` tool combines **rule-based analysis** with **Gemma 4 narration** for actionable recovery insights.

### Rule-Based Analysis Engine

| Insight Type | Detection Logic | Example Output |
|-------------|----------------|----------------|
| **Pain Trend** | Compare first 3 vs last 3 session averages | "Pain decreased 50% (from 6.0 to 3.0)" |
| **Progress Readiness** | Last 3 sessions all below Boonstra threshold for next level | "Ready to progress to Level 3" |
| **Adherence Warning** | Recent 3-session average <60% | "Adherence dropped — try doing your top 3 exercises" |
| **Difficulty Mismatch** | High difficulty + no pain improvement | "Consider maintaining current level longer" |
| **Stagnation Detection** | Pain range <0.5 over 5+ sessions | "A physiotherapist review could help optimize your plan" |
| **Streak Recognition** | 3+ or 7+ consecutive session days | "Amazing 7-day exercise streak!" |

### Recommendation Engine

| Recommendation | Criteria | Display |
|---------------|----------|---------|
| **Progress** | Ready-to-progress insight detected | Green: "Ready to Progress to Next Level!" |
| **Maintain** | Default — steady improvement | Blue: "Maintain Current Level — Keep Going!" |
| **Regress** | Pain worsening + concerns detected | Red: "Consider Stepping Back a Level" |
| **Insufficient Data** | <3 sessions logged | Gray: "Log More Sessions for Insights" |

### AI Narrative (Gemma 4)

After rule-based analysis, Gemma 4 generates a **warm, personalized recovery report** (4-6 sentences) that references specific numbers, encourages based on actual trajectory, addresses concerns gently if pain is worsening, and ends with one actionable tip.

---

## How Gemma 4 Is Used

> **Safety-critical decisions (red flags, exercise levels, BMI modifications) are NEVER left to LLM judgment — they are handled by deterministic rule-engine tools, making PhysioGemma safer than a pure LLM approach.**

Gemma 4 26B-A4B-IT is the **brain of the agent**, powering:

**1. Autonomous Decision-Making** — Decides what information to gather, when to call tools, and how to adapt the conversation flow.

**2. Function Calling** — Invokes clinical tools through Google AI Studio's function calling API with structured arguments.

**3. RAG-Enhanced Reasoning** — System prompt dynamically augmented with condition-specific clinical evidence from the knowledge base, grounding reasoning in Cochrane, NICE, ACSM, OARSI guidelines.

**4. Imaging-Aware Reasoning** — When a radiology report is provided, imaging findings (with contraindications and exercise bias) are injected alongside RAG knowledge. Gemma references these findings explicitly in its clinical explanation.

**5. Conversational Assessment** — Empathetic, condition-aware clinical interviews. Adapts language (English/Hindi), acknowledges pain, uses condition-specific screening in natural conversation.

**6. Clinical Reasoning** — After tools generate the prescription, Gemma 4 produces a comprehensive clinical report: personal summary, exercise reasoning, daily schedule, progression pathway, occupation guidance, safety precautions, and realistic timeline.

**7. Recovery Insights Narration** — Analyzes rule-based progress data and generates warm, encouraging recovery reports with specific numbers and actionable tips.

---

## Architecture Diagram

```
Patient (English/Hindi)
    |
    |-- [Optional] Paste MRI/X-ray report text
    |       |
    |       v
    |   imaging_parser.py (deterministic, <1ms)
    |   → findings, contraindications, exercise bias, imaging red flags
    |   → stored in state["collected"]["imaging"]
    |
    v
[Gemma 4 Agent] — Receives message + tool definitions
    |
    |-- [RAG] Condition known? → Inject clinical knowledge into system prompt
    |-- [Imaging] Report provided? → Inject findings + contraindications + bias
    |-- Thinks: "Check safety first"
    |-- Action: check_red_flags(message, condition)
    |-- Observation: {flags_found: false}
    |
    |-- Thinks: "Need SITCAR data - ask questions"
    |-- Responds: Empathetic SITCAR questions
    |
[Patient responds]
    |
    v
[Gemma 4 Agent] — Updated conversation context + RAG + imaging knowledge
    |
    |-- Action: classify_occupation(job_description)
    |-- Observation: {category: "sedentary"}
    |-- Action: determine_exercise_level(vas, age, chronic, ...)
    |-- Observation: {level: 2, reasoning: "..."}
    |-- Action: get_exercise_prescription(condition, level, ...)
    |-- Observation: {exercises: [...], modifiers: [...]}
    |
    |-- Generates: imaging-aware clinical reasoning + personalized report
    |
    v
Personalized Prescription with Exercise Videos + Reasoning Chain
    + Clinical Assessment Summary (with imaging findings if provided)
    |
    v
[Patient exercises at home]
    |
    v
[My Progress Tab] — Log session: pain VAS, exercises done, difficulty, notes
    |
    |-- [Rule Engine] Stats, adherence %, milestones, pain trend
    |-- [matplotlib] Recovery graph (pain + adherence dual chart)
    |-- [localStorage] Persist across browser sessions
    |
    v
[AI Insights Tab] — "Generate Recovery Insights"
    |
    |-- Action: analyze_progress(progress_data)
    |-- Observation: {pain_change: -50%, recommendation: "progress"}
    |-- [Gemma 4] Warm, personalized recovery narrative
    |
    v
Recovery Report + Level Progression Recommendation
```

**Tech Stack:** Gemma 4 26B-A4B-IT (Google AI Studio free tier), Function Calling API, Lightweight RAG (condition-based knowledge retrieval), Deterministic Imaging Parser (45+ regex patterns, negation handling), Gradio (tabbed UI), matplotlib (recovery charts), localStorage (progress persistence), HuggingFace Spaces, Python

---

## Agent vs Chatbot: What Changed

| Aspect | Before (Chatbot) | After (Agent) |
|--------|------------------|---------------|
| Flow control | 4 fixed stages, Python if/elif chain | Agent decides autonomously |
| Tool usage | None — all inline Python | 5 tools via Gemma function calling |
| Clinical grounding | Generic LLM knowledge only | RAG-injected evidence (Cochrane, NICE, ACSM) |
| Imaging integration | None | Radiology report text parsed, findings injected into prescription |
| Reasoning | Hidden in code logic | Transparent reasoning chain displayed |
| Flexibility | Same 4 questions regardless of input | Adapts: rich input = fewer turns |
| Exercise videos | Partial coverage, some broken links | 183 exercises, 120/120 video IDs verified working |
| Progress tracking | None — one-shot prescription | Session logging, recovery graph, AI insights |
| Patient retention | Single visit, no follow-up | Milestones, streaks, level progression |
| Transparency | Black box | Every decision logged and visible |

---

## Real-World Impact

- **1.71 billion** people with musculoskeletal conditions globally
- **80% of India** lacks physiotherapy access
- PhysioGemma provides evidence-based guidance where none exists
- Bilingual (English + Hindi) for 1.4 billion people
- Free, no login required — accessible to anyone with internet
- Progress tracking with recovery graphs increases exercise adherence (evidence: 35% → 60%+ with visual feedback)
- Imaging report parsing bridges the gap between radiology and physiotherapy — patients often have MRI reports but no one to interpret them for exercise planning
- **Resilient fallback:** If Gemma 4 function calling is unavailable, PhysioGemma falls back to a structured prompt mode that still generates valid prescriptions through the deterministic rule engine
- **80% adherence target** on the recovery graph is evidence-based (rehabilitation research threshold for meaningful clinical improvement)

---

## Limitations & Ethics

PhysioGemma covers 8 common musculoskeletal conditions. It does not handle post-surgical rehabilitation, neurological conditions, pediatric cases, or complex multi-joint presentations. Red flag detection uses keyword matching and may miss atypical presentations.

The imaging parser analyses **text reports only** — scan images (DICOM, JPEG) are intentionally excluded. Autonomous interpretation of raw scan plates would constitute a Software as a Medical Device (SaMD) requiring regulatory approval. This boundary is a deliberate clinical and ethical choice, not a technical limitation.

The RAG knowledge base contains 12 curated entries — future expansion could include rare conditions and comorbidity-specific guidance. Progress data is stored in browser localStorage — it does not sync across devices.

All outputs include a clinical disclaimer. PhysioGemma is designed to **supplement, not replace** professional physiotherapy care. Safety-critical decisions are **always deterministic** (rule engine tools), while communication and reasoning are **always intelligent** (Gemma 4).

---

## Links

- **Live Demo:** https://huggingface.co/spaces/birwatkar123/physiogemma
- **Code:** https://github.com/birwatkar123-collab/physiogemma
- **License:** CC-BY 4.0

## Author
Gaurav Birwatkar — Practicing Physiotherapist & Developer
