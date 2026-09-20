import time
import sys
from config.settings import (
    DISCLAIMER_TEXT, 
    DEFAULT_OLLAMA_MODEL, 
    DEFAULT_SENSOR_POLL_INTERVAL_SEC, 
    AI_COACHING_INTERVAL_SEC
)
from sensors.simulated import SimulatedHeartRateSensor
from sensors.camera import CameraFeedPlaceholder
from ai.ollama_client import OllamaClient
from core.assistant import StudyAssistant


def print_banner():
    print("=" * 70)
    print("         AI STUDY-FOCUS ASSISTANT (SIMULATED PROTOTYPE)")
    print("=" * 70)
    print(f"Default LLM Model: {DEFAULT_OLLAMA_MODEL}")
    print(f"\n[DISCLAIMER]\n{DISCLAIMER_TEXT}")
    print("=" * 70 + "\n")


def main():
    print_banner()

    # Instantiate simulated sensor & camera placeholder
    sensor = SimulatedHeartRateSensor(initial_condition="DEEP_STUDY")
    camera_placeholder = CameraFeedPlaceholder()
    ollama_client = OllamaClient()

    assistant = StudyAssistant(sensor=sensor, ollama_client=ollama_client)

    if not assistant.start_session():
        print("[FATAL] Could not initialize study session. Exiting.")
        sys.exit(1)

    print("Options:")
    print("  [1] Start Continuous Monitoring (Background)")
    print("  [2] Change simulated study condition")
    print("  [3] Ask AI Study Coach for feedback manually")
    print("  [4] Stop Continuous Monitoring")
    print("  [5] End session & Exit")
    print("-" * 70)

    try:
        while assistant.session_active:
            choice = input("\nSelect action (1-5): ").strip()

            if choice == "1":
                if getattr(assistant, "_monitor_thread", None) and assistant._monitor_thread.is_alive():
                    print("-> Continuous monitoring is already running.")
                else:
                    assistant.start_continuous_monitoring(
                        poll_interval=DEFAULT_SENSOR_POLL_INTERVAL_SEC,
                        ai_interval=AI_COACHING_INTERVAL_SEC,
                        print_callback=print
                    )

            elif choice == "2":
                conditions = sensor.get_available_conditions()
                print("\nAvailable Simulated Study Conditions:")
                for idx, cond in enumerate(conditions, 1):
                    print(f"  [{idx}] {cond}")
                cond_choice = input("Select condition number: ").strip()
                if cond_choice.isdigit() and 1 <= int(cond_choice) <= len(conditions):
                    selected = conditions[int(cond_choice) - 1]
                    sensor.set_condition(selected)
                    print(f"-> Switched simulated condition to: {selected}")
                else:
                    print("Invalid selection.")

            elif choice == "3":
                user_note = input("Add a note for your coach (optional, press Enter to skip): ").strip()
                print(f"-> Requesting advice from Ollama ({ollama_client.model})...")
                res = assistant.request_ai_coaching(user_note=user_note)
                if res.get("success"):
                    print("\n" + "=" * 50)
                    print("AI FOCUS COACH FEEDBACK:")
                    print("=" * 50)
                    print(res.get("response"))
                    print("=" * 50)
                else:
                    print(f"\n[Ollama Notice] {res.get('error')}")

            elif choice == "4":
                if getattr(assistant, "_monitor_thread", None) and assistant._monitor_thread.is_alive():
                    assistant.stop_continuous_monitoring()
                else:
                    print("-> Continuous monitoring is not running.")

            elif choice == "5":
                print("\nEnding session...")
                assistant.end_session()
                break

            else:
                print("Invalid input. Please enter 1, 2, 3, 4, or 5.")

    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user. Closing session...")
        assistant.end_session()

    print("\nThank you for using AI Study-Focus Assistant!")


if __name__ == "__main__":
    main()
