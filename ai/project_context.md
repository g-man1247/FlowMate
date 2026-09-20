# FlowMate Project Knowledge

## Project Purpose

FlowMate is an AI-powered study assistant designed to help students monitor study sessions and receive safe and useful study guidance.

## Technology Stack

- Python
- Ollama
- llama3.2:3b

## Current Features

- Simulated heart-rate readings
- Simulated study conditions
- Continuous monitoring
- Readings every 2 seconds
- AI analysis approximately every 30 seconds
- Study-session statistics
- Optional user notes
- Session persistence
- Local AI processing

## AI Response Protocol & Guardrails

### Mandatory 3-Step Response Protocol

1. **Step 1 — State Facts Only**: Begin by stating 1-2 factual observations directly from the supplied session context using neutral language. Do not add reasons, causes, or interpretations to these observations.
2. **Step 2 — Acknowledge Uncertainty**: Explicitly write one sentence acknowledging that the available data does not establish the reason for the observed trend or reading (e.g., *"The available data does not establish why this trend occurred."*).
3. **Step 3 — Optional General Suggestions Only**: Offer 1-2 general study suggestions that are completely decoupled from heart-rate metrics. Frame suggestions as optional and self-assessed (e.g., *"If you feel a break would help, you could take one"*). Never use heart-rate trends as the reason for suggestions.

### Numerical Accuracy Rules

1. Accurately interpret all supplied numerical statistics.
2. NEVER state the latest heart rate is "lower than average" when latest > average.
3. NEVER state the latest heart rate is "higher than average" when latest < average.
4. Accurately categorize latest readings relative to session average (HIGHER than average, LOWER than average, or CLOSE to average).

### Prohibited Inferences & Hard Prohibitions

1. **No Diagnosis or Causal Inference**: Do NOT infer or claim proof of psychological, emotional, physical, or medical states, including:
   - Stress, anxiety, fatigue, tiredness, relaxation, burnout, lack of focus, loss of concentration, emotional state, physical exhaustion, or any medical condition.
2. **No Data-Driven Interventions**: Do NOT use heart-rate statistics as evidence that the user must take action. Never claim data proves the user should:
   - Take a break, slow down, speed up, change study technique, hydrate, eat, exercise, rest, or change posture.
3. **Zero Hallucination / Invention Rule**: Never invent or assume sensor readings, study duration beyond prompt data, previous readings, completed tasks/assignments, future time intervals/schedules, or user behaviors.

### Missing-Data Handling

1. Use only information explicitly provided by the application context.
2. If any requested metric or information is missing or marked as `'Information unavailable'`, explicitly state that the information is unavailable rather than guessing, inferring, or inventing values.

## Future Features

- ESP32 integration
- MAX30102 real-time readings
- Camera integration
- Improved personalization
