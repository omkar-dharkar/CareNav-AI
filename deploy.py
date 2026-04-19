"""Deployment script for CareNav AI."""

import asyncio
import os
import sys

from dotenv import load_dotenv
from google.adk.sessions import VertexAiSessionService
from vertexai import agent_engines
from vertexai.preview.reasoning_engines import AdkApp

import vertexai
from carenav_agents.agent import root_agent


def load_deployment_config():
    """Load deployment configuration from deploy.env."""
    env_path = "deploy.env"
    if not os.path.exists(env_path):
        print(f"{env_path} file not found.")
        print("Create it from deploy.env.template and add your deployment values.")
        return None

    load_dotenv(env_path)

    return {
        "project_id": os.getenv("GOOGLE_CLOUD_PROJECT"),
        "location": os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
        "bucket": os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET"),
        "google_places_api_key": os.getenv("GOOGLE_PLACES_API_KEY"),
        "google_api_key": os.getenv("GOOGLE_API_KEY"),
        "default_model": os.getenv("DEFAULT_MODEL", "gemini-2.5-flash"),
        "deployment_name": os.getenv("DEPLOYMENT_NAME", "CareNav-AI"),
        "deployment_description": os.getenv(
            "DEPLOYMENT_DESCRIPTION",
            "CareNav AI: U.S.-focused healthcare navigation with symptom triage, nearby facility search, and safe home-care guidance.",
        ),
    }


def validate_config(config):
    """Validate required deployment configuration."""
    required_vars = [
        "project_id",
        "location",
        "bucket",
        "google_places_api_key",
    ]

    missing_vars = [var for var in required_vars if not config.get(var)]

    if missing_vars:
        print("Missing required environment variables in deploy.env:")
        for var in missing_vars:
            print(f"   - {var.upper()}")
        return False

    return True


def create_deployment(config):
    """Create a new Agent Engine deployment."""
    print("Creating CareNav AI deployment...")

    env_vars = {
        "GOOGLE_PLACES_API_KEY": config["google_places_api_key"],
        "DEFAULT_MODEL": config["default_model"],
        "GOOGLE_GENAI_USE_VERTEXAI": "False",
    }

    if config.get("google_api_key"):
        env_vars["GOOGLE_API_KEY"] = config["google_api_key"]

    print(f"Deployment environment variables: {list(env_vars.keys())}")

    app = AdkApp(
        agent=root_agent,
        enable_tracing=True,
        env_vars=env_vars,
    )

    remote_agent = agent_engines.create(
        app,
        display_name=config["deployment_name"],
        description=config["deployment_description"],
        requirements=[
            "google-adk==1.15.1",
            "google-cloud-aiplatform[agent_engines]==1.129.0",
            "google-genai==1.40.0",
            "pydantic==2.12.5",
            "requests>=2.32.3,<3.0.0",
            "python-dotenv==1.2.1",
        ],
        extra_packages=[
            "./carenav_agents",
        ],
    )
    print(f"Created remote agent: {remote_agent.resource_name}")
    print(f"Resource ID: {remote_agent.resource_name.split('/')[-1]}")
    return remote_agent.resource_name


def delete_deployment(resource_id):
    """Delete an existing deployment."""
    print(f"Deleting deployment: {resource_id}")
    remote_agent = agent_engines.get(resource_id)
    remote_agent.delete(force=True)
    print(f"Deleted remote agent: {resource_id}")


def _event_text(event):
    """Return assistant text from an Agent Engine stream event, if present."""
    if not isinstance(event, dict):
        return ""

    content = event.get("content") or {}
    if content.get("role") != "model":
        return ""

    text_parts = []
    for part in content.get("parts") or []:
        text = part.get("text") if isinstance(part, dict) else None
        if text:
            text_parts.append(text)

    return "\n".join(text_parts).strip()


def test_deployment(config, resource_id, message=None):
    """Test a deployed agent with a sample query."""
    print(f"Testing deployment: {resource_id}")

    session_service = VertexAiSessionService(config["project_id"], config["location"])

    session = asyncio.run(
        session_service.create_session(
            app_name=resource_id,
            user_id="carenav_test_user",
        )
    )

    remote_agent = agent_engines.get(resource_id)
    test_message = message or "I have chest pain and feel dizzy. What should I do?"

    print(f"Sending test message: {test_message}")
    print("Response:")

    response_parts = []
    for event in remote_agent.stream_query(
        user_id="carenav_test_user",
        session_id=session.id,
        message=test_message,
    ):
        text = _event_text(event)
        if text:
            response_parts.append(text)

    if response_parts:
        print("\n\n".join(response_parts))
    else:
        print("No assistant text was returned. Check Agent Engine logs for raw events.")

    print("Test completed.")


def main():
    """Handle deployment operations."""
    print("CareNav AI Deployment")
    print("=" * 50)

    config = load_deployment_config()
    if not config:
        return

    if not validate_config(config):
        return

    print("Configuration:")
    print(f"   Project ID: {config['project_id']}")
    print(f"   Location: {config['location']}")
    print(f"   Bucket: {config['bucket']}")
    print(f"   Deployment Name: {config['deployment_name']}")
    print()

    vertexai.init(
        project=config["project_id"],
        location=config["location"],
        staging_bucket=f"gs://{config['bucket']}",
    )

    if len(sys.argv) < 2:
        print("Please specify a command:")
        print("   python deploy.py create")
        print("   python deploy.py delete <resource_id>")
        print("   python deploy.py test <resource_id> [message]")
        return

    command = sys.argv[1].lower()

    if command == "create":
        resource_name = create_deployment(config)
        resource_id = resource_name.split("/")[-1]
        print("\nDeployment successful.")
        print(f"To test: python deploy.py test {resource_id}")
        print(f"To delete: python deploy.py delete {resource_id}")

    elif command == "delete":
        if len(sys.argv) < 3:
            print("Please provide resource_id for delete command.")
            print("   python deploy.py delete <resource_id>")
            return

        delete_deployment(sys.argv[2])

    elif command == "test":
        if len(sys.argv) < 3:
            print("Please provide resource_id for test command.")
            print("   python deploy.py test <resource_id> [message]")
            return

        message = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else None
        test_deployment(config, sys.argv[2], message)

    else:
        print(f"Unknown command: {command}")
        print("Available commands: create, delete, test")


if __name__ == "__main__":
    main()
