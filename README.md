# CareDesk Python / Streamlit build

This is a separate Python rebuild. It does not modify the existing Node.js app or import its local patient data, workbook, staff account, Gmail token, or message queue. It starts with an empty SQLite database under `data/`.

## Current scope

- Patient booking with service, doctor, day, and 30-minute slot validation.
- Unique booking slots and confirmation codes.
- Appointment lookup by email and confirmation code.
- Reminder opt-in capture and a persistent local message-preview queue.
- Clinic workspace gated by Google OIDC and an administrator email allowlist.

The first Python build queues email previews only. It does not send SMTP mail, import records, or send reminders. The existing Node implementation remains the source of truth until the Python version is completed and deliberately migrated.

## Run locally

Requires Python 3.12+.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

Local bookings are stored in `data/caredesk.sqlite3`.

## Hosting note

Streamlit Community Cloud deploys Python apps, but this local SQLite file is not a durable hosted database. Before public use, configure an external persistent database and add the Google OIDC and Gmail OAuth settings as deployment secrets. The clinic workspace is hidden unless `staff_emails` and `[auth]` / `[auth.google]` are configured. Do not commit secrets or real patient information.

This is a synthetic-data demo, not approved for live clinical use. Doctor availability must be verified by the clinic, and live email requires sender authorization, consent, and operational review.
