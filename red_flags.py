"""
red_flags.py — Clinical red flag detection for PhysioGemma
============================================================
Red flags are warning signs that indicate serious pathology requiring
immediate medical referral, NOT exercise prescription.

References:
  - NICE NG59 (Low back pain red flags)
  - BOA/BESS Guidelines (Knee red flags)
  - Canadian C-Spine Rules / Ottawa Rules
  - BSR Guidelines (Inflammatory arthritis screening)
  - Greenhalgh & Selfe 2006 (Red flags in MSK)
"""

# ── Red flags by condition ───────────────────────────────────────────────────

RED_FLAGS = {
    "LBP": {
        "name": "Lower Back Pain",
        "flags": [
            {
                "keywords": ["bladder", "bowel", "incontinence", "cant control urine",
                             "urine leaking", "peshab", "toilet control"],
                "flag": "Bladder or bowel dysfunction",
                "severity": "emergency",
                "indication": "Possible cauda equina syndrome",
                "action": "Seek emergency medical care immediately (within hours)",
            },
            {
                "keywords": ["saddle", "numbness between legs", "groin numb",
                             "perineal", "genital numbness"],
                "flag": "Saddle area numbness",
                "severity": "emergency",
                "indication": "Possible cauda equina syndrome",
                "action": "Seek emergency medical care immediately (within hours)",
            },
            {
                "keywords": ["both legs weak", "bilateral weakness", "legs giving way",
                             "cant walk properly", "both legs numb", "progressive weakness"],
                "flag": "Progressive bilateral leg weakness",
                "severity": "emergency",
                "indication": "Possible spinal cord compression",
                "action": "Seek emergency medical care immediately",
            },
            {
                "keywords": ["weight loss", "unexplained weight", "losing weight",
                             "wajan kam", "vajan kam"],
                "flag": "Unexplained weight loss with back pain",
                "severity": "urgent",
                "indication": "Screen for malignancy",
                "action": "See your doctor within 1-2 days for investigation",
            },
            {
                "keywords": ["night pain", "pain at night", "cant sleep", "wakes me up",
                             "no position helps", "raat ko dard"],
                "flag": "Unrelenting night pain not relieved by any position",
                "severity": "urgent",
                "indication": "Screen for tumor or infection",
                "action": "See your doctor within 1-2 days",
            },
            {
                "keywords": ["fever", "bukhar", "temperature", "chills", "sweating at night",
                             "night sweats"],
                "flag": "Fever or night sweats with back pain",
                "severity": "urgent",
                "indication": "Possible spinal infection (discitis/osteomyelitis)",
                "action": "See your doctor within 24 hours",
            },
            {
                "keywords": ["cancer", "tumor", "malignancy", "chemotherapy", "radiation treatment"],
                "flag": "History of cancer with new back pain",
                "severity": "urgent",
                "indication": "Screen for metastatic disease",
                "action": "See your oncologist or doctor urgently",
            },
            {
                "keywords": ["fall", "accident", "trauma", "injury", "hit", "crash",
                             "gir gaya", "chot"],
                "flag": "Significant trauma with sudden onset pain",
                "severity": "urgent",
                "indication": "Possible fracture",
                "action": "Get imaging (X-ray) before starting exercises",
            },
        ],
    },
    "KNEE_OA": {
        "name": "Knee Pain",
        "flags": [
            {
                "keywords": ["locked", "cant bend", "cant straighten", "stuck",
                             "knee wont move", "ghutna atka"],
                "flag": "Locked knee — unable to bend or straighten fully",
                "severity": "urgent",
                "indication": "Possible meniscal tear or loose body",
                "action": "See an orthopedic doctor for examination",
            },
            {
                "keywords": ["swollen immediately", "swelled up fast", "big swelling after",
                             "blew up", "rapid swelling", "sujan turant"],
                "flag": "Rapid swelling within 2 hours of injury",
                "severity": "urgent",
                "indication": "Possible ACL tear, fracture, or hemarthrosis",
                "action": "See a doctor urgently — may need imaging",
            },
            {
                "keywords": ["cant walk", "cant bear weight", "cant stand", "collapse",
                             "cant put weight", "chal nahi sakta"],
                "flag": "Unable to bear weight on the leg",
                "severity": "urgent",
                "indication": "Possible fracture or severe ligament injury",
                "action": "See a doctor — may need X-ray (Ottawa Knee Rules)",
            },
            {
                "keywords": ["hot knee", "red knee", "warm joint", "fever", "infected",
                             "lal sujan", "garam"],
                "flag": "Hot, red, swollen joint with or without fever",
                "severity": "emergency",
                "indication": "Possible septic arthritis — medical emergency",
                "action": "Seek emergency medical care — joint infection can cause permanent damage",
            },
            {
                "keywords": ["deformity", "bent wrong way", "looks different", "changed shape",
                             "bone sticking"],
                "flag": "Visible deformity after trauma",
                "severity": "emergency",
                "indication": "Possible fracture or dislocation",
                "action": "Seek emergency medical care immediately",
            },
            {
                "keywords": ["giving way", "buckles", "unstable", "knee collapses",
                             "gives out"],
                "flag": "Knee giving way repeatedly",
                "severity": "moderate",
                "indication": "Possible ligament insufficiency (ACL/PCL)",
                "action": "See an orthopedic doctor before starting exercises",
            },
        ],
    },
    "NECK": {
        "name": "Neck Pain",
        "flags": [
            {
                "keywords": ["both arms numb", "both hands tingling", "bilateral arm",
                             "weakness in hands", "dropping things", "clumsy hands",
                             "dono hath"],
                "flag": "Bilateral arm numbness or weakness",
                "severity": "emergency",
                "indication": "Possible cervical myelopathy (spinal cord compression)",
                "action": "Seek emergency medical care immediately",
            },
            {
                "keywords": ["walking problem", "gait", "balance", "unsteady", "stumbling",
                             "legs feel heavy", "difficulty walking"],
                "flag": "Gait disturbance with neck pain",
                "severity": "emergency",
                "indication": "Possible cervical spinal cord compression",
                "action": "Seek emergency medical care immediately",
            },
            {
                "keywords": ["drop attack", "sudden fall", "collapsed", "blacked out",
                             "dizzy turning head", "vertigo with neck"],
                "flag": "Drop attacks or dizziness with neck movement",
                "severity": "urgent",
                "indication": "Possible vertebral artery insufficiency",
                "action": "See a doctor before any neck exercises",
            },
            {
                "keywords": ["swallowing", "difficulty eating", "cant swallow", "throat",
                             "nigalna mushkil"],
                "flag": "Difficulty swallowing with neck pain",
                "severity": "urgent",
                "indication": "Possible retropharyngeal pathology",
                "action": "See a doctor within 24 hours",
            },
            {
                "keywords": ["fever", "stiff neck", "cant move neck at all", "severe stiffness",
                             "meningitis", "bukhar"],
                "flag": "Fever with severe neck stiffness",
                "severity": "emergency",
                "indication": "Possible meningitis",
                "action": "Seek emergency medical care immediately",
            },
            {
                "keywords": ["accident", "trauma", "fall", "hit head", "whiplash", "crash",
                             "chot lagi"],
                "flag": "Trauma with neck pain",
                "severity": "urgent",
                "indication": "Possible cervical fracture (Canadian C-Spine Rules)",
                "action": "Get imaging before any exercises — do NOT move neck forcefully",
            },
        ],
    },
    "FROZEN_SHOULDER": {
        "name": "Shoulder Pain",
        "flags": [
            {
                "keywords": ["cant lift arm", "arm wont move", "trauma", "fall on shoulder",
                             "injury", "dropped something heavy"],
                "flag": "Inability to lift arm after trauma",
                "severity": "urgent",
                "indication": "Possible rotator cuff rupture or fracture",
                "action": "See an orthopedic doctor — may need imaging",
            },
            {
                "keywords": ["deformity", "bump", "bone sticking out", "shoulder looks different",
                             "changed shape"],
                "flag": "Visible deformity of shoulder",
                "severity": "emergency",
                "indication": "Possible fracture or dislocation",
                "action": "Seek emergency medical care — do NOT force movement",
            },
            {
                "keywords": ["hot", "red", "fever", "infected", "warm shoulder",
                             "sujan bukhar"],
                "flag": "Hot, red, swollen shoulder with fever",
                "severity": "emergency",
                "indication": "Possible septic arthritis",
                "action": "Seek emergency medical care immediately",
            },
            {
                "keywords": ["chest pain", "arm pain", "breathing", "heart", "jaw pain",
                             "seene mein dard", "left arm"],
                "flag": "Shoulder/arm pain with chest pain or breathing difficulty",
                "severity": "emergency",
                "indication": "Possible cardiac event — NOT musculoskeletal",
                "action": "Call emergency services (112) immediately",
            },
        ],
    },
    # ── New conditions ───────────────────────────────────────────────────────
    "SCIATICA": {
        "name": "Sciatica",
        "flags": [
            {
                "keywords": ["bladder", "bowel", "incontinence", "saddle", "perineal"],
                "flag": "Bladder/bowel dysfunction or saddle numbness",
                "severity": "emergency",
                "indication": "Possible cauda equina syndrome",
                "action": "Seek emergency medical care immediately (within hours)",
            },
            {
                "keywords": ["foot drop", "cant lift foot", "tripping", "foot drags",
                             "progressive weakness"],
                "flag": "Progressive foot drop or leg weakness",
                "severity": "emergency",
                "indication": "Severe nerve compression requiring urgent intervention",
                "action": "Seek emergency medical care immediately",
            },
            {
                "keywords": ["both legs", "bilateral", "dono pair"],
                "flag": "Bilateral sciatica symptoms",
                "severity": "emergency",
                "indication": "Possible central disc herniation or cauda equina",
                "action": "Seek emergency medical care immediately",
            },
        ],
    },
    "HIP_OA": {
        "name": "Hip Pain / Osteoarthritis",
        "flags": [
            {
                "keywords": ["cant walk", "collapse", "cant bear weight", "fall",
                             "hip gave way"],
                "flag": "Unable to bear weight after fall/trauma",
                "severity": "emergency",
                "indication": "Possible hip fracture (especially age >65)",
                "action": "Seek emergency medical care — do NOT walk on it",
            },
            {
                "keywords": ["groin pain", "fever", "hot", "red", "swollen hip",
                             "bukhar"],
                "flag": "Hot, swollen hip joint with fever",
                "severity": "emergency",
                "indication": "Possible septic arthritis",
                "action": "Seek emergency medical care immediately",
            },
            {
                "keywords": ["sudden severe", "acute", "worst pain", "overnight"],
                "flag": "Sudden onset severe hip pain without trauma",
                "severity": "urgent",
                "indication": "Screen for avascular necrosis or fracture",
                "action": "See a doctor within 24 hours for imaging",
            },
        ],
    },
    "PLANTAR_FASCIITIS": {
        "name": "Plantar Fasciitis / Heel Pain",
        "flags": [
            {
                "keywords": ["numb foot", "foot numb", "tingling foot", "burning foot",
                             "no feeling in foot"],
                "flag": "Numbness or burning in the foot",
                "severity": "moderate",
                "indication": "Possible tarsal tunnel syndrome or neuropathy",
                "action": "See a doctor to rule out nerve compression",
            },
            {
                "keywords": ["swollen", "red", "hot", "fever", "infected"],
                "flag": "Red, hot, swollen foot with fever",
                "severity": "urgent",
                "indication": "Possible infection or gout",
                "action": "See a doctor within 24 hours",
            },
            {
                "keywords": ["snap", "popped", "tore", "rupture", "sudden sharp",
                             "cant walk"],
                "flag": "Sudden snap/pop in heel with inability to walk",
                "severity": "urgent",
                "indication": "Possible plantar fascia rupture",
                "action": "See a doctor — do NOT continue weight-bearing exercises",
            },
        ],
    },
    "TENNIS_ELBOW": {
        "name": "Tennis Elbow / Lateral Epicondylitis",
        "flags": [
            {
                "keywords": ["swollen", "red", "hot", "fever", "infected", "warm elbow"],
                "flag": "Red, hot, swollen elbow with fever",
                "severity": "urgent",
                "indication": "Possible septic bursitis or joint infection",
                "action": "See a doctor within 24 hours",
            },
            {
                "keywords": ["locked", "cant straighten", "cant bend", "deformity",
                             "trauma", "fall"],
                "flag": "Elbow locked or deformed after trauma",
                "severity": "urgent",
                "indication": "Possible fracture or dislocation",
                "action": "See a doctor — get X-ray before any exercises",
            },
            {
                "keywords": ["numb fingers", "tingling hand", "weak grip", "dropping",
                             "hand numb"],
                "flag": "Numbness/tingling radiating to hand",
                "severity": "moderate",
                "indication": "Possible nerve entrapment (radial/ulnar)",
                "action": "See a doctor to rule out nerve compression",
            },
        ],
    },
}

