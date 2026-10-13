# NovaDash Integrations

NovaDash connects with the tools your team already uses. This guide covers all available integrations — from real-time Slack notifications to full two-way GitHub synchronization — plus the REST API and webhook system for custom integrations.

---

## Slack Integration

Connect NovaDash to your Slack workspace to bring project activity directly into your team's communication channels.

### Connecting Slack

1. Go to **Settings → Integrations → Slack**.
2. Click **Connect Slack Workspace**.
3. You are redirected to Slack's OAuth authorization page.
4. Select the Slack workspace to connect and click **Allow**.
5. NovaDash installs the NovaDash bot in your Slack workspace.
6. You are returned to NovaDash with a confirmation message.

### Channel Routing

After connecting, configure which NovaDash events post to which Slack channels:

1. In **Settings → Integrations → Slack → Channel Routing**, click **Add Route**.
2. Select the event type (e.g., "Task status changed to Done", "New Urgent task", "Task overdue").
3. Select the Slack channel to post to (NovaDash must be invited to the channel first: `/invite @NovaDash`).
4. Optionally filter by project (e.g., only route events from "Web App v2" to `#engineering`).
5. Save the route.

Multiple routes can be configured — events can trigger multiple routes simultaneously.

### Slash Commands

Once the NovaDash bot is in a channel, team members can use slash commands:

| Command                         | Description                                      |
|---------------------------------|--------------------------------------------------|
| `/nova task "Title"`            | Create a task in the default project             |
| `/nova task "Title" in "Proj"`  | Create a task in a specific project              |
| `/nova status TASK-123`         | Get the current status of a task                 |
| `/nova assign TASK-123 @alice`  | Assign a task to a teammate                      |
| `/nova done TASK-123`           | Mark a task as Done                              |
| `/nova search "query"`          | Search for tasks matching a keyword              |

### Personal Slack Notifications

Individual users can connect their own Slack account (separate from the workspace connection) to receive personal notifications as Slack DMs. Each user does this at **Profile → Notifications → Connect Slack**.

---

## GitHub Integration

The GitHub integration links pull requests to NovaDash tasks, enabling automatic status updates based on code activity.

### Connecting GitHub

1. Go to **Settings → Integrations → GitHub**.
2. Click **Connect GitHub**.
3. Authorize via GitHub OAuth — choose to connect a personal account or an organization.
4. Select which repositories to link to NovaDash.

### Linking PRs to Tasks

In any GitHub PR title or body, mention a NovaDash task using its ID:

```
Fix login redirect bug — NovaDash: TASK-456
```

Or use the abbreviated format: `[TASK-456]` anywhere in the PR title or description. NovaDash detects this and creates a bi-directional link.

### Auto-Status Updates

Configure automatic status transitions based on GitHub events:

| GitHub Event         | NovaDash Action (configurable)              |
|---------------------|----------------------------------------------|
| PR opened           | Move linked task to "In Review"              |
| PR merged           | Move linked task to "Done"                   |
| PR closed (no merge)| Move linked task back to "In Progress"       |
| PR review requested | Add comment to task with reviewer's name     |
| PR approved         | Add comment to task: "PR approved by @name"  |

These rules are configured per project in **Project Settings → GitHub Automation Rules**.

### Branch Naming Convention

NovaDash generates a suggested branch name for each task, visible in the task's detail panel. Example: `feature/task-456-fix-login-redirect`. Using this naming convention allows NovaDash to auto-detect branch pushes and link them to tasks without needing to mention the task ID in the PR.

---

## Zapier Integration

NovaDash is available in Zapier's app directory with over 50 triggers and actions, enabling no-code integration with 6,000+ apps.

### Available Triggers

Zapier triggers fire when something happens in NovaDash:
- Task Created, Task Updated, Task Completed, Task Overdue
- New Comment on Task, Task Assigned to User
- Project Created, Project Archived
- New Member Joined Workspace

### Available Actions

Zapier actions let other apps create or update data in NovaDash:
- Create Task (with all fields)
- Update Task Status, Priority, Assignee
- Add Comment to Task
- Create Project
- Invite User to Workspace

### Connecting via Zapier

1. In Zapier, search for "NovaDash" and select it as a trigger or action app.
2. Click **Connect Account** — enter your NovaDash API key (generate one at **Profile → API Keys**).
3. Select a workspace and authorize.

---

## REST API

NovaDash's REST API allows full programmatic access to your workspace data.

### Authentication

All API requests require a Bearer token in the `Authorization` header:

```
Authorization: Bearer <your_api_key>
```

Session tokens (from `/auth/login`) and API keys (from **Profile → API Keys**) are both accepted. API keys are recommended for integrations.

### Base URL and Versioning

```
https://api.novadash.io/v2
```

NovaDash maintains two active API versions: `v1` and `v2`. `v1` is in maintenance mode — it receives security patches only, no new features. `v2` is the current stable version. New integrations should use `v2`.

**Deprecation Policy:** API versions are deprecated with a minimum **12-month notice**. During the deprecation window, both old and new behavior are supported. Breaking changes are never made within a version.

### Common Endpoints

| Endpoint                     | Methods          | Description                     |
|-----------------------------|------------------|---------------------------------|
| `/users`                    | GET              | List workspace users            |
| `/users/{id}`               | GET, PUT, DELETE | Get/update/remove a user        |
| `/projects`                 | GET, POST        | List or create projects         |
| `/projects/{id}`            | GET, PUT, DELETE | Get/update/delete a project     |
| `/projects/{id}/tasks`      | GET, POST        | List or create tasks in project |
| `/tasks/{id}`               | GET, PUT, DELETE | Get/update/delete a task        |
| `/tasks/{id}/comments`      | GET, POST        | List or add comments            |
| `/tasks/{id}/subtasks`      | GET, POST        | List or create subtasks         |
| `/webhooks`                 | GET, POST        | List or register webhooks       |

Full endpoint documentation with request/response schemas is available at `https://docs.novadash.io/api`.

---

## Rate Limits

NovaDash enforces per-workspace API rate limits:

| Plan       | Rate Limit              |
|-----------|-------------------------|
| Free       | 1,000 requests/hour     |
| Pro        | 5,000 requests/hour     |
| Enterprise | Custom (negotiated)     |

Rate limit headers are included in every API response:
```
X-RateLimit-Limit: 5000
X-RateLimit-Remaining: 4823
X-RateLimit-Reset: 1731672000
```

When the limit is exceeded, the API returns `429 Too Many Requests`. The `Retry-After` header indicates how many seconds to wait.

---

## Webhooks vs. Polling

Use this guide to choose between webhooks and polling for your integration:

| Use Case                                        | Recommendation |
|------------------------------------------------|----------------|
| Real-time event handling (task completed, PR merged) | Webhooks    |
| Syncing data on a schedule (nightly data export) | Polling       |
| Your server can receive inbound HTTP requests   | Webhooks       |
| Your environment is behind a firewall           | Polling        |
| You need guaranteed delivery with retry logic   | Webhooks (NovaDash retries 3 times) |
| Simple scripts that run periodically            | Polling        |

**Webhooks** are the preferred approach for real-time integrations. They push data to you immediately with retry guarantees.

**Polling** (repeatedly calling `GET /projects/{id}/tasks?updated_since=...`) is appropriate for batch processes or environments that cannot receive inbound HTTP connections. Use the `updated_since` query parameter with an ISO 8601 timestamp to efficiently retrieve only changed records.
