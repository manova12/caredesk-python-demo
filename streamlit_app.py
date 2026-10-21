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
    "Gastroenterology", "Neurology", "Cardiology",
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

PAGES = {}

APP_CSS = """
<style>
:root { --ink:#18303a; --muted:#687b7c; --teal:#0d8178; --teal-soft:#e5f4ef; --line:#e3ebe6; --wash:#f3f7f1; }
[data-testid="stAppViewContainer"] { background:var(--wash); color:var(--ink); }
[data-testid="stHeader"] { background:rgba(255,255,255,.94); border-bottom:1px solid var(--line); }
[data-testid="stMainBlockContainer"] { max-width:1240px; padding-top:1.4rem; padding-bottom:3rem; }
[data-testid="stSidebar"] { display:none; }
[data-testid="stDecoration"] { display:none; }
h1, h2, h3 { color:var(--ink); letter-spacing:-.025em; }
p, label, [data-testid="stCaption"] { color:var(--muted); }
[data-testid="stVerticalBlockBorderWrapper"] { border-color:var(--line)!important; border-radius:18px!important; background:white; box-shadow:0 12px 34px rgba(25,55,48,.05); }
[data-testid="stBaseButton-primary"] { background:var(--teal); border-color:var(--teal); border-radius:10px; min-height:2.8rem; }
[data-testid="stBaseButton-secondary"], [data-testid="stPageLink"] a { border-radius:10px; }
[data-testid="stWidgetLabel"] p { color:var(--ink); font-weight:600; }
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea, [data-testid="stDateInput"] input,
[data-testid="stSelectbox"] [role="combobox"] { border-radius:10px; }
.care-header { display:flex; align-items:center; gap:12px; padding:.25rem 0 .9rem; border-bottom:1px solid var(--line); margin-bottom:1.5rem; }
.care-mark { display:grid; place-items:center; width:38px; height:38px; border-radius:12px; background:var(--teal); color:white; font-weight:800; font-size:18px; }
.care-name { color:var(--ink); font-weight:800; font-size:18px; line-height:1.1; }
.care-tag { color:#718180; font-size:10px; letter-spacing:.09em; }
.care-eyebrow { color:#0d8178; font-size:11px; font-weight:800; letter-spacing:.16em; text-transform:uppercase; margin-bottom:.7rem; }
.care-hero-title { font-family:Georgia,serif; color:#17323a; font-size:clamp(2.4rem,5.8vw,4.8rem); line-height:1.02; letter-spacing:-.045em; margin:0 0 1rem; }
.care-hero-sub { font-family:Georgia,serif; color:#5b7270; font-size:1.45rem; margin:0 0 1rem; }
.care-body { color:#627676; font-size:1rem; line-height:1.8; max-width:40rem; }
.care-panel-title { font-family:Georgia,serif; font-size:1.65rem; color:#203a40; margin:.3rem 0 .5rem; }
.care-step { font-size:11px; color:#0d8178; font-weight:800; letter-spacing:.08em; }
.care-section-title { font-family:Georgia,serif; font-size:2rem; color:#1a363d; margin:.15rem 0 .65rem; }
.care-safety { background:#fff9ef; border:1px solid #f0dfc5; border-radius:14px; padding:1rem 1.2rem; color:#74552b; }
.care-muted-small { font-size:.78rem; color:#849090; }
.st-key-home-hero { max-width:1320px; margin:0 auto 1.25rem; padding:2.7rem 0 2.3rem; border-radius:0; background:radial-gradient(ellipse at 78% 24%,#e9f4ec 0,transparent 38%),linear-gradient(116deg,#f7f8f4 2%,#f2f6f1 100%); }
.care-hero-title { font-family:Georgia,"Times New Roman",serif!important; font-weight:500!important; color:#17333a!important; font-size:clamp(2.35rem,4vw,3.25rem)!important; line-height:1.08!important; letter-spacing:-.075rem!important; max-width:34rem; margin:0 0 .55rem!important; }
[data-testid="stMarkdownContainer"] h1.care-hero-title { font-family:Georgia,"Times New Roman",serif!important; font-weight:500!important; }
.care-hero-sub { font-family:Georgia,"Times New Roman",serif; color:#526b70; font-size:clamp(1.25rem,2.1vw,1.7rem); line-height:1.25; margin:.5rem 0 0; }
.care-body { color:#526b70; font-size:1rem; line-height:1.75; max-width:33rem; margin:1.05rem 0 1.45rem; }
.care-eyebrow { display:flex; align-items:center; gap:.65rem; color:#087c72; font-size:10px; font-weight:800; letter-spacing:.14em; }
.care-hero-eyebrow::before { content:""; width:7px; height:7px; border-radius:50%; background:#d98d72; box-shadow:0 0 0 4px #f4e6df; }
.care-secondary-link { color:#07655e; font-size:13px; font-weight:700; text-decoration:none; border-bottom:1px solid #9dc6bb; padding:5px 0; }
.care-secondary-link:hover { color:#087c72; }
.care-visit-card { min-height:330px; padding:1.65rem; display:flex; flex-direction:column; justify-content:center; }
.care-visit-icon { display:grid; place-items:center; width:48px; height:48px; margin:0 0 1.2rem; color:#087c72; background:#e5f4ef; border-radius:14px; font-size:24px; }
.care-visit-card .care-step { font-size:9px; letter-spacing:.14em; }
.care-visit-card .care-panel-title { font-size:1.55rem; margin:.45rem 0 .55rem; }
.care-demo-note { color:#87928e; font-size:.68rem; line-height:1.45; text-align:center; margin-top:.8rem; }
.care-steps-strip { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); align-items:center; gap:1.2rem; padding:1rem 1.55rem; background:#fff; border:1px solid var(--line); border-radius:13px; box-shadow:0 8px 24px rgba(25,55,48,.035); }
.care-step-item { display:flex; align-items:center; gap:.75rem; min-width:0; }
.care-step-badge { flex:0 0 34px; height:34px; display:grid; place-items:center; color:#087c72; background:#e5f4ef; border-radius:50%; font-size:11px; font-weight:800; }
.care-step-copy b { display:block; color:#203a40; font-size:12px; line-height:1.3; }
.care-step-copy span { display:block; color:#849090; font-size:10px; line-height:1.4; margin-top:2px; }
.st-key-visit-card [data-testid="stVerticalBlockBorderWrapper"] { min-height:330px; }
.st-key-visit-card [data-testid="stBaseButton-primary"] { width:100%; }
.st-key-home-hero [data-testid="stBaseButton-primary"] { box-shadow:0 5px 14px #087c7226; }
@media (max-width:700px) { [data-testid="stMainBlockContainer"] { padding-left:1rem; padding-right:1rem; } .st-key-home-hero { padding:1.8rem 1rem; } .care-hero-title { font-size:2.35rem!important; } .care-steps-strip { grid-template-columns:1fr; gap:.8rem; } .st-key-visit-card [data-testid="stVerticalBlockBorderWrapper"] { min-height:0; } }
</style>
"""


