"""
imaging_parser.py — Deterministic Radiology Report Text Parser
================================================================
Extracts structured findings from MRI / X-ray / CT radiology report
text to enrich PhysioGemma's clinical assessment.

This is Mode 1 of imaging integration: text interpretation only.
We intentionally do NOT analyse raw scan plates — that would cross
into diagnostic AI / SaMD territory (FDA Class II, regulatory
burden). Parsing the radiologist's written report gives most of
the clinical value with none of the legal risk.

Usage:
    from imaging_parser import parse_imaging_report
    parsed = parse_imaging_report("MRI lumbar spine: L4-L5 disc protrusion...")
    # → {"findings": [...], "contraindications": [...],
    #    "exercise_bias": "extension", "red_flags": [...], "summary": "..."}
"""

import re


# ── Finding patterns ────────────────────────────────────────────────────────
# Each entry maps a regex pattern to a structured finding with:
#   condition_hint: suggested condition code (links into rule engine)
#   contraindications: list of movement/loading flags to respect
#   exercise_bias: preferred movement direction ("flexion", "extension", "neutral")
#   severity: "mild" | "moderate" | "severe"
#   red_flag: optional string — if set, exercise prescription must be deferred

IMAGING_PATTERNS = [

    # ══════════════════════ SPINE / LUMBAR ══════════════════════
    {
        "pattern": r"\b(disc|disk)\s+(herniat|protru|extrus|prolaps)",
        "finding": "Disc herniation / protrusion",
        "condition_hint": "LBP",
        "contraindications": ["avoid_flexion_loading", "avoid_heavy_lifting", "avoid_prolonged_sitting"],
        "exercise_bias": "extension",
        "severity": "moderate",
    },
    {
        "pattern": r"\bdisc\s+bulge|diffuse\s+(disc\s+)?bulg",
        "finding": "Disc bulge",
        "condition_hint": "LBP",
        "contraindications": ["limit_heavy_lifting"],
        "exercise_bias": "neutral",
        "severity": "mild",
    },
    {
        "pattern": r"\b(central\s+canal|lateral\s+recess|foraminal|neural\s+foraminal)\s+stenosis|\bspinal\s+stenosis",
        "finding": "Spinal stenosis",
        "condition_hint": "LBP",
        "contraindications": ["avoid_extension_loading", "avoid_prolonged_standing"],
        "exercise_bias": "flexion",
        "severity": "moderate",
    },
    {
        "pattern": r"\bspondylolisthesis\b",
        "finding": "Spondylolisthesis",
        "condition_hint": "LBP",
        "contraindications": ["avoid_extension_loading", "avoid_heavy_lifting"],
        "exercise_bias": "flexion",
        "severity": "moderate",
    },
    {
        "pattern": r"\bspondylolysis|pars\s+(inter\w*\s+)?defect",
        "finding": "Spondylolysis (pars defect)",
        "condition_hint": "LBP",
        "contraindications": ["avoid_extension_loading", "avoid_impact"],
        "exercise_bias": "flexion",
        "severity": "moderate",
    },
    {
        "pattern": r"\bfacet\s+(arthropathy|hypertrophy|osteoarthritis|arthrosis|degenerat)",
        "finding": "Facet joint arthropathy",
        "condition_hint": "LBP",
        "contraindications": ["avoid_extension_loading"],
        "exercise_bias": "flexion",
        "severity": "mild",
    },
    {
        "pattern": r"\bnerve\s+root\s+(compression|impingement|contact|displacement)|\bradiculopathy|\bradicular",
        "finding": "Nerve root compression",
        "condition_hint": "SCIATICA",
        "contraindications": ["avoid_flexion_loading", "avoid_prolonged_sitting", "avoid_heavy_lifting"],
        "exercise_bias": "extension",
        "severity": "moderate",
    },
    {
        "pattern": r"\bannular\s+(tear|fissure)",
        "finding": "Annular tear",
        "condition_hint": "LBP",
        "contraindications": ["avoid_flexion_loading", "avoid_heavy_lifting"],
        "exercise_bias": "extension",
        "severity": "mild",
    },
    {
        "pattern": r"\bmodic\s+change|type\s+[12]\s+endplate",
        "finding": "Modic endplate changes",
        "condition_hint": "LBP",
        "severity": "mild",
    },

    # ── Spine red flags ──
    {
        "pattern": r"\b(compression|wedge|burst)\s+fracture|\bvertebral\s+body\s+fracture|\bvertebral\s+collapse",
        "finding": "Vertebral compression fracture",
        "condition_hint": "LBP",
        "contraindications": ["avoid_flexion_loading", "avoid_twisting", "avoid_heavy_lifting", "avoid_high_impact"],
        "exercise_bias": "neutral",
        "severity": "severe",
        "red_flag": "Vertebral compression fracture noted. Requires physician clearance before any loading program; screen for osteoporosis.",
    },
    {
        "pattern": r"\bcauda\s+equina|conus\s+medullaris\s+(compression|syndrome)",
        "finding": "Cauda equina compression",
        "condition_hint": "LBP",
        "contraindications": ["defer_exercise"],
        "severity": "severe",
        "red_flag": "SURGICAL EMERGENCY: Cauda equina compression. Do NOT prescribe exercise — immediate surgical referral required.",
    },
    {
        "pattern": r"\b(metastas|lytic\s+lesion|blastic\s+lesion|malignan|neoplas|tumor|tumour)",
        "finding": "Suspicious lesion / possible malignancy",
        "contraindications": ["defer_exercise"],
        "severity": "severe",
        "red_flag": "Imaging references possible malignancy/lesion. DEFER exercise prescription. Refer for oncology or spine specialist review before any program.",
    },
    {
        "pattern": r"\b(osteomyelitis|discitis|spondylodiscitis|spinal\s+infection|epidural\s+abscess)",
        "finding": "Spinal infection",
        "contraindications": ["defer_exercise"],
        "severity": "severe",
        "red_flag": "Imaging suggests spinal infection. DEFER exercise. Immediate medical referral required.",
    },
    {
        "pattern": r"\bcord\s+compression|myelomalacia|cord\s+signal\s+change",
        "finding": "Spinal cord compression",
        "contraindications": ["defer_exercise"],
        "severity": "severe",
        "red_flag": "Spinal cord compression noted. DEFER exercise. Neurosurgical consultation required.",
    },

    # ══════════════════════ CERVICAL / NECK ══════════════════════
    {
        "pattern": r"\bcervical\s+(disc\s+)?(herniation|protrusion|bulge|extrusion)",
        "finding": "Cervical disc herniation",
        "condition_hint": "NECK",
        "contraindications": ["avoid_forward_head_posture", "avoid_heavy_overhead_loading", "avoid_end_range_extension"],
        "severity": "moderate",
    },
    {
        "pattern": r"\bcervical\s+myelopathy|cervical\s+cord",
        "finding": "Cervical myelopathy",
        "condition_hint": "NECK",
        "contraindications": ["defer_exercise"],
        "severity": "severe",
        "red_flag": "Cervical myelopathy requires neurosurgical assessment before exercise. Defer program.",
    },
    {
        "pattern": r"\bcervical\s+(canal\s+)?stenosis",
        "finding": "Cervical stenosis",
        "condition_hint": "NECK",
        "contraindications": ["avoid_extension_loading", "avoid_heavy_overhead_loading"],
        "severity": "moderate",
    },
    {
        "pattern": r"\bcervical\s+(spondylosis|osteoarthritis|degenerat)",
        "finding": "Cervical spondylosis",
        "condition_hint": "NECK",
        "severity": "mild",
    },

    # ══════════════════════ KNEE ══════════════════════
    {
        "pattern": r"\b(medial|lateral|bucket[\s-]?handle|horizontal|radial)\s*meniscus\s+tear|\bmeniscal\s+tear",
        "finding": "Meniscus tear",
        "condition_hint": "KNEE_OA",
        "contraindications": ["avoid_deep_squats", "avoid_twisting", "avoid_pivoting"],
        "exercise_bias": "quad_strengthening",
        "severity": "moderate",
    },
    {
        "pattern": r"\b(ACL|anterior\s+cruciate\s+ligament)\s+(complete\s+)?(tear|rupture|disruption)",
        "finding": "ACL tear",
        "condition_hint": "KNEE_OA",
        "contraindications": ["avoid_pivoting", "avoid_cutting_sports", "avoid_open_chain_knee_extension"],
        "severity": "severe",
        "red_flag": "Complete ACL tear — surgical consultation recommended before high-demand program. Prescribe conservative rehab only if consulted.",
    },
    {
        "pattern": r"\b(PCL|posterior\s+cruciate|MCL|medial\s+collateral|LCL|lateral\s+collateral)\s+(ligament\s+)?(tear|rupture|sprain)",
        "finding": "Collateral/PCL ligament injury",
        "condition_hint": "KNEE_OA",
        "contraindications": ["avoid_pivoting", "avoid_lateral_stress"],
        "severity": "moderate",
    },
    {
        "pattern": r"\bkellgren[\s-]?lawrence\s*(grade\s*)?[1-4]|\bK[\s-]?L\s*(grade\s*)?[1-4]",
        "finding": "Knee osteoarthritis (Kellgren-Lawrence graded)",
        "condition_hint": "KNEE_OA",
        "severity": "moderate",
    },
    {
        "pattern": r"\b(chondromalacia|cartilage\s+(thinning|loss|defect|fissur)|chondral\s+(defect|lesion))",
        "finding": "Cartilage loss / chondromalacia",
        "condition_hint": "KNEE_OA",
        "contraindications": ["avoid_deep_squats", "avoid_high_impact"],
        "severity": "mild",
    },
    {
        "pattern": r"\bbaker'?s\s+cyst|popliteal\s+cyst",
        "finding": "Baker's cyst",
        "condition_hint": "KNEE_OA",
        "severity": "mild",
    },
    {
        "pattern": r"\bjoint\s+effusion|knee\s+effusion",
        "finding": "Joint effusion",
        "contraindications": ["reduce_loading_temporarily"],
        "severity": "mild",
    },
    {
        "pattern": r"\b(osteonecrosis|avascular\s+necrosis|\bAVN\b)",
        "finding": "Avascular necrosis / osteonecrosis",
        "contraindications": ["defer_exercise", "avoid_weight_bearing"],
        "severity": "severe",
        "red_flag": "Avascular necrosis requires orthopaedic management. DEFER loading program pending specialist review.",
    },

    # ══════════════════════ SHOULDER ══════════════════════
    {
        "pattern": r"\bfull[\s-]?thickness\s+(rotator\s+cuff|supraspinatus|infraspinatus|subscapularis)\s+tear|\bmassive\s+(rotator\s+cuff|cuff|RCT)\s+tear",
        "finding": "Full-thickness rotator cuff tear",
        "condition_hint": "FROZEN_SHOULDER",
        "contraindications": ["avoid_heavy_overhead_loading", "avoid_end_range_abduction", "avoid_loaded_external_rotation"],
        "severity": "severe",
        "red_flag": "Full-thickness / massive rotator cuff tear may warrant surgical consultation. Prescribe conservative rehab cautiously.",
    },
    {
        "pattern": r"\bpartial[\s-]?thickness\s+(rotator\s+cuff|supraspinatus|infraspinatus|subscapularis)\s+tear|\b(supraspinatus|infraspinatus|subscapularis)\s+tendinopathy|\brotator\s+cuff\s+tendinopathy",
        "finding": "Partial rotator cuff tear / tendinopathy",
        "condition_hint": "FROZEN_SHOULDER",
        "contraindications": ["limit_overhead_loading", "avoid_end_range_abduction"],
        "severity": "moderate",
    },
    {
        "pattern": r"\bsubacromial\s+impingement|\bsubacromial\s+bursitis|\bshoulder\s+impingement",
        "finding": "Subacromial impingement",
        "condition_hint": "FROZEN_SHOULDER",
        "contraindications": ["avoid_end_range_abduction", "limit_overhead_loading"],
        "severity": "mild",
    },
    {
        "pattern": r"\badhesive\s+capsulitis|frozen\s+shoulder",
        "finding": "Adhesive capsulitis (frozen shoulder)",
        "condition_hint": "FROZEN_SHOULDER",
        "severity": "moderate",
    },
    {
        "pattern": r"\b(SLAP\s+(lesion|tear)|labral\s+tear|labrum\s+tear|glenoid\s+labral)",
        "finding": "Labral tear",
        "condition_hint": "FROZEN_SHOULDER",
        "contraindications": ["avoid_heavy_overhead_loading", "avoid_end_range_external_rotation"],
        "severity": "moderate",
    },
    {
        "pattern": r"\bAC\s+(joint\s+)?(arthritis|osteoarthritis|OA|degenerat)|acromioclavicular\s+(arthritis|degenerat)",
        "finding": "AC joint osteoarthritis",
        "condition_hint": "FROZEN_SHOULDER",
        "severity": "mild",
    },
    {
        "pattern": r"\bbiceps\s+tendon\s+(tear|rupture|tendinopathy)|\blong\s+head\s+biceps",
        "finding": "Biceps tendon pathology",
        "condition_hint": "FROZEN_SHOULDER",
        "contraindications": ["avoid_heavy_resisted_flexion"],
        "severity": "mild",
    },

    # ══════════════════════ HIP ══════════════════════
    {
        "pattern": r"\bfemoroacetabular\s+impingement|\bFAI\b|\bcam\s+(lesion|deformity|morpho)|\bpincer\s+(lesion|deformity|morpho)",
        "finding": "Femoroacetabular impingement (FAI)",
        "condition_hint": "HIP_OA",
        "contraindications": ["avoid_deep_hip_flexion", "avoid_end_range_internal_rotation"],
        "severity": "moderate",
    },
    {
        "pattern": r"\b(hip|acetabular)\s+labral\s+tear",
        "finding": "Hip labral tear",
        "condition_hint": "HIP_OA",
        "contraindications": ["avoid_deep_hip_flexion", "avoid_end_range_internal_rotation"],
        "severity": "moderate",
    },
    {
        "pattern": r"\bhip\s+(osteoarthritis|OA|degenerat)|coxarthrosis",
        "finding": "Hip osteoarthritis",
        "condition_hint": "HIP_OA",
        "severity": "moderate",
    },
    {
        "pattern": r"\btrochanteric\s+bursitis|greater\s+trochanteric\s+pain|gluteal\s+tendinopathy",
        "finding": "Trochanteric bursitis / gluteal tendinopathy",
        "condition_hint": "HIP_OA",
        "contraindications": ["avoid_crossed_leg_sitting", "avoid_side_sleeping_painful_side"],
        "severity": "mild",
    },

    # ══════════════════════ FOOT / PLANTAR ══════════════════════
    {
        "pattern": r"\bplantar\s+(fasciitis|fasciopathy|fascia\s+(thickening|tear))",
        "finding": "Plantar fasciopathy",
        "condition_hint": "PLANTAR_FASCIITIS",
        "severity": "mild",
    },
    {
        "pattern": r"\b(calcaneal|heel)\s+spur",
        "finding": "Calcaneal spur",
        "condition_hint": "PLANTAR_FASCIITIS",
        "severity": "mild",
    },
    {
        "pattern": r"\bachilles\s+(tendinopathy|tendinitis|tendinosis|tear)",
        "finding": "Achilles tendinopathy",
        "condition_hint": "PLANTAR_FASCIITIS",
        "contraindications": ["avoid_high_impact", "avoid_jumping"],
        "severity": "moderate",
    },

    # ══════════════════════ ELBOW ══════════════════════
    {
        "pattern": r"\b(common\s+extensor\s+tendinopathy|lateral\s+epicondyl(itis|algia|opathy)|ECRB\s+tendinosis)",
        "finding": "Lateral epicondylopathy",
        "condition_hint": "TENNIS_ELBOW",
        "contraindications": ["avoid_repetitive_gripping"],
        "severity": "mild",
    },
    {
        "pattern": r"\bmedial\s+epicondyl(itis|algia|opathy)|golfer'?s\s+elbow",
        "finding": "Medial epicondylopathy",
        "condition_hint": "TENNIS_ELBOW",
        "contraindications": ["avoid_repetitive_gripping", "avoid_wrist_flexion_loading"],
        "severity": "mild",
    },

    # ══════════════════════ GENERAL / SYSTEMIC ══════════════════════
    {
        "pattern": r"\bosteoporos(is|ie)|\blow\s+bone\s+(density|mineral)|\bT[\s-]?score\s*[-:]?\s*-[23]",
        "finding": "Osteoporosis / low bone density",
        "contraindications": ["avoid_flexion_loading", "avoid_twisting", "avoid_high_impact"],
        "severity": "moderate",
    },
    {
        "pattern": r"\brheumatoid\s+arthritis|\bRA\b|inflammatory\s+arthritis",
        "finding": "Inflammatory arthritis",
        "contraindications": ["avoid_loading_during_flares", "gentle_ROM_only_in_acute"],
        "severity": "moderate",
    },
]

