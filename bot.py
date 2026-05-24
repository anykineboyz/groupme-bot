from flask import Flask, request
import requests

app = Flask(__name__)

BOT_ID = "cc3d639a659583736f23c3858f"

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
    app.run(port=5000)