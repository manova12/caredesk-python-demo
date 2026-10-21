# Google staff sign-in setup

Configure this in Streamlit Community Cloud for the deployed CareDesk app. This is separate from Gmail SMTP authorization.

## Google OAuth client

In Google Cloud Console, create or select an OAuth client with application type **Web application**. Add this authorized redirect URI exactly:

```text
https://caredesk-python-demo-9daqbaanc8qyk7qrs9cjfy.streamlit.app/oauth2callback
```

Copy the OAuth client ID and client secret from that Google client. Keep them private.

## Streamlit app secrets

Open the app's **Manage app → Settings → Secrets** page in Streamlit Community Cloud. Add this configuration, replacing the three placeholder values and the staff email with the real values:

```toml
staff_emails = ["staff@example.com"]

[auth]
redirect_uri = "https://caredesk-python-demo-9daqbaanc8qyk7qrs9cjfy.streamlit.app/oauth2callback"
cookie_secret = "REPLACE_WITH_A_LONG_RANDOM_SECRET"

[auth.google]
client_id = "REPLACE_WITH_GOOGLE_OAUTH_CLIENT_ID"
client_secret = "REPLACE_WITH_GOOGLE_OAUTH_CLIENT_SECRET"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

Set `staff_emails` to only the Google account(s) authorized to open the clinic workspace. Generate a unique, long `cookie_secret` privately (for example, with a password manager). Do not commit completed secrets to GitHub or send them in chat. The repository ignores `.streamlit/secrets.toml`.

After saving secrets, verify that an allowlisted account can sign in and that a different Google account is denied. If Google OAuth is in **Testing** mode, each staff account must also be listed as a test user in Google Auth Platform. The app uses Google identity for staff access only; this does not connect Gmail sending.

## Optional clinic user ID and password

The clinic page can also use one administrator-configured user ID and password. In **Manage app → Settings → Secrets**, add:

```toml
[clinic_login]
username = "clinicadmin"
password = "REPLACE_WITH_A_LONG_UNIQUE_PASSWORD"
```

Replace the example password with a long, unique password before saving. Keep it only in Streamlit Secrets or a password manager; do not commit it to GitHub or send it in chat. The password form appears after the app restarts. Google sign-in remains available as a separate method when Google OIDC is configured. This is one shared login, so it does not provide individual staff identities or an audit trail; use individual Google accounts for real clinic operations.

## Scope note

This only enables sign-in and allowlist-based authorization for the clinic page. It does not migrate local patient records or make the hosted SQLite database durable. The current hosted app remains a synthetic-data demonstration until storage, privacy, and clinic operational requirements are separately addressed.
