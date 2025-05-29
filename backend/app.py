
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime, timedelta

app = Flask(__name__, instance_relative_config=True)
CORS(app)
DB_PATH = os.path.join(app.instance_path, 'sqlite.db')

if not os.path.exists(app.instance_path):
    os.makedirs(app.instance_path)

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS vouchers (
                        code TEXT PRIMARY KEY,
                        start_date TEXT,
                        duration INTEGER
                    )''')
        conn.commit()

@app.route('/check/<code>', methods=['GET'])
def check_voucher(code):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT start_date, duration FROM vouchers WHERE code=?", (code,))
        row = c.fetchone()
        if row:
            start_date = datetime.strptime(row[0], "%Y-%m-%d") if row[0] else None
            duration = row[1]
            if start_date:
                expiry = start_date + timedelta(days=duration)
                remaining = (expiry - datetime.today()).days
                if remaining >= 0:
                    return jsonify(status="valid", expiry=expiry.strftime("%Y-%m-%d"), remaining=remaining)
                else:
                    return jsonify(status="expired", expiry=expiry.strftime("%Y-%m-%d"), remaining=0)
            else:
                return jsonify(status="not_started")
        return jsonify(status="invalid")

@app.route('/add', methods=['POST'])
def add_voucher():
    data = request.json
    code = data['code']
    start_date = data.get('start_date')
    duration = data['duration']
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO vouchers (code, start_date, duration) VALUES (?, ?, ?)", (code, start_date, duration))
        conn.commit()
    return jsonify(status="success")

@app.route('/upload', methods=['POST'])
def upload_csv():
    file = request.files['file']
    if file:
        content = file.read().decode('utf-8').splitlines()
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            for line in content:
                parts = line.strip().split(',')
                if len(parts) == 3:
                    c.execute("INSERT OR REPLACE INTO vouchers (code, start_date, duration) VALUES (?, ?, ?)", (parts[0], parts[1], int(parts[2])))
            conn.commit()
        return jsonify(status="uploaded")
    return jsonify(status="error")

@app.route('/all', methods=['GET'])
def get_all():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM vouchers")
        rows = c.fetchall()
    return jsonify(rows)

@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/admin')
def admin():
    return send_from_directory('../frontend', 'admin.html')

@app.route('/<path:path>')
def static_proxy(path):
    return send_from_directory('../frontend', path)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
        