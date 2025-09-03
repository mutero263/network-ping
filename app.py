import os
import json
import subprocess
import time
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from flask_bcrypt import Bcrypt
import sqlite3
import requests
import netifaces
from scapy.all import ARP, Ether, srp

app = Flask(__name__)
app.secret_key = 'your-secret-key-here' 
bcrypt = Bcrypt(app)

# === DATABASE SETUP ===
DATABASE = 'database/network_monitor.db'

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        # Users
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT
        )''')
        # Ping Logs
        c.execute('''CREATE TABLE IF NOT EXISTS ping_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            target TEXT NOT NULL,
            avg_latency REAL,
            packet_loss REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )''')
        # Uptime Logs
        c.execute('''CREATE TABLE IF NOT EXISTS uptime_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            url TEXT NOT NULL,
            status TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )''')
        # Bandwidth Logs
        c.execute('''CREATE TABLE IF NOT EXISTS bandwidth_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            download REAL,
            upload REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )''')
        conn.commit()

# === UTILITY FUNCTIONS ===

def get_public_ip():
    try:
        return requests.get("https://api.ipify.org", timeout=5).text
    except:
        return "N/A"

def get_local_ip():
    try:
        gateway_iface = netifaces.gateways()['default'][netifaces.AF_INET][1]
        addr = netifaces.ifaddresses(gateway_iface)[netifaces.AF_INET][0]['addr']
        return addr
    except:
        return "127.0.0.1"

def ping_host(target):
    try:
        # Use correct ping command based on OS
        if os.name == 'nt':  # Windows
            cmd = ["ping", "-n", "4", target]
        else:  # Linux/Mac
            cmd = ["ping", "-c", "4", target]

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10
        )
        output = result.stdout

        if os.name == 'nt':  # Windows parsing
            if "Lost = 0" in output:
                for line in output.splitlines():
                    if "Average" in line:
                        try:
                            avg_ms = line.split("Average =")[-1].replace("ms", "").strip()
                            avg = float(avg_ms)
                            return {"avg_latency": avg, "packet_loss": 0.0}
                        except:
                            pass
                return {"avg_latency": 0.0, "packet_loss": 0.0}
            else:
                for line in output.splitlines():
                    if "Packets:" in line:
                        parts = line.split(",")
                        lost = int(parts[2].strip().split()[0])
                        loss_percent = (lost / 4) * 100
                        return {"avg_latency": 999.0, "packet_loss": loss_percent}
                return {"avg_latency": 999.0, "packet_loss": 100.0}
        else:  # Linux/Mac parsing
            if "0% packet loss" in output:
                lines = [l for l in output.splitlines() if "avg" in l]
                if lines:
                    stats = lines[0].split("=")[1].strip().split("/")
                    avg = float(stats[1])
                    return {"avg_latency": avg, "packet_loss": 0.0}
            return {"avg_latency": 999.0, "packet_loss": 100.0}
    except Exception as e:
        return {"avg_latency": 999.0, "packet_loss": 100.0}

def check_uptime(url):
    try:
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "http://" + url
        response = requests.get(url, timeout=5)
        return "Online" if response.status_code == 200 else "Offline"
    except:
        return "Offline"

def scan_local_devices():
    devices = []
    try:
        local_ip = get_local_ip()
        subnet = ".".join(local_ip.split(".")[:-1]) + ".0/24"
        arp = ARP(pdst=subnet)
        ether = Ether(dst="ff:ff:ff:ff:ff:ff")
        packet = ether / arp
        result = srp(packet, timeout=2, verbose=0)[0]
        for sent, received in result:
            devices.append({'ip': received.psrc, 'mac': received.hwsrc})
    except Exception as e:
        print("Device scan failed:", e)
    return devices

def simulate_bandwidth():
    import random
    return {
        "download": round(random.uniform(50, 100), 2),
        "upload": round(random.uniform(10, 30), 2)
    }

def log_ping(user_id, target, result):
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO ping_logs (user_id, target, avg_latency, packet_loss) VALUES (?, ?, ?, ?)",
                  (user_id, target, result['avg_latency'], result['packet_loss']))
        conn.commit()

def log_uptime(user_id, url, status):
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO uptime_logs (user_id, url, status) VALUES (?, ?, ?)",
                  (user_id, url, status))
        conn.commit()

def log_bandwidth(user_id, data):
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO bandwidth_logs (user_id, download, upload) VALUES (?, ?, ?)",
                  (user_id, data['download'], data['upload']))
        conn.commit()

# === ROUTES ===

@app.before_request
def require_login():
    allowed_routes = ['login', 'register', 'forgot_password', 'static']
    if 'username' not in session and request.endpoint not in allowed_routes:
        return redirect(url_for('login'))

@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute("SELECT id, password FROM users WHERE username=?", (username,))
            row = c.fetchone()
            if row and bcrypt.check_password_hash(row[1], password):
                session['user_id'] = row[0]
                session['username'] = username
                return redirect(url_for('dashboard'))
            else:
                flash("Invalid credentials.")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        email = request.form['email']
        try:
            with sqlite3.connect(DATABASE) as conn:
                c = conn.cursor()
                c.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                          (username, password, email))
                conn.commit()
            flash("Account created! Please log in.")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Username already exists.")
    return render_template('register.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        flash(f"Password reset link sent to {email}")
        print(f"Password reset requested for: {email}")
    return render_template('forgot_password.html')

@app.route('/dashboard')
def dashboard():
    public_ip = get_public_ip()
    local_ip = get_local_ip()
    devices = scan_local_devices()
    # Simulate and log bandwidth when dashboard is loaded
    data = simulate_bandwidth()
    log_bandwidth(session['user_id'], data)
    return render_template('dashboard.html',
                           public_ip=public_ip,
                           local_ip=local_ip,
                           devices=devices,
                           bandwidth=data)

@app.route('/api/ping', methods=['POST'])
def api_ping():
    data = request.json
    target = data.get('target', 'google.com')
    result = ping_host(target)
    log_ping(session['user_id'], target, result)
    return jsonify(result)

@app.route('/api/uptime', methods=['POST'])
def api_uptime():
    data = request.json
    url = data.get('url', 'google.com')
    status = check_uptime(url)
    log_uptime(session['user_id'], url, status)
    return jsonify({"status": status, "url": url})

@app.route('/api/simulate_bandwidth', methods=['POST'])
def api_simulate_bandwidth():
    data = simulate_bandwidth()
    log_bandwidth(session['user_id'], data)
    return jsonify(data)

@app.route('/api/bandwidth/history')
def bandwidth_history():
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute("SELECT download, upload, timestamp FROM bandwidth_logs WHERE user_id=? ORDER BY timestamp DESC LIMIT 10",
                  (session['user_id'],))
        rows = c.fetchall()
    return jsonify([{"download": r[0], "upload": r[1], "time": r[2]} for r in rows])

@app.route('/api/logs/ping')
def ping_logs():
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute("SELECT target, avg_latency, packet_loss, timestamp FROM ping_logs WHERE user_id=? ORDER BY timestamp DESC LIMIT 20",
                  (session['user_id'],))
        rows = c.fetchall()
    return jsonify([{"target": r[0], "avg": r[1], "loss": r[2], "time": r[3]} for r in rows])

@app.route('/api/logs/uptime')
def uptime_logs():
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute("SELECT url, status, timestamp FROM uptime_logs WHERE user_id=? ORDER BY timestamp DESC LIMIT 20",
                  (session['user_id'],))
        rows = c.fetchall()
    return jsonify([{"url": r[0], "status": r[1], "time": r[2]} for r in rows])

@app.route('/help')
def help():
    faqs = [
        {"q": "How do I run a ping test?", "a": "Enter a domain or IP in the Ping Test section and click 'Test'."},
        {"q": "Why is my bandwidth changing?", "a": "It's simulated every 2 seconds for demo purposes."},
        {"q": "How is uptime checked?", "a": "The system pings the website and checks for HTTP response."},
        {"q": "Why did my ping fail?", "a": "Firewall may block ICMP. Try pinging 8.8.8.8 directly."}
    ]
    return render_template('help.html', faqs=faqs)

@app.route('/admin')
def admin():
    if session.get('username') != 'admin':
        return "Access Denied", 403
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute("SELECT id, username, email FROM users")
        users = c.fetchall()
    return render_template('admin.html', users=users)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# === INIT AND RUN ===
if __name__ == '__main__':
    if not os.path.exists('database'):
        os.makedirs('database')
    init_db()

    # Default admin user
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username='mutero'")
        if not c.fetchone():
            pwd = bcrypt.generate_password_hash('mutero1234').decode('utf-8')
            c.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)", ('admin', pwd, 'politemakamanzi@gmail.com'))
            conn.commit()

    app.run(host='0.0.0.0', port=5000, debug=False)