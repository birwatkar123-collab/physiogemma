"""
knowledge_base.py — Lightweight condition-based RAG for PhysioGemma
====================================================================
Simple keyword retrieval: no embeddings, no vector DB, O(n) list scan.
Injects relevant clinical knowledge into the system prompt to improve
Gemma's reasoning accuracy for specific conditions.
"""

PHYSIO_KB = [
    # ── Low Back Pain ──
    {"condition": "LBP", "text": (
        "For chronic low back pain, core stabilization exercises like McGill Big 3 "
        "(curl-up, side plank, bird dog) are first-line. Avoid prolonged sitting >30 min. "
        "Graded activity approach is superior to rest. McKenzie extension preferred when "
        "sitting aggravates. Evidence: NICE NG59, Hayden 2021 Cochrane."
    )},
    {"condition": "LBP", "text": (
        "Red flag differentials for LBP: cauda equina (bilateral leg weakness, saddle "
        "anaesthesia, bladder/bowel dysfunction) requires emergency referral. Night pain "
        "unrelieved by position may indicate malignancy. Fever + LBP suggests infection."
    )},
    # ── Knee Osteoarthritis ──
    {"condition": "KNEE_OA", "text": (
        "Quadriceps strengthening is the single most effective intervention for knee OA. "
        "Step-ups, wall sits, and straight leg raises are evidence-based. Avoid deep squats "
        "and high-impact loading in early stages. Cycling and swimming are joint-friendly "
        "cardio. Evidence: Fransen 2015 Cochrane, OARSI guidelines."
    )},
    {"condition": "KNEE_OA", "text": (
        "BMI >30 increases knee joint load by 3-4x body weight per step. Weight management "
        "combined with exercise produces greater symptom relief than either alone. "
        "Morning stiffness <30 min differentiates OA from inflammatory arthritis."
    )},
    # ── Sciatica ──
    {"condition": "SCIATICA", "text": (
        "Extension-based exercises (McKenzie press-ups) reduce disc-related nerve compression. "
        "Avoid prolonged sitting, forward flexion, and heavy lifting during acute phase. "
        "Neural glides (sciatic nerve flossing) improve nerve mobility. Centralization of "
        "symptoms is a positive prognostic sign. Evidence: Albert 2012, Cochrane 2023."
    )},
    {"condition": "SCIATICA", "text": (
        "Progressive neurological deficit (worsening foot drop, spreading numbness) or "
        "bilateral sciatica warrants urgent imaging and surgical referral. Cough/sneeze "
        "aggravation suggests disc involvement. SLR >30-70 degrees positive is diagnostic."
    )},
    # ── Neck Pain ──
    {"condition": "NECK", "text": (
        "Postural correction (chin tucks, scapular retraction) and deep neck flexor "
        "strengthening are first-line for mechanical neck pain. Avoid sustained forward "
        "head posture. Multimodal approach: exercise + manual therapy is superior to either "
        "alone. Evidence: Gross 2015 Cochrane, Blanpied 2017 CPG."
    )},
    {"condition": "NECK", "text": (
        "Canadian C-Spine Rule: high-risk factors (age >65, dangerous mechanism, limb "
        "paraesthesia) require imaging. Dizziness with neck movement may indicate vertebral "
        "artery involvement — refer for assessment before exercise."
    )},
    # ── Frozen Shoulder ──
    {"condition": "FROZEN_SHOULDER", "text": (
        "Adhesive capsulitis progresses through freezing (2-9 mo), frozen (4-12 mo), and "
        "thawing (5-24 mo) phases. Gentle ROM in pain-free range during freezing phase. "
        "Aggressive stretching in the freezing phase worsens inflammation. Progress to "
        "active stretching only in frozen/thawing phases. Evidence: Kelley 2009, BESS guidelines."
    )},
    # ── Hip OA ──
    {"condition": "HIP_OA", "text": (
        "Hip abductor strengthening (clamshells, side-lying leg raises) and gentle ROM "
        "exercises are first-line. Groin pain with internal rotation is classic hip OA. "
        "Aquatic therapy is highly effective for hip OA. Walking aid on contralateral side "
        "reduces joint load 60%. Evidence: Bennell 2014, EULAR guidelines."
    )},
    # ── Plantar Fasciitis ──
    {"condition": "PLANTAR_FASCIITIS", "text": (
        "Calf stretching (gastrocnemius and soleus) combined with plantar fascia-specific "
        "stretching reduces pain. High-load strength training (heel raises with towel under "
        "toes) is superior to stretching alone. Night splints maintain dorsiflexion. "
        "First-step morning pain is pathognomonic. Evidence: Rathleff 2015, APTA CPG."
    )},
    # ── Tennis Elbow ──
    {"condition": "TENNIS_ELBOW", "text": (
        "Eccentric wrist extension exercises are the gold standard for lateral epicondylalgia. "
        "Tyler twist (FlexBar) shows strong evidence. Avoid repetitive gripping during acute "
        "phase. Counterforce brace reduces tendon load during activities. Isometric holds "
        "provide immediate analgesic effect. Evidence: Coombes 2015, Bisset 2006."
    )},
]


def retrieve_knowledge(condition: str) -> str:
    """Retrieve clinical knowledge entries matching a condition code.

    Args:
        condition: Condition code (LBP, KNEE_OA, SCIATICA, etc.) or empty string.

    Returns:
        Newline-joined relevant knowledge paragraphs, or empty string if no match.
    """
    if not condition:
        return ""
    condition = condition.upper().strip()
    results = [item["text"] for item in PHYSIO_KB if item["condition"] == condition]
    return "\n".join(results)