def site_header() -> None:
    left, right = st.columns([5, 1.4], vertical_alignment="center")
    with left:
        st.markdown(
            '<div class="care-header"><div class="care-mark">C</div>'
            '<div><div class="care-name">CareDesk</div><div class="care-tag">CARE, MADE EASIER</div></div></div>',
            unsafe_allow_html=True,
        )
    with right:
        if "clinic" in PAGES:
            st.page_link(PAGES["clinic"], label="Clinic team", icon=":material/medical_services:")


def home_page() -> None:
    site_header()
    with st.container(key="home-hero"):
        left, right = st.columns([1.05, .75], gap="large", vertical_alignment="center")
        with left:
            st.markdown('<div class="care-eyebrow care-hero-eyebrow">Patient care, made easier</div>', unsafe_allow_html=True)
            st.markdown('<h1 class="care-hero-title">KUMAR CLINIC AND PHARMACY</h1>', unsafe_allow_html=True)
            st.markdown('<div class="care-hero-sub">A clear next step for your health.</div>', unsafe_allow_html=True)
            st.markdown('<div class="care-body">Tell us what you need help with. We’ll guide you to a suitable service and help you find an appointment that works for you.</div>', unsafe_allow_html=True)
            cta, explore = st.columns([1, 1.05], vertical_alignment="center")
            with cta:
                if st.button("Book an appointment  →", type="primary", key="home_book", use_container_width=True):
                    st.switch_page(PAGES["booking"])
            with explore:
                st.markdown('<a class="care-secondary-link" href="#care-services">Explore care services</a>', unsafe_allow_html=True)
        with right:
            with st.container(border=True, key="visit-card"):
                st.markdown('<div class="care-visit-icon" aria-hidden="true">▦</div><div class="care-step">YOUR VISIT STARTS HERE</div><div class="care-panel-title">Find the care you need</div>', unsafe_allow_html=True)
                st.write("Choose a service, share a few details, and review your appointment before booking.")
                if st.button("Start booking  ↗", type="primary", key="home_start_booking", use_container_width=True):
                    st.switch_page(PAGES["booking"])
                if st.button("Already booked? Find your demo appointment", key="home_lookup", use_container_width=True):
                    st.switch_page(PAGES["lookup"])
                st.markdown('<div class="care-demo-note">This is a demonstration. Bookings use a separate demo database. Emails are previews only.</div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="care-steps-strip">'
        '<div class="care-step-item"><span class="care-step-badge">01</span><div class="care-step-copy"><b>Guided choice</b><span>Find a department with a little help</span></div></div>'
        '<div class="care-step-item"><span class="care-step-badge">02</span><div class="care-step-copy"><b>Your preferred time</b><span>Choose from a doctor’s available hours</span></div></div>'
        '<div class="care-step-item"><span class="care-step-badge">03</span><div class="care-step-copy"><b>Human care</b><span>Your care plan stays with your clinician</span></div></div>'
        '</div>', unsafe_allow_html=True,
    )

    st.markdown('<div id="care-services" class="care-eyebrow" style="margin-top:2.2rem">Care that meets you where you are</div><div class="care-section-title">Explore our services</div><p>Choose a department to start booking:</p>', unsafe_allow_html=True)
    service_cols = st.columns(3)
    for index, department in enumerate(DEPARTMENTS):
        with service_cols[index % 3]:
            if st.button(department, key=f"home_service_{index}", use_container_width=True):
                st.session_state["booking_department"] = department
                st.session_state["booking_step"] = 1
                st.switch_page(PAGES["booking"])

    with st.expander("Help me choose"):
        concern = st.text_area("What would you like help with?", key="home_routing_concern", max_chars=1500)
        if st.button("Suggest a service", key="suggest_service"):
            text = concern.lower()
            routing = [
                ("skin", "Dermatology"), ("rash", "Dermatology"),
                ("bone", "Orthopedics"), ("joint", "Orthopedics"),
                ("stomach", "Gastroenterology"), ("digest", "Gastroenterology"),
                ("heart", "Cardiology"), ("chest", "Cardiology"),
                ("headache", "Neurology"), ("nerve", "Neurology"),
            ]
            suggestion = next((dept for term, dept in routing if term in text), "General Medicine")
            st.info(f"Suggested starting point: {suggestion}. This is administrative routing only, not a diagnosis.")

    st.markdown('<div class="care-eyebrow" style="margin-top:2.2rem">A simple path to care</div><div class="care-section-title">What happens next</div><p>We’ll keep the steps clear, from your first question to your visit.</p>', unsafe_allow_html=True)
    flow = st.columns(4)
    for col, number, title, body in zip(
        flow,
        ("1", "2", "3", "4"),
        ("Tell us what’s on your mind", "Choose a doctor and time", "Meet with your clinician", "Stay informed"),
        ("Share your concern in your own words. A service suggestion is only a starting point.", "Review clinic hours and choose an appointment that suits you.", "Your clinician will assess your needs and discuss next steps.", "The clinic team can help with reminders and follow-up arrangements."),
    ):
        with col:
            with st.container(border=True):
                st.markdown(f'<div class="care-step">{number}</div><strong>{title}</strong><br><span class="care-muted-small">{body}</span>', unsafe_allow_html=True)
    st.markdown('<div class="care-eyebrow" style="margin-top:2.2rem">Here when you need us</div><div class="care-section-title">Need urgent help?</div><div class="care-safety">This booking demo is not for emergencies. If you may be experiencing a medical emergency, or symptoms are severe or sudden, contact your local emergency services now.</div>', unsafe_allow_html=True)


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
        configured = st.secrets.get("staff_emails", [])
        if isinstance(configured, str):
            configured = [configured]
        allowed = {str(email).strip().casefold() for email in configured if str(email).strip()}
        current_email = str(st.user.get("email", "")).strip().casefold()
        return bool(current_email and current_email in allowed)
    except Exception:
        return False


