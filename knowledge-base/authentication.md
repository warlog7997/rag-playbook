# NovaDash Authentication

NovaDash uses a secure, token-based authentication system to protect your workspace and team data. This document covers every aspect of authentication, from the initial login to advanced enterprise SSO configurations.

---

## Login Flow

NovaDash supports standard email and password authentication. When a user submits their credentials at `app.novadash.io/login`, the following sequence occurs:

1. The client sends a `POST /auth/login` request with `{ email, password }`.
2. The server validates credentials against the hashed password store.
3. On success, the server returns a **session token** — a signed JWT with a 30-day expiry.
4. The client stores this token in a secure, HTTP-only cookie.
5. All subsequent API requests must include `Authorization: Bearer <session_token>`.

The session token contains the user's `user_id`, `workspace_id`, role claims, and an `exp` (expiry) field. It is signed with the workspace's private key and cannot be tampered with.

Failed logins do not return detailed error messages. Whether the email doesn't exist or the password is wrong, the server always returns a generic "Invalid credentials" message — this prevents email enumeration attacks.

---

## SSO Setup — Identity Provider Binding

For teams that use a central identity provider (IdP), NovaDash supports SAML 2.0-based Single Sign-On. Internally, this process is called **identity provider binding** — the act of linking NovaDash's service provider metadata to an external IdP.

### Supported Providers

- **Okta**: Use the NovaDash app from the Okta Integration Network. Configure attribute mapping for `email`, `given_name`, `family_name`.
- **Google Workspace**: Configure a SAML custom app in your Google Admin console. NovaDash's ACS URL is `https://app.novadash.io/auth/saml/callback`.
- **Azure Active Directory**: Use the "Enterprise Applications" section and configure SAML-based sign-on.
- **Generic SAML 2.0**: Any SAML 2.0-compliant IdP is supported.

### Configuration Steps

1. In NovaDash, go to **Settings → Security → Identity Provider Binding**.
2. Click **Add Identity Provider**.
3. Select your provider type (Okta, Google, Azure, Generic SAML).
4. Download the NovaDash **Service Provider (SP) metadata XML** — upload this to your IdP.
5. Paste the **IdP metadata XML** (or the IdP metadata URL) into NovaDash.
6. Configure attribute mappings: the `email` attribute is required. `first_name` and `last_name` are optional but recommended.
7. Enable **Just-in-Time (JIT) provisioning** if you want users to be auto-created on first SSO login.
8. Click **Test Connection** — NovaDash will attempt an auth flow and show you the attributes received.
9. Once validated, click **Enable** to make SSO the primary login method.

### SSO Enforcement

In the Security settings, admins can enable **SSO Enforcement**, which disables email/password login for all non-owner users. Owners always retain email/password access as a fallback to prevent lockout.

---

## Two-Factor Authentication

Two-factor authentication (2FA) adds a second layer of security on top of email/password login. NovaDash supports two 2FA methods:

### TOTP (Time-Based One-Time Password)

The recommended method. Compatible with Google Authenticator, Authy, 1Password, and any RFC 6238-compliant app.

**Setup:**
1. Go to **Profile → Security → Enable 2FA**.
2. Scan the displayed QR code with your authenticator app.
3. Enter the 6-digit code from the app to verify setup.
4. Download and store your **backup codes** (10 single-use codes for account recovery).

Once enabled, every new login session will require a TOTP code after the password step.

### SMS Fallback

If TOTP is unavailable, users can request a 6-digit code via SMS. NovaDash sends codes using a 10-minute expiry window. SMS codes can only be used if the user has a verified phone number on their profile.

**Note for Admins:** Admins can enforce 2FA for all workspace members via **Settings → Security → Require 2FA**. Users who haven't enabled 2FA will be prompted on every login until they comply.

---

## Account Recovery via Email Verification Token Flow

When users can no longer access their account due to a forgotten credential, NovaDash initiates the **account recovery via email verification token flow**. This is a multi-step process designed to verify identity before allowing credential updates.

**Steps:**
1. Navigate to `app.novadash.io/recover`.
2. Enter the email address associated with the account.
3. NovaDash generates a **time-limited recovery token** (valid for 2 hours) and emails a recovery link.
4. The user clicks the link, which verifies the token's validity and ownership.
5. The user is prompted to set a new password and re-confirm it.
6. All active sessions are immediately invalidated upon successful recovery.
7. A notification email is sent to the account's email address confirming the credential change.

**Security Notes:**
- Recovery tokens are single-use — they expire immediately upon use.
- If no email is received within 5 minutes, check spam or contact support.
- If you no longer have access to the account's email address, contact Enterprise support for manual identity verification.

---

## API Key Generation and Rotation

For programmatic access, NovaDash supports long-lived **API keys** in addition to session tokens.

### Generating an API Key

1. Go to **Profile → API Keys → New API Key**.
2. Give the key a descriptive name (e.g., "CI Pipeline", "Zapier Integration").
3. Select a permission scope: `read`, `write`, or `admin`.
4. Copy the key immediately — it is shown only once.

API keys do not expire by default but can be given a custom expiry date. They are stored as hashed values — NovaDash cannot retrieve them after creation.

### Key Rotation

For security, rotate API keys regularly:
1. Go to **Profile → API Keys**.
2. Click **Rotate** next to an existing key.
3. A new key value is generated immediately, and the old key continues to work for a 24-hour grace period.
4. Update your integration with the new key before the grace period expires.

### Revoking Keys

To revoke a key immediately (e.g., on suspected compromise), click **Revoke**. The key is invalidated instantly with no grace period.

---

## Session Expiry and Management

NovaDash sessions have a **30-day default expiry**. Workspace admins can configure this in **Settings → Security → Session Duration** to any value between 1 hour and 90 days.

Sessions expire on:
- The configured time limit
- Manual logout (DELETE `/auth/session`)
- Account recovery completion (all sessions invalidated)
- Admin-forced session termination (Settings → Users → Force Logout)

Users can view all active sessions at **Profile → Security → Active Sessions**, including device type, IP address, and last-used timestamp.

---

## Failed Login Lockout

To prevent brute-force attacks, NovaDash implements automatic account lockout:

- **After 5 consecutive failed login attempts**, the account is locked for **15 minutes**.
- During the lockout period, all login attempts (even with correct credentials) are rejected.
- After 15 minutes, the lockout resets automatically.
- Admins can manually unlock accounts immediately via **Settings → Users → [User] → Unlock Account**.
- A notification email is sent to the account owner when a lockout occurs.

The lockout counter resets on a successful login. It is per-account and per-IP — both must clear for access to be restored.