# ── General red flags (apply to ALL conditions) ─────────────────────────────

GENERAL_RED_FLAGS = [
    {
        "keywords": ["weight loss", "losing weight", "unexplained", "wajan kam",
                     "patla ho raha"],
        "flag": "Unexplained weight loss (>5kg in 3 months)",
        "severity": "urgent",
        "indication": "Screen for malignancy or systemic disease",
        "action": "See your doctor for blood tests and investigation",
    },
    {
        "keywords": ["night sweats", "sweating at night", "raat ko pasina"],
        "flag": "Night sweats",
        "severity": "urgent",
        "indication": "Screen for infection, malignancy, or inflammatory condition",
        "action": "See your doctor for investigation",
    },
    {
        "keywords": ["cancer", "tumor", "malignancy", "chemotherapy", "radiation",
                     "cancer tha", "cancer hai"],
        "flag": "History of cancer",
        "severity": "urgent",
        "indication": "New musculoskeletal pain may indicate metastasis",
        "action": "See your oncologist or doctor before starting exercises",
    },
    {
        "keywords": ["steroids long term", "immunosuppressed", "hiv", "transplant",
                     "immune system weak"],
        "flag": "Immunosuppression",
        "severity": "moderate",
        "indication": "Higher risk of infection; pain may have atypical cause",
        "action": "See your doctor to confirm musculoskeletal cause",
    },
    {
        "keywords": ["iv drug", "injection drug", "needle", "heroin"],
        "flag": "IV drug use history",
        "severity": "urgent",
        "indication": "Higher risk of spinal infection or endocarditis",
        "action": "See your doctor to rule out infection before exercises",
    },
    {
        "keywords": ["getting worse every day", "rapidly worsening", "much worse",
                     "cant function", "emergency"],
        "flag": "Rapidly worsening symptoms despite rest",
        "severity": "urgent",
        "indication": "Progressive pathology needs investigation",
        "action": "See your doctor within 24-48 hours",
    },
]


