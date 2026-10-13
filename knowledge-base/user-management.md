# NovaDash User Management

Managing your team effectively is at the core of NovaDash. This guide covers everything from inviting your first team member to managing large organizations with hundreds of users, including roles, permissions, and the full lifecycle of a workspace member.

---

## User Roles and Permissions

NovaDash uses a hierarchical role system. Every user in a workspace has exactly one workspace-level role. Roles can be further overridden at the project level.

### Workspace Roles

| Permission                     | Owner | Admin | Member | Viewer |
|-------------------------------|-------|-------|--------|--------|
| Manage billing                | ✓     | ✗     | ✗      | ✗      |
| Delete workspace              | ✓     | ✗     | ✗      | ✗      |
| Transfer ownership            | ✓     | ✗     | ✗      | ✗      |
| Invite users                  | ✓     | ✓     | ✗      | ✗      |
| Remove users                  | ✓     | ✓     | ✗      | ✗      |
| Configure SSO/security        | ✓     | ✓     | ✗      | ✗      |
| Create projects               | ✓     | ✓     | ✓      | ✗      |
| Create/edit tasks             | ✓     | ✓     | ✓      | ✗      |
| View all projects             | ✓     | ✓     | ✗      | ✗      |
| View assigned projects        | ✓     | ✓     | ✓      | ✓      |
| Comment on tasks              | ✓     | ✓     | ✓      | ✓      |
| View reports and analytics    | ✓     | ✓     | ✓      | ✓      |

**Owner:** Each workspace has exactly one Owner. The Owner has unrestricted access to all settings, billing, and data. Ownership can be transferred but not deleted.

**Admin:** Can manage users, configure integrations, and access all projects. Multiple Admins are allowed. Recommended for team leads and managers.

**Member:** The standard role for contributors. Can create and manage tasks, projects, and participate in all collaboration features within projects they belong to.

**Viewer:** Read-only access. Useful for stakeholders, auditors, or clients who need visibility without edit rights.

---

## Inviting Users

Adding new team members to your workspace follows a multi-step flow:

### Invite Flow

1. Go to **Settings → Users → Invite Members**.
2. Enter the email address(es) of the people to invite. You can paste a comma-separated list to invite multiple users at once.
3. Select the role: Admin, Member, or Viewer (Owner cannot be assigned during invite).
4. Optionally, select one or more projects to add the invitee to immediately.
5. Click **Send Invites**.

### Invitation States

- **Pending**: The invite email has been sent. The invitee has not yet accepted. The invite link is valid for **7 days**.
- **Accepted**: The user clicked the invite link, created or linked their account, and joined the workspace. Status changes to **Active**.
- **Expired**: The invite was not accepted within 7 days. Admins can resend from **Settings → Users → Pending Invites**.
- **Revoked**: An admin manually cancelled the invite before acceptance.

### Re-inviting

If a user never received the invite or it expired, go to **Settings → Users → Pending Invites** and click **Resend** to generate a fresh invite link.

---

## Member Offboarding

When a team member leaves the organization, their workspace access must be properly removed. NovaDash refers to this process as **member offboarding** — a structured removal workflow that preserves data integrity and audit trails.

### Offboarding Steps

1. Navigate to **Settings → Users → [User Name]**.
2. Click **Offboard Member**.
3. The offboarding wizard presents three decisions:
   - **Task Reassignment**: Choose a user to inherit all of the departing member's open tasks, or leave them unassigned.
   - **Project Membership**: Remove the user from all projects, or retain project membership in read-only Viewer mode for 30 days (useful for knowledge transfer).
   - **Data Retention**: All comments, files, and history created by the user are retained permanently (never deleted with the user).
4. Confirm the offboarding.

### After Offboarding

- The user immediately loses login access.
- All their active sessions are invalidated.
- Their profile remains visible in task history, comments, and activity logs (attributed as "[User Name] — Former Member").
- If they had API keys, those are immediately revoked.
- Admins can still access all data the user created.

### Deactivation vs. Deletion

- **Deactivate**: The user cannot log in but all their data and history is preserved. Their seat is freed immediately.
- **Delete**: Permanently removes the user account. Data is retained but attributed to "[Deleted User]". This action is irreversible.

For compliance and audit purposes, NovaDash recommends deactivation over deletion.

---

## Transferring Workspace Ownership

Only the current Owner can transfer workspace ownership. This is irreversible without the new owner's cooperation.

1. Go to **Settings → Workspace → Transfer Ownership**.
2. Select the new Owner from the list of active Admins (only Admins can be designated as new Owners).
3. The new Owner receives an email requiring them to **confirm acceptance** within 48 hours.
4. On acceptance, the original Owner is demoted to Admin.
5. Both parties receive a confirmation email.

If the new Owner does not confirm within 48 hours, the transfer is cancelled. To transfer to a Member, first promote them to Admin.

---

## User Profile

Each user can manage their personal profile at **Profile → Edit Profile**:

- **Name**: Display name shown across all workspaces.
- **Avatar**: Upload a custom image (PNG/JPG, max 2MB) or use the auto-generated initial-based avatar.
- **Timezone**: Used for due date display, digest scheduling, and do-not-disturb hours. Defaults to browser-detected timezone.
- **Notification Preferences**: Control which events trigger notifications (see Notifications documentation).
- **Language**: NovaDash supports English, French, German, Spanish, and Japanese.
- **Linked Accounts**: Connect GitHub or Google for single-click auth in integrations.

Profile changes are reflected immediately across all workspaces the user belongs to.

---

## Bulk User Import via CSV

For onboarding large teams, NovaDash supports bulk user import via CSV upload.

### CSV Format

```
email,first_name,last_name,role,projects
alice@example.com,Alice,Smith,Member,"Project Alpha,Project Beta"
bob@example.com,Bob,Jones,Viewer,
carol@example.com,Carol,Lee,Admin,
```

**Required fields:** `email`, `role`
**Optional fields:** `first_name`, `last_name`, `projects` (comma-separated project names in quotes)

### Import Steps

1. Go to **Settings → Users → Import Users**.
2. Download the CSV template.
3. Fill in your users and upload the file.
4. NovaDash validates the CSV and shows a preview of all rows.
5. Rows with errors (invalid email, unrecognized role, unknown project) are highlighted — fix inline or skip.
6. Confirm import — invites are sent to all valid rows simultaneously.

**Limits:** Free plan — max 5 users. Pro plan — max 500 users per import batch. Enterprise — unlimited.

---

## User Activity Audit Log

Every action performed by users is recorded in the **Audit Log**, accessible to Admins and Owners at **Settings → Audit Log**.

### What Is Logged

- Login and logout events (with IP address and device)
- Failed login attempts
- User invites, role changes, and offboarding
- Project creation, archiving, and deletion
- Task creation, status changes, and deletion
- Settings changes (SSO, billing, security)
- API key generation and revocation

### Filtering and Export

The audit log supports filtering by:
- **User**: View all actions by a specific user.
- **Action Type**: Filter by event category (auth, users, projects, tasks, settings).
- **Date Range**: Up to 1 year of history on Pro, unlimited on Enterprise.

Logs can be exported as CSV or JSON. Enterprise plans can stream audit logs to a SIEM (Splunk, Datadog) via webhook.

**Retention:** Free plan — 30 days. Pro — 1 year. Enterprise — unlimited with external streaming support.
