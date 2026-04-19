"""
Configuration for CareNav AI.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set Google Application Credentials for Vertex AI if provided
if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

class HealthcareAgentConfig:
    """Configuration settings for the CareNav AI assistant."""

    PROJECT_NAME = "CareNav AI"
    AUTHOR = "Omkar A Dharkar"
    
    # Google AI API Configuration
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    GOOGLE_GENAI_USE_VERTEXAI = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "False").lower() == "true"
    
    # Google Cloud Configuration (for Vertex AI)
    GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    
    # API Keys for Agent Tools
    GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")
    
    # Model Configuration
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini-2.5-flash")
    
    # U.S.-specific safety resources
    EMERGENCY_NUMBER = "911"
    POISON_CONTROL_NUMBER = "1-800-222-1222"
    CRISIS_LIFELINE_NUMBER = "988"
    
    @classmethod
    def validate_config(cls) -> list:
        """Validate essential configuration and return any missing requirements"""
        missing = []
        
        if not cls.GOOGLE_API_KEY:
            missing.append("GOOGLE_API_KEY is required")
        
        if cls.GOOGLE_GENAI_USE_VERTEXAI and not cls.GOOGLE_CLOUD_PROJECT:
            missing.append("GOOGLE_CLOUD_PROJECT is required when using Vertex AI")
        
        if cls.GOOGLE_GENAI_USE_VERTEXAI and not cls.GOOGLE_APPLICATION_CREDENTIALS:
            missing.append("GOOGLE_APPLICATION_CREDENTIALS is required when using Vertex AI")
        
        if not cls.GOOGLE_PLACES_API_KEY:
            missing.append("GOOGLE_PLACES_API_KEY is required for hospital finder")
        
        return missing
    
    @classmethod
    def is_vertex_ai_enabled(cls) -> bool:
        """Check if Vertex AI is enabled and properly configured"""
        return (cls.GOOGLE_GENAI_USE_VERTEXAI and 
                bool(cls.GOOGLE_CLOUD_PROJECT) and 
                bool(cls.GOOGLE_APPLICATION_CREDENTIALS))

# Create a global config instance
config = HealthcareAgentConfig() 
