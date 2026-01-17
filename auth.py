from fastapi import HTTPException
from utils.json_db import read_json, append_json
from utils.security import hash_password, verify_password
import uuid

def register_user(name, phone, password):
    users = read_json("users.json")

    for u in users:
        if u["phone"] == phone:
            raise HTTPException(status_code=400, detail="User already exists")

    user = {
        "id": str(uuid.uuid4()),
        "name": name,
        "phone": phone,
        "password": hash_password(password)
    }

    append_json("users.json", user)
    return {"message": "User registered successfully"}

def login_user(phone, password):
    users = read_json("users.json")

    for u in users:
        if u["phone"] == phone and verify_password(password, u["password"]):
            return {
                "message": "Login successful",
                "user_id": u["id"]
            }

    raise HTTPException(status_code=401, detail="Invalid credentials")
