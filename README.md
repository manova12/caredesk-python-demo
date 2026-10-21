# CareDesk Python / Streamlit build

This is a separate Python rebuild. It does not modify the existing Node.js app or import its local patient data, workbook, staff account, Gmail token, or message queue. It starts with an empty SQLite database under `data/`.

## Current scope

- Patient booking with service, doctor, day, and 30-minute slot validation.
- Unique booking slots and confirmation codes.
- Appointment lookup by email and confirmation code.
- A clinic-team patient list seeded from the supplied 200-row synthetic demo import file.
- Reminder opt-in capture and a persistent local message-preview queue.
- Clinic workspace gated by Google OIDC and an administrator email allowlist.

The first Python build queues email previews only. It does not send SMTP mail or reminders. The existing Node implementation remains the source of truth until the Python version is completed and deliberately migrated.

The clinic workspace imports `data_seed/patients_for_caredesk_import.csv` into a separate patient-record table using stable patient IDs. The sample contains fictional records, uses `example.com` email addresses, and marks every record as not opted in to email. It is only visible after staff authorization. Do not replace it with real patient information in this public demo.

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
