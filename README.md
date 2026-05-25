# IncidentForge

One command. Full incident workflow.

IncidentForge is a Slack-native, Jira-first AI incident commander. It turns a messy incident command into a validated action plan, executes the workflow across incident tools, stores a timeline, answers status questions, and drafts the postmortem.

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