# ── Helper regexes ──────────────────────────────────────────────────────────
LEVEL_PATTERN = re.compile(
    r"\b([CTLS][1-9][0-9]?)[\s\-\u2013/]*([CTLS]?[1-9][0-9]?)?\b",
    re.IGNORECASE,
)
GRADE_PATTERN = re.compile(r"grade\s*([1-5]|I{1,3}|IV|V)", re.IGNORECASE)
KL_GRADE_PATTERN = re.compile(r"(?:kellgren[\s-]?lawrence|K[\s-]?L)\s*(?:grade\s*)?([1-4])", re.IGNORECASE)

# Negation words that, when found before a finding, invalidate the match
NEGATION_WORDS = (
    "no ", "not ", "without ", "absent ", "negative for ", "ruled out",
    "rule out", "r/o ", "free of ", "denies ", "no evidence of ",
    "no acute ", "unremarkable for ", "no significant ",
)


def _is_negated(text: str, match_start: int, lookback: int = 30) -> bool:
    """Check if a finding match is negated by a preceding word like 'no' or 'without'.

    Only looks back within the current sentence/clause (stops at . ; :).
    """
    window_start = max(0, match_start - lookback)
    window = text[window_start:match_start].lower()
    # Truncate at clause boundary
    for sep in (". ", "; ", ": ", ".\n", ";\n", ":\n"):
        idx = window.rfind(sep)
        if idx >= 0:
            window = window[idx + len(sep):]
    return any(neg in window for neg in NEGATION_WORDS)


