# 📞 AI-Powered Medicine & Water Reminder System (IVR Based)

An end-to-end **voice-based reminder system** that calls users automatically for **medicine intake and water consumption**, supports **English & Kannada**, and records **adherence logs** using **DTMF (Press 1 / Press 2)** input.

This system is designed for:

* Elderly users
* Patients with chronic illness
* Users without smartphones
* Rural / accessibility-focused healthcare use cases

---

## 🚀 Features

### ✅ Core Functionality

* 📱 User Registration & Login (Phone-based, +91 normalized)
* 💊 Medicine reminders (fixed time per day)
* 💧 Water reminders (interval-based, e.g. every 120 mins)
* 📞 Automatic voice calls using IVR
* 🎙️ English & Kannada voice support
* 🔢 DTMF input:

  * **Press 1 → Taken**
  * **Press 2 → Skipped**
* 📝 Adherence logging with timestamps
* 🕒 Background scheduler for continuous execution

---

## 🧠 System Architecture

```
┌────────────┐      ┌──────────────┐      ┌──────────────┐
│  Frontend  │ ---> │  FastAPI API │ ---> │ JSON Storage │
└────────────┘      └──────────────┘      └──────────────┘
                          │
                          ▼
                   ┌──────────────┐
                   │  Scheduler   │
                   │ (scheduler.py)│
                   └──────────────┘
                          │
                          ▼
                   ┌──────────────┐
                   │ Twilio Calls │
                   │  (IVR)       │
                   └──────────────┘
```

---

## 🧩 Tech Stack

* **Backend**: FastAPI (Python)
* **Scheduler**: Custom Python loop (`scheduler.py`)
* **Voice / IVR**: Twilio
* **Database**: JSON files (for demo & hackathon)
* **Tunneling**: ngrok
* **Frontend**: Single-page HTML (optional dashboard)

---

## 📁 Project Structure

```
.
├── app.py                 # FastAPI backend (API + IVR)
├── scheduler.py           # Background reminder scheduler
├── call_handler.py        # Twilio call trigger logic
├── utils/
│   └── json_db.py         # JSON read/write helpers
├── data/
│   ├── users.json
│   ├── reminders.json
│   ├── adherence_logs.json
│   └── call_history.json
├── static/
│   ├── kannada_medicine.mp3
│   ├── kannada_water.mp3
│   ├── kannada_thanks.mp3
│   └── kannada_skip.mp3
├── index.html              # Frontend (optional)
└── README.md
```

---

## 🔁 Reminder Types

### 💊 Medicine Reminder

* Triggered **once per day**
* Time-based (`HH:MM`)
* Grace window (±2 minutes)
* Only one call per day per medicine

### 💧 Water Reminder

* Triggered **every N minutes**
* Interval-based (default: 120 mins)
* Continues throughout the day

---

## 📞 IVR Call Flow (Twilio)

### English

1. System speaks reminder
2. Speaks options:

   * Press 1 if taken
   * Press 2 if skipped
3. System listens for DTMF
4. Response is logged

### Kannada

1. Kannada MP3 plays (medicine / water)
2. English numeric instruction plays
3. User presses 1 or 2
4. Kannada confirmation audio plays
5. Response is logged

---

## 📝 Adherence Logging

All user responses are stored in:

```
data/adherence_logs.json
```

Example:

```json
{
  "id": "log_123",
  "time": "2026-01-17T10:32:11",
  "status": "taken",
  "reminder_id": "rem_001",
  "user_id": "user_001",
  "type": "medicine"
}
```

This enables:

* Daily compliance tracking
* Missed dose detection
* Reports for doctors / caregivers

---

## ⚙️ Scheduler (`scheduler.py`) – How It Works

* Runs continuously
* Checks reminders every **20 seconds**
* Decides whether a call is needed
* Prevents duplicate daily medicine calls
* Updates `last_triggered` for water reminders
* Logs every call in `call_history.json`

### Key Parameters

```python
GRACE_MINUTES = 2
SLEEP_SECONDS = 20
```

---

## ▶️ How to Run the Project

### 1️⃣ Install Dependencies

```bash
pip install fastapi uvicorn twilio
```

### 2️⃣ Start Backend API

```bash
uvicorn app:app --reload
```

### 3️⃣ Expose API (ngrok)

```bash
ngrok http 8000
```

### 4️⃣ Configure Twilio Webhook

Set voice webhook to:

```
https://<ngrok-url>/voice?reminder_id=REMINDER_ID
```

### 5️⃣ Start Scheduler

```bash
python scheduler.py
```

---

## 🌍 Language Support

* 🇬🇧 English (TTS – Polly.Aditi)
* 🇮🇳 Kannada (MP3 audio)
* Language selected during user registration

---

## ⚠️ Notes & Limitations

* JSON DB is **not for production**
* Passwords are stored in plain text (demo only)
* Sessions are in-memory (restart clears them)
* Designed for hackathon / prototype use

---

## 🚀 Future Enhancements

* OTP-based authentication
* Caregiver dashboard
* WhatsApp fallback
* Daily adherence percentage
* Doctor PDF reports
* Cloud DB (PostgreSQL / Firebase)
* Kannada TTS (instead of MP3)
* Retry logic for missed calls

---

## 🏁 Conclusion

This project demonstrates a **real-world, accessibility-focused healthcare system** using **voice technology**, suitable for regions where smartphone usage is limited.

It combines:

* Automation
* Multilingual support
* User interaction via IVR
* Practical healthcare use cases

---

