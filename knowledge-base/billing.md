# NovaDash Billing and Subscriptions

NovaDash offers flexible pricing plans to suit teams of every size. This document covers all aspects of billing — from choosing a plan to understanding what happens when a subscription ends.

---

## Plans

NovaDash offers three pricing tiers:

### Free Plan

- **Price:** Free forever
- **Users:** Up to 5 team members
- **Projects:** Up to 3 active projects
- **Storage:** 1 GB
- **Integrations:** Slack and GitHub (read-only)
- **Support:** Community forum only
- **API Rate Limit:** 1,000 requests/hour

The Free plan is ideal for small teams or individuals evaluating NovaDash. No credit card is required to sign up.

### Pro Plan

- **Price:** $12 per user per month (billed monthly) or $9 per user per month (billed annually)
- **Users:** Unlimited
- **Projects:** Unlimited active projects
- **Storage:** 100 GB per workspace
- **Integrations:** All integrations (Slack, GitHub, Zapier, Webhooks, SSO)
- **Support:** Email and in-app chat, 24-hour response SLA
- **API Rate Limit:** 5,000 requests/hour
- **Extras:** Audit log (1 year), custom fields, priority support queue

The Pro plan is the most popular choice for growing teams. Billing is per active seat — deactivated users do not count toward the bill.

### Enterprise Plan

- **Price:** Custom — contact sales at enterprise@novadash.io
- **Users:** Unlimited
- **Projects:** Unlimited
- **Storage:** Custom (starting at 1 TB)
- **Integrations:** All Pro integrations plus SAML SSO, SCIM provisioning, custom webhooks
- **Support:** Dedicated account manager, 4-hour SLA, custom SLAs available
- **API Rate Limit:** Custom (negotiated)
- **Extras:** Unlimited audit log retention, SIEM streaming, SLA guarantees, on-premise option, custom contracts, invoice billing, ACH payment

Enterprise contracts are annual minimum. Custom pricing is based on seat count, usage, and required SLAs.

---

## Subscription Lifecycle

A NovaDash subscription moves through the following states:

### `trial`
All new workspaces start on a **14-day free trial** of the Pro plan. No credit card is required to start. Full Pro features are available immediately. At day 10, day 13, and day 14, NovaDash sends conversion prompts.

### `active`
A paid subscription is active when a valid payment method is on file and the last payment succeeded. All features of the subscribed plan are available without restriction.

### `past_due`
If a scheduled payment fails, the subscription enters `past_due` state. NovaDash retries the charge **3 times over 7 days** (Day 1, Day 3, Day 7). During `past_due`, all workspace features remain available — NovaDash does not immediately restrict access.

### `suspended`
If all 3 retry attempts fail, the subscription is suspended. Access to the workspace is read-only — users can view data but cannot create or edit tasks, projects, or invite users. The workspace owner receives a suspension notice with a link to update the payment method.

### `cancelled`
When a workspace owner initiates a voluntary subscription termination (see below), the subscription transitions to `cancelled` at the end of the current billing period. During the remaining period, full access continues.

### `terminated`
After the billing period ends on a cancelled subscription, or after 30 days of suspension with no payment, the subscription is `terminated`. Data is retained for 90 days post-termination before permanent deletion. The workspace owner can reactivate within 90 days by adding a payment method.

---

## Upgrading

To upgrade from Free to Pro, or from monthly to annual billing:

1. Go to **Settings → Billing → Change Plan**.
2. Select the new plan.
3. Confirm the payment method.
4. Click **Upgrade Now**.

**Prorated Billing:** Upgrades take effect immediately. NovaDash calculates the remaining days in the current billing period and applies a prorated credit for unused Free time. The first invoice will reflect the prorated amount.

**Immediate Access:** All Pro features are unlocked the moment the upgrade is confirmed — no waiting for the next billing cycle.

**Adding Seats:** When new users are invited to a Pro workspace, they are billed immediately on a prorated basis for the remaining days in the current billing period.

---

## Downgrading

To downgrade from Pro to Free:

1. Go to **Settings → Billing → Change Plan**.
2. Select **Free Plan**.
3. Review the feature comparison — features not available on Free will be disabled at cycle end.
4. Confirm the downgrade.

**Effective Date:** Downgrades take effect at the **end of the current billing cycle** — you retain Pro access until then.

**Data Retention After Downgrade:** If your workspace exceeds Free plan limits (>5 users, >3 projects), NovaDash will prompt you to reduce before the downgrade takes effect. Data is retained for **90 days** — archived projects and deactivated users can be reactivated if you upgrade back to Pro within 90 days.

---

## Subscription Termination with Data Retention Policy

When a workspace owner decides to permanently end their NovaDash subscription, the process is called **subscription termination with data retention policy**. This is distinct from a simple cancellation — it initiates a formal data lifecycle.

### Termination Steps

1. Navigate to **Settings → Billing → Terminate Subscription**.
2. Read and confirm the **Data Retention Notice**: all workspace data is retained for **90 days** after termination.
3. Optionally, download a full workspace export (JSON/CSV) before terminating.
4. Enter the workspace name to confirm.
5. Click **Terminate**.

### What Happens After Termination

- **Day 0**: Subscription marked `cancelled`. Access continues until end of billing period.
- **End of Period**: Subscription becomes `terminated`. Workspace is read-only for 90 days.
- **Day 90**: All workspace data is permanently and irreversibly deleted: tasks, projects, files, comments, audit logs, and user data.
- **Day 91+**: No recovery is possible.

NovaDash sends reminder emails at Day 60, Day 80, Day 88, and Day 89 of the retention window.

### Reactivation During Retention Window

Within the 90-day retention window, the workspace owner can reactivate by subscribing to any paid plan. All data is restored immediately.

---

## Payment Methods

### Credit Card

Visa, Mastercard, and American Express are accepted. Cards are processed via Stripe. NovaDash does not store raw card numbers — only Stripe payment method tokens.

### ACH (US Bank Transfer)

Available on Pro and Enterprise plans for US-based customers. ACH payments have a 5-business-day processing time. ACH payments must be verified with micro-deposits before the first charge.

### Invoice (Enterprise Only)

Enterprise customers can receive a monthly or annual invoice paid via wire transfer or check. Net-30 payment terms by default; Net-60 available on request. Invoices are sent to the billing contact email on file.

---

## Failed Payments and Retry Logic

When a payment fails (insufficient funds, expired card, bank decline):

1. **Day 1**: First retry attempt. If it fails, an email is sent to the workspace owner with a link to update the payment method.
2. **Day 3**: Second retry attempt.
3. **Day 7**: Third and final retry attempt.
4. **After Day 7**: If all retries fail, the subscription enters `suspended` state (read-only access).

To resolve: go to **Settings → Billing → Payment Method → Update** and add a valid payment method. The outstanding charge will be attempted immediately upon update.

---

## Refund Policy

- **Annual Plans**: NovaDash offers a **14-day money-back guarantee** on annual subscriptions. If you are not satisfied within the first 14 days of an annual plan, contact support for a full refund.
- **Monthly Plans**: No automatic refunds. Unused portions of a monthly billing cycle are not refunded upon cancellation, but access continues until the period ends.
- **Enterprise**: Refund terms are negotiated in the contract.

To request a refund, contact billing@novadash.io with your workspace name and order ID.
