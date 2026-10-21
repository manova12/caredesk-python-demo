from __future__ import annotations

import json
import os
import secrets
import sqlite3
from datetime import date, datetime, time, timedelta
from pathlib import Path

import streamlit as st


APP_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("CAREDESK_DB_PATH", APP_DIR / "data" / "caredesk.sqlite3"))
DEPARTMENTS = [
    "General Medicine", "Dermatology", "Orthopedics",
    "Gastroenterology", "Cardiology", "Neurology",
]
DOCTORS = {
    "A. Mehta": {"dept": "General Medicine", "days": {1, 2, 3, 4, 5, 6}, "start": 9, "end": 13},
    "V. Sinha": {"dept": "General Medicine", "days": {2, 3, 4, 5, 6}, "start": 14, "end": 17},
    "R. Iyer": {"dept": "Dermatology", "days": {1, 2, 3, 4, 5}, "start": 10, "end": 15},
    "N. Kapoor": {"dept": "Dermatology", "days": {2, 3, 4, 5, 6}, "start": 9, "end": 14},
    "S. Rao": {"dept": "Orthopedics", "days": {1, 2, 3, 4, 5, 6}, "start": 9, "end": 14},
    "T. Menon": {"dept": "Orthopedics", "days": {1, 2, 3, 4, 5}, "start": 14, "end": 17},
    "P. Nair": {"dept": "Gastroenterology", "days": {1, 2, 3, 4, 5}, "start": 11, "end": 16},
    "L. Desai": {"dept": "Gastroenterology", "days": {2, 3, 4, 5, 6}, "start": 9, "end": 13},
    "K. Shah": {"dept": "Cardiology", "days": {1, 2, 3, 4, 5, 6}, "start": 9, "end": 12},
    "N. Reddy": {"dept": "Cardiology", "days": {1, 2, 3, 4, 5}, "start": 14, "end": 17},
    "M. Das": {"dept": "Neurology", "days": {1, 2, 3, 4, 5}, "start": 13, "end": 17},
    "S. Banerjee": {"dept": "Neurology", "days": {2, 3, 4, 5, 6}, "start": 9, "end": 13},
}


def connect_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=15)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA busy_timeout=15000")
    return db


