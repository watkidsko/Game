from flask import Flask, render_template, request, redirect, url_for, jsonify
import threading
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

app = Flask(__name__)

# In-memory data for dashboard (replace with persistent storage as needed)
USAGE_STATS = {
    'total_battles': 0,
    'active_players': 0,
    'custom_characters': 0,
    'custom_bosses': 0,
}
API_KEYS = {
    'openai': os.environ.get('OPENAI_API_KEY', 'Not Set'),
    'other_ai': os.environ.get('OTHER_AI_KEY', 'Not Set'),
}
ADMIN_PASSWORD = os.environ.get('DASHBOARD_ADMIN_PASS', 'admin')

# These will be shared with the bot
DASHBOARD_DATA = {
    'characters': [],
    'bosses': [],
}

@app.route('/')
def dashboard():
    return render_template('dashboard.html', usage=USAGE_STATS, api_keys=API_KEYS, characters=DASHBOARD_DATA['characters'], bosses=DASHBOARD_DATA['bosses'])

@app.route('/api/usage')
def api_usage():
    return jsonify(USAGE_STATS)

@app.route('/api/characters')
def api_characters():
    return jsonify(DASHBOARD_DATA['characters'])

@app.route('/api/bosses')
def api_bosses():
    return jsonify(DASHBOARD_DATA['bosses'])

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        pw = request.form.get('password')
        if pw != ADMIN_PASSWORD:
            return 'Unauthorized', 403
        # Add admin character or boss
        if 'add_character' in request.form:
            char = {
                'emoji': request.form['emoji'],
                'name': request.form['name'],
                'hp': int(request.form['hp']),
                'atk': int(request.form['atk']),
                'skills': [s.strip() for s in request.form['skills'].split(',')],
            }
            DASHBOARD_DATA['characters'].append(char)
        if 'add_boss' in request.form:
            boss = {
                'emoji': request.form['boss_emoji'],
                'name': request.form['boss_name'],
                'hp': int(request.form['boss_hp']),
                'atk': int(request.form['boss_atk']),
                'skills': [s.strip() for s in request.form['boss_skills'].split(',')],
            }
            DASHBOARD_DATA['bosses'].append(boss)
        return redirect(url_for('admin'))
    return render_template('admin.html', characters=DASHBOARD_DATA['characters'], bosses=DASHBOARD_DATA['bosses'])

# Utility to start Flask in a thread
def run_dashboard():
    app.run(host='0.0.0.0', port=5000)

def start_dashboard_thread():
    t = threading.Thread(target=run_dashboard, daemon=True)
    t.start()

# To be called from bot.py on startup
if __name__ == '__main__':
    start_dashboard_thread()
    print('Dashboard running on http://localhost:5000')
