from flask import Flask, request
import requests

app = Flask(__name__)

BOT_ID = "8f6741295884416bc63a76c784"

def send_message(text):
    url = "https://api.groupme.com/v3/bots/post"
    data = {
        "bot_id": BOT_ID,
        "text": text
    }
    requests.post(url, json=data)

@app.route("/", methods=["POST"])
def webhook():
    data = request.json

    message = data.get("text", "").lower()

    if message == "!hello":
        send_message("Hello from your bot!")

    elif message == "!help":
        send_message("Try !hello")

    return "ok", 200

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
