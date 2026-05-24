from flask import Flask, request
import requests
from time import time
import os

app = Flask(__name__)

BOT_ID = "8f6741295884416bc63a76c784"

user_activity = {}
user_counts = {}

TARGET_NAME = "lone wolf niko"

def send_message(text):
    requests.post(
        "https://api.groupme.com/v3/bots/post",
        json={"bot_id": BOT_ID, "text": text}
    )

@app.route("/", methods=["POST"])
def webhook():
    data = request.json

    if not data:
        return "no data", 200

    message = data.get("text", "").lower()
  def webhook():
    name = data.get("name")
    user_id = data.get("user_id")
    now = time()

    # --- simple command ---
    if message == "hello":
        send_message("Shut up, Niko")

    elif message == "":
        send_message("Try hello")

    # --- spam tracking (by user_id) ---
    if user_id:
        if user_id not in user_activity:
            user_activity[user_id] = []

        user_activity[user_id] = [
            t for t in user_activity[user_id] if now - t < 5
        ]

        user_activity[user_id].append(now)

        if len(user_activity[user_id]) > 5:
            send_message("Don't spam the chat, Niko")
            return "ok", 200

    # --- name-based tracking ---
    if name:
        if name not in user_counts:
            user_counts[name] = 0

        user_counts[name] += 1

        if name == TARGET_NAME and user_counts[name] % 3 == 0:
            send_message("Niko, calm down")

    return "ok", 200

if name == "lone wolf niko":
    send_message("Shut up, Niko")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
