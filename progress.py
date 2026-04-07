"""
progress.py — Patient Progress Tracking, Recovery Chart & AI Insights
======================================================================
Session logging, adherence tracking, milestone detection, recovery
visualization, and rule-based progress analysis for PhysioGemma Agent.

Data persists via browser localStorage (synced through Gradio JS bridge).
"""

import json
import uuid
from datetime import datetime, timedelta

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches


# ── Data Model ──────────────────────────────────────────────────────────────

def create_empty_progress(condition: str = "", exercise_level: int = 0) -> dict:
    """Return a fresh progress_data dict."""
    return {
        "patient_id": str(uuid.uuid4())[:8],
        "condition": condition,
        "exercise_level": exercise_level,
        "sessions": [],
        "milestones": [],
    }


def log_session(
    progress_data: dict,
    pain_vas: float,
    exercises_completed: list,
    exercises_prescribed: list,
    difficulty_rating: int,
    notes: str,
    exercise_level: int = 0,
) -> dict:
    """Append a new session entry. Returns updated progress_data."""
    session = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.now().strftime("%H:%M"),
        "pain_vas": round(float(pain_vas), 1),
        "exercises_completed": list(exercises_completed),
        "exercises_prescribed": list(exercises_prescribed),
        "adherence_pct": get_adherence_percentage_raw(exercises_completed, exercises_prescribed),
        "difficulty_rating": int(difficulty_rating),
        "notes": str(notes),
        "exercise_level": int(exercise_level),
    }
    progress_data["sessions"].append(session)

    # Update level if changed
    if exercise_level:
        progress_data["exercise_level"] = exercise_level

    # Check for new milestones
    new_milestones = check_milestones(progress_data)
    progress_data["milestones"].extend(new_milestones)

    return progress_data


# ── Stats & Analysis ────────────────────────────────────────────────────────

def get_adherence_percentage_raw(completed: list, prescribed: list) -> float:
    """Calculate adherence % from raw lists."""
    if not prescribed:
        return 100.0
    return round(len(completed) / len(prescribed) * 100, 1)


def get_pain_trend(progress_data: dict, window: int = 7) -> dict:
    """Pain stats over recent sessions."""
    sessions = progress_data.get("sessions", [])
    if not sessions:
        return {"current": None, "average": None, "min": None, "max": None,
                "delta": None, "trend": "insufficient_data"}

    recent = sessions[-window:]
    pain_vals = [s["pain_vas"] for s in recent]

    current = pain_vals[-1]
    first = pain_vals[0]
    delta = round(current - first, 1)

    if delta < -0.5:
        trend = "improving"
    elif delta > 0.5:
        trend = "worsening"
    else:
        trend = "stable"

    return {
        "current": current,
        "average": round(sum(pain_vals) / len(pain_vals), 1),
        "min": min(pain_vals),
        "max": max(pain_vals),
        "delta": delta,
        "trend": trend,
        "sessions_analyzed": len(recent),
    }


def get_overall_stats(progress_data: dict) -> dict:
    """Aggregate stats across all sessions."""
    sessions = progress_data.get("sessions", [])
    if not sessions:
        return {"total_sessions": 0}

    pain_vals = [s["pain_vas"] for s in sessions]
    adherence_vals = [s["adherence_pct"] for s in sessions]
    difficulty_vals = [s["difficulty_rating"] for s in sessions]

    # Calculate streak (consecutive days with sessions)
    dates = sorted(set(s["date"] for s in sessions))
    current_streak = 1
    best_streak = 1
    for i in range(1, len(dates)):
        d1 = datetime.strptime(dates[i - 1], "%Y-%m-%d")
        d2 = datetime.strptime(dates[i], "%Y-%m-%d")
        if (d2 - d1).days == 1:
            current_streak += 1
            best_streak = max(best_streak, current_streak)
        else:
            current_streak = 1

    # Level changes
    levels = [s.get("exercise_level", 0) for s in sessions if s.get("exercise_level")]
    level_changes = 0
    for i in range(1, len(levels)):
        if levels[i] != levels[i - 1]:
            level_changes += 1

    first_pain = pain_vals[0]
    last_pain = pain_vals[-1]
    pain_change_pct = round((last_pain - first_pain) / max(first_pain, 0.1) * 100, 1)

    return {
        "total_sessions": len(sessions),
        "date_range": f"{sessions[0]['date']} to {sessions[-1]['date']}",
        "first_pain": first_pain,
        "current_pain": last_pain,
        "pain_change_pct": pain_change_pct,
        "avg_pain": round(sum(pain_vals) / len(pain_vals), 1),
        "avg_adherence": round(sum(adherence_vals) / len(adherence_vals), 1),
        "avg_difficulty": round(sum(difficulty_vals) / len(difficulty_vals), 1),
        "current_streak": current_streak,
        "best_streak": best_streak,
        "level_changes": level_changes,
        "current_level": levels[-1] if levels else progress_data.get("exercise_level", 0),
        "level_at_start": levels[0] if levels else progress_data.get("exercise_level", 0),
        "milestones_earned": len(progress_data.get("milestones", [])),
    }


