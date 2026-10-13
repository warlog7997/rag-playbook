# NovaDash Troubleshooting

This guide covers common issues users and admins encounter with NovaDash and provides step-by-step resolution instructions. If you don't find your answer here, see the Contacting Support section at the end.

---

## Login Issues

### SSO Misconfiguration

**Symptom:** Clicking "Login with SSO" returns an error like "SAML response is invalid" or "Assertion validation failed."

**Causes and Fixes:**

1. **Expired SP Metadata:** If you rotated your IdP signing certificate without updating NovaDash, the SAML signature will fail. Fix: go to **Settings → Security → Identity Provider Binding → [Your Provider] → Update Metadata**, then re-upload the IdP metadata XML.

2. **Clock Skew:** SAML assertions are time-sensitive. If your IdP's server clock is more than 5 minutes off from NovaDash's servers, assertions will be rejected as expired or not-yet-valid. Fix: ensure your IdP server uses NTP synchronization.

3. **Incorrect ACS URL:** The Assertion Consumer Service URL in your IdP must exactly match `https://app.novadash.io/auth/saml/callback`. Even a trailing slash difference will cause failures.

4. **Attribute Mapping Missing:** If the `email` attribute is not mapped in your IdP, NovaDash cannot identify the user. Fix: verify the email attribute is named `email` (or configure a custom mapping in **Identity Provider Binding → Attribute Mappings**).

5. **User Not Provisioned:** With JIT provisioning disabled, the user must already exist in NovaDash before SSO login is possible. Fix: invite the user via **Settings → Users → Invite Members** first, then they can use SSO.

### Expired Session Tokens

**Symptom:** User is logged in but gets redirected to the login page unexpectedly. API calls return `401 TOKEN_EXPIRED`.

**Cause:** Session tokens have a configurable expiry (default: 30 days). If the user hasn't interacted with NovaDash in that period, their session expires.

**Fix:** The user simply logs in again. If frequent expiry is disruptive, workspace admins can extend the session duration: **Settings → Security → Session Duration**.

**For API keys:** API keys with an expiry date expire silently. Check **Profile → API Keys** — if the key shows "Expired," generate a new one and update your integration.

### Lockout Reset

**Symptom:** User receives "Account locked. Try again in X minutes" after multiple failed logins.

**Automatic Reset:** After 15 minutes, the lockout clears automatically. No action needed.

**Admin Manual Reset:** If the user can't wait, any Admin can manually unlock the account:
1. Go to **Settings → Users → [User Name] → Unlock Account**.
2. Click **Confirm Unlock**.
The user can attempt login immediately.

**If the Owner is locked out:** Contact NovaDash support at support@novadash.io with your workspace ID for identity verification and manual unlock.

---

## Performance Issues

### Slow Dashboard Loading

**Symptom:** The project dashboard takes >5 seconds to load. The activity feed spins indefinitely.

**Cause:** For large projects with hundreds of tasks and thousands of activity events, the dashboard — especially the Activity Feed — can be slow.

**Fixes in order of impact:**

1. **Disable the Activity Feed:** In the project dashboard, click the settings gear icon on the Activity Feed widget and toggle it off. This is the single biggest performance improvement for large projects.

2. **Use Filters:** The default task view loads all tasks. Apply filters (assignee, status, date range) to limit the result set. Save frequently used filters for the whole team.

3. **Archive Completed Tasks:** Archived tasks are excluded from the default task view. Periodically archive all "Done" tasks older than 30 days.

4. **Disable Unused Dashboard Widgets:** Each dashboard widget makes a separate API call. Disable widgets you don't actively use (**Dashboard → Edit Widgets**).

5. **Check Browser Extensions:** Ad blockers and privacy extensions sometimes interfere with WebSocket connections used for real-time updates. Disable extensions temporarily to test.

### Slow API Response Times

