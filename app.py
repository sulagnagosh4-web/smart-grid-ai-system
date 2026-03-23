import sqlite3
import csv
import io
import os
import random
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'smart_grid_final_omni_secure_2026'

# --- DATABASE PATHING (Crucial for Cloud Deployment) ---
# This locates the database file relative to this script's location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "energy_data.db")

def init_db():
    """Initializes the SQLite database with User and Energy tables."""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS users 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                             username TEXT UNIQUE, 
                             password TEXT)''')
            conn.execute('''CREATE TABLE IF NOT EXISTS records 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                             timestamp TEXT, 
                             energy REAL)''')
    except Exception as e:
        print(f"Database Init Error: {e}")

init_db()

# --- AUTHENTICATION HELPER ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- ROUTES ---

@app.route('/')
@login_required
def index():
    return render_template('dashboard.html', user=session['user'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username')
        p = request.form.get('password')
        with sqlite3.connect(DB_NAME) as conn:
            user = conn.execute("SELECT password FROM users WHERE username = ?", (u,)).fetchone()
        
        if user and check_password_hash(user[0], p):
            session['user'] = u
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u = request.form.get('username')
        p = request.form.get('password')
        try:
            with sqlite3.connect(DB_NAME) as conn:
                conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                             (u, generate_password_hash(p)))
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Error: Username already exists."
    return render_template('register.html')

@app.route('/api/data')
@login_required
def get_data():
    sector = request.args.get('sector', 'Residential')
    
    # --- 1. WEATHER ENGINE SIMULATION ---
    weather_options = [
        {"type": "Sunny", "temp": "32°C", "solar_eff": 1.0, "load_mult": 1.0, "icon": "☀️"},
        {"type": "Cloudy", "temp": "24°C", "solar_eff": 0.35, "load_mult": 1.15, "icon": "☁️"},
        {"type": "Stormy", "temp": "18°C", "solar_eff": 0.05, "load_mult": 1.45, "icon": "⛈️"},
        {"type": "Heatwave", "temp": "42°C", "solar_eff": 1.15, "load_mult": 1.75, "icon": "🔥"}
    ]
    current_weather = random.choice(weather_options)

    # --- 2. DATA RETRIEVAL ---
    with sqlite3.connect(DB_NAME) as conn:
        # Get last 25 readings to show on the chart
        rows = conn.execute("SELECT timestamp, energy FROM records ORDER BY id DESC LIMIT 25").fetchall()
    
    records = []
    anomaly_detected = False
    
    for r in reversed(rows):
        val = r[1]
        
        # --- 3. SECTOR LOAD LOGIC ---
        if sector == 'Industrial': 
            val = val * 1.95 + 45
        elif sector == 'Commercial': 
            val = val * 1.35 + 18
        
        # Apply Weather Impact
        val = val * current_weather['load_mult']
        
        # --- 4. CYBERSECURITY ANOMALY DETECTION (HEURISTICS) ---
        # Heuristic: If load spikes > 165kWh unexpectedly in non-industrial sectors
        if sector != 'Industrial' and val > 165:
            anomaly_detected = True
            
        records.append({"timestamp": r[0], "energy": round(val, 2)})

    # --- 5. AI FORECASTING (Simple Linear Regression / SMA) ---
    if len(records) > 5:
        # Predict next value based on trend of last 5
        avg_recent = sum([rec['energy'] for rec in records[-5:]]) / 5
        prediction = avg_recent + 1.5 
    else:
        prediction = 0

    return jsonify({
        "records": records, 
        "prediction": round(prediction, 2), 
        "weather": current_weather,
        "security_alert": anomaly_detected,
        "status": "Healthy" if not anomaly_detected else "Threat Detected"
    })

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/download/report')
@login_required
def download_report():
    with sqlite3.connect(DB_NAME) as conn:
        rows = conn.execute("SELECT timestamp, energy FROM records").fetchall()
    
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['Timestamp', 'Usage (kWh)'])
    cw.writerows(rows)
    
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=grid_audit_log.csv"
    output.headers["Content-type"] = "text/csv"
    return output

if __name__ == '__main__':
    # host='0.0.0.0' allows local network sharing (Option 3 from earlier)
    app.run(debug=True, host='0.0.0.0', port=5000)