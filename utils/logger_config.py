import logging
import threading
from utils.crewid import CrewID

# Define a custom formatter
class CrewIDFormatter(logging.Formatter):
    def format(self, record):
        record.msg = f"CrewID:{CrewID.get_crewid()} - {record.msg}"
        return super().format(record)

# Create a lock to synchronize access to the logger
logging_lock = threading.Lock()

def setup_logger():
    with logging_lock:
        # Get the root logger
        logger = logging.getLogger()

        # Create a handler (e.g., StreamHandler for console output)
        handler = logging.StreamHandler()

        # Create an instance of your custom formatter
        formatter = CrewIDFormatter('%(filename)s:%(lineno)d - %(message)s')

        # Set the formatter for the handler
        handler.setFormatter(formatter)

        # Add the handler to the logger ONLY IF NO HANDLERS ARE DEFINED
        if not logger.handlers:  
            logger.addHandler(handler)

        # Set the logging level
        logger.setLevel(logging.DEBUG)