def booking_page() -> None:
    site_header()
    st.markdown('<div class="care-eyebrow">Your visit starts here</div>', unsafe_allow_html=True)
    st.markdown('<div class="care-section-title">Let’s arrange your visit</div>', unsafe_allow_html=True)
    st.caption("A clinic team member can review your request. This demo is not medical advice.")
    step = st.session_state.setdefault("booking_step", 1)
    step_cols = st.columns(3)
    for col, number, label in zip(step_cols, ("01", "02", "03"), ("About you", "Service & time", "Review")):
        with col:
            active = int(number) // 1 <= step
            st.markdown(f'<div class="care-step">{number}  {"●" if active else "○"} {label}</div>', unsafe_allow_html=True)

    previous = st.session_state.get("booking_payload", {})
    if st.session_state.get("booking_result"):
        result = st.session_state["booking_result"]
        with st.container(border=True):
            st.success(f"Appointment request saved. Your confirmation code is **{result['code']}**.")
            st.write(f"{result['department']} · Dr. {result['doctor']} · {result['visit_date']} at {result['visit_time']}")
            st.info("Email confirmations and reminders are previews only on this demo site.")
            if st.button("Book another appointment", type="primary"):
                st.session_state.pop("booking_result", None)
                st.session_state.pop("booking_payload", None)
                st.session_state["booking_step"] = 1
                st.rerun()
        return

    if step == 1:
        with st.container(border=True):
            st.markdown('<div class="care-panel-title">About you</div><p>Share a few details so the clinic team can help arrange your visit.</p>', unsafe_allow_html=True)
            with st.form("about_you_form"):
                name = st.text_input("Your name", value=previous.get("name", ""), max_chars=120)
                email = st.text_input("Email address", value=previous.get("email", ""), max_chars=254)
                age_text = st.text_input("Age (optional)", value=str(previous.get("age") or ""), max_chars=3)
                preferred_date = st.date_input("Preferred appointment date", value=previous.get("visit_date", date.today()), min_value=date.today())
                concern = st.text_area("What would you like help with?", value=previous.get("concern", ""), max_chars=2000)
                st.markdown('<div class="care-safety">Your message is used to suggest a service. It is not a diagnosis. For severe or sudden symptoms, contact local emergency services now.</div>', unsafe_allow_html=True)
                continue_about = st.form_submit_button("Continue", type="primary")
            if continue_about:
                if not name.strip() or not concern.strip() or "@" not in email or "." not in email.rsplit("@", 1)[-1]:
                    st.error("Enter your name, a valid email address, and a short description of what you need help with.")
                else:
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
                    st.session_state["booking_payload"] = {
                        "name": name.strip(), "email": email.strip().lower(), "phone": "",
                        "age": age, "concern": concern.strip(), "visit_date": preferred_date,
                        "department": st.session_state.get("booking_department", "General Medicine"),
                    }
                    st.session_state["booking_step"] = 2
                    st.rerun()
        return

    if step == 2:
        with st.container(border=True):
            st.markdown('<div class="care-panel-title">Choose a service and time</div><p>Suggested starting point: General Medicine. A clinic team member can review this with you.</p>', unsafe_allow_html=True)
            department = st.selectbox("Service", DEPARTMENTS, index=DEPARTMENTS.index(previous.get("department", "General Medicine")), key="booking_department")
            visit_date = st.date_input("Choose your appointment date", value=previous.get("visit_date", date.today()), min_value=date.today(), key="booking_date")
            doctor_options = [name for name, roster in DOCTORS.items() if roster["dept"] == department and visit_date.weekday() in roster["days"]]
            if doctor_options:
                doctor = st.selectbox("Doctor", doctor_options, format_func=lambda name: f"Dr. {name} · {DOCTORS[name]['start']:02d}:00–{DOCTORS[name]['end']:02d}:00", key=f"booking_doctor_{department}_{visit_date.isoformat()}")
            else:
                doctor = ""
                st.info("No doctors are scheduled for this service on the selected day.")
            slot_options = times_for(doctor, visit_date) if doctor else []
            if slot_options:
                visit_time = st.selectbox("Preferred time", slot_options, key=f"booking_time_{doctor}_{visit_date.isoformat()}")
                st.caption(f"Dr. {doctor} is available at {visit_time}. {len(slot_options)} open times remain. Times are shown in the clinic’s local time.")
            else:
                visit_time = ""
                st.info("No open times are available. Choose a different date or doctor.")
            back, forward = st.columns(2)
            with back:
                if st.button("← Back to your details"):
                    st.session_state["booking_step"] = 1
                    st.rerun()
            with forward:
                next_step = st.button("Continue", type="primary", disabled=not slot_options)
            if next_step:
                st.session_state["booking_payload"] = {**previous, "department": department, "doctor": doctor, "visit_date": visit_date, "visit_time": visit_time}
                st.session_state["booking_step"] = 3
                st.rerun()
        return

    payload = st.session_state.get("booking_payload", {})
    if not payload.get("doctor"):
        st.session_state["booking_step"] = 2
        st.rerun()
    with st.container(border=True):
        st.markdown('<div class="care-panel-title">Review your appointment</div><div class="care-eyebrow">Your appointment</div>', unsafe_allow_html=True)
        st.subheader(payload["department"])
        st.write(f"**Doctor:** Dr. {payload['doctor']}  ·  **Date and time:** {payload['visit_date'].strftime('%d-%m-%Y')} at {payload['visit_time']}  ·  **Patient:** {payload['name']}")
        if st.button("Change details"):
            st.session_state["booking_step"] = 2
            st.rerun()
        with st.form("confirm_booking_form"):
            consent = st.checkbox("I agree to receive appointment reminders by email. I can withdraw consent later.")
            st.caption("Messages are simulated in this demo; no email message will be sent.")
            st.caption("The service suggestion is for appointment routing only. Your clinician will assess your health concern during the visit.")
            confirm = st.form_submit_button("Confirm appointment", type="primary")
        if confirm:
            saved = {**payload, "reminder_consent": consent}
            ok, message, code = save_booking(saved)
            if ok:
                st.session_state["booking_result"] = {**saved, "code": code}
                st.rerun()
            st.error(message)


