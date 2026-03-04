import streamlit as st
import os
import tempfile
import json
from helpers.file_loader import load_notes
from agents.study_agent import build_study_agent

# ── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="Agentic AI Study Assistant", page_icon="🎓", layout="wide")

# Custom CSS for Premium Look
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #4CAF50; color: white; }
    .stHeader { color: #00d4ff; }
    .stSuccess { background-color: #1e2a1e; color: #4CAF50; border: 1px solid #4CAF50; }
    .stInfo { background-color: #1a1c24; color: #00d4ff; border: 1px solid #00d4ff; }
    </style>
    """, unsafe_allow_html=True)

# ── SIDEBAR: Configuration ───────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Brain Settings")
    
    provider = st.radio("Select AI Provider", ["Gemini (GCP)", "Groq (Free)"])
    
    if provider == "Gemini (GCP)":
        api_key = st.text_input("Google API Key", type="password", help="Use your GCP Cloud Console key")
        model_name = "gemini-1.5-flash"
    else:
        api_key = st.text_input("Groq API Key", type="password")
        model_name = "llama-3.3-70b-versatile"

    st.divider()
    st.info("Your credits will be used when Gemini is selected with a valid key.")

# ── MAIN UI ──────────────────────────────────────────────────────────────────
st.title("🎓 Agentic AI Study Assistant")
st.markdown("### Accelerate your learning with AI-powered summaries and quizzes.")

# ── STEP 1: Upload Notes ──────────────────────────────────────────────────────
st.header("1️⃣ Upload Your Notes")
uploaded_files = st.file_uploader(
    "Select files (PDF, PPTX, DOCX, TXT)", 
    type=["pdf", "pptx", "docx", "txt"], 
    accept_multiple_files=True
)

if uploaded_files:
    # Process files
    all_content = []
    with st.status("Processing files...", expanded=False) as status:
        for uploaded_file in uploaded_files:
            # We must save to a temporary file because our loader expects paths
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            
            try:
                content = load_notes(tmp_path)
                all_content.append(f"--- {uploaded_file.name} ---\n{content}")
                st.write(f"✅ Loaded {uploaded_file.name}")
            finally:
                os.unlink(tmp_path)
        status.update(label="File processing complete!", state="complete")

    full_notes_text = "\n\n".join(all_content)
    st.success(f"Success! Loaded {len(uploaded_files)} files ({len(full_notes_text)} characters)")

    # ── Initialize Agent ─────────────────────────────────────────────────────
    if not api_key:
        st.warning("Please enter an API Key in the sidebar to proceed.")
    else:
        # Save key to environment temporarily for the agent
        if provider == "Gemini (GCP)":
            os.environ["GOOGLE_API_KEY"] = api_key
            os.environ.pop("GROQ_API_KEY", None)
        else:
            os.environ["GROQ_API_KEY"] = api_key
            os.environ.pop("GOOGLE_API_KEY", None)
            
        agent = build_study_agent()

        # ── Navigation Tabs ──────────────────────────────────────────────────
        tab1, tab2, tab3 = st.tabs(["📄 Summary", "📝 Quiz", "📊 Performance"])

        with tab1:
            st.header("Note Summary")
            if st.button("Generate Summary"):
                with st.spinner("Analyzing notes..."):
                    response = agent.invoke({"input": f"Summarize these notes:\n{full_notes_text}"})
                    st.session_state.summary = response["output"]
            
            if "summary" in st.session_state:
                st.markdown(st.session_state.summary)

        with tab2:
            st.header("Challenge Yourself")
            if st.button("Generate Quiz Questions"):
                with st.spinner("Creating quiz..."):
                    response = agent.invoke({
                        "input": f"Use the generate_quiz tool for these notes. Return ONLY the JSON array.\nNOTES:\n{full_notes_text}"
                    })
                    try:
                        # Find the JSON part in case agent adds text
                        raw = response["output"]
                        start = raw.find('[')
                        end = raw.rfind(']') + 1
                        st.session_state.questions = json.loads(raw[start:end])
                        st.session_state.answers = {}
                    except:
                        st.error("Could not parse quiz. Try generating again.")

            if "questions" in st.session_state:
                for idx, q in enumerate(st.session_state.questions):
                    st.subheader(f"Q{idx+1}: {q['question']}")
                    choice = st.radio(f"Select your answer for Q{idx+1}:", list(q['options'].values()), key=f"q_{idx}")
                    # Map display string back to A, B, C, D
                    rev_options = {v: k for k, v in q['options'].items()}
                    st.session_state.answers[idx] = rev_options[choice]

        with tab3:
            st.header("Performance Analysis")
            if "questions" in st.session_state and st.button("Submit Quiz for Review"):
                correct_count = 0
                results_to_agent = []
                
                for idx, q in enumerate(st.session_state.questions):
                    user_ans = st.session_state.answers.get(idx)
                    correct_ans = q['answer'].upper()
                    is_correct = user_ans == correct_ans
                    
                    if is_correct:
                        correct_count += 1
                    else:
                        results_to_agent.append({
                            "topic": q.get("topic", "General"),
                            "question": q["question"],
                            "user_answer": f"{user_ans} - {q['options'].get(user_ans)}",
                            "correct_answer": f"{correct_ans} - {q['options'].get(correct_ans)}"
                        })
                
                score = (correct_count / len(st.session_state.questions)) * 100
                st.metric("Your Score", f"{score:.0f}%", delta=f"{correct_count}/{len(st.session_state.questions)}")
                
                if results_to_agent:
                    st.info("Sending weak areas to agent for review...")
                    for wa in results_to_agent:
                        agent.invoke({"input": f"Save this weak area: {wa}"})
                    
                    report = agent.invoke({"input": "Show me my weak areas report and study tips."})
                    st.markdown(report["output"])
                else:
                    st.success("Perfect score! You've mastered these notes!")

else:
    st.info("Please upload some notes to start the study session.")
    st.image("https://plus.unsplash.com/premium_photo-1663040331003-8d6263545dfc?q=80&w=2070&auto=format&fit=crop", caption="Empowering your studies with AI")
