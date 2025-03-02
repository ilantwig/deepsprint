import html
import json
import unicodedata
from utils.capabilities.Search import logger
from utils.utils import clean_emoji


import os
from pathlib import Path
from typing import List

class File:
    """Util for file operations."""

    OUTPUT_DIR = Path("./output")
    CREWS_DIR = Path("./crews")
    PROMPTS_DIR = Path("./prompts")

    CREWID_OUTPUT_DIR = None  # Initialize as None
    CREWID_PROMPTS_DIR = None

    @classmethod
    def _ensure_directories(cls, crewid=None) -> None:
        """Ensure input and output directories exist."""
        cls.CREWID_OUTPUT_DIR = Path.joinpath(cls.OUTPUT_DIR, crewid)
        # cls.CREWID_PROMPTS_DIR = Path.joinpath(cls.PROMPTS_DIR, crewid)
        logger.debug(f"CREWID_DIR: {cls.CREWID_OUTPUT_DIR}")

        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        cls.CREWID_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        # cls.CREWID_PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directories exist")

    # @staticmethod
    # def read_file(filename: str) -> str:
    #     """Read content from file in input directory."""
    #     # File._ensure_directories()
    #     file_path = File.INPUT_DIR / filename
    #     try:
    #         with open(file_path, 'rb') as file:
    #             content = file.read()
    #             return content.decode('utf-8', errors='surrogatepass')
    #     except FileNotFoundError:
    #         return f"Error: File '{filename}' not found in {File.INPUT_DIR}"
    #     except Exception as e:
    #         return f"Error reading file '{filename}': {str(e)}"

    @staticmethod
    def write_file(crew_id: str, step_number: str, filename: str, _content: str) -> str:
        """
        Write content to file in output directory. Handles html, txt, md, and json files.
        If file exists, append a counter to filename.
        """
        logger.debug(f"Starting write_file with filename: {filename}")

        File._ensure_directories(crew_id)

        # Split filename into name and extension
        name, ext = os.path.splitext(filename)
        counter = 0

        file_path = Path.joinpath(File.CREWID_OUTPUT_DIR, f"{step_number}_{filename}")

        logger.debug(f"Starting write_file with filename: {file_path}")
        content=""
        if "html" in ext:
            # Normalize the string to replace no-break spaces with regular spaces
            content = unicodedata.normalize('NFKD', _content) 
            content = content.replace("```html", "").replace("```", "")
            content = html.unescape(content)  # Unescape HTML entities
            # Escape apostrophes 
            content = content.replace("'", "&#39;")


            # Remove excessive backslashes for newlines, quotes, and backslashes themselves.
            content = content.replace("\\\\n", "\n")  # \\\\n to \n
            content = content.replace("\\\"", "\"")    # \\\" to "
            content = content.replace("\\\\", "\\")    # \\\\ to \

            # 2. Handle potential edge cases (less likely, but good to have)
            content = content.replace("\\/", "/") #\/ to /

        elif "json" in ext:
            try:
                # Attempt to prettify JSON for better readability
                content = json.dumps(json.loads(_content), indent=4)
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON content: {e}")
                # If invalid JSON, proceed with the original content

        # Keep incrementing counter until we find an available filename
        while file_path.exists():
            counter += 1
            new_filename = f"{name}_{counter}{ext}"
            file_path = File.CREWID_OUTPUT_DIR / new_filename
            logger.debug(f"File exists, trying: {file_path}")

        logger.debug(f"Final file path: {file_path}")

        try:
            content = clean_emoji(content)  # Make sure this returns a string!

            # Determine the appropriate file mode and error handling
            if "html" in ext:
                mode = 'w'
                errors = 'xmlcharrefreplace'
            elif "json" in ext:
                mode = 'w'
                errors = 'strict'  # Strict JSON encoding
            else:  # For txt and md
                mode = 'w'
                errors = 'surrogatepass'

            logger.debug(f"\n\n\n==================================================================================================\n==================== FILE TOOL SAVING FILE ==================================\n=======================================")
            logger.debug(f"file_path:{file_path}")
            logger.debug(f"original content:{_content}")
            logger.debug(f"escaped content:{content}")
            with open(file_path, mode, encoding='utf-8', errors=errors) as file:
                file.write(_content)
                logger.debug(f"Wrote content to file: {file_path}")
            logger.debug(f"==================== FILE TOOL SUCCESS!  ==================================\n=============================================================================\n\n\n")
            return f"Successfully wrote to {file_path}"

        except (UnicodeEncodeError) as e:
            logger.debug(f"File Tool: Error writing to file '{file_path}': {str(e)}")
            return f"FileTool: Error writing to file '{file_path}': {str(e)}"

    # @staticmethod
    # def list_input_files() -> List[str]:
    #     """List all files in input directory."""
    #     File._ensure_directories()
    #     return [f.name for f in File.INPUT_DIR.iterdir() if f.is_file()]
# 
    # @staticmethod
    # def list_output_files() -> List[str]:
    #     """List all files in output directory."""
    #     File._ensure_directories()
    #     return [f.name for f in File.OUTPUT_DIR.iterdir() if f.is_file()]

    # @staticmethod
    # def append_to_file(filename: str, content: str) -> str:
    #     """Append content to file in output directory."""
    #     File._ensure_directories()
    #     file_path = File.OUTPUT_DIR / filename
    #     try:
    #         with open(file_path, 'a', encoding='utf-8') as file:
    #             file.write(content)
    #         return f"Successfully appended to {file_path}"
    #     except Exception as e:
    #         return f"Error appending to file '{filename}': {str(e)}"

    # @staticmethod
    # def delete_file(filename: str, directory: str = "output") -> str:
    #     """Delete file from specified directory."""
    #     File._ensure_directories()
    #     if directory not in ["input", "output"]:
    #         return "Error: Invalid directory specified. Use 'input' or 'output'."

    #     dir_path = File.INPUT_DIR if directory == "input" else File.OUTPUT_DIR
    #     file_path = dir_path / filename

    #     try:
    #         os.remove(file_path)
    #         return f"Successfully deleted {file_path}"
    #     except FileNotFoundError:
    #         return f"Error: File '{filename}' not found in {dir_path}"
    #     except Exception as e:
    #         return f"Error deleting file '{filename}': {str(e)}"