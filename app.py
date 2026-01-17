import json
import uuid
import re
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator

# ================== APP ==================
app = FastAPI(title="Medicine Reminder System (EN + KN IVR)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "static"

DATA_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ================== JSON DB ==================
class JsonDB:
    def __init__(self, filename):
        self.path = DATA_DIR / filename
        if not self.path.exists():
            self.path.write_text("[]")

    def read(self):
        try:
            return json.loads(self.path.read_text())
        except:
            return []

    def write(self, data):
        self.path.write_text(json.dumps(data, indent=2))

    def append(self, item):
        data = self.read()
        data.append(item)
        self.write(data)

db_users = JsonDB("users.json")
db_reminders = JsonDB("reminders.json")
db_logs = JsonDB("adherence_logs.json")

sessions = {}

# ================== HELPERS ==================
def normalize_phone(v: str) -> str:
    digits = re.sub(r"\D", "", v)
    if len(digits) == 10:
        return "+91" + digits
    if len(digits) == 11 and digits.startswith("0"):
        return "+91" + digits[1:]
    if len(digits) == 12 and digits.startswith("91"):
        return "+" + digits
    raise ValueError("Invalid phone number")

def get_user_id(request: Request):
    token = request.headers.get("Authorization")
    if token not in sessions:
        raise HTTPException(status_code=401)
    return sessions[token]

# ================== MODELS ==================
class RegisterPayload(BaseModel):
    name: str
    phone: str
    password: str
    language: str  # en | kn

    @validator("phone")
    def v_phone(cls, v):
        return normalize_phone(v)

class LoginPayload(BaseModel):
    phone: str
    password: str

    @validator("phone")
    def v_phone(cls, v):
        return normalize_phone(v)

class MedicinePayload(BaseModel):
    name: str
    dosage: str
    schedule_time: str

# ================== FRONTEND ==================
@app.get("/", response_class=HTMLResponse)
async def index():
    f = BASE_DIR / "index.html"
    return f.read_text() if f.exists() else "<h1>No frontend</h1>"

# ================== AUTH ==================
@app.post("/register")
async def register(p: RegisterPayload):
    users = db_users.read()
    if any(u["phone"] == p.phone for u in users):
        raise HTTPException(400, "User exists")

    db_users.append({
        "id": str(uuid.uuid4()),
        "name": p.name,
        "phone": p.phone,
        "password": p.password,
        "language": p.language
    })
    return {"ok": True}

@app.post("/login")
async def login(p: LoginPayload):
    users = db_users.read()
    u = next((x for x in users if x["phone"] == p.phone and x["password"] == p.password), None)
    if not u:
        raise HTTPException(400, "Invalid credentials")

    token = str(uuid.uuid4())
    sessions[token] = u["id"]
    return {"token": token, "user": u}

# ================== REMINDERS ==================
@app.post("/add-medicine")
async def add_medicine(p: MedicinePayload, request: Request):
    uid = get_user_id(request)
    db_reminders.append({
        "id": str(uuid.uuid4()),
        "user_id": uid,
        "type": "medicine",
        "name": p.name,
        "dosage": p.dosage,
        "schedule_time": p.schedule_time
    })
    return {"ok": True}

@app.get("/my-reminders")

async def my_reminders(request: Request):
    uid = get_user_id(request)
    return [r for r in db_reminders.read() if r["user_id"] == uid]
@app.get("/my-adherence")
async def my_adherence(request: Request):
    uid = get_user_id(request)
    logs = db_logs.read()

    return [l for l in logs if l["user_id"] == uid]


# ================== VOICE (EN + KN, PRESS 1 / 2) ==================
@app.post("/voice")
async def voice(request: Request):
    reminder_id = request.query_params.get("reminder_id")
    if not reminder_id:
        return Response("<Response><Say>Error</Say></Response>", media_type="application/xml")

    reminders = db_reminders.read()
    users = db_users.read()

    r = next((x for x in reminders if x["id"] == reminder_id), None)
    if not r:
        return Response("<Response><Say>Reminder not found</Say></Response>", media_type="application/xml")

    u = next(x for x in users if x["id"] == r["user_id"])
    lang = u["language"]

    # ---------- ENGLISH ----------
    if lang == "en":
        main_msg = (
            "This is a water reminder. Please drink water now."
            if r["type"] == "water"
            else f"This is your medicine reminder. Please take {r['name']} now."
        )

        xml = f"""
<Response>
  <Say voice="Polly.Aditi">{main_msg}</Say>
  <Pause length="1"/>
  <Say voice="Polly.Aditi">
    Press 1 if you have taken it.
    Press 2 if you want to skip.
  </Say>
  <Gather input="dtmf" numDigits="1" timeout="7"
          action="/gather?reminder_id={reminder_id}" method="POST"/>
  <Say voice="Polly.Aditi">No input received. Goodbye.</Say>
</Response>
"""
        return Response(xml.strip(), media_type="application/xml")

    # ---------- KANNADA ----------
    # Kannada content via MP3 + English numeric instruction (DTMF-safe)
    kannada_audio = (
        "/static/kannada_water.mp3"
        if r["type"] == "water"
        else "/static/kannada_medicine.mp3"
    )

    xml = f"""
<Response>
  <Play>{kannada_audio}</Play>
  <Pause length="1"/>
  <Say voice="Polly.Aditi">
    Press 1 if taken.
    Press 2 if skipped.
  </Say>
  <Gather input="dtmf" numDigits="1" timeout="7"
          action="/gather?reminder_id={reminder_id}" method="POST"/>
  <Say voice="Polly.Aditi">No input received. Goodbye.</Say>
</Response>
"""
    return Response(xml.strip(), media_type="application/xml")

# ================== GATHER (STORE LOGS) ==================
@app.post("/gather")
async def gather(request: Request):
    form = await request.form()
    digit = form.get("Digits")
    reminder_id = request.query_params.get("reminder_id")

    reminders = db_reminders.read()
    users = db_users.read()

    r = next((x for x in reminders if x["id"] == reminder_id), None)
    if not r:
        return Response("<Response><Say>Error</Say></Response>", media_type="application/xml")

    u = next(x for x in users if x["id"] == r["user_id"])
    lang = u["language"]

    if digit == "1":
        status = "taken"
        reply_en = "Thank you. We have recorded that you took it."
        reply_kn_audio = "/static/kannada_thanks.mp3"
    elif digit == "2":
        status = "skipped"
        reply_en = "Okay. We have recorded that you skipped it."
        reply_kn_audio = "/static/kannada_skip.mp3"
    else:
        status = "invalid"
        reply_en = "Invalid input received."
        reply_kn_audio = None

    # 🔥 STORE IN LOGS 🔥
    db_logs.append({
        "id": str(uuid.uuid4()),
        "time": datetime.now().isoformat(),
        "status": status,
        "reminder_id": reminder_id,
        "user_id": r["user_id"],
        "type": r["type"]
    })

    # RESPONSE
    if lang == "kn" and reply_kn_audio:
        xml = f"<Response><Play>{reply_kn_audio}</Play></Response>"
    else:
        xml = f"<Response><Say voice='Polly.Aditi'>{reply_en}</Say></Response>"

    return Response(xml, media_type="application/xml")
