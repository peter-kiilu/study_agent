import os
import sys

# Ensure the project root is on the path so 'tools' resolves correctly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.memory import ConversationBufferMemory
from dotenv import load_dotenv

from tools.summarize_tool import summarize_notes
from tools.quiz_tool import generate_quiz
from tools.weak_areas_tool import save_weak_area, get_weak_areas

load_dotenv()

def build_study_agent() -> AgentExecutor:
    """
    Build the agentic study assistant.
    Dynamically picks provider based on available keys.
    """
    
    # ── BRAIN ────────────────────────────────────────────────────────────────
    if os.getenv("GOOGLE_API_KEY"):
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.3,
            max_output_tokens=4000
        )
    elif os.getenv("GROQ_API_KEY"):
        llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_tokens=4000
        )
    else:
        raise ValueError("No API Key found. Configure GOOGLE_API_KEY or GROQ_API_KEY.")
    
    # ── TOOLS ────────────────────────────────────────────────────────────────
    tools = [summarize_notes, generate_quiz, save_weak_area, get_weak_areas]
    
        # ── SYSTEM PROMPT ────────────────────────────────────────────────────────
    system_prompt = """You are an intelligent Study Assistant Agent. You help students 
learn by processing their lecture notes through a structured study workflow.

Your available tools:
- summarize_notes    → Summarize lecture notes into key concepts
- generate_quiz      → Create multiple-choice questions from notes  
- save_weak_area     → Save topics a student answered incorrectly
- get_weak_areas     → Show the student's weak areas and study gaps

HOW TO BEHAVE:
1. When given lecture notes → call summarize_notes → present a clean summary
2. When asked to generate a quiz → call generate_quiz with the notes content
3. When a student answers quiz questions → evaluate each answer, call save_weak_area 
   for every WRONG answer with the topic, question, their answer, and correct answer
4. When asked about weak areas → call get_weak_areas and present findings clearly

Always be encouraging, educational, and precise. After showing weak areas,
suggest which topics the student should revise.
"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    # ── MEMORY ───────────────────────────────────────────────────────────────
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )
    
    
    # ── AGENT (ReAct-style tool calling) ─────────────────────────────────────
    agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)
    
    # executing action
    executor = AgentExecutor(
        agent = agent,
        tools = tools,
        memory = memory,
        verbose = True, # SHOWING THE AGENT REASONING STEP 
        handle_parsing_errors= True,
        max_iterations= 5
       
    )
    
    return executor
