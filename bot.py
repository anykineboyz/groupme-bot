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
SPAM_WINDOW = 15
QUIET_WARNING_COOLDOWN = 90

IMMUNE_USERS = {
    "ethan",
    "breyden",
    "sidney",
    "jacob",
    "zach"
}

GENERAL_BANNED_WORDS = [
    "fuck",
    "bitch",
    "nigga",
    "nigger",
    "retard",
    "faggot",
    "shit",
    "fagget"
]

NIKO_ONLY_BANNED_WORDS = [
    "eva",
    "rene",
    "brendon",
    "drill sergeant",
    "clanker",
    "shh",
    "die",
    "kill",
    "stupid",
    "dumb",
    "mom",
    "dad",
    "shhh",
    "idiot",
    "ass",
    "shut",
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

# -----------------------------
# STORAGE
# -----------------------------
user_activity = {}
warnings = {}
niko_message_count = {}
quiet_users = {}

stop_active = False

# prevents repeated admin alerts
five_warnings_alerted = set()

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
# CHECK IMMUNITY
# -----------------------------
def is_immune(name):

    return any(
        user in name.lower()
        for user in IMMUNE_USERS
    )

# -----------------------------
# ADD WARNING
# -----------------------------
def add_warning(name):

    if is_immune(name):
        return

    warnings[name] = warningss.get(name, 0) + 1

    warnings = warnings[name]

    if warnings == 1:

        send_message(
            f"{name}, this is your first warning. The limit is 5."
        )

    elif warnings == 2:

        send_message(
            f"{name}, this is your second warning. Be careful about your actions."
        )

    elif warnings == 3:

        send_message(
            f"{name}, you now have 3 warnings. Watch your behavior."
        )

    elif warnings == 4:

        send_message(
            f"{name}, you now have 4 warnings. One more  will alert section leaders, and they will most likely remove you."
        )

    elif warnings >= 5:

        if name not in five_warnings_alerted:

            send_message(
                f"⚠️ Ethan Vera and Breyden: {name} has reached 5 warnings. Please proceed to remove him."
            )

            five_warnings_alerted.add(name)

# -----------------------------
# REMOVE WARNING
# -----------------------------
def remove_warning(name):

    if name not in warnings:
        warnings[name] = 0

    if warnings[name] > 0:
        warnings[name] -= 1

# -----------------------------
# WEBHOOK
# -----------------------------
@app.route("/", methods=["POST"])
def webhook():

    global stop_active

    data = request.json

    if not data:
        return "ok", 200

    # ignore bot messages
    if data.get("sender_type") == "bot":
        return "ok", 200

    message = data.get("text", "").strip()
    message_lower = message.lower()

    name = data.get("name", "Unknown")
    name_lower = name.lower()

    user_id = data.get("user_id")

    now = time()

    # -----------------------------
    # STOP TRACKING
    # -----------------------------
    if stop_active:

        if "niko" in name_lower:

            send_message(
                "Niko ignored STOP and received a warning."
            )

            add_warning(name)

        stop_active = False

    # -----------------------------
    # ADMIN COMMANDS
    # -----------------------------
    if is_immune(name):

        # /addwarning NAME
        if message_lower.startswith("/addwarning "):

            target = message[9:].strip()

            if target:

                add_warning(target)

                send_message(
                    f"{target} received a warning."
                )

            return "ok", 200

        # /removewarning NAME
        elif message_lower.startswith("/removewarning "):

            target = message[12:].strip()

            if target:

                remove_warning(target)

                send_message(
                    f"Removed one warning from {target}."
                )

            return "ok", 200

    # -----------------------------
    # COMMANDS
    # -----------------------------
    if message_lower == "/rules":

        send_message(RULES)
        return "ok", 200

    elif message_lower == "hello":

        send_message(f"Hi {name}!")
        return "ok", 200

    elif message_lower == "/warnings":

        if is_immune(name):

            send_message(
                f"{name}, you nomore warnings buggah, u chilling."
            )

        else:

            send_message(
                f"{name}, you have {warnings.get(name, 0)} warnings."
            )

        return "ok", 200

    elif message_lower == "stop":

        send_message(
            "Remember Niko, STOP means STOP. Do not send another message or you will receive a warning."
        )

        stop_active = True
        return "ok", 200

    elif "boss" in message_lower:

        send_message("Good boy, Niko!")
        return "ok", 200

    # -----------------------------
    # NIKO MESSAGE COUNTER
    # -----------------------------
    if "niko" in name_lower:

    niko_message_count[name] = (
        niko_message_count.get(name, 0) + 1
    )

    if niko_message_count[name] % 20 == 0:

        send_message(
            "Niko, please be considerate of others and try not to chat too much."
        )

    # -----------------------------
    # GENERAL PROFANITY
    # -----------------------------
    for word in GENERAL_BANNED_WORDS:

        if re.search(rf"\b{re.escape(word)}\b", message_lower):

            send_message(
                f"{name}, watch your language and follow the rules."
            )

            add_warning(name)
            break

    # -----------------------------
    # NIKO ONLY WORDS
    # -----------------------------
    if "niko" in name_lower:

        for word in NIKO_ONLY_BANNED_WORDS:

            if re.search(rf"\b{re.escape(word)}\b", message_lower):

                send_message(
                    f"{name}, watch your language."
                )

                add_warning(name)
                break

    # -----------------------------
    # SPAM DETECTION
    # -----------------------------
    if user_id:

        if user_id not in user_activity:
            user_activity[user_id] = []

        user_activity[user_id] = [
            t for t in user_activity[user_id]
            if now - t < SPAM_WINDOW
        ]

        user_activity[user_id].append(now)

        if len(user_activity[user_id]) > SPAM_LIMIT:

            send_message(
                f"{name}, stop spamming the chat."
            )

            add_warning(name)

    # -----------------------------
    # QUIET HOURS
    # 12:00 AM -> 6:30 AM
    # -----------------------------
    hawaii_time = datetime.now(
        ZoneInfo("Pacific/Honolulu")
    )

    current = (
        hawaii_time.hour
        + hawaii_time.minute / 60
    )

    if current < 6.5:

        if (
            name not in quiet_users
            or now - quiet_users[name]
            > QUIET_WARNING_COOLDOWN
        ):

            send_message(
                f"{name}, please don't message between 12 AM and 6:30 AM. Goodnight!"
            )

            quiet_users[name] = now
             return "ok", 200

# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )
