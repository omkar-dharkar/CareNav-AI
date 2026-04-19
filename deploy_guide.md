# CareNav AI Deployment Guide

This guide explains how to deploy **CareNav AI** to Google Cloud Vertex AI Agent Engine.

Author: **Omkar A Dharkar**

## Prerequisites

You need:

- Google Cloud project with billing enabled
- Vertex AI API enabled
- Cloud Storage bucket for staging
- Places API (New) enabled
- Gemini API key or Vertex AI-compatible model configuration
- Python 3.9+
- Local dependencies installed from `requirements.txt`

Recommended IAM roles:

- `Vertex AI User` or `Vertex AI Administrator`
- `Storage Object Admin` or `Storage Admin`
- `Service Account User` when using service accounts

## Create `deploy.env`

Copy the template:

```bash
copy deploy.env.template deploy.env
```

Example:

```env
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_CLOUD_STORAGE_BUCKET=your-staging-bucket

GOOGLE_PLACES_API_KEY=your-places-api-key
GOOGLE_API_KEY=your-google-ai-api-key
DEFAULT_MODEL=gemini-2.5-flash

DEPLOYMENT_NAME=CareNav-AI
DEPLOYMENT_DESCRIPTION=CareNav AI: U.S.-focused healthcare navigation with symptom triage, nearby facility search, and safe home-care guidance.
```

Do not commit `deploy.env`.

## Enable Required APIs

```bash
gcloud services enable aiplatform.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable places.googleapis.com
```

## Create a Staging Bucket

```bash
gsutil mb -l us-central1 gs://YOUR_BUCKET_NAME
gsutil versioning set on gs://YOUR_BUCKET_NAME
```

Use the bucket name without `gs://` in `deploy.env`.

## Deploy

```bash
python deploy.py create
```

Expected output:

```text
CareNav AI Deployment
==================================================
Configuration:
   Project ID: your-project-id
   Location: us-central1
   Bucket: your-staging-bucket
   Deployment Name: CareNav-AI

Creating CareNav AI deployment...
Created remote agent: projects/.../locations/us-central1/reasoningEngines/...
Resource ID: ...

Deployment successful.
To test: python deploy.py test <resource_id>
To delete: python deploy.py delete <resource_id>
```

## Test

```bash
python deploy.py test <resource_id>
```

The deployment test sends:

```text
I have chest pain and feel dizzy. What should I do?
```

Expected behavior:

- The response should direct the user to call 911.
- It should not recommend home remedies.
- It should preserve the medical disclaimer.

## Delete

```bash
python deploy.py delete <resource_id>
```

## Monitor

List deployments:

```bash
gcloud ai reasoning-engines list --location=us-central1
```

Describe a deployment:

```bash
gcloud ai reasoning-engines describe RESOURCE_ID --location=us-central1
```

Read logs:

```bash
gcloud logging read "resource.type=vertex_ai_reasoning_engine" --limit=50
```

## Troubleshooting

### `deploy.env file not found`

Create it from the template:

```bash
copy deploy.env.template deploy.env
```

### Missing environment variables

Confirm these values are set:

- `GOOGLE_CLOUD_PROJECT`
- `GOOGLE_CLOUD_LOCATION`
- `GOOGLE_CLOUD_STORAGE_BUCKET`
- `GOOGLE_PLACES_API_KEY`

### Places API errors

CareNav AI uses **Places API (New)**:

```text
https://console.cloud.google.com/apis/library/places.googleapis.com
```

Do not rely on the legacy Places web service endpoint for this project.

### Gemini quota errors

Free-tier Gemini requests can return 429 errors during rapid testing. The default model is:

```env
DEFAULT_MODEL=gemini-2.5-flash
```

Wait for the retry window or enable billing / higher quota in Google AI Studio.

### Permission errors

Check:

- Billing is enabled.
- Your account has Vertex AI and Storage permissions.
- Your staging bucket exists.
- Your bucket location is compatible with the Vertex AI location you choose.

## Security Checklist

- Never commit `.env`.
- Never commit `deploy.env`.
- Never commit API keys.
- Never commit service account JSON files.
- Restrict API keys by API.
- Rotate exposed keys immediately.

## Production Notes

CareNav AI is a portfolio-grade prototype, not a regulated clinical product. Before production use, add:

- User-entered location fallback
- Stronger audit logging
- Rate limiting
- PHI handling policy
- Human escalation workflow
- Clinical safety review
- HIPAA and compliance review where applicable
