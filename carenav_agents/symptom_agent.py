"""
Agent 1: Symptom Analysis Agent for CareNav AI.
All prompts are stored in prompt.py.
"""

import os
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.tools import google_search
from .prompt import SYMPTOM_ANALYZER_PROMPT
from .config import config

# Load environment variables from .env file
load_dotenv()

# Create the Symptom Analysis Agent with only Google Search
symptom_agent = LlmAgent(
    name="symptom_analyzer",
    model=config.DEFAULT_MODEL,
    description=(
        "U.S.-focused symptom triage assistant with multimodal capabilities. "
        "Analyzes symptoms from text and images, identifies red flags, provides "
        "educational health guidance, and routes emergencies to 911."
    ),
    instruction=SYMPTOM_ANALYZER_PROMPT,
    tools=[google_search],
) 
