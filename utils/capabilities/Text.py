from utils.config import default_model
from utils.crewid import CrewID
from utils.capabilities.File import File

class TextUtils:
    """Not a tool. Summarize text using LLM."""

    @staticmethod
    def perform_task(text: str, task: str) -> str:
        """This is NOT a tool.  Run an LLM task on the provided text."""
        prompt = f"""
Here is a text:
{text}


Your goal is to perform this task:
{task}
-------

Answer:"""

        # Save the text processing prompt
        crewid = CrewID.get_crewid()
        File.save_prompt(crewid, "text_processing", prompt)
        
        response = default_model.invoke(prompt)
        return response.content.strip()