def check_milestones(progress_data: dict) -> list:
    """Detect newly earned milestones."""
    sessions = progress_data.get("sessions", [])
    existing = {m.get("type") for m in progress_data.get("milestones", [])}
    new_milestones = []
    today = datetime.now().strftime("%Y-%m-%d")

    n = len(sessions)
    if n == 0:
        return []

    # First session
    if n == 1 and "first_session" not in existing:
        new_milestones.append({"date": today, "type": "first_session", "label": "First session logged!"})

    # 7 sessions
    if n >= 7 and "seven_sessions" not in existing:
        new_milestones.append({"date": today, "type": "seven_sessions", "label": "7 sessions completed!"})

    # 14 sessions
    if n >= 14 and "fourteen_sessions" not in existing:
        new_milestones.append({"date": today, "type": "fourteen_sessions", "label": "14 sessions — 2 week warrior!"})

    # Pain below 3.5 (moderate threshold)
    if sessions[-1]["pain_vas"] < 3.5 and "pain_below_moderate" not in existing:
        new_milestones.append({"date": today, "type": "pain_below_moderate", "label": "Pain dropped below moderate!"})

    # 50% pain reduction
    if n >= 3:
        first_avg = sum(s["pain_vas"] for s in sessions[:3]) / 3
        last_avg = sum(s["pain_vas"] for s in sessions[-3:]) / 3
        if first_avg > 0 and last_avg <= first_avg * 0.5 and "half_pain_reduction" not in existing:
            new_milestones.append({"date": today, "type": "half_pain_reduction", "label": "50% pain reduction achieved!"})

    # Perfect adherence streak (3+ sessions at 100%)
    if n >= 3 and "perfect_streak_3" not in existing:
        last_3 = sessions[-3:]
        if all(s["adherence_pct"] >= 100 for s in last_3):
            new_milestones.append({"date": today, "type": "perfect_streak_3", "label": "3 perfect adherence sessions!"})

    return new_milestones


# ── Recovery Chart ──────────────────────────────────────────────────────────

