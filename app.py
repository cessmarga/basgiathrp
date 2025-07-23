from flask import Flask, render_template, request
import time
import random
import requests
import os

app = Flask(__name__)

def send_to_discord(username, roll_type, result):
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    
    if not webhook_url:
        raise ValueError("❌ Discord webhook URL is not set in environment variables.")
    
    message = f"🎲 **{username}** rolled **{roll_type}** → **{result}**"
    payload = {"content": message}

    print("Sending payload:", payload)
    if os.getenv("FLASK_ENV") == "development":
        print("Webhook URL:", webhook_url)

    for attempt in range(3):  # Try up to 3 times
        try:
            response = requests.post(webhook_url, json=payload)
            print(f"{response.status_code} - {response.text}")
            
            if response.status_code == 204:
                print("✅ Webhook sent successfully!")
                return
            
            elif response.status_code == 429:
                try:
                    data = response.json()
                    retry_after = data.get("retry_after", 2000)
                except ValueError:
                    retry_after = 2000
                print(f"🔁 Rate limited. Retrying after {retry_after}ms...")
                time.sleep(retry_after / 1000)

            elif 400 <= response.status_code < 500:
                print(f"❌ Client error {response.status_code}: {response.text}")
                break  # Do not retry client errors except 429

            else:
                print(f"⚠️ Server error {response.status_code}: {response.text}")
                time.sleep(2)

        except requests.RequestException as e:
            print(f"❌ Request failed: {e}")
            time.sleep(2)

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
