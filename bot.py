from flask import Flask, request
import requests
from time import time
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import re

app = Flask(__name__)

# -----------------------------
# CONFIG
# -----------------------------
BOT_ID = os.environ.get("BOT_ID")

SPAM_LIMIT = 5
SPAM_WINDOW = 5
QUIET_WARNING_COOLDOWN = 1800  # 30 min

IMMUNE_USERS = {
    "ethan",
    "breyden",
    "sidney",
    "jacob"
}

BANNED_WORDS = [
    "fuck",
    "bitch",
    "die",
    "kill",
    "nigga",
    "nigger",
    "retard",
    "faggot",
    "eva",
    "rene",
    "brendon",
    "drill sergeant",
    "clanker",
    "shhh",
]

RULES = """
GROUPCHAT RULES

1. Use your real name/nickname.
2. No swearing or inappropriate content.
3. No NSFW content.
4. Respect everyone.
5. No spam.
6. Avoid messaging too early or too late.
7. No impersonation.
8. Stop means stop.
"""

user_activity = {}
niko_marks = {}
niko_message_count = {}
quiet_users = {}
stop_active = False

# -----------------------------
# SEND MESSAGE
# -----------------------------
def send_message(text):
    if not BOT_ID:
        print("BOT_ID missing")
        return

    requests.post(
        "https://api.groupme.com/v3/bots/post",
        json={
            "bot_id": BOT_ID,
            "text": text
        }
    )

# -----------------------------
# NIKO MARKS
# -----------------------------
def add_niko_mark(name):

    if any(user in name.lower() for user in IMMUNE_USERS):
        return

    niko_marks[name] = niko_marks.get(name,0) + 1

    if niko_marks[name] == 2:
        send_message(
            f"{name}, this is your second Niko Mark."
        )

    elif niko_marks[name] >= 3:
        send_message(
            f"{name} has received 3 Niko Marks. EJ, Breyden and possibly the drum majors will be notified. They and/or Mr. Otsuka will decide your consequences."
        )

# -----------------------------
# WEBHOOK
# -----------------------------
@app.route("/", methods=["POST"])
def webhook():

    global stop_active

    data = request.json

    if not data:
        return "ok",200

    if data.get("sender_type") == "bot":
        return "ok",200

    message = data.get("text","").lower().strip()
    name = data.get("name","Unknown")
    name_lower = name.lower()
    user_id = data.get("user_id")

    now = time()

    # -----------------------------
    # STOP TRACKING
    # -----------------------------
    if stop_active:

        if "niko" in name_lower:
            send_message(
                "Niko ignored STOP and received a Niko Mark."
            )
            add_niko_mark(name)

        stop_active = False

    # -----------------------------
    # COMMANDS
    # -----------------------------
    if message == "/rules":
        send_message(RULES)
        return "ok",200

    elif message == "hello":
        send_message(f"Hi {name}!")
        return "ok",200

    elif message == "/nikomarks":

        if any(user in name_lower for user in IMMUNE_USERS):
            send_message(
                f"{name}, you are immune to Niko Marks."
            )
        else:
            send_message(
                f"{name}, you have {niko_marks.get(name,0)} Niko Marks."
            )

        return "ok",200

    elif message == "stop":

        send_message(
            "Remember Niko, STOP means STOP. Do not send another message or you will receive a Niko Mark."
        )

        stop_active=True
        return "ok",200

    elif "boss" in message:
        send_message("Good boy, Niko!")
        return "ok",200

    # -----------------------------
    # NIKO MESSAGE COUNTER
    # -----------------------------
    if "niko" in name_lower:

        niko_message_count[name] = (
            niko_message_count.get(name,0)+1
        )

        if niko_message_count[name] % 13 == 0:
            send_message(
                "Niko, be considerate of others and try not to chat too much."
            )

    # -----------------------------
    # PROFANITY
    # -----------------------------
    for word in BANNED_WORDS:

        if re.search(rf"\b{re.escape(word)}\b",message):
            send_message(
                f"{name}, watch your language and follow the rules."
            )
            add_niko_mark(name)
            break

    # -----------------------------
    # SPAM DETECTION
    # -----------------------------
    if user_id:

        if user_id not in user_activity:
            user_activity[user_id]=[]

        user_activity[user_id]=[
            t for t in user_activity[user_id]
            if now-t<SPAM_WINDOW
        ]

        user_activity[user_id].append(now)

        if len(user_activity[user_id]) > SPAM_LIMIT:
            send_message(
                f"{name}, stop spamming the chat."
            )
            add_niko_mark(name)

    # -----------------------------
    # QUIET HOURS
    # -----------------------------
    hawaii_time = datetime.now(
        ZoneInfo("Pacific/Honolulu")
    )

    current = hawaii_time.hour + hawaii_time.minute/60

    if current >= 21.5 or current < 6.5:

        if (
            name not in quiet_users
            or now - quiet_users[name]
            > QUIET_WARNING_COOLDOWN
        ):

            send_message(
                f"{name}, please avoid messaging between 9:30 PM and 6:30 AM."
            )

            quiet_users[name]=now
            add_niko_mark(name)

    return "ok",200

# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":

    port=int(os.environ.get("PORT",5000))

    app.run(
        host="0.0.0.0",
        port=port
    )

