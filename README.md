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

Streamlit Community Cloud deploys Python apps, but this local SQLite file is not a durable hosted database. The hosted clinic workspace uses Google OIDC and an email allowlist.

Follow [STREAMLIT_OIDC_SETUP.md](STREAMLIT_OIDC_SETUP.md) to configure Google staff sign-in and the email allowlist.

The hosted app starts with a separate SQLite database. On Streamlit Community Cloud, that file is not durable across all restarts/redeploys, so configure an external persistent database before relying on saved bookings. Do not commit real patient information.

This is a synthetic-data demo, not approved for live clinical use. Doctor availability must be verified by the clinic, and live email requires sender authorization, consent, and operational review.
