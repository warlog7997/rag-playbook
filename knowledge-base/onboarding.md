# NovaDash Onboarding

Getting your team up and running in NovaDash should take less than 30 minutes. This guide walks through the free trial, the setup wizard, team onboarding, and importing data from your existing tools.

---

## 14-Day Free Trial

Every new NovaDash workspace starts on a **14-day free trial** of the Pro plan. There is no credit card required to begin — enter only your email and a workspace name to get started.

### What You Get During the Trial

- Full access to all Pro plan features: unlimited projects, all integrations, SSO, audit logs, advanced reporting, and priority support.
- Up to 20 users can join during the trial without any payment.
- 100 GB of storage.
- No automatic charges — at the end of 14 days, if you haven't added a payment method, the workspace transitions to the Free plan (not deleted).

### Trial Limitations

- You cannot process invoice-based payments during the trial (Enterprise feature).
- SLA guarantees are not available during the trial.
- SCIM provisioning is not available during the trial.

### Trial-to-Paid Conversion

To prevent feature disruption, NovaDash prompts workspace owners to add a payment method:
- **Day 10**: In-app banner and email: "4 days left in your trial."
- **Day 13**: Prominent in-app modal and email: "Trial ends tomorrow."
- **Day 14**: Final email: "Your trial has ended — add a payment method to keep Pro features."

Conversion takes less than 2 minutes: **Settings → Billing → Add Payment Method → Select Plan → Confirm**. All data and settings are preserved through the transition.

If you do not convert, the workspace moves to the Free plan. Projects beyond the 3-project limit and users beyond the 5-user limit become read-only. No data is deleted — you can upgrade at any time to restore full access.

---

## Setup Wizard

When a new workspace is created, NovaDash launches a **Setup Wizard** — a guided 4-step process to get your workspace configured in minutes.

### Step 1: Name Your Workspace

Enter a workspace name (e.g., "Acme Engineering Team" or "Alice's Freelance Studio"). This name appears in all notification emails, in the browser tab, and in your workspace URL: `app.novadash.io/your-workspace-name`.

You can also upload a workspace logo and choose a brand color for emails and the sidebar.

### Step 2: Invite Your Team

Enter the email addresses of team members to invite. Assign each a role (Admin, Member, or Viewer). Invites are optional — you can skip this step and invite users later from **Settings → Users**.

**Tip:** Invite at least one other Admin during setup so you have a backup workspace owner in case you lose access.

### Step 3: Create Your First Project

The wizard prompts you to create your first project:
1. Enter a project name.
2. Choose a template: Software, Marketing, HR, or Custom (blank).
3. Select visibility: Private, Team, or Public.

The project is created immediately. If you chose a template, sample task lists and example tasks are created to show you the workflow.

### Step 4: Create Your First Task

A quick-add prompt for your first task:
1. Enter a task title.
2. Assign it to yourself or an invited team member.
3. Set a due date (optional).
4. Click **Create Task**.

After this step, the wizard closes and you land in your first project's task view with a **"Getting Started" checklist** in the sidebar.

---

## Team Onboarding Checklist

After completing the setup wizard, use this checklist to fully prepare your workspace for the whole team:

### Admin Tasks (Owner/Admin)

- [ ] Configure SSO if your organization uses Okta, Google Workspace, or Azure AD (**Settings → Security → Identity Provider Binding**)
- [ ] Set up 2FA enforcement (**Settings → Security → Require 2FA**)
- [ ] Connect Slack integration (**Settings → Integrations → Slack**)
- [ ] Connect GitHub integration if you have engineering projects (**Settings → Integrations → GitHub**)
- [ ] Create project templates for your team's common workflows (**Projects → New Template**)
- [ ] Set up billing (**Settings → Billing → Add Payment Method**) to avoid trial disruption
- [ ] Review and configure workspace notification defaults (**Settings → Notifications**)
- [ ] Import existing data from Asana, Jira, or Trello (see Data Import below)

### All Team Members

- [ ] Update your profile (avatar, timezone, notification preferences) at **Profile → Edit Profile**
- [ ] Enable 2FA at **Profile → Security → Enable 2FA**
- [ ] Connect your personal Slack account for DM notifications at **Profile → Notifications → Connect Slack**
- [ ] Review your notification settings and configure digest mode if preferred
- [ ] Join the projects relevant to your work (**Projects → Browse Projects**)

---

## Admin Quick-Start Guide

For admins taking ownership of a new NovaDash workspace, here is a concise order of operations:

1. **Security first**: Configure SSO and enforce 2FA before inviting the full team.
2. **Structure second**: Create the core projects and templates before inviting members — this way new users land in an organized workspace.
3. **Invite in waves**: Start with team leads (Admins), let them validate the setup, then invite the broader team.
4. **Billing third**: Set up billing on Day 10 of the trial — don't wait for Day 13.
5. **Integrations last**: Connect Slack, GitHub, and other integrations after the core structure is stable.

The **Admin Dashboard** (**Settings → Overview**) shows a health scorecard: security settings configured, billing status, active users, and integration status. Use this as a quick-check during setup.

---

## Data Import: From Asana, Jira, and Trello

If your team is migrating from another project management tool, NovaDash can import your existing data.

### Supported Import Sources

| Source    | Import Method            | What Imports                                              |
|-----------|--------------------------|-----------------------------------------------------------|
| Asana     | OAuth connection or CSV  | Projects, tasks, subtasks, assignees, due dates, comments |
| Jira      | CSV export from Jira     | Issues (as tasks), epics (as projects), comments, priority |
| Trello    | Trello JSON export       | Boards (as projects), cards (as tasks), checklists (as subtasks), labels |
| Generic   | NovaDash CSV format      | Tasks with standard fields                                |

### CSV Import Format

For tools not directly supported, use NovaDash's generic CSV import format:

```
title,description,status,priority,assignee_email,due_date,project_name,labels
"Fix login bug","Users report 401 on refresh","Todo","High","alice@example.com","2024-12-01","Web App","bug,auth"
```

### Import Steps

1. Go to **Settings → Data → Import**.
2. Select your source tool.
3. Upload the file or authorize the OAuth connection.
4. NovaDash shows a **mapping preview** — verify that fields from your old tool map correctly to NovaDash fields.
5. Fix any unmapped fields or errors.
6. Click **Start Import**.
7. A progress bar shows import status. For large imports (1,000+ tasks), you receive an email when complete.

### After Import

- Imported tasks are marked with an "[Imported]" label for easy identification.
- Assignees are matched by email address. If an imported assignee's email doesn't match a NovaDash user, the task is created unassigned with the original assignee name in the description.
- Imports are not reversible — test with a small batch first by importing one project before doing a full workspace import.