def lookup_page() -> None:
    site_header()
    st.markdown('<div class="care-eyebrow">Your visit starts here</div><div class="care-section-title">Find your appointment</div>', unsafe_allow_html=True)
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
        with st.container(border=True):
            st.markdown('<div class="care-eyebrow">Appointment details</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="care-panel-title">{booking["department"]}</div>', unsafe_allow_html=True)
            st.write(f"Dr. {booking['doctor']} · {booking['visit_date']} at {booking['visit_time']} · {booking['outcome']}")
            st.caption("To change or cancel an appointment, contact the clinic team for this demo.")


def clinic_page() -> None:
    site_header()
    st.markdown('<div class="care-eyebrow">Restricted staff access</div><div class="care-section-title">Clinic team sign in</div>', unsafe_allow_html=True)
    if not staff_is_authorized():
        with st.container(border=True):
            st.write("Sign in with an approved Google account configured by the clinic administrator.")
        try:
            if st.user.is_logged_in:
                st.error("This Google account is not on the clinic staff allowlist.")
                if st.button("Sign out of this account"):
                    st.logout()
            elif st.button("Sign in with Google", type="primary"):
                st.login("google")
        except Exception:
            st.warning("Staff sign-in is not configured yet. Add the Streamlit Google OIDC settings and staff email allowlist before deployment.")
        return

    st.markdown('<div class="care-section-title">Good morning, clinic team</div><p>Here’s your patient coordination overview.</p>', unsafe_allow_html=True)
    bookings = get_bookings()
    metric_cols = st.columns(4)
    for col, label, value, hint in zip(
        metric_cols,
        ("Appointments", "Appointments today", "Awaiting action", "Reminders queued"),
        (len(bookings), sum(b["visit_date"] == date.today().isoformat() for b in bookings), 0, 0),
        ("In this demo database", "Across all departments", "Needs staff review", "Preview only"),
    ):
        with col:
            with st.container(border=True):
                st.metric(label, value, help=hint)
    st.markdown('<div class="care-section-title">Clinic operations</div><p>A live overview of this demo’s visits and next actions.</p>', unsafe_allow_html=True)
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


st.set_page_config(page_title="CareDesk | Kumar Clinic and Pharmacy", page_icon="🩺", layout="wide")
st.markdown(APP_CSS, unsafe_allow_html=True)
init_db()
PAGES["home"] = st.Page(home_page, title="Patient portal", icon=":material/home:", default=True)
PAGES["booking"] = st.Page(booking_page, title="Book an appointment", icon=":material/calendar_add_on:")
PAGES["lookup"] = st.Page(lookup_page, title="Find your appointment", icon=":material/search:")
PAGES["clinic"] = st.Page(clinic_page, title="Clinic team", icon=":material/medical_services:")
selected = st.navigation(list(PAGES.values()), position="hidden")
selected.run()
