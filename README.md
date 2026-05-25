# IncidentForge

One command. Full incident workflow.

IncidentForge is a Slack-native, Jira-first AI incident commander. It turns a messy incident command into a validated action plan, executes the workflow across incident tools, stores a timeline, answers status questions, and drafts the postmortem.

## Hackathon Shipping

For a hackathon, users do not configure env vars. Deploy one hosted backend with your secrets, connect it to one demo Slack workspace, and let judges use `/incident`.

See [docs/HACKATHON_SHIP.md](docs/HACKATHON_SHIP.md).

## Local Setup

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
copy .env.example .env
```

`DEMO_MODE=true` lets the app run without real Slack, Jira, Confluence, PagerDuty, or Redis credentials.

## Run

```powershell
python -m uvicorn app.main:app --reload
```

Open:

- `http://localhost:8000/health`
- `http://localhost:8000/docs`
- `http://localhost:8000/dashboard/incidents/{incident_id}`

## Demo API Flow

Create a plan:

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/api/incidents/plan `
  -ContentType "application/json" `
  -Body '{"message":"P1 down. Checkout service returning 500s. Notify backend, create a critical Jira ticket, open an incident channel, page Sarah, and remind us in 20 minutes.","created_by":"U123","slack_channel_id":"C123"}'
```

Execute the returned plan:

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/api/incidents/{incident_id}/execute `
  -ContentType "application/json" `
  -Body '{"plan_id":"{plan_id}","confirmed":true}'
```

## Verify

```powershell
python -m ruff check app tests
python -m pytest tests -p no:cacheprovider
```

## Credential Check

See [docs/ENV_SETUP.md](docs/ENV_SETUP.md) for where each value comes from.

After filling `.env`, run:

```powershell
python scripts/check_credentials.py
```

The command reports whether OpenAI, Slack, Jira, Confluence, PagerDuty, and Upstash Redis are configured without printing any secret values.

For live mode readiness:

```powershell
python scripts/check_credentials.py --strict
```

## Hosted Smoke Test

```powershell
python scripts/smoke_test.py https://your-deployed-app.example.com
```