# ── Contraindication → plain-English mapping ────────────────────────────────
CONTRAINDICATION_LABELS = {
    "avoid_flexion_loading": "avoid forward bending / flexion under load",
    "avoid_extension_loading": "avoid repeated back extension / arching",
    "avoid_heavy_lifting": "avoid heavy lifting",
    "avoid_prolonged_sitting": "minimise prolonged sitting",
    "avoid_prolonged_standing": "minimise prolonged standing",
    "avoid_twisting": "avoid rotational/twisting movements",
    "avoid_high_impact": "avoid high-impact activities (running, jumping)",
    "avoid_deep_squats": "avoid deep squats",
    "avoid_pivoting": "avoid pivoting / cutting movements",
    "avoid_cutting_sports": "avoid cutting sports until cleared",
    "avoid_open_chain_knee_extension": "avoid loaded open-chain knee extensions",
    "avoid_lateral_stress": "avoid lateral knee stress",
    "avoid_weight_bearing": "protect from full weight-bearing",
    "defer_exercise": "DEFER exercise — medical referral required",
    "reduce_loading_temporarily": "reduce loading temporarily",
    "limit_heavy_lifting": "limit heavy lifting",
    "avoid_heavy_overhead_loading": "avoid heavy overhead loading",
    "avoid_end_range_abduction": "avoid end-range shoulder abduction",
    "avoid_loaded_external_rotation": "avoid loaded external rotation",
    "avoid_end_range_external_rotation": "avoid end-range external rotation",
    "avoid_end_range_extension": "avoid end-range extension",
    "limit_overhead_loading": "limit overhead loading",
    "avoid_forward_head_posture": "avoid prolonged forward head posture",
    "avoid_heavy_resisted_flexion": "avoid heavy resisted elbow flexion",
    "avoid_deep_hip_flexion": "avoid deep hip flexion (>90°)",
    "avoid_end_range_internal_rotation": "avoid end-range hip internal rotation",
    "avoid_crossed_leg_sitting": "avoid sitting cross-legged",
    "avoid_side_sleeping_painful_side": "avoid side-sleeping on painful hip",
    "avoid_impact": "avoid impact / jarring activities",
    "avoid_jumping": "avoid jumping / plyometrics",
    "avoid_repetitive_gripping": "avoid repetitive gripping activities",
    "avoid_wrist_flexion_loading": "avoid loaded wrist flexion",
    "avoid_loading_during_flares": "avoid loading during inflammatory flares",
    "gentle_ROM_only_in_acute": "gentle ROM only during acute phase",
}


