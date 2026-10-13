# NovaDash Tasks

Tasks are the core unit of work in NovaDash. Every piece of work — from a one-hour bug fix to a multi-week feature — lives as a task inside a project. This guide covers everything from creating your first task to advanced automation with recurring tasks and bulk operations.

---

## Task Creation

To create a task, click **+ Add Task** in any project view, or press `T` anywhere in a project to open the quick-add bar.

### Required Fields

- **Title**: A short, descriptive name for the task. Max 255 characters.

### Optional Fields

- **Description**: Full-text description supporting Markdown. Use it for requirements, acceptance criteria, context, or reproduction steps. Supports code blocks, tables, and embedded images.
- **Assignee**: The team member responsible for completing the task. Only project members can be assigned.
- **Due Date**: The date (and optionally time) by which the task must be completed. Used for calendar views, reminders, and burndown charts.
- **Priority**: How urgent/important the task is. See Priority Levels below.
- **Status**: Initial status (defaults to `Todo`).
- **Labels**: Free-form tags for filtering (e.g., "bug", "frontend", "Q2").
- **Estimate**: Story points or hours, for capacity planning.
- **Attachments**: Files, images, or links attached directly to the task.

### Priority Levels

NovaDash uses four priority levels:

| Priority | Color  | Meaning                                                        |
|----------|--------|----------------------------------------------------------------|
| Urgent   | Red    | Blocking other work or has a critical deadline. Needs immediate attention. |
| High     | Orange | Important but not blocking. Should be completed this sprint.   |
| Medium   | Yellow | Normal priority. Default for most tasks.                       |
| Low      | Blue   | Nice to have. Complete when higher-priority work is clear.     |

---

## Task Status Workflow

Every task moves through a defined status lifecycle. The default workflow is:

```
Todo → In Progress → In Review → Done → Archived
```

### Status Descriptions

- **Todo**: The task is ready to start but no one has picked it up yet.
- **In Progress**: Actively being worked on. The task should have an assignee.
- **In Review**: Work is complete and awaiting review or approval (code review, QA, stakeholder sign-off).
- **Done**: The task is fully complete and accepted.
- **Archived**: The task is closed and no longer shown in active views. Archived tasks are still searchable and accessible in history.

### Custom Workflows (Pro/Enterprise)

Pro and Enterprise workspaces can define custom status columns per project. For example:
- `Backlog → Spec → Development → Staging → Released`
- `Idea → Approved → Assigned → In Progress → QA → Live`

Custom statuses can be named, colored, and ordered. Each status maps to one of three categories: `not_started`, `in_progress`, or `done`.

---

## Subtasks

Subtasks allow complex tasks to be broken into smaller, trackable pieces.

- Subtasks support up to **3 levels of nesting** (task → subtask → sub-subtask).
- Each subtask has the same fields as a parent task (title, assignee, due date, priority, status).
- Subtask completion does NOT automatically complete the parent — the parent must be manually moved to Done.
- The parent task shows a completion counter: "3 of 5 subtasks done."
- Subtasks can be independently assigned to different team members.

**To create a subtask:** Open a task, click **Add Subtask** in the task detail panel.

---

## Task Dependencies

NovaDash supports task dependency relationships to model real-world blocking constraints.

### Dependency Types

- **Blocks**: Task A blocks Task B — Task B cannot logically begin until Task A is done.
- **Blocked By**: Task B is blocked by Task A — the mirror of "blocks."

### Setting Dependencies

1. Open a task.
2. In the **Dependencies** section, click **Add Dependency**.
3. Search for the blocking or blocked-by task.
4. Select the relationship type.

### Dependency Visualization

In the **Timeline / Gantt view**, tasks with dependencies are connected by arrows. Blocked tasks are highlighted when their blocking task is overdue. NovaDash does NOT automatically prevent moving a blocked task to "In Progress" — this is intentional to accommodate flexible workflows.

---

## Recurring Tasks

For work that repeats on a schedule, NovaDash supports recurring tasks that auto-generate new instances.

### Recurrence Options

- **Daily**: A new task instance is created every day.
- **Weekly**: Created every N weeks on specified day(s) of the week.
- **Monthly**: Created on a specific date each month (e.g., the 1st) or a relative date (e.g., last Friday).
- **Custom Cron**: Advanced users can define any schedule using cron syntax (e.g., `0 9 * * 1-5` for every weekday at 9 AM).

### How Recurring Tasks Work

When a recurring task is marked **Done** or **Archived**, the next instance is automatically created with:
- The same title, description, assignee, priority, and labels.
- A new due date calculated from the recurrence rule.
- Fresh status: `Todo`.
- A link back to the previous instance in the task history.

To stop recurrence, open the task and click **Stop Recurring** — this completes the current instance and no new instance is created.

---

## Bulk Operations

For managing large numbers of tasks at once, NovaDash supports bulk operations via multi-select.

### How to Multi-Select

- In list view, click the checkbox on the left of each task.
- Or use `Shift+Click` to select a range of consecutive tasks.
- Or use `Ctrl+A` (Windows) / `Cmd+A` (Mac) to select all visible tasks.

### Available Bulk Operations

- **Assign**: Set the assignee for all selected tasks.
- **Change Status**: Move all selected tasks to a new status.
- **Set Priority**: Update priority for all selected tasks.
- **Move to Project**: Transfer selected tasks to a different project (must be a member of the destination project).
- **Set Due Date**: Assign the same due date to all selected tasks, or shift all due dates by N days.
- **Add/Remove Labels**: Apply or remove labels in bulk.
- **Archive**: Archive all selected tasks.
- **Delete**: Soft-delete all selected tasks (30-day recovery window).

Bulk operations are logged in the project's Activity Feed with the user who performed them and the number of tasks affected.

---

## Task Search and Filtering

### Search

Use the global search bar (`Ctrl+K` / `Cmd+K`) to search across all projects and tasks. The search engine indexes task titles, descriptions, comments, and attachment names.

**Operators:**
- `assignee:alice` — tasks assigned to Alice
- `status:in-progress` — tasks with a specific status
- `priority:urgent` — filter by priority
- `project:"Alpha"` — search within a specific project
- `due:today`, `due:overdue`, `due:this-week`

### Saved Filters

Frequently used filter combinations can be saved as **Saved Filters** and shared with the team. They appear in the project's left sidebar.

### Filter Panel

In any project view, click **Filter** to open the filter panel. Combine multiple filter conditions:

- **Assignee**: one or more users
- **Status**: one or more statuses
- **Priority**: any combination
- **Label**: any label tags
- **Due Date**: date ranges or relative dates
- **Created Date**: when the task was created
- **Custom Fields**: filter by any custom field value

Filters can be combined with AND (all conditions must match) or OR (any condition matches) logic, configurable in the filter panel.
