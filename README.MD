# 🎓 Agentic AI Study Assistant

An intelligent, multi-provider AI Study Assistant that supercharges your learning by automatically generating summaries, quizzes, and personalized performance reports from your lecture notes.

Built with **LangChain**, it supports multiple LLMs including **Google Gemini** (GCP) and **Groq** (LLaMA 3) to process your study material and help you master it.

## ✨ Features

- **Document Ingestion**: Upload individual files or point to a local directory to auto-load multi-format lecture notes (`.pdf`, `.pptx`, `.docx`, `.txt`).
- **AI Summarization**: The agent automatically analyzes and distills long notes into digestible summaries, key concepts, and important definitions.
- **Dynamic Quiz Generation**: Automatically generates multiple-choice questions directly from the provided study material.
- **Interactive Quiz Session**: Answer generated questions via the CLI or Streamlit app interface.
- **Weak Area Tracking**: The AI evaluates your responses and logs specific topics you struggled with for targeted revision.
- **Personalized Reports**: Receive a performance breakdown along with recommended study tips based on your weak areas.
- **Flexible AI Backends**: Work with either Google GenAI (`gemini-2.5-flash`) or Groq (`llama-3.3-70b-versatile`).

## 📁 Project Structure

- `main.py`: Command Line Interface (CLI) application for a 5-step guided study session.
- `app.py`: Interactive web-based user interface using Streamlit.
- `agents/study_agent.py`: LangChain ReAct-style agent definition utilizing tool calling and conversation buffer memory.
- `tools/`: LangChain tools specifically designed for summarization, quiz generation, and managing weak areas.
- `helpers/file_loader.py`: Utility functions to parse text out of PDFs, Word documents, and PowerPoints.
- `Dockerfile`: Pre-configured for deployment to Google Cloud Run.

## 🚀 Getting Started

### 1. Prerequisites

Ensure you have Python 3.9+ installed. Clone the repository and navigate to the project directory:

```bash
cd study_assist
```

### 2. Install Dependencies

Create a virtual environment and install the required packages:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Environment Variables

Create a `.env` file in the root of your project and configure your API keys. You only need the key for the provider you plan to use:

```env
GOOGLE_API_KEY="your_google_cloud_api_key_here"
GROQ_API_KEY="your_groq_api_key_here"
```

### 4. Run the Application

#### Option A: Interactive UI (Streamlit)

To launch the beautiful, web-based interface:

```bash
streamlit run app.py
```

#### Option B: Terminal / CLI Mode

To run the terminal-based interactive guided session:

```bash
python main.py
```

## ☁️ Deployment (Google Cloud Run)

This project contains a `Dockerfile` optimized for Google Cloud Run deployment. To deploy via the gcloud CLI:

```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/study-assistant
gcloud run deploy study-assistant --image gcr.io/YOUR_PROJECT_ID/study-assistant --platform managed --allow-unauthenticated
```

_(Make sure to pass your environment secrets to Cloud Run so the app can access your chosen AI provider)_

## 🛠️ Built With

- [LangChain](https://python.langchain.com/) - LLM Framework & Tool Calling
- [Streamlit](https://streamlit.io/) - Web Interface
- [Google GenAI](https://ai.google.dev/) / [Groq](https://groq.com/) - Large Language Models
- [pypdf](https://pypi.org/project/pypdf/), [python-docx](https://python-docx.readthedocs.io/), [python-pptx](https://python-pptx.readthedocs.io/) - Document parsing

## 📄 Developer Documentation

For a detailed breakdown of the system architecture, tool definitions, and extension guides, please refer to the [System Documentation](SYSTEM_DOCUMENTATION.md).
