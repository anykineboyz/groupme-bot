from flask import Flask, request
import requests
from time import time, sleep
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import re
import threading
import random

app = Flask(__name__)

# -----------------------------
# CONFIG
# -----------------------------

BOT_ID = os.environ.get("BOT_ID")

SPAM_LIMIT = 5
SPAM_WINDOW = 15
QUIET_WARNING_COOLDOWN = 90

# Daily quote time
# 7:50 AM Hawaii time
DAILY_QUOTE_HOUR = 7
DAILY_QUOTE_MINUTE = 50

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
    "hehe",
    "haha",
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
    "uncle",
    "aunty",
    "what",
    "no",
    "stop",
    "fine",
    "why"
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
# DAILY INSPIRATIONAL QUOTES
# -----------------------------

INSPIRATIONAL_QUOTES = [
    ("Success is the sum of small efforts, repeated day in and day out.", "Robert Collier"),
    ("We fall, but we get up because the ground is no place for a champion.", "Dustin Poirier"),
    ("Believe you can and you're halfway there.", "Theodore Roosevelt"),
    ("The secret of getting ahead is getting started.", "Mark Twain"),
    ("I don’t celebrate my victories too much because I’m always looking forward to the next challenge.", "Jon Jones"),
    ("Great things are done by a series of small things brought together.", "Vincent van Gogh"),
    ("It always seems impossible until it's done.", "Nelson Mandela"),
    ("I’m not the best. I just believe I can do things other people think are impossible.", "Anderson Silva"),
    ("The future depends on what you do today.", "Mahatma Gandhi"),
    ("Hardships often prepare ordinary people for an extraordinary destiny.", "C.S. Lewis"),
    ("You don't have to be great to start, but you have to start to be great.", "Zig Ziglar"),
    ("A little progress each day adds up to big results.", "Palm Beach Pete"),
    ("If you want to be the best, you’ve got to beat the best, and the best is Blessed, baby.", "Max Holloway"),
    ("Your only limit is your mind.", "Kent Sato"),
    ("Keep going. Your future self will thank you.", "Ethan Vera"),
    ("Difficult roads often lead to beautiful destinations.", "Breyden Lacar"),
    ("Small steps every day.", "Hardeep Saluja"),
    ("Be stronger than your excuses.", "Ahren Awong"),
    ("Make today count.", "Joseph Holtzmann"),
    ("Progress, not perfection.", "Clement Zhang"),
    ("The harder you work for something, the greater you'll feel when you achieve it.", "Hideki Tojo"),
    ("I always have doubts. I'm always afraid. But that's what makes someone courageous.", "Georges St-Pierre"),
    ("You have to believe in yourself and believe that you can do anything.", "Amanda Nunes"),
    ("Blessed is a mindset.", "Max Holloway"),
    ("There is no substitute for hard work.", "Michael Chandler"),
    ("We are here to take over.", "Conor McGregor"),
    ("You have to work hard every day if you want to be the best.", "Islam Makhachev"),
    ("I train hard, I fight easy.", "Khabib Nurmagomedov"),
    ("I've always believed that if you work hard enough, good things will happen.", "Dustin Poirier"),
    ("The more you learn, the more you realize how much you don't know.", "Georges St-Pierre"),
    ("You have to keep moving forward and never give up.", "Alex Pereira"),
    ("I want to be remembered as someone who never gave up.", "Jon Jones"),
    ("You can never underestimate what hard work and determination can accomplish.", "Dustin Poirier"),
    ("It is what it is. I just keep moving forward.", "Max Holloway"),
    ("I don't need to be perfect. I just need to be better.", "Israel Adesanya"),
    ("You have to be willing to work harder than everyone else.", "Daniel Cormier"),
    ("You have to believe in yourself before anyone else will.", "Georges St-Pierre")
]

# Quotes that have already been used
used_quotes = set()

# Prevents the quote from being sent twice on the same day
last_quote_date = None

# -----------------------------
# STORAGE
# -----------------------------

user_activity = {}
warnings = {}
niko_message_count = {}
quiet_users = {}

stop_active = False

# Prevents repeated admin alerts
five_warnings_alerted = set()

# -----------------------------
# SEND MESSAGE
# -----------------------------

def send_message(text):

    if not BOT_ID:
        print("BOT_ID missing")
        return

    try:
        response = requests.post(
            "https://api.groupme.com/v3/bots/post",
            json={
                "bot_id": BOT_ID,
                "text": text
            },
            timeout=10
        )

        print(
            "GroupMe response:",
            response.status_code
        )

    except Exception as error:
        print(
            "Error sending GroupMe message:",
            error
        )

# -----------------------------
# DAILY QUOTE
# -----------------------------

