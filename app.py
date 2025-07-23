from flask import Flask, request, redirect, url_for, render_template, session, flash
import time
import random
import os
import sqlite3
# import discord
# import asyncio
# from threading import Thread

# ─── Flask Setup ───────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = 'your_super_secret_key'  # Needed for sessions

# Hardcoded admin credentials for now
ADMIN_USERNAME = 'empyrean'
ADMIN_PASSWORD = 'staffusethis123!'

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
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute("SELECT attack_odds, defend_odds FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()

    if row:
        if roll_type.lower() == 'attack':
            return float(row[0])
        elif roll_type.lower() == 'defend':
            return float(row[1])
    return None

def update_odds(username, roll_type, delta=0.05):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    column = "attack_odds" if roll_type.lower() == "attack" else "defend_odds"
    cursor.execute(f"""
        UPDATE users
        SET {column} = MIN({column} + ?, 0.95)
        WHERE username = ?
    """, (delta, username))

    conn.commit()
    conn.close()

# ─── Flask Routes ──────────────────────────────────────────────────────────────
@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    username = None
    roll_type = None

    if request.method == "POST":
        roll_type = request.form.get("roll_type")
        username = request.form.get("username", "").strip()

        if username:
            odds = get_user_odds(username, roll_type)
            if odds is None:
                result = "User not found or invalid roll type"
            else:
                result = "Success" if random.random() < odds else "Fail"
                if result == "Success":
                    update_odds(username, roll_type)
                # send_to_discord(username, roll_type, result)

    return render_template("index.html", result=result, username=username, roll_type=roll_type)

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
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
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

    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM users ORDER BY username')
    users = c.fetchall()
    conn.close()
    
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
        
        if fighter_type == 'Offensive': attack_odds += 2; defend_odds-=5
        if fighter_type == 'Defensive': defend_odds += 2; attack_odds-=5
        if fighter_type == 'Non-combatant': attack_odds -= 10; defend_odds -= 10
        flash(f'{username} Fighter Type Odds of Attack {attack_odds}% / Defend {defend_odds}%', 'success')
        
        if magic_type == "Mental": defend_odds+=2
        if magic_type == "Elemental": attack_odds+=2
        if magic_type == "Physical": defend_odds+=1; attack_odds+=1
        flash(f'{username} Magic Odds of Attack {attack_odds}% / Defend {defend_odds}%', 'success')
        
        if pre_war_status == "Trained": defend_odds+=2; attack_odds+=2
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
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO users (username, member_group, graduate, leadership, pre_war_status, frontlines, age, magic_type, fighter_type, attack_odds, defend_odds)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (username, member_group, graduate, leadership, pre_war_status, frontlines, age, magic_type, fighter_type, attack_odds, defend_odds))
        conn.commit()
        conn.close()

        flash(f'User {username} added with Attack {attack_odds}% / Defend {defend_odds}%', 'success')
        return redirect(url_for('add_user'))

    return render_template('add_user.html')

@app.route('/admin/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()

    flash('User deleted successfully.', 'success')
    return redirect(url_for('admin_dashboard'))
