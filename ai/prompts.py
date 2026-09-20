"""
System prompts and message templates for the AI Study-Focus Assistant.
Strictly grounded to prevent LLM hallucinations and enforce non-medical guardrails.
"""

from pathlib import Path
from typing import List, Optional
from core.statistics import SessionStatistics

SYSTEM_PROMPT_STUDY_COACH = """You are an empathetic, encouraging AI Study-Focus Coach.
Your primary role is to help students optimize their study sessions, manage study pacing, recommend effective study techniques (such as the Pomodoro technique), and give tips for taking productive breaks.

STRICT ACCURACY & RELIABILITY CONSTRAINTS:
1. GROUNDING MANDATE: You must ONLY make statements based on data explicitly provided in the session context prompt below.
2. ZERO HALLUCINATION / INVENTION RULE: You must NEVER invent or assume:
   - study duration or session length beyond what is stated in the prompt
   - previous heart-rate readings not listed in recent readings
   - number of completed tasks, assignments, or study topics
   - future time intervals or exact schedules not explicitly provided
   - physiological conditions, health status, or physical states
   - user actions or past behaviors
3. MISSING DATA HANDLING: If any requested information is missing or marked 'Information unavailable', explicitly state that the information is unavailable rather than guessing or inferring it.
4. NUMERICAL ACCURACY: You must accurately interpret the supplied numerical statistics. 
   - NEVER say the latest heart rate is "lower than average" when latest > average. 
   - NEVER say it is "higher than average" when latest < average.
5. NO DIAGNOSIS OR CAUSAL INFERENCE: You must NOT infer a user's psychological, emotional, physical, or medical state from heart rate. 
   - Do NOT infer or claim proof of: stress, anxiety, fatigue, tiredness, relaxation, burnout, lack of focus, loss of concentration, emotional state, physical exhaustion, or any medical condition.
6. NO DATA-DRIVEN INTERVENTIONS: You must NOT use heart-rate statistics as evidence that the user should do something.
   - Do NOT claim the data proves they should: take a break, slow down, speed up, change study technique, hydrate, eat, exercise, rest, or change posture.
7. SUGGESTIONS vs FACTS: General study suggestions (like taking a break or hydrating) are allowed, but they must be explicitly framed as optional general suggestions rather than conclusions from heart-rate data. (e.g., prefer "If you feel a short break would help, you could take one" instead of "Your decreasing heart rate means you should take a break").
8. NEUTRAL LANGUAGE & UNCERTAINTY: When discussing heart-rate data, you must use neutral language and explicitly acknowledge uncertainty regarding the reason for the trend. 
   - Acceptable phrases: "The data shows...", "The recorded readings indicate...", "The recent trend is...", "The available data does not establish why this trend occurred."
   - Example acceptable sentence: "The simulated readings show a decreasing trend, but the available data does not establish the reason for that change."
9. SIMULATED SENSOR METRICS: Heart-rate readings supplied to you are SIMULATED and are used purely as general engagement markers for study session pacing.
"""


def load_project_context(relative_path: str = "ai/project_context.md") -> str:
    """
    Safely load project context markdown from a project-root-safe path.
    Gracefully returns an empty string if the file is missing or unreadable.
    """
    try:
        project_root = Path(__file__).resolve().parent.parent
        target_path = project_root / relative_path
        if target_path.is_file():
            return target_path.read_text(encoding="utf-8").strip()
    except Exception:
        pass
    return ""


def get_combined_system_prompt() -> str:
    """
    Get the full system prompt combining SYSTEM_PROMPT_STUDY_COACH
    with project knowledge from ai/project_context.md if available.
    """
    context = load_project_context()
    if context:
        return f"{SYSTEM_PROMPT_STUDY_COACH}\n\nADDITIONAL PROJECT KNOWLEDGE & CONTEXT:\n{context}"
    return SYSTEM_PROMPT_STUDY_COACH


