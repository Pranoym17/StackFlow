# Hackathon Shipping Setup

For the hackathon, users and judges should not configure env vars. You configure one hosted IncidentForge backend and one demo Slack workspace. Everyone uses that same Slack app.

## Target Experience

Judges only do this:

```text
/incident P1 down. Checkout service returning 500s. Notify backend, create a critical Jira ticket, open an incident channel, page Sarah, and remind us in 20 minutes.
```

Your server owns all secrets.

## 1. Deploy Backend

Recommended quick path: Render.

1. Push this repo to GitHub.
2. Create a Render Web Service from the repo.
3. Use:

```text
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
Health Check Path: /health
```

The included `render.yaml` can also be used as a blueprint.

## 2. Set Hosted Environment Variables

In Render, add environment variables from `.env.example`.

Minimum strong hackathon setup:

```env
DEMO_MODE=true
APP_BASE_URL=https://your-render-service.onrender.com
OPENAI_API_KEY=...
SLACK_BOT_TOKEN=...
SLACK_SIGNING_SECRET=...
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=...
JIRA_API_TOKEN=...
JIRA_PROJECT_KEY=OPS
UPSTASH_REDIS_REST_URL=...
UPSTASH_REDIS_REST_TOKEN=...
```

Optional for real side effects:

```env
CONFLUENCE_BASE_URL=https://your-domain.atlassian.net
CONFLUENCE_EMAIL=...
CONFLUENCE_API_TOKEN=...
CONFLUENCE_SPACE_ID=...
PAGERDUTY_ROUTING_KEY=...
```

Keep `DEMO_MODE=true` until the final rehearsal. It allows Confluence/PagerDuty/demo-safe fallback behavior.

## 3. Configure Slack App

Create a Slack app in the demo workspace.

Bot scopes:

```text
commands
chat:write
channels:manage
channels:read
groups:read
```

Slash command:

```text
Command: /incident
Request URL: https://your-render-service.onrender.com/slack/commands
Short Description: Start or query an incident
```

Interactivity:

```text
Request URL: https://your-render-service.onrender.com/slack/actions
```

Install the app to the demo workspace, then copy:

```text
Bot User OAuth Token -> SLACK_BOT_TOKEN
Signing Secret -> SLACK_SIGNING_SECRET
```

## 4. Verify Hosted App

Open:

```text
https://your-render-service.onrender.com/health
https://your-render-service.onrender.com/docs
```

Then run in Slack:

```text
/incident P1 down. Checkout service returning 500s. Notify backend, create a critical Jira ticket, open an incident channel, page Sarah, and remind us in 20 minutes.
```

Click confirm.

Then run:

```text
/incident status
/incident timeline
/incident resolve rollback completed and checkout error rate normalized
```

## 5. What Users Need

Users only need access to your demo Slack workspace or a screen share of it. They do not need:

- `.env`
- API keys
- Jira admin access
- PagerDuty admin access
- local Python setup

## 6. Final Demo Mode Recommendation

For the safest live demo:

```env
DEMO_MODE=true
```

Use real Slack, OpenAI, Jira, and Upstash Redis. Let Confluence and PagerDuty safely mock if credentials or permissions are unreliable.
