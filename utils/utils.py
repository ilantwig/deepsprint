import os
import re

from utils.capabilities.Search import logger
    
def clean_emoji(input_text: str) -> str:
    """
    Remove emoji characters from input string.

    Args:
        input_text: String to clean

    Returns:
        Cleaned string without emoji characters
    """
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\u03c0"                 # pi
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', input_text)


def create_subfolder(parent_dir, subfolder_name):
  """Creates a subfolder, even if it already exists.

  Args:
    parent_dir: The path to the parent directory.
    subfolder_name: The name of the subfolder to create.
  """
  try:
    subfolder_path = os.path.join(parent_dir, subfolder_name)
    os.makedirs(subfolder_path, exist_ok=True)
    logger.debug(f"Subfolder '{subfolder_name}' created (or already exists) at '{subfolder_path}'")
  except OSError as e:
    logger.debug(f"Error creating subfolder: {e}")