def _human_contra(codes):
    """Translate contraindication codes to plain-English labels."""
    return [CONTRAINDICATION_LABELS.get(c, c.replace("_", " ")) for c in codes]


# ── Main parser ─────────────────────────────────────────────────────────────

def parse_imaging_report(report_text: str) -> dict:
    """Parse a radiology report and extract structured findings.

    Args:
        report_text: Raw text of an MRI/X-ray/CT report.

    Returns:
        dict with keys:
            findings: list of {finding, severity, condition_hint,
                               contraindications, exercise_bias, snippet}
            contraindications: deduped list of contraindication codes
            contraindications_human: plain-English contraindication labels
            exercise_bias: dominant movement bias ("flexion"/"extension"/"neutral"/"")
            red_flags: list of red-flag warnings (empty = safe to prescribe)
            condition_hints: list of suggested condition codes
            summary: one-line human-readable summary
    """
    if not report_text or not report_text.strip():
        return _empty_result()

    # Track what we've matched to avoid duplicate findings
    seen_findings = set()
    findings = []
    all_contra = []
    all_red_flags = []
    all_conditions = []
    bias_votes = {"extension": 0, "flexion": 0, "neutral": 0}

    for entry in IMAGING_PATTERNS:
        # Find the first NON-negated occurrence of this pattern
        match = None
        for candidate in re.finditer(entry["pattern"], report_text, re.IGNORECASE):
            if not _is_negated(report_text, candidate.start()):
                match = candidate
                break
        if not match:
            continue

        base_label = entry["finding"]
        if base_label in seen_findings:
            continue
        seen_findings.add(base_label)

        # Extract nearby vertebral level (e.g., L4-L5)
        window_start = max(0, match.start() - 25)
        window_end = min(len(report_text), match.end() + 45)
        window = report_text[window_start:window_end]

        level_str = ""
        level_match = LEVEL_PATTERN.search(window)
        if level_match:
            g1 = level_match.group(1).upper()
            g2 = level_match.group(2)
            level_str = f"{g1}-{g2.upper()}" if g2 else g1

        # Extract grade (spondylolisthesis, OA)
        grade_str = ""
        if "spondylolisthesis" in base_label.lower():
            gm = GRADE_PATTERN.search(window)
            if gm:
                grade_str = f"grade {gm.group(1)}"
        elif "osteoarthritis" in base_label.lower():
            klm = KL_GRADE_PATTERN.search(window)
            if klm:
                grade_str = f"K-L grade {klm.group(1)}"

        # Build display label
        finding_label = base_label
        if level_str and any(x in base_label.lower() for x in
                             ("disc", "stenosis", "spondyl", "facet", "nerve", "annular", "cervical")):
            finding_label += f" at {level_str}"
        if grade_str:
            finding_label += f" ({grade_str})"

        # Snippet for context
        snip_start = max(0, match.start() - 20)
        snip_end = min(len(report_text), match.end() + 60)
        snippet = report_text[snip_start:snip_end].strip()

        findings.append({
            "finding": finding_label,
            "severity": entry.get("severity", "mild"),
            "condition_hint": entry.get("condition_hint", ""),
            "contraindications": entry.get("contraindications", []),
            "exercise_bias": entry.get("exercise_bias", ""),
            "snippet": snippet,
        })

        all_contra.extend(entry.get("contraindications", []))
        if entry.get("condition_hint"):
            all_conditions.append(entry["condition_hint"])
        if entry.get("red_flag"):
            all_red_flags.append(entry["red_flag"])
        bias = entry.get("exercise_bias")
        if bias in bias_votes:
            bias_votes[bias] += 1

    # Dominant exercise bias
    dominant_bias = ""
    if any(bias_votes.values()):
        # Remove neutral from voting unless it's the only one
        directional = {k: v for k, v in bias_votes.items() if k != "neutral" and v > 0}
        if directional:
            dominant_bias = max(directional, key=directional.get)
        elif bias_votes["neutral"] > 0:
            dominant_bias = "neutral"

    unique_contra = sorted(set(all_contra))
    unique_conditions = sorted(set(all_conditions))

    if findings:
        top_findings = [f["finding"] for f in findings[:4]]
        summary = "Detected: " + "; ".join(top_findings)
        if len(findings) > 4:
            summary += f" (+{len(findings)-4} more)"
        if dominant_bias and dominant_bias != "neutral":
            summary += f" — {dominant_bias}-biased approach indicated"
    else:
        summary = "No structured findings detected in imaging text"

    return {
        "findings": findings,
        "contraindications": unique_contra,
        "contraindications_human": _human_contra(unique_contra),
        "exercise_bias": dominant_bias,
        "red_flags": all_red_flags,
        "condition_hints": unique_conditions,
        "summary": summary,
    }