# ── Red flag detection engine ────────────────────────────────────────────────

def check_red_flags(text: str, condition: str = None) -> list:
    """
    Scan patient text for red flag keywords.
    Returns list of detected red flags sorted by severity.
    """
    text_lower = text.lower()
    detected = []

    # Check condition-specific flags
    if condition and condition in RED_FLAGS:
        for flag in RED_FLAGS[condition]["flags"]:
            if any(kw in text_lower for kw in flag["keywords"]):
                detected.append(flag)

    # Check ALL condition flags if no condition specified
    if not condition:
        for cond_flags in RED_FLAGS.values():
            for flag in cond_flags["flags"]:
                if any(kw in text_lower for kw in flag["keywords"]):
                    if flag not in detected:
                        detected.append(flag)

    # Always check general red flags
    for flag in GENERAL_RED_FLAGS:
        if any(kw in text_lower for kw in flag["keywords"]):
            detected.append(flag)

    # Sort by severity: emergency > urgent > moderate
    severity_order = {"emergency": 0, "urgent": 1, "moderate": 2}
    detected.sort(key=lambda f: severity_order.get(f["severity"], 3))

    return detected


def format_red_flag_warning(flags: list) -> str:
    """Format detected red flags into a clear warning message."""
    if not flags:
        return ""

    has_emergency = any(f["severity"] == "emergency" for f in flags)

    lines = []
    if has_emergency:
        lines.append("## IMPORTANT MEDICAL WARNING\n")
        lines.append("**Your symptoms include signs that need IMMEDIATE medical attention.**\n")
        lines.append("**DO NOT start exercises until a doctor has examined you.**\n")
    else:
        lines.append("## Medical Advisory\n")
        lines.append("**Some of your symptoms need medical evaluation before starting exercises.**\n")

    for flag in flags:
        severity_icon = {"emergency": "🔴", "urgent": "🟡", "moderate": "🟠"}.get(flag["severity"], "⚪")
        lines.append(f"\n{severity_icon} **{flag['flag']}**")
        lines.append(f"- *Possible concern:* {flag['indication']}")
        lines.append(f"- *Recommended action:* {flag['action']}")

    lines.append("\n---")
    lines.append("*PhysioGemma prioritizes your safety. These warnings are based on ")
    lines.append("established clinical guidelines (NICE, Canadian C-Spine Rules, BOA/BESS). ")
    lines.append("Please consult a qualified healthcare professional.*")

    return "\n".join(lines)
