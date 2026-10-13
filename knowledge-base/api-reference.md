# NovaDash API Reference

The NovaDash REST API gives you full programmatic access to your workspace. Build integrations, automate workflows, export data, and connect NovaDash to your internal tooling.

---

## Authentication

All API requests must be authenticated. NovaDash supports two authentication methods:

### API Keys (Recommended for Integrations)

Generate an API key at **Profile → API Keys → New API Key**. Use it in the `Authorization` header:

```http
GET /v2/projects HTTP/1.1
Host: api.novadash.io
Authorization: Bearer nd_live_aBcDeFgHiJkLmNoPqRsTuVwXyZ
```

API keys have configurable permission scopes: `read`, `write`, `admin`. Use the least-privilege scope for your use case.

### Session Tokens

Session tokens obtained via `POST /v2/auth/login` are also accepted as Bearer tokens. These are suitable for user-facing applications where the user logs in interactively.

Session tokens expire after 30 days (configurable per workspace). API keys do not expire unless given an explicit expiry date.

---

## Base URL and Versioning

```
https://api.novadash.io/v2
```

**Current stable version:** `v2`
**Maintenance version:** `v1` (security patches only, no new features)

The version is part of the path. Example:
```
https://api.novadash.io/v2/projects
https://api.novadash.io/v2/tasks/task_abc123
```

**Version headers:** You can also specify the version via header instead of path:
```
X-NovaDash-API-Version: 2024-11-01
```

Date-based versioning (YYYY-MM-DD) is used for minor changes within v2. Your API key is pinned to the version active when the key was created. Opt into newer versions by updating the header.

**Deprecation Policy:** Versions are deprecated with a minimum 12-month notice. Both versions remain fully functional during the deprecation window. Breaking changes are never made within a single version.

---

## Common Endpoints

### Users

```
GET    /v2/users                List all workspace users
GET    /v2/users/{id}           Get a specific user
PUT    /v2/users/{id}           Update a user's role or profile
DELETE /v2/users/{id}           Deactivate (offboard) a user
POST   /v2/users/invite         Invite a new user
```

**Example — List Users:**
```http
GET /v2/users?role=admin&status=active HTTP/1.1
Authorization: Bearer <token>
```
```json
{
  "users": [
    {
      "id": "usr_abc123",
      "email": "alice@example.com",
      "name": "Alice Johnson",
      "role": "admin",
      "status": "active",
      "created_at": "2024-01-15T09:00:00Z"
    }
  ],
  "next_cursor": "usr_xyz789",
  "total_count": 47
}
```

### Projects

```
GET    /v2/projects             List all accessible projects
POST   /v2/projects             Create a new project
GET    /v2/projects/{id}        Get a specific project
PUT    /v2/projects/{id}        Update project settings
DELETE /v2/projects/{id}        Soft-delete a project (30-day recovery)
POST   /v2/projects/{id}/archive    Archive a project
POST   /v2/projects/{id}/duplicate  Duplicate a project
```

### Tasks

```
GET    /v2/projects/{id}/tasks      List tasks in a project
POST   /v2/projects/{id}/tasks      Create a task
GET    /v2/tasks/{id}               Get a specific task
PUT    /v2/tasks/{id}               Update a task
DELETE /v2/tasks/{id}               Soft-delete a task
POST   /v2/tasks/{id}/status        Change task status
POST   /v2/tasks/{id}/assign        Assign a task to a user
GET    /v2/tasks/{id}/subtasks      List subtasks
POST   /v2/tasks/{id}/subtasks      Create a subtask
GET    /v2/tasks/{id}/comments      List comments on a task
POST   /v2/tasks/{id}/comments      Add a comment to a task
```

### Comments

```
GET    /v2/comments/{id}        Get a specific comment
PUT    /v2/comments/{id}        Edit a comment (own comments only)
DELETE /v2/comments/{id}        Delete a comment
```

---

## Pagination

NovaDash uses **cursor-based pagination** for all list endpoints. Cursor-based pagination is more efficient than offset-based for large datasets and handles concurrent modifications gracefully.

### Request

Use the `limit` and `cursor` query parameters:
```
GET /v2/projects/{id}/tasks?limit=20&cursor=task_xyz789
```

