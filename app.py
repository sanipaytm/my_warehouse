from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3
import pandas as pd
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'secret123')  # Better security

# Database path for Render
DATABASE_PATH = '/tmp/data.db'  # Render uses /tmp for writable storage

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS store (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle TEXT,
            model TEXT,
            qty INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Better column access
    return conn

# Login decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Use environment variables for better security
        admin_user = os.environ.get('ADMIN_USER', 'admin')
        admin_pass = os.environ.get('ADMIN_PASS', '1234')
        
        if username == admin_user and password == admin_pass:
            session['user'] = 'admin'
            return redirect('/')
        else:
            return render_template('login.html', error="Invalid username or password")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ---------------- HOME ----------------
@app.route('/')
@login_required
def home():
    conn = get_db()
    c = conn.cursor()
    
    c.execute("SELECT * FROM store ORDER BY id DESC")  # Show latest first
    data = c.fetchall()
    
    c.execute("SELECT SUM(qty) FROM store")
    total = c.fetchone()[0] or 0
    
    conn.close()
    
    return render_template('index.html', data=data, total=total)

# ---------------- ADD ----------------
@app.route('/submit', methods=['POST'])
@login_required
def submit():
    vehicle = request.form.get('vehicle', '').strip()
    model = request.form.get('model', '').strip()
    qty = request.form.get('qty', 0)
    
    if not vehicle or not model or not qty:
        return redirect('/')
    
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO store (vehicle, model, qty) VALUES (?, ?, ?)", 
              (vehicle, model, qty))
    conn.commit()
    conn.close()
    
    return redirect('/')

# ---------------- DELETE ----------------
@app.route('/delete/<int:id>')
@login_required
def delete(id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM store WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/')

# ---------------- EDIT ----------------
@app.route('/edit/<int:id>')
@login_required
def edit(id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM store WHERE id=?", (id,))
    data = c.fetchone()
    conn.close()
    
    if not data:
        return redirect('/')
    
    return render_template('edit.html', data=data)

# ---------------- UPDATE ----------------
@app.route('/update/<int:id>', methods=['POST'])
@login_required
def update(id):
    vehicle = request.form.get('vehicle')
    model = request.form.get('model')
    qty = request.form.get('qty')
    
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE store SET vehicle=?, model=?, qty=? WHERE id=?", 
              (vehicle, model, qty, id))
    conn.commit()
    conn.close()
    
    return redirect('/')

# ---------------- EXPORT ----------------
@app.route('/export')
@login_required
def export():
    conn = get_db()
    df = pd.read_sql_query("SELECT id, vehicle, model, qty FROM store", conn)
    conn.close()
    
    # Create Excel file
    file_path = '/tmp/data_export.xlsx'
    df.to_excel(file_path, index=False, engine='openpyxl')
    
    return send_file(file_path, 
                    as_attachment=True, 
                    download_name='warehouse_data.xlsx')

# ---------------- RUN ----------------
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