def init_db() -> None:
    with connect_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS bookings (
                id TEXT PRIMARY KEY,
                confirmation_code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL DEFAULT '',
                age INTEGER,
                concern TEXT NOT NULL,
                department TEXT NOT NULL,
                doctor TEXT NOT NULL,
                visit_date TEXT NOT NULL,
                visit_time TEXT NOT NULL,
                reminder_consent INTEGER NOT NULL DEFAULT 0,
                outcome TEXT NOT NULL DEFAULT 'Booked',
                created_at TEXT NOT NULL,
                UNIQUE(doctor, visit_date, visit_time)
            );
            CREATE TABLE IF NOT EXISTS message_queue (
                id TEXT PRIMARY KEY,
                booking_id TEXT NOT NULL,
                kind TEXT NOT NULL,
                recipient TEXT NOT NULL,
                scheduled_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'simulated',
                note TEXT NOT NULL DEFAULT 'Preview only; email is not configured.',
                created_at TEXT NOT NULL,
                FOREIGN KEY(booking_id) REFERENCES bookings(id)
            );
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id TEXT NOT NULL,
                event TEXT NOT NULL,
                at TEXT NOT NULL
            );
        """)


def get_bookings() -> list[dict]:
    with connect_db() as db:
        return [dict(row) for row in db.execute("SELECT * FROM bookings ORDER BY visit_date, visit_time")]


def taken_slots(doctor: str, visit_date: date) -> set[str]:
    with connect_db() as db:
        rows = db.execute(
            "SELECT visit_time FROM bookings WHERE doctor=? AND visit_date=? AND outcome='Booked'",
            (doctor, visit_date.isoformat()),
        )
        return {row[0] for row in rows}


def times_for(doctor: str, visit_date: date) -> list[str]:
    roster = DOCTORS.get(doctor)
    if not roster or visit_date.weekday() not in roster["days"]:
        return []
    busy = taken_slots(doctor, visit_date)
    slots = []
    cursor = datetime.combine(visit_date, time(roster["start"], 0))
    end = datetime.combine(visit_date, time(roster["end"], 0))
    while cursor < end:
        if cursor > datetime.now() and cursor.strftime("%H:%M") not in busy:
            slots.append(cursor.strftime("%H:%M"))
        cursor += timedelta(minutes=30)
    return slots


def queue_messages(db: sqlite3.Connection, booking: dict) -> None:
    now = datetime.now().astimezone()
    local_zone = now.tzinfo
    visit_at = datetime.combine(
        date.fromisoformat(booking["visit_date"]),
        time.fromisoformat(booking["visit_time"]),
    ).replace(tzinfo=local_zone)
    reminder_at = visit_at - timedelta(hours=2)
    for kind, scheduled in (("booking_confirmation", now), ("appointment_reminder", reminder_at)):
        if kind == "appointment_reminder" and (not booking["reminder_consent"] or scheduled <= now):
            continue
        db.execute(
            "INSERT INTO message_queue(id,booking_id,kind,recipient,scheduled_at,status,note,created_at) VALUES(?,?,?,?,?,?,?,?)",
            (secrets.token_hex(12), booking["id"], kind, booking["email"], scheduled.isoformat(),
             "simulated", "Preview only; connect and approve an email sender before live delivery.", now.isoformat()),
        )


def save_booking(payload: dict) -> tuple[bool, str, str | None]:
    if not payload["name"].strip() or not payload["concern"].strip():
        return False, "Enter your name and a short description of what you need help with.", None
    if "@" not in payload["email"] or "." not in payload["email"].rsplit("@", 1)[-1]:
        return False, "Enter a valid email address.", None
    roster = DOCTORS.get(payload["doctor"])
    when = datetime.combine(payload["visit_date"], time.fromisoformat(payload["visit_time"]))
    if not roster or roster["dept"] != payload["department"]:
        return False, "Choose a doctor listed for this service.", None
    if payload["visit_date"].weekday() not in roster["days"] or not roster["start"] <= when.hour < roster["end"] or when.minute not in (0, 30) or when <= datetime.now():
        return False, "That doctor is not available at the selected time. Choose another open slot.", None

    booking_id = "PT-" + secrets.token_hex(7).upper()
    code = "CD" + secrets.token_hex(5).upper()
    now = datetime.now().astimezone().isoformat()
    record = {**payload, "id": booking_id, "confirmation_code": code, "email": payload["email"].strip().lower(),
              "outcome": "Booked", "created_at": now}
    try:
        with connect_db() as db:
            db.execute("""INSERT INTO bookings
                (id,confirmation_code,name,email,phone,age,concern,department,doctor,visit_date,visit_time,reminder_consent,outcome,created_at)
                VALUES (:id,:confirmation_code,:name,:email,:phone,:age,:concern,:department,:doctor,:visit_date,:visit_time,:reminder_consent,:outcome,:created_at)""", record)
            queue_messages(db, record)
            db.execute("INSERT INTO audit_log(booking_id,event,at) VALUES(?,?,?)", (booking_id, "Appointment booked through patient portal", now))
        return True, "Your appointment is booked.", code
    except sqlite3.IntegrityError:
        return False, "That time was just booked. Please choose another available slot.", None


def staff_is_authorized() -> bool:
    try:
        if not st.user.is_logged_in:
            return False
        allowed = {email.strip().lower() for email in st.secrets.get("staff_emails", [])}
        return bool(allowed) and str(st.user.email).lower() in allowed
    except Exception:
        return False


def booking_page() -> None:
    st.title("Book an appointment")
    st.caption("Choose a clinic service, doctor, and available time. This demo does not provide medical advice.")
    department = st.selectbox("Service", DEPARTMENTS, key="booking_department")
    visit_date = st.date_input("Preferred date", min_value=date.today(), key="booking_date")
    doctor_options = [name for name, d in DOCTORS.items() if d["dept"] == department and visit_date.weekday() in d["days"]]
    if doctor_options:
        doctor = st.selectbox("Doctor", doctor_options, key="booking_doctor")
    else:
        doctor = ""
        st.info("No doctors are scheduled for this service on the selected day.")
    slot_options = times_for(doctor, visit_date) if doctor in DOCTORS else []
    if slot_options:
        visit_time = st.selectbox("Available time", slot_options, key="booking_time")
    else:
        visit_time = ""
        st.info("No open times are available. Select another date or doctor.")

    with st.form("booking_form"):
        name = st.text_input("Full name", max_chars=120)
        email = st.text_input("Email address", max_chars=254)
        phone = st.text_input("Phone (optional)", max_chars=40)
        age_text = st.text_input("Age (optional)", max_chars=3, help="Leave blank if you prefer not to provide it.")
        concern = st.text_area("What would you like help with?", max_chars=2000)
        consent = st.checkbox("I agree to receive appointment reminders by email.")
        submitted = st.form_submit_button("Confirm booking", type="primary", disabled=not slot_options)
    if submitted:
        age = None
        if age_text.strip():
            try:
                age = int(age_text)
            except ValueError:
                st.error("Age must be a whole number between 0 and 120.")
                return
            if not 0 <= age <= 120:
                st.error("Age must be a whole number between 0 and 120.")
                return
        payload = {"name": name, "email": email, "phone": phone, "age": age,
                   "concern": concern, "department": department, "doctor": doctor,
                   "visit_date": visit_date, "visit_time": visit_time, "reminder_consent": consent}
        ok, message, code = save_booking(payload)
        if ok:
            st.success(f"{message} Your confirmation code is **{code}**. Email is currently preview-only.")
            st.session_state["last_booking_code"] = code
        else:
            st.error(message)


def lookup_page() -> None:
    st.title("Find your appointment")
    st.caption("Use the email address and confirmation code from your booking.")
    with st.form("lookup_form"):
        email = st.text_input("Booking email")
        code = st.text_input("Confirmation code")
        submitted = st.form_submit_button("Find appointment")
    if submitted:
        with connect_db() as db:
            row = db.execute("SELECT * FROM bookings WHERE lower(email)=? AND upper(confirmation_code)=?", (email.strip().lower(), code.strip().upper())).fetchone()
        if row:
            st.session_state["lookup_booking"] = dict(row)
        else:
            st.error("We couldn't match that email and confirmation code.")
    booking = st.session_state.get("lookup_booking")
    if booking:
        st.info(f"{booking['department']} with Dr. {booking['doctor']} · {booking['visit_date']} at {booking['visit_time']} · {booking['outcome']}")
        st.caption("To change or cancel an appointment, contact the clinic team for this demo.")


def clinic_page() -> None:
    st.title("Clinic team workspace")
    if not staff_is_authorized():
        st.info("Clinic staff sign-in is restricted to email addresses configured by the administrator.")
        try:
            if st.user.is_logged_in:
                st.error("This Google account is not on the clinic staff allowlist.")
            elif st.button("Sign in with Google", type="primary"):
                st.login("google")
        except Exception:
            st.warning("Staff sign-in is not configured yet. Add the Streamlit Google OIDC settings and staff email allowlist before deployment.")
        return

    bookings = get_bookings()
    with st.container(border=True):
        st.metric("Appointments", len(bookings))
    if bookings:
        st.dataframe([{k: b[k] for k in ("name", "email", "department", "doctor", "visit_date", "visit_time", "outcome")} for b in bookings], hide_index=True)
    else:
        st.info("No demo bookings yet.")
    with connect_db() as db:
        messages = [dict(row) for row in db.execute("SELECT kind,recipient,scheduled_at,status,note FROM message_queue ORDER BY scheduled_at DESC LIMIT 100")]
    st.subheader("Message queue")
    if messages:
        st.dataframe(messages, hide_index=True)
    else:
        st.caption("No messages are queued.")
    st.warning("Email delivery and reminder scheduling are preview-only in this first Python build. Configure an approved provider and persistent hosted database before relying on them.")


st.set_page_config(page_title="CareDesk", page_icon="🩺", layout="wide")
init_db()
pages = [
    st.Page(booking_page, title="Book an appointment", icon=":material/calendar_add_on:", default=True),
    st.Page(lookup_page, title="Find your appointment", icon=":material/search:"),
    st.Page(clinic_page, title="Clinic team", icon=":material/medical_services:"),
]
selected = st.navigation(pages, position="sidebar")
with st.sidebar:
    st.markdown("### CareDesk")
    st.caption("Patient booking and clinic coordination demo")
    st.divider()
    st.caption("For emergencies, contact your local emergency services.")
selected.run()
