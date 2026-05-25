# IncidentForge Environment Setup

Do not paste secrets into chat, commits, screenshots, or shared docs. Put them only in `.env`.

Start from:

```powershell
copy .env.example .env
```

Then fill these values.

## Required For Local Demo

```env
APP_BASE_URL=http://localhost:8000
DEMO_MODE=true
```

With `DEMO_MODE=true`, IncidentForge can run the full demo path using mock Jira, Slack, Confluence, and PagerDuty outputs.

## OpenAI

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4.1-mini
OPENAI_POSTMORTEM_MODEL=gpt-4.1
```

Where to get it:

1. Open the OpenAI dashboard API keys page.
2. Create a project API key.
3. Paste it into `OPENAI_API_KEY`.

Without this, the app uses the fallback parser and deterministic postmortem/status text.

## Slack

```env
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...
```

Where to get it:

1. Create or open a Slack app at `api.slack.com/apps`.
2. Add bot scopes:
   - `commands`
   - `chat:write`
   - `channels:manage`
   - `channels:read`
   - `groups:read`
3. Install the app to your workspace.
4. Copy the Bot User OAuth Token into `SLACK_BOT_TOKEN`.
5. Copy the Signing Secret from Basic Information into `SLACK_SIGNING_SECRET`.
6. Add slash command `/incident` with request URL:

```text
{APP_BASE_URL}/slack/commands
```

7. Enable Interactivity with request URL:

```text
{APP_BASE_URL}/slack/actions
```

For local Slack testing, `APP_BASE_URL` must be a public HTTPS tunnel URL, not `localhost`.

## Jira Cloud

```env
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=you@example.com
JIRA_API_TOKEN=...
JIRA_PROJECT_KEY=OPS
```

Where to get it:

1. Use your Atlassian site URL for `JIRA_BASE_URL`.
2. Use your Atlassian login email for `JIRA_EMAIL`.
3. Create an Atlassian API token and paste it into `JIRA_API_TOKEN`.
4. Use the project key where incident issues should be created, for example `OPS`.

Jira is the source of truth. When `DEMO_MODE=false`, Jira must be configured correctly.

## Confluence Cloud

```env
CONFLUENCE_BASE_URL=https://your-domain.atlassian.net
CONFLUENCE_EMAIL=you@example.com
CONFLUENCE_API_TOKEN=...
CONFLUENCE_SPACE_ID=...
```

Use the same Atlassian account email and API token as Jira if that account has Confluence permissions.

To find `CONFLUENCE_SPACE_ID`, open the target space in Confluence and use the REST API or browser network response for the space details. If this slows the demo down, keep `DEMO_MODE=true` and use the Confluence mock fallback.

## PagerDuty

```env
PAGERDUTY_ROUTING_KEY=...
```

Where to get it:

1. Create or open a PagerDuty service.
2. Add an Events API v2 integration.
3. Copy the Integration Key into `PAGERDUTY_ROUTING_KEY`.

With `DEMO_MODE=true`, PagerDuty returns a mock alert.

## Upstash Redis

```env
UPSTASH_REDIS_REST_URL=https://...
UPSTASH_REDIS_REST_TOKEN=...
```

Where to get it:

1. Create an Upstash Redis database.
2. Open the REST API section.
3. Copy `UPSTASH_REDIS_REST_URL`.
4. Copy `UPSTASH_REDIS_REST_TOKEN`.

Without this, IncidentForge uses in-memory state, which resets when the server restarts.

## Verify

```powershell
python scripts/check_credentials.py
```

For live integrations:

```env
DEMO_MODE=false
```

Then run:

```powershell
python scripts/check_credentials.py --strict
```

Strict mode exits with an error if live-mode credentials are incomplete.
