# NovaDash Notifications

Notifications keep your team informed without overwhelming anyone's inbox. NovaDash offers a flexible notification system with multiple channels, granular triggers, and smart digest modes that consolidate alerts into summaries.

---

## Notification Channels

NovaDash delivers notifications through four channels. You can enable any combination.

### In-App Notifications

The bell icon (🔔) in the top-right navigation shows your in-app notification feed. In-app notifications appear in real time and persist until dismissed. You can mark them as read individually or click **Mark All Read**.

In-app notifications are always enabled and cannot be disabled — they are the base channel. All other channels are supplementary.

### Email Notifications

Email notifications are sent to the email address on your NovaDash profile. They are enabled by default for all users but can be configured at a granular level.

- Emails are sent in real time by default.
- Alternatively, configure **Digest Mode** (see below) to batch them.
- HTML email format with direct deep-links back to the task or comment.
- Unsubscribe link in every email footer (temporarily suppresses all email for 30 days).

### Slack Notifications

Connect your NovaDash workspace to a Slack workspace (see Integrations documentation) to route notifications to Slack.

**Slack notification modes:**
- **Personal DM**: Each user receives their own notifications as Slack DMs from the NovaDash bot.
- **Channel Routing**: Specific notification types can be sent to shared channels (e.g., all `Urgent` task assignments go to `#urgent-tasks`; all completed tasks go to `#project-updates`).

Slack notification content mirrors the in-app notification with a deep-link back to NovaDash.

### Webhooks

For custom integrations and automated pipelines, NovaDash can deliver notifications as HTTP POST requests to any URL you specify.

Webhook notifications contain a JSON payload with full event context. They can be filtered by event type, project, or priority. See the Webhook Payload Format section for details.

---

## Notification Triggers

You control exactly which events generate notifications. Configure triggers at **Profile → Notifications → Trigger Settings**.

### Available Triggers

| Trigger                     | Description                                                      |
|-----------------------------|------------------------------------------------------------------|
| Task assigned to me         | Someone assigns a task to you                                    |
| Task unassigned from me     | A task is unassigned from you                                    |
| Due date approaching        | Task due date is within 24 hours (configurable: 1h, 4h, 24h, 48h) |
| Task overdue                | Task passes due date without being completed                     |
| Comment mention             | Someone @mentions you in a task comment                          |
| Status change on my tasks   | Status changes on tasks you own or are assigned to               |
| Status change on watched tasks | Status changes on tasks you've explicitly "watched"           |
| New task in project         | A new task is created in a project you're a member of            |
| Task moved to my project    | A task is moved into one of your projects                        |
| Project update              | Project-level events (member added, settings changed)            |
| Comment on my tasks         | Any comment on a task assigned to you                            |

### Per-Channel Trigger Configuration

Each trigger can be independently enabled or disabled per channel. For example, you can enable "comment mention" for in-app and email, but disable "new task in project" for email to reduce noise while keeping it visible in-app.

---

## Digest Mode

Instead of receiving individual emails for each event, Digest Mode batches your notifications into periodic summary emails.

### Digest Options

- **Daily Digest**: One email per day, sent at a configurable time (default: 8:00 AM in your profile timezone).
- **Weekly Digest**: One email per week, sent on a configurable day and time (default: Monday 8:00 AM).
- **No Digest (Real-Time)**: Default behavior — individual emails as events occur.

### Configuring Digest Mode

Go to **Profile → Notifications → Email Delivery**:
1. Select **Digest Mode**: Daily or Weekly.
2. Set the delivery time and day.
3. Choose which trigger types to include in the digest vs. send real-time (e.g., @mentions can still be sent immediately even in digest mode).

### What's in a Digest

The digest email contains:
- A list of all events since the last digest, grouped by project.
- A count of total unread in-app notifications.
- Direct links to each item.
- A "View All" link to the full in-app notification feed.

---

## Do-Not-Disturb Hours

Do-Not-Disturb (DND) mode silences email and Slack notifications during specified hours — useful for maintaining work-life balance or focus blocks.

### Configuration

Go to **Profile → Notifications → Do-Not-Disturb**:
1. Toggle **Enable DND Hours**.
2. Set **Start Time** and **End Time** (uses your profile timezone).
3. Select which days DND applies (e.g., weekdays only, or all 7 days).

### How DND Works

During DND hours:
- In-app notifications continue to accumulate normally (visible when you return).
- Email and Slack notifications are **held** and delivered as a batch at the end of the DND window.
- Webhook notifications are **not** held — they fire in real time regardless of DND.

**Override:** Notifications triggered by tasks with **Urgent** priority bypass DND by default. This can be disabled in advanced DND settings if desired.

---

## Webhook Payload Format

NovaDash webhooks deliver a JSON POST to your configured endpoint. Each webhook is signed for authenticity.

### Example Payload

```json
{
  "event_id": "evt_01j8k9m2n3p4q5r6s7t8",
  "event_type": "task.status_changed",
  "timestamp": "2024-11-15T14:32:00Z",
  "workspace_id": "ws_abc123",
  "actor": {
    "id": "usr_xyz789",
    "name": "Alice Johnson",
    "email": "alice@example.com"
  },
  "data": {
    "task_id": "task_def456",
    "task_title": "Fix login redirect bug",
    "project_id": "proj_ghi012",
    "project_name": "Web App v2",
    "old_status": "In Progress",
    "new_status": "In Review",
    "assignee": {
      "id": "usr_xyz789",
      "name": "Alice Johnson"
    }
  }
}
```

### Event Types

- `task.created`, `task.updated`, `task.deleted`, `task.status_changed`
- `task.assigned`, `task.commented`, `task.due_soon`, `task.overdue`
- `project.created`, `project.archived`, `project.member_added`
- `user.invited`, `user.joined`

### Signature Verification

Every webhook request includes an `X-NovaDash-Signature` header. This is an HMAC-SHA256 signature of the raw request body using your **webhook secret** (visible in **Settings → Integrations → Webhooks → [Webhook] → Show Secret**).

To verify in Python:
```python
import hmac, hashlib

def verify_signature(payload_bytes: bytes, secret: str, signature_header: str) -> bool:
    expected = hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature_header)
```

### Retry Logic

If your endpoint returns a non-2xx HTTP status or times out (>30 seconds), NovaDash retries with **exponential backoff**:
- Attempt 1: Immediate
- Attempt 2: 5 minutes later
- Attempt 3: 30 minutes later

If all 3 attempts fail, the webhook event is marked as **failed** and logged in **Settings → Integrations → Webhooks → [Webhook] → Delivery Log**. Failed deliveries can be manually replayed from the Delivery Log.
