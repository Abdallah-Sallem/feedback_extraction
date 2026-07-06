import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database File Path
DB_PATH = os.environ.get("DB_PATH", "hr_feedback.db")

# Watched folder for auto-processing
WATCHED_FOLDER = os.environ.get("WATCHED_FOLDER", "watched_feedback")

# Ensure watched folder exists
os.makedirs(WATCHED_FOLDER, exist_ok=True)

def get_api_key():
    """
    Get Mistral API Key from environment or .env file.
    Returns None if not set.
    """
    return os.environ.get("MISTRAL_API_KEY")
