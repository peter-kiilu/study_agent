from langchain_core.tools import tool


@tool
def summarize_notes(notes_content: str) -> str:
    """
    Summarize the provided lecture notes into key concepts,
    main points, and important definitions.
    Input: raw notes text.
    Output: structured summary.
    """
    # This tool is a signal to the agent to perform summarization.
    # The agent will use its LLM capability after receiving this context.
    return notes_content  # passed back to agent for LLM summarization
