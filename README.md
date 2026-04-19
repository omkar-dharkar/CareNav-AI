# CareNav AI

CareNav AI is a U.S.-focused healthcare navigation assistant by **Omkar A Dharkar**. It combines Gemini, Google ADK, Google Places API, and a custom FastAPI web interface to help users understand care urgency and find nearby care options.

Live demo: https://carenav-ai-493647769398.us-central1.run.app

> CareNav AI is an educational prototype, not a medical device and not a substitute for licensed medical care. In a medical emergency in the United States, call 911.

## What It Does

- Routes health questions through a multi-agent Google ADK system.
- Gives U.S.-specific emergency guidance: 911, Poison Help, and 988.
- Finds nearby hospitals, emergency departments, urgent care clinics, pharmacies, primary care clinics, and labs.
- Uses browser/device location in the public UI for nearby care results, with server IP lookup only as a fallback.
- Adds insurance-verification guidance for Medicaid, UnitedHealthcare, Medicare, and private plans.
- Presents results in a custom, original UI instead of the default ADK debugger.
- Deploys to Vertex AI Agent Engine for agent hosting and Cloud Run for the public web app.

## Tech Stack

- Python
- FastAPI and Uvicorn
- Google Agent Development Kit
- Gemini API
- Google Places API (New)
- Google Cloud Run
- Vertex AI Agent Engine
- Secret Manager
- HTML, CSS, and vanilla JavaScript

## Architecture

```text
User
  |
  v
Custom CareNav UI on Cloud Run
  |-- /api/chat -> Google ADK coordinator agent -> Gemini
  |-- /api/hospitals -> browser/device coordinates -> Google Places API (New)
  |
  v
Specialist agents
  |-- Symptom Analyzer
  |-- Hospital Finder
  `-- Home Care Advisor
```

## Project Structure

```text
CareNav-AI/
|-- carenav_agents/
|   |-- agent.py
|   |-- config.py
|   |-- prompt.py
|   |-- symptom_agent.py
|   |-- hospital_finder_agent.py
|   `-- home_remedies_agent.py
|-- ui/
|   |-- assets/
|   |-- app.js
|   |-- index.html
|   `-- styles.css
|-- web_app.py
|-- deploy.py
|-- deploy.env.template
|-- deploy_guide.md
|-- setup_env.py
|-- requirements.txt
|-- Procfile
|-- .gcloudignore
|-- LICENSE
`-- README.md
```

## Local Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Create a local `.env` file:

```powershell
python setup_env.py
```

Add your keys:

```env
GOOGLE_API_KEY=your_google_ai_api_key
GOOGLE_GENAI_USE_VERTEXAI=False
DEFAULT_MODEL=gemini-2.5-flash

GOOGLE_PLACES_API_KEY=your_google_places_api_key

GOOGLE_CLOUD_PROJECT=your-google-cloud-project
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_CLOUD_STORAGE_BUCKET=your-staging-bucket
```

Run the custom UI:

```powershell
python web_app.py
```

Open:

```text
http://127.0.0.1:8080
```

Optional ADK debug UI:

```powershell
adk web
```

## Deployment

### Cloud Run Web App

The public UI is designed for Cloud Run. Runtime API keys should be stored in Google Secret Manager, not committed to GitHub.

Example:

```powershell
gcloud run deploy carenav-ai --source . --region us-central1 --allow-unauthenticated
```

This repository includes:

- `Procfile` for the Cloud Run web process
- `.gcloudignore` to exclude local secrets, logs, virtual environments, and Git data
- `deploy.env.template` for local deployment configuration

### Vertex AI Agent Engine

The ADK agent can also be deployed to Vertex AI Agent Engine:

```powershell
copy deploy.env.template deploy.env
python deploy.py create
```

See `deploy_guide.md` for more detail.

## Example Prompts

```text
I have chest pain and feel dizzy. What should I do and where can I go nearby?
```

```text
Find urgent care near me and explain how to verify Medicaid or UnitedHealthcare acceptance.
```

```text
I have mild nausea with no emergency symptoms. What safe home care can I try?
```

Expected safety behavior:

- Tell users to call 911 for potential emergencies.
- Avoid home remedies for high-risk symptoms.
- Recommend Poison Help at 1-800-222-1222 for poisoning or overdose concerns.
- Mention 988 for mental health crisis or suicidal thoughts.
- Explain that Google Places does not verify insurance-network status.

## Security Notes

- Do not commit `.env`, `deploy.env`, API keys, or service account JSON files.
- The public Cloud Run deployment uses Secret Manager for runtime API keys.
- Insurance acceptance must be verified with the facility and insurer.
- This project is a portfolio-grade prototype, not a regulated clinical product.

## Author

Omkar A Dharkar

## License

MIT
