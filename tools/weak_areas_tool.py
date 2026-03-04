import json
import os
from datetime import datetime
from langchain_core.tools import tool

WEAK_AREAS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "weak_areas.json")


def _load_weak_areas() -> list:
    if not os.path.exists(WEAK_AREAS_FILE):
        return []
    with open(WEAK_AREAS_FILE, "r") as f:
        return json.load(f)


def _save_weak_areas(data: list):
    os.makedirs(os.path.dirname(WEAK_AREAS_FILE), exist_ok=True)
    with open(WEAK_AREAS_FILE, "w") as f:
        json.dump(data, f, indent=2)


@tool
def save_weak_area(topic: str, question: str, user_answer: str, correct_answer: str) -> str:
    """
    Save a weak area when the student answers a quiz question incorrectly.
    Inputs:
      - topic: the topic/subject of the question
      - question: the quiz question text
      - user_answer: what the student answered
      - correct_answer: the correct answer
    """
    weak_areas = _load_weak_areas()

    # Check if this topic already exists
    existing = next((w for w in weak_areas if w["topic"] == topic), None)

    entry = {
        "question": question,
        "user_answer": user_answer,
        "correct_answer": correct_answer,
        "timestamp": datetime.now().isoformat()
    }

    if existing:
        existing["count"] = existing.get("count", 1) + 1
        existing["mistakes"].append(entry)
    else:
        weak_areas.append({
            "topic": topic,
            "count": 1,
            "mistakes": [entry]
        })

    _save_weak_areas(weak_areas)
    return f"✅ Weak area saved under topic: '{topic}'"


@tool
def get_weak_areas(dummy: str = "") -> str:
    """
    Retrieve all saved weak areas for the student.
    Returns a formatted summary of topics the student struggles with.
    """
    weak_areas = _load_weak_areas()

    if not weak_areas:
        return "No weak areas recorded yet. Keep studying!"

    result = "📌 WEAK AREAS REPORT\n" + "=" * 40 + "\n"
    for area in sorted(weak_areas, key=lambda x: x["count"], reverse=True):
        result += f"\n🔴 Topic: {area['topic']} (missed {area['count']} time(s))\n"
        for m in area["mistakes"][-2:]:  # Show last 2 mistakes per topic
            result += f"   Q: {m['question']}\n"
            result += f"   Your answer: {m['user_answer']} | Correct: {m['correct_answer']}\n"
    return result


def get_all_weak_areas_raw() -> list:
    """Direct access for main.py display (bypasses tool decorator)."""
    return _load_weak_areas()
