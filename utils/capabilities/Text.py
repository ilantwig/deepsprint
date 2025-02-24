from utils.config import default_model

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
        response = default_model.invoke(prompt)
        return response.content.strip()