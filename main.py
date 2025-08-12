from linkedin_api import LinkedInAutomator
from config import LINKEDIN_CREDS, QUESTION_DATABASE
import logging


def main():
    # Initialize
    bot = LinkedInAutomator(
        username=LINKEDIN_CREDS['email'],
        password=LINKEDIN_CREDS['password'],
        question_db=QUESTION_DATABASE
    )

    try:
        # Execute workflow
        bot.login()
        bot.search_jobs("Python Developer", location="Remote")
        bot.process_applications(max_jobs=2)

    except Exception as e:
        logging.error(f"Critical failure: {str(e)}")
        bot.take_screenshot("critical_error.png")


if __name__ == "__main__":
    main()