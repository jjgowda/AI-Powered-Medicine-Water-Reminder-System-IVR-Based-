from twilio.rest import Client
import os


# 🔴 Hardcoded for now (OK for demo)
ACCOUNT_SID = ""
AUTH_TOKEN = ""
FROM_NUMBER = ""




client = Client(ACCOUNT_SID, AUTH_TOKEN)

def make_call(user, reminder):
    """
    reminder can be:
    - medicine reminder
    - water reminder
    """

    to_number = user["phone"]

    # Decide URL params based on type
    if reminder["type"] == "water":
        query = f"reminder_id={reminder['id']}"
        label = "WATER"
    else:
        query = f"reminder_id={reminder['id']}"
        label = f"MEDICINE ({reminder.get('name', '')})"

    print(
        f"📡 Placing call [{label}] | "
        f"User={user['name']} | Phone={to_number}"
    )

    call = client.calls.create(
        to=to_number,
        from_=FROM_NUMBER,
        url=f"https://ununionized-matilda-unofficiously.ngrok-free.dev/voice?{query}",
        method="POST"
    )

    return call.sid