- `limit`: Number of results per page. Default: 20. Maximum: 100.
- `cursor`: The cursor value from the previous response's `next_cursor` field.

### Response

Every list response includes:
```json
{
  "data": [...],
  "next_cursor": "task_abc456",
  "has_more": true,
  "total_count": 243
}
```

- `next_cursor`: Pass this as the `cursor` parameter in the next request. If `null`, you've reached the end.
- `has_more`: Boolean — `true` if more pages exist.
- `total_count`: Total number of records matching the query (not just the current page).

When `has_more` is `false`, `next_cursor` will be `null` — stop paginating.

---

## Error Codes

NovaDash uses standard HTTP status codes. All errors return a JSON body with a `code`, `message`, and optional `details` field.

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The 'title' field is required.",
    "details": {
      "field": "title",
      "constraint": "required"
    },
    "request_id": "req_01j8k9m2n3p4q5r6"
  }
}
```

### Status Codes

| Status | Code                  | Meaning                                                            |
|--------|-----------------------|--------------------------------------------------------------------|
| 400    | VALIDATION_ERROR      | Request body or query parameters failed validation                 |
| 400    | INVALID_FORMAT        | Malformed JSON or incorrect data type                              |
| 401    | UNAUTHORIZED          | Missing, invalid, or expired authentication token                  |
| 401    | TOKEN_EXPIRED         | Session token or API key has expired                               |
| 403    | FORBIDDEN             | Authenticated, but insufficient permissions for this action        |
| 403    | PLAN_LIMIT_EXCEEDED   | Action would exceed a plan limit (e.g., >3 projects on Free plan)  |
| 404    | NOT_FOUND             | The requested resource does not exist                              |
| 409    | CONFLICT              | The resource already exists or state conflict (e.g., duplicate invite) |
| 422    | UNPROCESSABLE_ENTITY  | Semantically invalid request (e.g., assigning a non-member to a task) |
| 429    | RATE_LIMIT_EXCEEDED   | Too many requests — see rate limit headers                         |
| 500    | INTERNAL_ERROR        | Server error — retry with exponential backoff                      |
| 503    | SERVICE_UNAVAILABLE   | Scheduled maintenance or incident — check status.novadash.io       |

---

## Webhooks

Register webhooks via the API or through **Settings → Integrations → Webhooks**.

```
GET    /v2/webhooks             List registered webhooks
POST   /v2/webhooks             Register a new webhook
GET    /v2/webhooks/{id}        Get webhook details
PUT    /v2/webhooks/{id}        Update webhook URL or events
DELETE /v2/webhooks/{id}        Remove a webhook
POST   /v2/webhooks/{id}/test   Send a test event to the webhook
```

### Signature Verification

All webhook payloads are signed using HMAC-SHA256. The signature is in the `X-NovaDash-Signature` header. Verify it to ensure the payload came from NovaDash:

```python
import hmac, hashlib

def verify_webhook(payload: bytes, secret: str, signature: str) -> bool:
    computed = "sha256=" + hmac.new(
        secret.encode("utf-8"), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(computed, signature)
```

Always verify signatures before processing webhook events. Reject requests with missing or invalid signatures.

---

## SDK Availability

Official SDKs are available for the three most popular languages:

### Python SDK

```bash
pip install novadash-sdk
```

```python
from novadash import NovaDash

client = NovaDash(api_key="nd_live_...")
tasks = client.tasks.list(project_id="proj_abc123", status="in_progress")
```

### JavaScript / TypeScript SDK

```bash
npm install @novadash/sdk
```

```typescript
import { NovaDash } from "@novadash/sdk";

const client = new NovaDash({ apiKey: "nd_live_..." });
const tasks = await client.tasks.list({ projectId: "proj_abc123" });
```

### Ruby SDK

```bash
gem install novadash
```

```ruby
require "novadash"

client = Novadash::Client.new(api_key: "nd_live_...")
tasks = client.tasks.list(project_id: "proj_abc123")
```

All SDKs are open-source (MIT license), available on GitHub at `github.com/novadash/sdk-*`, and follow the same versioning as the REST API. They handle authentication, pagination, and retries automatically.