def generate_recovery_chart(progress_data: dict):
    """Generate a dual-axis recovery chart. Returns matplotlib Figure or None."""
    sessions = progress_data.get("sessions", [])
    if len(sessions) < 1:
        return None

    dates = []
    pain_vals = []
    adherence_vals = []
    for s in sessions:
        try:
            dates.append(datetime.strptime(s["date"], "%Y-%m-%d"))
        except (ValueError, KeyError):
            dates.append(datetime.now())
        pain_vals.append(s.get("pain_vas", 0))
        adherence_vals.append(s.get("adherence_pct", 0))

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), height_ratios=[2, 1],
                                     sharex=True, facecolor='#f8fafc')

    # ── Top: Pain VAS over time ──
    ax1.set_facecolor('#f8fafc')

    # Pain zone backgrounds
    ax1.axhspan(0, 3.5, alpha=0.08, color='#10b981', label='Mild (0-3.5)')
    ax1.axhspan(3.5, 7.5, alpha=0.08, color='#f59e0b', label='Moderate (3.5-7.5)')
    ax1.axhspan(7.5, 10, alpha=0.08, color='#ef4444', label='Severe (7.5-10)')

    # Pain line
    ax1.plot(dates, pain_vals, 'o-', color='#3b82f6', linewidth=2.5,
             markersize=8, markerfacecolor='white', markeredgewidth=2,
             markeredgecolor='#3b82f6', zorder=5)

    # Fill under curve
    ax1.fill_between(dates, pain_vals, alpha=0.15, color='#3b82f6')

    # Milestones
    milestones = progress_data.get("milestones", [])
    for m in milestones:
        try:
            m_date = datetime.strptime(m["date"], "%Y-%m-%d")
            if dates[0] <= m_date <= dates[-1]:
                ax1.axvline(x=m_date, color='#8b5cf6', linestyle='--', alpha=0.5, linewidth=1)
                ax1.annotate(m["label"], xy=(m_date, 9.5), fontsize=7,
                             color='#8b5cf6', ha='center', rotation=30)
        except (ValueError, KeyError):
            pass

    # Boonstra cutoff lines
    ax1.axhline(y=3.5, color='#f59e0b', linestyle=':', alpha=0.4, linewidth=1)
    ax1.axhline(y=7.5, color='#ef4444', linestyle=':', alpha=0.4, linewidth=1)

    ax1.set_ylim(0, 10)
    ax1.set_ylabel('Pain Level (VAS)', fontsize=11, fontweight='bold', color='#334155')
    ax1.set_title('Recovery Progress', fontsize=14, fontweight='bold', color='#1e40af', pad=12)
    ax1.grid(True, alpha=0.2, color='#94a3b8')
    ax1.tick_params(colors='#64748b')

    # Legend
    handles = [
        mpatches.Patch(color='#10b981', alpha=0.3, label='Mild'),
        mpatches.Patch(color='#f59e0b', alpha=0.3, label='Moderate'),
        mpatches.Patch(color='#ef4444', alpha=0.3, label='Severe'),
    ]
    ax1.legend(handles=handles, loc='upper right', fontsize=8, framealpha=0.8)

    # ── Bottom: Adherence bars ──
    ax2.set_facecolor('#f8fafc')

    bar_colors = []
    for a in adherence_vals:
        if a >= 80:
            bar_colors.append('#10b981')
        elif a >= 50:
            bar_colors.append('#f59e0b')
        else:
            bar_colors.append('#ef4444')

    bar_width = max(0.5, min(2, 30 / max(len(dates), 1)))
    ax2.bar(dates, adherence_vals, width=bar_width, color=bar_colors, alpha=0.8, edgecolor='white')
    ax2.axhline(y=80, color='#10b981', linestyle='--', alpha=0.5, linewidth=1, label='Target (80%)')
    ax2.set_ylim(0, 110)
    ax2.set_ylabel('Adherence %', fontsize=11, fontweight='bold', color='#334155')
    ax2.grid(True, alpha=0.2, color='#94a3b8')
    ax2.tick_params(colors='#64748b')
    ax2.legend(loc='lower right', fontsize=8)

    # Date formatting
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    if len(dates) > 14:
        ax2.xaxis.set_major_locator(mdates.WeekdayLocator())
    plt.xticks(rotation=30, fontsize=9)

    plt.tight_layout()
    return fig


# ── AI Insights (Rule-Based Analysis) ──────────────────────────────────────