If your API calls are consistently slow:
- Check `status.novadash.io` for active incidents.
- Ensure you're using `v2` not `v1` — v1 queries are on older infrastructure.
- Use pagination (`limit` parameter) instead of loading all records in one call.
- Cache frequently accessed read-only data (project lists, user lists) on your side.

---

## Data Sync Issues

### Integration Reconnection Steps

**Symptom:** Slack notifications stopped. GitHub PRs are no longer linking to tasks. Zapier zaps are failing with "Authentication Error."

**Cause:** OAuth tokens for integrations expire or are revoked when passwords change, users leave, or org-level permissions change.

**Fix — Re-authenticate the Integration:**

1. Go to **Settings → Integrations → [Integration Name]**.
2. If the connection shows "Disconnected" or "Error," click **Reconnect**.
3. You'll be sent through the OAuth flow again.
4. After reconnecting, verify the integration by triggering a test event.

**For Slack specifically:** If you changed your Slack workspace's OAuth permissions or rotated the NovaDash bot token, you need to disconnect fully (**Disconnect Slack**) and re-connect from scratch — not just re-authenticate.

**For GitHub:** If a team member who authorized the GitHub connection left the organization and their account was deactivated, the GitHub token may be invalid. Have a new admin re-authorize the integration.

### Zapier Sync Delays

Zapier zaps have a polling delay of 5-15 minutes depending on your Zapier plan. This is a Zapier limitation, not a NovaDash issue. For real-time event handling, switch to NovaDash webhooks instead of Zapier triggers.

---

## Common API Errors and Fixes

### 401 UNAUTHORIZED
- **Missing token:** Ensure the `Authorization: Bearer <token>` header is included.
- **Malformed token:** Check for extra whitespace, missing `Bearer ` prefix, or truncated key.
- **Revoked key:** Check **Profile → API Keys** — the key may have been manually revoked.

### 403 FORBIDDEN
- **Permission scope:** Your API key may have `read` scope when `write` is needed. Generate a new key with the correct scope.
- **Role restriction:** The user associated with the token doesn't have permission for this action (e.g., a Member trying to delete a project).
- **Plan limit:** `PLAN_LIMIT_EXCEEDED` means you've hit a Free plan restriction. Upgrade or free up resources.

### 429 RATE_LIMIT_EXCEEDED
- Check the `X-RateLimit-Reset` header for when the window resets.
- Implement exponential backoff: wait 1s, 2s, 4s, 8s between retries.
- If you consistently hit rate limits, upgrade your plan or contact support for a custom limit.

### 404 NOT_FOUND
- Verify the resource ID is correct. IDs are case-sensitive.
- Check if the resource was soft-deleted (tasks/projects have a 30-day recovery window).
- Ensure the authenticated user has access to the resource (private projects require membership).

### 500 INTERNAL_ERROR
- NovaDash server error. Retry with exponential backoff.
- If the error persists after 3 retries, check `status.novadash.io`.
- Include the `request_id` from the error response when contacting support.

---

## Contacting Support

### In-App Chat (Fastest)

Click the **?** icon in the bottom-right corner of any NovaDash screen. The in-app chat connects you to the support team. Pro users receive responses within 24 hours. Free users receive community-level support.

### Email Support

Send to support@novadash.io. Include:
- Your workspace name or ID (visible in **Settings → Workspace → Workspace ID**)
- Your user email
- A description of the issue and steps to reproduce
- Any error messages or `request_id` values from API errors
- Screenshots if relevant

### Enterprise SLA

Enterprise customers have a dedicated account manager and a custom SLA. Your account manager's contact is in your Enterprise contract and in **Settings → Billing → Enterprise Contact**. For critical incidents (workspace inaccessible), use the dedicated Emergency Support line provided in your Enterprise onboarding documentation.

### Status Page

Check `status.novadash.io` for real-time system status, active incidents, and historical uptime data. Subscribe to status updates via email or webhook from the status page.