def _empty_result():
    return {
        "findings": [],
        "contraindications": [],
        "contraindications_human": [],
        "exercise_bias": "",
        "red_flags": [],
        "condition_hints": [],
        "summary": "",
    }


# ── Formatting helpers ──────────────────────────────────────────────────────

def format_imaging_for_prompt(parsed: dict) -> str:
    """Format parsed findings as a compact block for system-prompt injection."""
    if not parsed or not parsed.get("findings"):
        return ""

    lines = ["=== IMAGING REPORT FINDINGS (objective clinical data from radiology) ==="]
    for f in parsed["findings"]:
        sev = f.get("severity", "").upper()
        lines.append(f"- [{sev}] {f['finding']}")

    if parsed.get("contraindications_human"):
        lines.append("\nMovement contraindications to respect:")
        for c in parsed["contraindications_human"]:
            lines.append(f"  - {c}")

    if parsed.get("exercise_bias") and parsed["exercise_bias"] != "neutral":
        lines.append(f"\nExercise direction bias: {parsed['exercise_bias']}-biased "
                     f"(prefer exercises that load the spine/joint in this direction)")

    if parsed.get("condition_hints"):
        lines.append(f"\nImaging suggests condition code(s): {', '.join(parsed['condition_hints'])}")

    if parsed.get("red_flags"):
        lines.append("\n!!! IMAGING RED FLAGS — DO NOT PRESCRIBE EXERCISE !!!")
        for rf in parsed["red_flags"]:
            lines.append(f"  ! {rf}")
        lines.append("If any red flag above is present, explain the situation to the patient "
                     "and recommend medical/specialist review instead of prescribing exercises.")

    lines.append("\nIMPORTANT: Use these imaging findings to tailor exercise selection. "
                 "Respect all contraindications. Reference the findings in your clinical "
                 "reasoning explanation so the patient understands WHY the plan was adjusted.")

    return "\n".join(lines)


def format_imaging_for_display(parsed: dict) -> str:
    """Format parsed findings as markdown for the UI assessment summary."""
    if not parsed or not parsed.get("findings"):
        return ""

    sev_icon = {"severe": "🔴", "moderate": "🟡", "mild": "🔵"}
    parts = ["**🩻 Imaging Report Analysis**\n"]

    for f in parsed["findings"]:
        icon = sev_icon.get(f.get("severity", ""), "•")
        parts.append(f"{icon} **{f['finding']}** — _{f.get('severity', '')}_")

    if parsed.get("contraindications_human"):
        parts.append("\n**Contraindications respected:**")
        for c in parsed["contraindications_human"]:
            parts.append(f"- {c}")

    if parsed.get("exercise_bias") and parsed["exercise_bias"] != "neutral":
        parts.append(f"\n**Exercise bias:** {parsed['exercise_bias']}-biased approach")

    if parsed.get("red_flags"):
        parts.append("\n**⚠️ Imaging Red Flags:**")
        for rf in parsed["red_flags"]:
            parts.append(f"- {rf}")

    return "\n".join(parts)