def send_daily_quote():

    global used_quotes
    global last_quote_date

    hawaii_time = datetime.now(
        ZoneInfo("Pacific/Honolulu")
    )

    today = hawaii_time.date()

    # Don't send more than once per day
    if last_quote_date == today:
        return

    # Wait until 7:50 AM
    if hawaii_time.hour < DAILY_QUOTE_HOUR:
        return

    if (
        hawaii_time.hour == DAILY_QUOTE_HOUR
        and hawaii_time.minute < DAILY_QUOTE_MINUTE
    ):
        return

    # If we've used every quote, start over
    if len(used_quotes) >= len(INSPIRATIONAL_QUOTES):
        used_quotes.clear()

    # Pick an unused quote
    available_quotes = [
        quote
        for quote in INSPIRATIONAL_QUOTES
        if quote not in used_quotes
    ]

    quote, author = random.choice(
        available_quotes
    )

    send_message(
        f"🌟 DAILY INSPIRATION 🌟\n\n"
        f"“{quote}”\n"
        f"— {author}"
    )

    used_quotes.add(
        (quote, author)
    )

    last_quote_date = today

    print(
        f"Daily quote sent for {today}: {quote}"
    )

# -----------------------------
# DAILY QUOTE BACKGROUND LOOP
# -----------------------------

def daily_quote_loop():

    print(
        "✅ Daily quote system started."
    )

    while True:

        try:
            send_daily_quote()

        except Exception as error:

            print(
                "Daily quote error:",
                error
            )

        # Check every 30 seconds
        sleep(30)

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

    warnings[name] = (
        warnings.get(name, 0) + 1
    )

    count = warnings[name]

    if count == 1:

        send_message(
            f"{name}, this is your first warning. The limit is 5."
        )

    elif count == 2:

        send_message(
            f"{name}, this is your second warning. Be careful about your actions."
        )

    elif count == 3:

        send_message(
            f"{name}, you now have 3 warnings. Watch your behavior."
        )

    elif count == 4:

        send_message(
            f"{name}, you now have 4 warnings. One more will alert section leaders, and they will most likely remove you."
        )

    elif count >= 5:

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

    # Ignore bot messages
    if data.get("sender_type") == "bot":
        return "ok", 200

    message = data.get(
        "text",
        ""
    ).strip()

    message_lower = message.lower()

    name = data.get(
        "name",
        "Unknown"
    )

    name_lower = name.lower()

    user_id = data.get(
        "user_id"
    )

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
        if message_lower.startswith(
            "/addwarning "
        ):

            target = message[12:].strip()

            if target:

                add_warning(target)

                send_message(
                    f"{target} received a warning."
                )

            return "ok", 200

        # /removewarning NAME
        elif message_lower.startswith(
            "/removewarning "
        ):

            target = message[15:].strip()

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

        send_message(
            f"Hi {name}!"
        )

        return "ok", 200

    elif message_lower == "/warnings":

        if is_immune(name):

            send_message(
                f"{name}, you no more warnings buggah, u chilling."
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

        send_message(
            "Good boy, Niko!"
        )

        return "ok", 200

    # -----------------------------
    # NIKO MESSAGE COUNTER
    # -----------------------------

    if "niko" in name_lower:

        niko_message_count[name] = (
            niko_message_count.get(
                name,
                0
            ) + 1
        )

        if (
            niko_message_count[name]
            % 10 == 0
        ):

            send_message(
                "Niko, please be considerate of others and try not to chat too much. Chat more and you may receive a warning."
            )

    # -----------------------------
    # GENERAL PROFANITY
    # -----------------------------

    for word in GENERAL_BANNED_WORDS:

        if re.search(
            rf"\b{re.escape(word)}\b",
            message_lower
        ):

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

            if re.search(
                rf"\b{re.escape(word)}\b",
                message_lower
            ):

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
            t
            for t in user_activity[user_id]
            if now - t < SPAM_WINDOW
        ]

        user_activity[user_id].append(
            now
        )

        if (
            len(user_activity[user_id])
            > SPAM_LIMIT
        ):

            send_message(
                f"{name}, stop spamming the chat."
            )

            add_warning(name)

    # -----------------------------
    # QUIET HOURS
    # 10:00 PM -> 6:30 AM
    # -----------------------------

    hawaii_time = datetime.now(
        ZoneInfo("Pacific/Honolulu")
    )

    current = (
        hawaii_time.hour
        + hawaii_time.minute / 60
    )

    if (
        current >= 22
        or current < 6.5
    ):

        if (
            name not in quiet_users
            or now - quiet_users[name]
            > QUIET_WARNING_COOLDOWN
        ):

            send_message(
                f"{name}, please don't message between 10 PM and 6:30 AM. Goodnight!"
            )

            quiet_users[name] = now

            return "ok", 200

    return "ok", 200

# -----------------------------
# START DAILY QUOTE THREAD
# -----------------------------

quote_thread = threading.Thread(
    target=daily_quote_loop,
    daemon=True
)

quote_thread.start()

# -----------------------------
# RUN
# -----------------------------

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
