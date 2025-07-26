from flask import Flask, request, redirect, url_for, render_template, session, flash, send_file
from flask_sqlalchemy import SQLAlchemy
import time
import random
import os
# import discord
# import asyncio
# from threading import Thread

# ─── Flask Setup ───────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = 'your_super_secret_key'  # Needed for sessions

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    member_group = db.Column(db.String)
    graduate = db.Column(db.String)
    leadership = db.Column(db.String)
    pre_war_status = db.Column(db.String)
    frontlines = db.Column(db.String)
    disability = db.Column(db.String)
    age = db.Column(db.Integer)
    magic_type = db.Column(db.String)
    fighter_type = db.Column(db.String)
    attack_success = db.Column(db.Float)
    defend_success = db.Column(db.Float)
    attack_odds = db.Column(db.Float)
    defend_odds = db.Column(db.Float)

# ─── Discord Bot Setup (Disabled) ──────────────────────────────────────────────
# intents = discord.Intents.default()
# client = discord.Client(intents=intents)
# DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", 1234567890))  # Replace later
# DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
# bot_ready = asyncio.Event()

# @client.event
# async def on_ready():
#     print(f"✅ Logged in as {client.user}")
#     bot_ready.set()

# def send_to_discord(username, roll_type, result):
#     message = f"🎲 **{username}** rolled **{roll_type}** → **{result}**"

#     async def send():
#         await bot_ready.wait()
#         channel = client.get_channel(DISCORD_CHANNEL_ID)
#         if channel:
#             await channel.send(message)
#         else:
#             print("❌ Could not find Discord channel.")

#     asyncio.run_coroutine_threadsafe(send(), client.loop)

# ─── Odds System ────────────────────────────────────────────────────────────────
def get_user_odds(username, roll_type):
    user = User.query.filter_by(username=username).first()
    if not user:
        return None
    return (getattr(user, f"{roll_type.lower()}_odds", None) + getattr(user, f"{roll_type.lower()}_success", None))

def update_odds(username, roll_type, random_value):
    user = User.query.filter_by(username=username).first()
    if user:
        success_attr = f"{roll_type.lower()}_success"
        current_success = getattr(user, success_attr, 0)

        # Add random value
        new_success = current_success + (random_value / 10)

        # Combine with base odds and clamp
        base_odds = getattr(user, f"{roll_type.lower()}_odds", 0)
        total = base_odds + new_success
        total = min(max(total, 10), 90)  # Clamp between 10 and 90

        # Adjust only the success value so that total stays in range
        new_success = total - base_odds
        setattr(user, f"{roll_type.lower()}_success", new_success)
        
        db.session.commit()

# ─── Flask Routes ──────────────────────────────────────────────────────────────
@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    username = None
    roll_type = None
    random_value = None
    user_odds = None
    final_odds = None

    if request.method == "POST":
        roll_type = request.form.get("roll_type")
        username = request.form.get("username", "").strip()

        if username:
            odds = get_user_odds(username, roll_type)

            if odds is None:
                result = "User not found or invalid roll type"
            else:
                user_odds = {
                    "attack": get_user_odds(username, "attack"),
                    "defend": get_user_odds(username, "defend")
                }
                # Step 1: Generate random value
                random_value = round(random.random(), 4)

                # Step 2: Determine success
                result = "Success" if random_value < (odds / 100) else "Fail"

                # Step 3: If success, add random_value to odds
                if result == "Success":
                    update_odds(username, roll_type, random_value)
                else:
                    final_odds = odds  # No change on fail

    return render_template("index.html",
                           result=result,
                           username=username,
                           roll_type=roll_type,
                           random_value=random_value,
                           final_odds=final_odds,
                           user_odds=user_odds)

# ─── Run Flask Only (Discord Bot Disabled) ─────────────────────────────────────
if __name__ == "__main__":
    # Thread(target=run_bot).start()
    app.run(debug=True)

# ─── Admin Things for the Sparring Proctor ─────────────────────────────────────
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == os.getenv('ADMIN_USERNAME') and password == os.getenv('ADMIN_PASSWORD'):
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials', 'error')
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('Logged out', 'info')
    return redirect(url_for('admin_login'))

