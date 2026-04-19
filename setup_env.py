#!/usr/bin/env python3
"""
Environment setup helper for CareNav AI.
"""

import os
import sys


def create_env_file():
    """Create a .env file with required environment variables."""

    env_template = """# CareNav AI - Local Configuration

# Google AI Studio / Gemini API
GOOGLE_API_KEY=your_google_ai_api_key_here
GOOGLE_GENAI_USE_VERTEXAI=False
DEFAULT_MODEL=gemini-2.5-flash

# Google Places API (New)
GOOGLE_PLACES_API_KEY=your_google_places_api_key_here

# Google Cloud / Vertex AI deployment settings
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_CLOUD_STORAGE_BUCKET=your_staging_bucket
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json

# Application settings
LOG_LEVEL=INFO
DEBUG_MODE=False
MAX_SEARCH_RESULTS=10
CACHE_TIMEOUT=3600

# Security settings
ENABLE_RATE_LIMITING=True
MAX_REQUESTS_PER_MINUTE=60
ENABLE_AUDIT_LOG=True

# U.S. emergency resources
EMERGENCY_SERVICES=911
POISON_CONTROL=1-800-222-1222
SUICIDE_PREVENTION=988
MENTAL_HEALTH_CRISIS=988
"""

    env_file_path = ".env"

    if os.path.exists(env_file_path):
        response = input(f"{env_file_path} already exists. Overwrite it? (y/N): ")
        if response.lower() not in ["y", "yes"]:
            print("Setup cancelled. Existing .env file preserved.")
            return False

    try:
        with open(env_file_path, "w", encoding="utf-8") as f:
            f.write(env_template)

        print(f"{env_file_path} created successfully.")
        print("\nNext steps:")
        print("1. Edit .env and replace placeholder values.")
        print("2. Get GOOGLE_API_KEY from https://aistudio.google.com/app/apikey")
        print("3. Get GOOGLE_PLACES_API_KEY from Google Cloud Credentials.")
        print("4. Enable Places API (New) for the Places key.")
        print("5. Run: pip install -r requirements.txt")
        print("6. Run: adk web")
        return True

    except Exception as e:
        print(f"Error creating {env_file_path}: {str(e)}")
        return False


def validate_env_file():
    """Validate the .env file and check for required variables."""

    env_file_path = ".env"

    if not os.path.exists(env_file_path):
        print(f"{env_file_path} file not found. Run this script first to create it.")
        return False

    required_vars = {
        "GOOGLE_API_KEY": "Google AI API key",
        "GOOGLE_PLACES_API_KEY": "Google Places API key",
    }

    vertex_ai_vars = {
        "GOOGLE_CLOUD_PROJECT": "Google Cloud project ID",
        "GOOGLE_APPLICATION_CREDENTIALS": "Path to service account JSON file",
    }

    missing_vars = []
    placeholder_vars = []

    try:
        with open(env_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        vertex_ai_enabled = "GOOGLE_GENAI_USE_VERTEXAI=True" in content

        for var_name, description in required_vars.items():
            if f"{var_name}=" not in content:
                missing_vars.append(f"{var_name} ({description})")
            elif f"{var_name}=your_" in content:
                placeholder_vars.append(f"{var_name} ({description})")

        if vertex_ai_enabled:
            for var_name, description in vertex_ai_vars.items():
                if f"{var_name}=" not in content:
                    missing_vars.append(f"{var_name} ({description}) - required for Vertex AI")
                elif f"{var_name}=your_" in content or f"{var_name}=path/to/" in content:
                    placeholder_vars.append(f"{var_name} ({description}) - required for Vertex AI")

        if missing_vars:
            print("Missing required environment variables:")
            for var in missing_vars:
                print(f"   - {var}")

        if placeholder_vars:
            print("Environment variables still using placeholder values:")
            for var in placeholder_vars:
                print(f"   - {var}")
            print("\nUpdate these values before running CareNav AI.")

        if not missing_vars and not placeholder_vars:
            print("Environment variables look good.")
            if vertex_ai_enabled:
                print("Vertex AI is enabled. Confirm your service account JSON path exists.")
            return True

        return False

    except Exception as e:
        print(f"Error reading {env_file_path}: {str(e)}")
        return False


def show_api_key_instructions():
    """Show instructions for obtaining API keys."""

    print("\nHow to get your API keys")
    print("=" * 60)

    print("\nGoogle AI API key (GOOGLE_API_KEY):")
    print("1. Go to https://aistudio.google.com/app/apikey")
    print("2. Sign in with your Google account.")
    print("3. Create or copy an API key.")
    print("4. Paste it into .env as GOOGLE_API_KEY=your_actual_api_key")

    print("\nGoogle Places API key (GOOGLE_PLACES_API_KEY):")
    print("1. Go to https://console.cloud.google.com/apis/credentials")
    print("2. Select your Google Cloud project.")
    print("3. Enable Places API (New): https://console.cloud.google.com/apis/library/places.googleapis.com")
    print("4. Create or copy an API key.")
    print("5. Restrict the key to Places API when possible.")
    print("6. Paste it into .env as GOOGLE_PLACES_API_KEY=your_actual_api_key")

    print("\nVertex AI service account (optional deployment path):")
    print("1. Go to https://console.cloud.google.com/iam-admin/serviceaccounts")
    print("2. Create or select a service account.")
    print("3. Add Vertex AI and Storage permissions.")
    print("4. Download a JSON key file.")
    print("5. Set GOOGLE_APPLICATION_CREDENTIALS to that local path.")

    print("\nSecurity tips:")
    print("- Never commit .env, deploy.env, service account JSON, or API keys.")
    print("- Rotate keys if they are accidentally exposed.")
    print("- Restrict API keys by API and application where possible.")


def main():
    """CLI entry point."""

    print("CareNav AI - Environment Setup")
    print("=" * 50)

    if len(sys.argv) > 1 and sys.argv[1] == "--validate":
        validate_env_file()
        return

    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        show_api_key_instructions()
        return

    print("\nThis script creates a local .env file for CareNav AI.")

    if create_env_file():
        print("\n" + "-" * 50)
        validate_env_file()
        print("\nNeed API key help? Run:")
        print("   python setup_env.py --help")
        print("\nValidate your .env later with:")
        print("   python setup_env.py --validate")


if __name__ == "__main__":
    main()
