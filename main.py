"""
╔═══════════════════════════════════════════════════════════╗
║          AGENTIC AI STUDY ASSISTANT                       ║
║                                                           ║
║  Flow:                                                    ║
║  1. Point to a notes folder (.pdf .pptx .docx .txt)      ║
║  2. Agent auto-loads all notes from every course folder   ║
║  3. Agent summarizes the notes                            ║
║  4. Agent generates a quiz                                ║
║  5. You answer → Agent evaluates & saves weak areas       ║
║  6. Review your weak areas report                         ║
╚═══════════════════════════════════════════════════════════╝
"""


import os
import sys
import json
from colorama import Fore, Style, init

init(autoreset=True)
# ── path setup (fixes Windows 'tools' namespace conflict) ───────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from helpers.file_loader import load_notes, scan_directory, load_all_from_directory, SUPPORTED_EXTENSIONS
from tools.quiz_tool import parse_quiz_json
from tools.weak_areas_tool import get_all_weak_areas_raw
from agents.study_agent import build_study_agent


# ── UI helpers Colorama ───────────────────────────────────────────────────────────────

def header(text: str):
    print(f"\n{Fore.CYAN}{'═' * 60}")
    print(f"  {text}")
    print(f"{'═' * 60}{Style.RESET_ALL}\n")


def success(text: str):
    print(f"{Fore.GREEN}✅ {text}{Style.RESET_ALL}")


def error(text: str):
    print(f"{Fore.RED}❌ {text}{Style.RESET_ALL}")


def info(text: str):
    print(f"{Fore.YELLOW}ℹ️  {text}{Style.RESET_ALL}")


def agent_say(text: str):
    print(f"{Fore.MAGENTA}🤖 Agent: {text}{Style.RESET_ALL}")
    

# ── STEP 1: Upload Notes ──────────────────────────────────────────────────────

def step_upload_notes() -> tuple[str, str]:
    """Prompt user for a directory or file path, load and return (path, content)."""
    header("STEP 1: Upload Your Lecture Notes")
    supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
    info(f"Supported formats: {supported}")
    info("You can enter a FOLDER path to auto-load all notes inside it.")

    while True:
        path = input(f"{Fore.WHITE}📂 Enter path to your notes folder or file: {Style.RESET_ALL}").strip()
        path = path.strip('"').strip("'")  # handle dragged paths

        if not path:
            error("Please enter a path.")
            continue

        try:
            if os.path.isdir(path):
                # ── Directory mode: scan and let user choose ──────────
                courses = scan_directory(path)
                if not courses:
                    error(f"No supported files found in: {path}")
                    continue

                # Show discovered courses with numbers
                course_list = list(courses.items())
                total_files = sum(len(f) for f in courses.values())
                success(f"Found {total_files} note(s) across {len(courses)} course(s):\n")
                for idx, (course_name, files) in enumerate(course_list, 1):
                    ext_counts = {}
                    for f in files:
                        ext_counts[f['ext']] = ext_counts.get(f['ext'], 0) + 1
                    ext_summary = ", ".join(f"{c} {e}" for e, c in ext_counts.items())
                    print(f"  {Fore.YELLOW}[{idx}] 📁 {course_name}{Style.RESET_ALL}  ({ext_summary})")
                print()

                # ── Pick a course ─────────────────────────────────────
                while True:
                    choice = input(f"{Fore.WHITE}Select a course (1-{len(course_list)}): {Style.RESET_ALL}").strip()
                    if choice.isdigit() and 1 <= int(choice) <= len(course_list):
                        break
                    error(f"Enter a number between 1 and {len(course_list)}")

                selected_course, selected_files = course_list[int(choice) - 1]
                print()
                success(f"Course: {selected_course}\n")

                # ── Show files in the selected course ─────────────────
                for idx, f in enumerate(selected_files, 1):
                    print(f"  {Fore.YELLOW}[{idx}]{Style.RESET_ALL} {f['name']}")
                print(f"  {Fore.YELLOW}[A]{Style.RESET_ALL} Load ALL files in this course")
                print()

                # ── Pick file(s) ──────────────────────────────────────
                while True:
                    pick = input(f"{Fore.WHITE}Select a file (1-{len(selected_files)}) or 'A' for all: {Style.RESET_ALL}").strip().upper()
                    if pick == "A":
                        files_to_load = selected_files
                        break
                    elif pick.isdigit() and 1 <= int(pick) <= len(selected_files):
                        files_to_load = [selected_files[int(pick) - 1]]
                        break
                    error(f"Enter a number (1-{len(selected_files)}) or 'A'")

                # ── Load the chosen files ─────────────────────────────
                info(f"Loading {len(files_to_load)} file(s)...")
                text_parts = []
                for file_info in files_to_load:
                    try:
                        file_content = load_notes(file_info["path"])
                        if file_content:
                            text_parts.append(f"--- {file_info['name']} ---")
                            text_parts.append(file_content)
                    except Exception as e:
                        error(f"Skipped {file_info['name']}: {e}")

                content = "\n\n".join(text_parts).strip()
                if not content:
                    error("Selected files were empty. Try different files.")
                    continue

                success(f"Notes loaded! ({len(content)} characters)")
                print(f"\n{Fore.WHITE}Preview (first 300 chars):\n{content[:300]}...{Style.RESET_ALL}")
                return path, content

            elif os.path.isfile(path):
                # ── Single file mode (backwards compatible) ───────────
                content = load_notes(path)
                if not content:
                    error("File is empty. Please provide a file with content.")
                    continue
                success(f"Notes loaded! ({len(content)} characters)")
                print(f"\n{Fore.WHITE}Preview (first 300 chars):\n{content[:300]}...{Style.RESET_ALL}")
                return path, content

            else:
                error(f"Path not found: {path}")

        except FileNotFoundError as e:
            error(str(e))
        except NotADirectoryError as e:
            error(str(e))
        except ValueError as e:
            error(str(e))
            