@app.route('/admin')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    users = User.query.order_by(User.username).all()
    return render_template('admin_dashboard.html', users=users)

@app.route('/admin/add_user', methods=['GET', 'POST'])
def add_user():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        username = request.form['username']
        member_group = request.form['member_group']
        graduate = request.form['graduate']
        leadership = request.form['leadership']
        pre_war_status = request.form['pre_war_status']
        frontlines = request.form['frontlines']
        disability = request.form['disability']
        age = int(request.form['age'])
        magic_type = request.form['magic_type']
        fighter_type = request.form['fighter_type']

        # === Calculate default odds ===
        base_odds = {
            "Rider": (65, 65),
            "Flier": (60, 60),
            "Infantry": (55, 60),
            "Healer": (40, 60),
            "Scribe": (35, 50),
            "Civilian": (30, 40),
            "Outlier": (50, 50),
        }
        
        attack_odds, defend_odds = base_odds.get(member_group, (0.5, 0.5))  # fallback default
        flash(f'{username} Base Odds of Attack {attack_odds}% / Defend {defend_odds}%', 'success')

        if graduate == "yes": attack_odds += 5; defend_odds += 5
        flash(f'{username} Graduate Odds of Attack {attack_odds}% / Defend {defend_odds}%', 'success')
        
        if leadership == "yes": attack_odds += 2; defend_odds += 2
        flash(f'{username} Leadership Odds of Attack {attack_odds}% / Defend {defend_odds}%', 'success')

        if frontlines == "yes": attack_odds += 5; defend_odds += 5
        flash(f'{username} Frontlines Odds of Attack {attack_odds}% / Defend {defend_odds}%', 'success')

        if disability == "yes": attack_odds -= 3; defend_odds -= 3
        flash(f'{username} Disability Odds of Attack {attack_odds}% / Defend {defend_odds}%', 'success')
        
        if fighter_type == 'Offensive': attack_odds += 2; defend_odds-=5
        if fighter_type == 'Defensive': defend_odds += 2; attack_odds-=5
        if fighter_type == 'Non-combatant': attack_odds -= 10; defend_odds -= 10
        flash(f'{username} Fighter Type Odds of Attack {attack_odds}% / Defend {defend_odds}%', 'success')
        
        if magic_type == "Mental": defend_odds+=2
        if magic_type == "Elemental": attack_odds+=2
        if magic_type == "Physical": defend_odds+=1; attack_odds+=1
        flash(f'{username} Magic Odds of Attack {attack_odds}% / Defend {defend_odds}%', 'success')
        
        if pre_war_status == "Trained": defend_odds+=2; attack_odds+=2
        if pre_war_status == "Untrained": defend_odds-=1; attack_odds-=1
        flash(f'{username} Legacy Odds of Attack {attack_odds}% / Defend {defend_odds}%', 'success')
        

        if age < 40:
            attack_odds += 1
            defend_odds -= 2
        elif age > 40:
            attack_odds -= 2
            defend_odds += 1

        flash(f'{username} Age Odds of Attack {attack_odds}% / Defend {defend_odds}%', 'success')

        # Clamp odds between 10 and 100
        attack_odds = min(max(attack_odds, 10), 90)
        defend_odds = min(max(defend_odds, 10), 90)

        # Save to database
        user = User(
            username=username,
            member_group=member_group,
            graduate=graduate,
            leadership=leadership,
            pre_war_status=pre_war_status,
            frontlines=frontlines,
            disability=disability,
            age=age,
            magic_type=magic_type,
            fighter_type=fighter_type,
            attack_odds=attack_odds,
            defend_odds=defend_odds
        )
        db.session.add(user)
        db.session.commit()

        flash(f'User {username} added with Attack {attack_odds}% / Defend {defend_odds}%', 'success')
        return redirect(url_for('add_user'))

    return render_template('add_user.html')

@app.route('/admin/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        
    return redirect(url_for('admin_dashboard'))

@app.route('/download-db')
def download_db():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    try:
        return send_file('users.db', as_attachment=True)
    except FileNotFoundError:
        return "Database file not found.", 404
