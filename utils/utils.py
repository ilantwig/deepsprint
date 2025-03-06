import os
import re
import logging

# Get the logger
logger = logging.getLogger(__name__)
    
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

def get_report_css_style() -> str:
    """
    Returns the CSS style for the report.
    """
    return """<style>
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      line-height: 1.6;
      margin: 30px;
      background-color: #f8f8f8;
      color: #333;
    }

    h1, h2, h3 {
      margin-bottom: 15px;
      color: #2c3e50;
    }

    h1 {
      font-size: 20px;
      border-bottom: 3px solid #3498db;
      padding-bottom: 8px;
      text-transform: uppercase;
      letter-spacing: 1px;
    }

    h2 {
      font-size: 18px;
      color: #34495e;
    }

    h3 {
      font-size: 16px;
      color: #2980b9;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 30px;
      box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
      background-color: white;
      border-radius: 5px;
    }

    th, td {
      border: 1px solid #e0e0e0;
      padding: 12px 15px;
      text-align: left;
    }

    th {
      background-color: #3498db;
      color: white;
      font-weight: 600;
    }

    tr:nth-child(even) {
      background-color: #f2f2f2;
    }

    tr:hover {
      background-color: #e8f5ff;
    }
    </style>"""