# ── STEP 2: Summarize ─────────────────────────────────────────────────────────

def step_summarize(agent: object, notes_content: str) -> str:
    """Agent summarizes the notes and returns the summary."""
    header("STEP 2: Summarizing Your Notes")
    agent_say("Let me analyze and summarize your lecture notes...")

    response = agent.invoke({
        "input": f"""Please summarize these lecture notes for me. 
Use the summarize_notes tool and then present a clear, structured summary 
with: Key Concepts, Main Points, and Important Definitions.

NOTES:
{notes_content}"""
    })

    summary = response["output"]
    print(f"\n{Fore.WHITE}{summary}{Style.RESET_ALL}")
    return summary


# ── STEP 3: Generate Quiz ─────────────────────────────────────────────────────

def step_generate_quiz(agent: object, notes_content: str) -> list:
    """Agent generates quiz questions. Returns parsed list of questions."""
    header("STEP 3: Generating Quiz")
    agent_say("Generating 5 quiz questions from your notes...")

    response = agent.invoke({
        "input": f"""Use the generate_quiz tool to create 5 multiple choice questions 
from the notes below. After calling the tool, return ONLY the raw JSON array 
(starting with [ and ending with ]) with no extra text, no markdown fences.

NOTES:
{notes_content}"""
    })

    raw_output = response["output"]

    try:
        questions = parse_quiz_json(raw_output)
        success(f"Generated {len(questions)} questions!")
        return questions
    except Exception as e:
        # Fallback: ask agent to retry with stricter format
        info("Retrying quiz generation with strict JSON format...")
        retry = agent.invoke({
            "input": "Return ONLY the JSON array from the quiz you just generated. No markdown, no text before or after the array."
        })
        try:
            return parse_quiz_json(retry["output"])
        except Exception:
            error(f"Could not parse quiz: {e}")
            return []
        
# ── STEP 4: Run Quiz Session ──────────────────────────────────────────────────

