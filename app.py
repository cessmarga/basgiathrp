from flask import Flask, render_template, request
import time
import random
import requests
import os

app = Flask(__name__)

def send_to_discord(username, roll_type, result):
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    message = f"🎲 **{username}** rolled **{roll_type}** → **{result}**"
    payload = {"content": message}

    for attempt in range(3):  # Try up to 3 times
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 429:
            try:
                data = response.json()
                retry_after = data.get("retry_after", 2000)  # fallback ms
            except ValueError:
                retry_after = 2000  # default to 2s if not JSON
            print(f"🔁 Rate limited. Retrying after {retry_after}ms...")
            time.sleep(retry_after / 1000)
        else:
            try:
                response.raise_for_status()
                print("✅ Webhook sent!")
                return
            except requests.HTTPError as e:
                print(f"❌ HTTP error: {e} - {response.text}")
                return
    raise Exception("❌ Failed to send webhook after 3 retries")

@app.route("/", methods=["GET", "POST"])
def index():
        result = None
        username = None
        roll_type = None

        if request.method == "POST":
            roll_type = request.form.get("roll_type")
            username = request.form.get("username", "").strip()

            if username:
                result = "Success" if random.random() < 0.5 else "Fail"
                send_to_discord(username, roll_type, result)

        return render_template("index.html", result=result, username=username, roll_type=roll_type)

if __name__ == "__main__":
        app.run(debug=True)
