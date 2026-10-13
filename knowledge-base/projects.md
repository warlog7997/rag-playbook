# NovaDash Projects

Projects are the top-level organizational unit in NovaDash. Each project contains tasks, members, files, and its own settings. This guide covers creating and managing projects from initial setup through archiving and deletion.

---

## Project Creation

To create a new project, click **+ New Project** in the left sidebar or go to **Projects → New Project**.

### Required Fields

- **Project Name**: The display name of the project. Must be unique within the workspace. Max 100 characters.
- **Visibility**: Controls who can see and access the project (see below).

### Optional Fields

- **Description**: A markdown-supported project summary shown on the project dashboard. Supports links, lists, and basic formatting.
- **Template**: Start from a pre-built template to auto-create task lists and workflows.
- **Color/Icon**: Choose a color and icon for the project — displayed in the sidebar and dashboards.
- **Start Date / Target Date**: Defines the project timeline for burndown charts.
- **Project Lead**: Designate a responsible owner from the project's members.

---

## Project Visibility

Every project has a visibility setting that controls who can access it:

### Private

Only explicitly added members can see the project. It does not appear in workspace search or the Projects directory for non-members. Best for confidential or sensitive work.

### Team

All workspace members can see the project exists and view its basic details, but only added members can edit tasks and access full content. Members can request to join. Ideal for most internal team projects.

### Public

Anyone with the workspace link can view the project and its tasks. Tasks are read-only for non-members. Public projects appear in the workspace's public portfolio (if enabled by the admin). Best for open-source or client-facing work.

---

## Project Templates

Templates pre-populate your project with a standard set of task lists, statuses, and example tasks to help teams get started faster.

### Built-In Templates

**Software Development:**
- Lists: Backlog, Sprint 1, In Progress, Code Review, Done
- Includes sample tasks for planning, development, testing, and deployment
- Pre-configured task priorities and custom fields (Story Points, PR Link)

**Marketing Campaign:**
- Lists: Ideas, Planned, In Production, Review, Published
- Sample tasks for content calendar, asset creation, and distribution
- Custom fields: Channel, Budget, Target Audience

**HR and Onboarding:**
- Lists: Offer Sent, Pre-Start, Week 1, Week 2, Month 1, Completed
- Sample onboarding checklist tasks
- Custom fields: Department, Buddy, Start Date

**Custom Template:**
- Start from scratch with a blank project and define your own lists and workflow.

### Saving Custom Templates

Pro and Enterprise users can save any project as a custom template:
1. Open the project.
2. Go to **Project Settings → Save as Template**.
3. Name the template.
4. The template appears in the template picker for all workspace members.

---

## Project Settings

Each project has its own settings panel, accessible at **Project → Settings** (visible to project Admins and workspace Admins/Owners).

### General Settings

- Rename the project, update description, change color/icon.
- Update visibility level.
- Set or change the Project Lead.

### Archiving a Project

Archiving freezes a project in its current state. Archived projects:
- Are hidden from the main project list (toggle "Show Archived" to view them).
- Cannot have new tasks created.
- Remain fully searchable.
- Do not count against plan limits.
- Can be unarchived at any time.

To archive: **Project Settings → Archive Project → Confirm**.

### Duplicating a Project

Create a full copy of a project, including all task lists and task names (but not content, assignments, or dates — these are reset). Useful for repeating projects or creating a new sprint baseline.

1. **Project Settings → Duplicate Project**.
2. Name the duplicate.
3. Choose whether to copy tasks with content, assignments, and due dates (optional).
4. Click **Duplicate**.

### Deleting a Project

Project deletion is a **soft delete** — the project is immediately hidden and marked as deleted, but all data is retained for **30 days** in a recoverable state.

- **Recovery Window:** Within 30 days, any Admin can recover the project at **Settings → Deleted Projects → Restore**.
- **Permanent Deletion:** After 30 days, all project data (tasks, comments, files) is permanently deleted.

To delete: **Project Settings → Delete Project → Type the project name to confirm → Delete**.

---

## Project Members

Projects have their own member list, separate from workspace membership.

### Adding Members to a Project

1. Go to **Project → Members → Add Members**.
2. Search for workspace users by name or email.
3. Assign a project-level role: **Project Admin**, **Editor**, or **Viewer**.
4. Click **Add**.

**Project Roles Override Workspace Roles:**
- A workspace Member can be a Project Admin for a specific project.
- A workspace Admin who is not added to a private project cannot see it.

### Project-Level Roles

| Permission              | Project Admin | Editor | Viewer |
|------------------------|---------------|--------|--------|
| Manage project settings | ✓             | ✗      | ✗      |
| Add/remove members      | ✓             | ✗      | ✗      |
| Create/delete tasks     | ✓             | ✓      | ✗      |
| Edit task details       | ✓             | ✓      | ✗      |
| Comment on tasks        | ✓             | ✓      | ✓      |
| View tasks and files    | ✓             | ✓      | ✓      |

---

## Project Limits by Plan

| Limit                  | Free Plan       | Pro Plan    | Enterprise |
|-----------------------|-----------------|-------------|------------|
| Active projects        | 3               | Unlimited   | Unlimited  |
| Archived projects      | Unlimited       | Unlimited   | Unlimited  |
| Members per project    | 5               | Unlimited   | Unlimited  |
| Custom templates       | 0               | Unlimited   | Unlimited  |
| File storage per project | 200 MB        | 10 GB       | Custom     |

Free plan workspaces that reach their 3-project limit cannot create new projects. To create more, either archive an existing project or upgrade to Pro.

---

## Project Dashboards

Each project has a built-in dashboard providing real-time visibility into project health.

### Progress Overview

- **Completion Rate**: Tasks completed / total tasks, shown as a percentage and donut chart.
- **Tasks by Status**: Breakdown of tasks across all status columns.
- **Tasks by Assignee**: Work distribution across team members.
- **Overdue Tasks**: Tasks with past due dates that are not yet done.

### Burndown Chart

The burndown chart tracks remaining work over time against the project's target date. Tasks are counted by number (or optionally by Story Points if the custom field is enabled). A healthy burndown shows a steadily decreasing line trending toward zero at the target date.

### Activity Feed

The activity feed shows a real-time log of all project actions:
- Task created, updated, completed
- Comments and @mentions
- Member added or removed
- Status and priority changes

The activity feed can be filtered by event type and date range. For large, high-activity projects, the feed can be disabled in project settings to improve dashboard load performance (see Troubleshooting).
