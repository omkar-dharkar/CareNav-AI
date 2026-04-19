"""
Agent 3: Home Care Advisor for CareNav AI.
All prompts are stored in prompt.py.
"""

import os
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.tools import google_search
from .prompt import HOME_REMEDIES_PROMPT
from .config import config

# Load environment variables from .env file
load_dotenv()

# Create the Home Remedies Agent with Google Search for additional remedy information
home_remedies_agent = LlmAgent(
    name="home_remedies_advisor",
    model=config.DEFAULT_MODEL,
    description=(
        "Conservative U.S.-focused home-care advisor for mild symptoms only. "
        "Provides safe self-care ideas, label-following reminders, and clear "
        "escalation guidance for urgent or emergency symptoms."
    ),
    instruction=HOME_REMEDIES_PROMPT,
    tools=[google_search],
)