def build_coaching_prompt(
    stats: SessionStatistics,
    simulated_condition: str,
    recent_readings: List[str],
    user_note: str = ""
) -> str:
    """
    Build a strictly grounded prompt containing explicit study session metrics for the LLM.
    """
    bpm_str = f"{stats.latest_bpm:.1f} BPM" if stats.latest_bpm is not None else "Information unavailable"
    avg_str = f"{stats.average_bpm:.1f} BPM" if stats.average_bpm is not None else "Information unavailable"
    min_str = f"{stats.min_bpm:.1f} BPM" if stats.min_bpm is not None else "Information unavailable"
    max_str = f"{stats.max_bpm:.1f} BPM" if stats.max_bpm is not None else "Information unavailable"
    
    delta_prev = f"{stats.delta_latest_vs_previous:+.1f} BPM" if stats.delta_latest_vs_previous is not None else "Information unavailable"
    delta_avg = f"{stats.delta_latest_vs_average:+.1f} BPM" if stats.delta_latest_vs_average is not None else "Information unavailable"

    if stats.delta_latest_vs_average is not None:
        if stats.delta_latest_vs_average > 0.5:
            comparison_to_average = "HIGHER than average"
        elif stats.delta_latest_vs_average < -0.5:
            comparison_to_average = "LOWER than average"
        else:
            comparison_to_average = "CLOSE to average"
    else:
        comparison_to_average = "Information unavailable"

    cond_str = simulated_condition if simulated_condition else "Information unavailable"
    
    if stats.sample_count >= 2 and stats.duration_seconds is not None and stats.duration_seconds > 0:
        duration_str = f"{stats.duration_seconds:.1f} seconds"
    else:
        duration_str = "Information unavailable"

    if recent_readings:
        readings_formatted = "\n".join(f"  - {r}" for r in recent_readings)
    else:
        readings_formatted = "  - Information unavailable (No readings recorded yet)"

    note_formatted = user_note.strip() if user_note.strip() else "None provided"

    return (
        f"EXPLICIT STUDY SESSION CONTEXT (DO NOT ASSUME OR INVENT EXTRA DATA):\n"
        f"Data Source Note: Heart-rate metrics provided below are SIMULATED and used for engagement pacing only.\n\n"
        f"1. Current Heart Rate: {bpm_str}\n"
        f"2. Simulated Study Condition: {cond_str}\n"
        f"3. Session Duration (Measured): {duration_str}\n"
        f"4. Total Recorded Samples: {stats.sample_count}\n"
        f"5. Session Statistics:\n"
        f"   - Average: {avg_str}\n"
        f"   - Minimum: {min_str}\n"
        f"   - Maximum: {max_str}\n"
        f"   - Recent Trend: {stats.recent_trend}\n"
        f"   - Change from previous reading: {delta_prev}\n"
        f"   - Change from session average: {delta_avg}\n"
        f"   - Comparison to Average: {comparison_to_average}\n"
        f"6. Recent Heart-Rate Readings:\n{readings_formatted}\n"
        f"7. User's Optional Note: {note_formatted}\n\n"
        f"INSTRUCTIONS — YOU MUST FOLLOW THESE EXACTLY:\n"
        f"STEP 1 — STATE FACTS ONLY: Begin by stating 1-2 factual observations directly from the supplied data above, using neutral language.\n"
        f"  - Use phrases like: \"The data shows...\", \"The recorded readings indicate...\", \"The recent trend is...\"\n"
        f"  - Do NOT add reasons, causes, or interpretations to these observations.\n"
        f"STEP 2 — ACKNOWLEDGE UNCERTAINTY: After stating the facts, explicitly write one sentence acknowledging that the available data does not establish the reason for the observed trend or reading.\n"
        f"  - Example: \"The available data does not establish why this trend occurred.\"\n"
        f"STEP 3 — OPTIONAL GENERAL SUGGESTIONS ONLY: You may offer 1-2 general study suggestions, but they MUST be decoupled from the heart-rate data.\n"
        f"  - Frame them as optional and self-assessed: \"If you feel a break would help, you could take one.\"\n"
        f"  - Do NOT use the heart-rate trend as the reason for the suggestion.\n"
        f"  - Do NOT say phrases like: \"since your HR is decreasing\", \"given the trend\", \"your heart rate means you should\", \"your heart rate shows you are\".\n"
        f"HARD PROHIBITIONS — NEVER do any of the following:\n"
        f"  - Infer: stress, anxiety, fatigue, tiredness, relaxation, burnout, lack of focus, loss of concentration, emotional state, physical exhaustion, or any medical condition.\n"
        f"  - Claim the data proves the user should: take a break, slow down, speed up, hydrate, eat, exercise, rest, change posture, or change study technique.\n"
        f"  - Invent: statistics, previous readings, tasks completed, physiological states, future schedules, or user behaviors.\n"
        f"  - If any value is 'Information unavailable', state it is unavailable rather than guessing."
    )
