import json
import re
from langchain_core.tools import tool


@tool
def generate_quiz(notes_content: str) -> str:
    """
    Generate a quiz with 5 multiple-choice questions based on the lecture notes.
    Returns a JSON string of questions with options and correct answers.
    Input: notes_content (str) - the lecture notes or summary.
    """
    # Returns a structured prompt for the agent to fill in
    return f"""Generate exactly 5 multiple-choice quiz questions from this content:

{notes_content}

Return ONLY a valid JSON array with this exact structure (no markdown, no extra text):
[
  {{
    "question": "Question text here?",
    "options": {{
      "A": "Option A",
      "B": "Option B", 
      "C": "Option C",
      "D": "Option D"
    }},
    "answer": "A",
    "topic": "short topic label"
  }}
]"""


def parse_quiz_json(raw: str) -> list:
    """
    Extract and parse the JSON quiz array from LLM output.
    """
    # Strip markdown code fences if present
    cleaned = re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()

    # Find JSON array
    start = cleaned.find("[")
    end = cleaned.rfind("]") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON array found in quiz response")

    return json.loads(cleaned[start:end])
