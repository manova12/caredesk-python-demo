# SMTP email setup

The hosted Python app can send a booking confirmation immediately after a new appointment is saved. SMTP credentials are read from Streamlit Community Cloud Secrets and are never written to the repository. The confirmation contains only the service, doctor, date, time, and confirmation code; it does not include the patient's reported concern.

## Configure the sender

Open **Manage app → Settings → Secrets** and add an `[smtp]` section. Choose one authentication method.

### SMTP password or app password

```toml
[smtp]
send_enabled = false
host = "smtp.gmail.com"
port = 587
use_ssl = false
username = "your-sender@gmail.com"
from_email = "your-sender@gmail.com"
auth_method = "password"
password = "REPLACE_WITH_SMTP_OR_APP_PASSWORD"
```

Use a provider-issued SMTP password. For Gmail, this normally means an App Password; a regular Google account password will not work. If Google does not offer App Passwords for this account, use the OAuth2 option or an SMTP provider that issues SMTP credentials.

### Gmail SMTP OAuth2

```toml
[smtp]
send_enabled = false
host = "smtp.gmail.com"
port = 587
use_ssl = false
username = "your-sender@gmail.com"
from_email = "your-sender@gmail.com"
auth_method = "oauth2"
client_id = "YOUR_GOOGLE_OAUTH_CLIENT_ID"
client_secret = "YOUR_GOOGLE_OAUTH_CLIENT_SECRET"
refresh_token = "REFRESH_TOKEN_GRANTED_FOR_GMAIL_SMTP"
```

The refresh token must come from an OAuth authorization that grants `https://mail.google.com/` to the same sender address. The normal Streamlit Google sign-in only identifies clinic staff; it does not grant Gmail sending permission. Gmail SMTP OAuth uses XOAUTH2 and the full Gmail mail scope, so approve that access only for an account the clinic controls. [Google's SMTP documentation](https://developers.google.com/workspace/gmail/imap/xoauth2-protocol) describes the required scope and XOAUTH2 exchange.

## Verify and enable

1. Save the Secrets. Keep them out of GitHub, screenshots, and chat.
2. Leave `send_enabled = false` while setting up the sender.
3. Sign in to the clinic portal and choose **Verify SMTP connection**. This checks SMTP authentication and sends no email.
4. Once the clinic approves live confirmations, change `send_enabled` to `true` and save.
5. Make a new booking using an email address you control to check inbox and spam. Historical simulated queue entries are not resent.

## Important behavior

- Only new booking confirmations are sent by SMTP. The booking is saved even if delivery fails; the clinic page records the delivery result.
- Confirmation is sent to the address typed by the person booking. The email is limited to appointment logistics and the confirmation code.
- The reminders checkbox records consent, but this Streamlit deployment has no reliable background scheduler. Reminder emails remain previews and will not be sent automatically.
- SMTP acceptance does not prove the message reached the recipient's inbox.
- Streamlit Community Cloud local files are not durable. The current app's SQLite database and any token files must not be treated as production-persistent storage.