def tool_analyze_progress(progress_data_json: str) -> dict:
    """Analyze patient progress and return structured insights for Gemma narration."""
    try:
        progress_data = json.loads(progress_data_json) if isinstance(progress_data_json, str) else progress_data_json
    except (json.JSONDecodeError, TypeError):
        return {"error": "Invalid progress data", "insights": [], "recommendation": "insufficient_data"}

    sessions = progress_data.get("sessions", [])
    if len(sessions) < 1:
        return {
            "summary": {"total_sessions": 0},
            "insights": [{"type": "info", "text": "No sessions logged yet. Start tracking to see insights!"}],
            "recommendation": "insufficient_data",
        }

    stats = get_overall_stats(progress_data)
    pain_trend = get_pain_trend(progress_data)
    insights = []

    # ── Pain trend insights ──
    if stats["total_sessions"] >= 3:
        pct = stats["pain_change_pct"]
        if pct <= -30:
            insights.append({"type": "improvement",
                             "text": f"Excellent! Pain decreased {abs(pct):.0f}% (from {stats['first_pain']} to {stats['current_pain']})"})
        elif pct <= -10:
            insights.append({"type": "improvement",
                             "text": f"Good progress — pain down {abs(pct):.0f}% (from {stats['first_pain']} to {stats['current_pain']})"})
        elif pct >= 20:
            insights.append({"type": "concern",
                             "text": f"Pain has increased {pct:.0f}%. Consider consulting your physiotherapist."})
        else:
            insights.append({"type": "info",
                             "text": f"Pain is stable around {stats['avg_pain']}/10. Keep consistent with exercises."})

    # ── Progress readiness (Boonstra thresholds) ──
    if len(sessions) >= 3:
        last_3_pain = [s["pain_vas"] for s in sessions[-3:]]
        avg_last_3 = sum(last_3_pain) / 3
        current_level = stats.get("current_level", 0)

        # Check if ready to progress based on Boonstra cutoffs
        thresholds = {1: 7.5, 2: 5.0, 3: 3.5, 4: 1.0}
        if current_level in thresholds:
            next_threshold = thresholds[current_level]
            if avg_last_3 < next_threshold and all(p < next_threshold for p in last_3_pain):
                insights.append({"type": "ready_to_progress",
                                 "text": f"Last 3 sessions average pain {avg_last_3:.1f}/10 — you may be ready to progress to Level {current_level + 1}"})

    # ── Adherence insights ──
    if len(sessions) >= 3:
        recent_adherence = [s["adherence_pct"] for s in sessions[-3:]]
        avg_recent_adh = sum(recent_adherence) / 3
        if avg_recent_adh >= 90:
            insights.append({"type": "achievement",
                             "text": f"Outstanding adherence ({avg_recent_adh:.0f}% over last 3 sessions)! Keep it up."})
        elif avg_recent_adh < 60:
            insights.append({"type": "concern",
                             "text": f"Adherence dropped to {avg_recent_adh:.0f}% recently. Even partial sessions help — try doing your top 3 exercises."})

    # ── Difficulty trend ──
    if len(sessions) >= 3:
        recent_diff = [s["difficulty_rating"] for s in sessions[-3:]]
        avg_diff = sum(recent_diff) / 3
        if avg_diff >= 4.0 and pain_trend.get("trend") != "improving":
            insights.append({"type": "suggestion",
                             "text": "Exercises feel hard and pain isn't improving — consider maintaining current level longer or asking about modifications."})
        elif avg_diff <= 2.0 and stats.get("current_level", 0) < 5:
            insights.append({"type": "suggestion",
                             "text": "Exercises feel easy — you might benefit from progressing to the next level."})

    # ── Stagnation detection ──
    if len(sessions) >= 5:
        last_5_pain = [s["pain_vas"] for s in sessions[-5:]]
        pain_range = max(last_5_pain) - min(last_5_pain)
        if pain_range < 0.5:
            insights.append({"type": "info",
                             "text": f"Pain has been steady at {stats['current_pain']}/10 for 5+ sessions. A physiotherapist review could help optimize your plan."})

    # ── Streak recognition ──
    if stats.get("current_streak", 0) >= 7:
        insights.append({"type": "achievement",
                         "text": f"Amazing {stats['current_streak']}-day exercise streak! Consistency is key to recovery."})
    elif stats.get("current_streak", 0) >= 3:
        insights.append({"type": "achievement",
                         "text": f"{stats['current_streak']}-day streak — great consistency!"})

    # ── Milestones ──
    milestones = progress_data.get("milestones", [])
    if milestones:
        latest = milestones[-1]
        insights.append({"type": "milestone",
                         "text": f"Latest milestone: {latest['label']}"})

    # ── Recommendation ──
    recommendation = "maintain"
    if len(sessions) >= 3:
        if any(i["type"] == "ready_to_progress" for i in insights):
            recommendation = "progress"
        elif any(i["type"] == "concern" for i in insights) and pain_trend.get("trend") == "worsening":
            recommendation = "regress"

    return {
        "summary": stats,
        "pain_trend": pain_trend,
        "insights": insights,
        "recommendation": recommendation,
    }


# ── Serialization ───────────────────────────────────────────────────────────

def serialize_progress(progress_data: dict) -> str:
    """JSON-serialize for localStorage."""
    return json.dumps(progress_data, default=str)


def deserialize_progress(json_str: str) -> dict:
    """Parse JSON from localStorage. Returns empty progress if invalid."""
    if not json_str or json_str == '{}':
        return create_empty_progress()
    try:
        data = json.loads(json_str)
        if isinstance(data, dict) and "sessions" in data:
            return data
        return create_empty_progress()
    except (json.JSONDecodeError, TypeError):
        return create_empty_progress()
