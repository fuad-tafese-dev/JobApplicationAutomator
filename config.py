import os
from dotenv import load_dotenv  # pip install python-dotenv

load_dotenv()

LINKEDIN_CREDS = {
    'email': os.getenv('LINKEDIN_EMAIL'),
    'password': os.getenv('LINKEDIN_PASSWORD')
}

QUESTION_DATABASE = {
    "years of experience": "2",
    "visa sponsorship": "No"
}