def step_run_quiz(agent: object, questions: list) -> dict:
    """
    Show questions to user, collect answers, evaluate them.
    Agent saves weak areas for wrong answers.
    Returns results dict.
    """
    header("STEP 4: Quiz Time! 📝")
    agent_say(f"You have {len(questions)} questions. Type the letter of your answer (A/B/C/D).")
    print()

    results = {"correct": 0, "wrong": 0, "details": []}
    wrong_answers = []

    for i, q in enumerate(questions, 1):
        print(f"{Fore.CYAN}Question {i}/{len(questions)}:{Style.RESET_ALL}")
        print(f"{Fore.WHITE}{q['question']}{Style.RESET_ALL}")
        for key, val in q["options"].items():
            print(f"  {Fore.YELLOW}{key}.{Style.RESET_ALL} {val}")

        # Get valid answer
        while True:
            answer = input(f"\n{Fore.WHITE}Your answer: {Style.RESET_ALL}").strip().upper()
            if answer in ["A", "B", "C", "D"]:
                break
            error("Please enter A, B, C, or D")

        correct = q["answer"].upper()
        is_correct = answer == correct

        if is_correct:
            success("Correct! 🎉")
            results["correct"] += 1
        else:
            error(f"Wrong! The correct answer was: {correct} — {q['options'].get(correct, '')}")
            results["wrong"] += 1
            wrong_answers.append({
                "topic": q.get("topic", "General"),
                "question": q["question"],
                "user_answer": f"{answer} - {q['options'].get(answer, '')}",
                "correct_answer": f"{correct} - {q['options'].get(correct, '')}"
            })

        results["details"].append({
            "question": q["question"],
            "user": answer,
            "correct": correct,
            "passed": is_correct
        })
        print()

    # ── Agent saves all weak areas ────────────────────────────────────────────
    if wrong_answers:
        header("Saving Your Weak Areas...")
        agent_say("I'm recording the topics you need to review...")
        for wa in wrong_answers:
            save_msg = agent.invoke({
                "input": f"""Call the save_weak_area tool with these exact values:
- topic: "{wa['topic']}"
- question: "{wa['question']}"
- user_answer: "{wa['user_answer']}"
- correct_answer: "{wa['correct_answer']}"
"""
            })
            info(save_msg["output"])

    return results


# ── STEP 5: Weak Areas Report ─────────────────────────────────────────────────

def step_weak_areas_report(agent: object, results: dict):
    """Show quiz results and fetch weak areas report from agent."""
    header("STEP 5: Your Performance Report 📊")

    total = results["correct"] + results["wrong"]
    pct = round((results["correct"] / total) * 100) if total else 0

    print(f"{Fore.WHITE}Score: {results['correct']}/{total} ({pct}%){Style.RESET_ALL}")

    if pct == 100:
        success("Perfect score! Excellent work! 🏆")
    elif pct >= 70:
        info("Good job! Review the missed topics to master this material.")
    else:
        error("You have significant gaps. Focus on your weak areas below.")

    if results["wrong"] > 0:
        print()
        agent_say("Here are your weak areas and study recommendations:")
        response = agent.invoke({
            "input": """Call the get_weak_areas tool and show me my weak areas. 
Then give me 3 specific study tips for the topics I struggled with."""
        })
        print(f"\n{Fore.WHITE}{response['output']}{Style.RESET_ALL}")
    else:
        agent_say("No weak areas to report. You aced it! 🌟")
        
        

# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print(f"""
{Fore.CYAN}
╔═══════════════════════════════════════════════════════╗
║        🎓 AGENTIC AI STUDY ASSISTANT                  ║
║                                                       ║
║  Powered by: LangChain + Groq (LLaMA 3.3 70B)        ║
║  Memory: ConversationBufferMemory                     ║
║  Tools: summarize | quiz | save_weakness | report     ║
║  Notes:  .pdf  .pptx  .docx  .txt  (folder scan)     ║
╚═══════════════════════════════════════════════════════╝
{Style.RESET_ALL}""")

    info("Building Study Agent (Brain + Memory + Tools)...")
    agent = build_study_agent()
    success("Agent ready!\n")

    # ── Run the 5-step workflow ───────────────────────────────────────────────
    try:
        # Step 1
        _, notes_content = step_upload_notes()

        # Step 2
        summary = step_summarize(agent, notes_content)

        # Confirm before quiz
        proceed = input(f"\n{Fore.WHITE}Ready to take the quiz? (y/n): {Style.RESET_ALL}").strip().lower()
        if proceed != "y":
            info("Quiz skipped. Come back when you're ready!")
            return

        # Step 3
        questions = step_generate_quiz(agent, notes_content)
        if not questions:
            error("Could not generate quiz. Try again with clearer notes.")
            return

        # Step 4
        results = step_run_quiz(agent, questions)

        # Step 5
        step_weak_areas_report(agent, results)

        # ── Offer free chat ───────────────────────────────────────────────────
        print(f"\n{Fore.CYAN}{'─' * 60}{Style.RESET_ALL}")
        agent_say("Session complete! You can keep chatting with me about your notes.")
        info("Type 'exit' to quit.\n")

        while True:
            user_input = input(f"{Fore.WHITE}You: {Style.RESET_ALL}").strip()
            if user_input.lower() in ["exit", "quit", "bye"]:
                agent_say("Good luck with your studies! 📚")
                break
            if not user_input:
                continue
            response = agent.invoke({"input": user_input})
            agent_say(response["output"])
            print()

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Session interrupted. Goodbye!{Style.RESET_ALL}")


if __name__ == "__main__":
    main()