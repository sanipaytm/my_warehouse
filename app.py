from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3
import pandas as pd

app = Flask(__name__)
app.secret_key = 'secret123'

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect('data.db')
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

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == '1234':
            session['user'] = 'admin'
            return redirect('/')
        else:
            return "Invalid Login"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ---------------- HOME ----------------
@app.route('/')
def home():
    if 'user' not in session:
        return redirect('/login')

    conn = sqlite3.connect('data.db')
    c = conn.cursor()

    c.execute("SELECT * FROM store")
    data = c.fetchall()

    c.execute("SELECT SUM(qty) FROM store")
    total = c.fetchone()[0]

    conn.close()

    return render_template('index.html', data=data, total=total)

# ---------------- ADD ----------------
@app.route('/submit', methods=['POST'])
def submit():
    vehicle = request.form['vehicle']
    model = request.form['model']
    qty = request.form['qty']

    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute("INSERT INTO store (vehicle, model, qty) VALUES (?, ?, ?)", (vehicle, model, qty))
    conn.commit()
    conn.close()

    return redirect('/')

# ---------------- DELETE ----------------
@app.route('/delete/<int:id>')
def delete(id):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute("DELETE FROM store WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/')

# ---------------- EDIT ----------------
@app.route('/edit/<int:id>')
def edit(id):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute("SELECT * FROM store WHERE id=?", (id,))
    data = c.fetchone()
    conn.close()
    return render_template('edit.html', data=data)

# ---------------- UPDATE ----------------
@app.route('/update/<int:id>', methods=['POST'])
def update(id):
    vehicle = request.form['vehicle']
    model = request.form['model']
    qty = request.form['qty']

    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute("UPDATE store SET vehicle=?, model=?, qty=? WHERE id=?", (vehicle, model, qty, id))
    conn.commit()
    conn.close()

    return redirect('/')

# ---------------- EXPORT ----------------
@app.route('/export')
def export():
    conn = sqlite3.connect('data.db')
    df = pd.read_sql_query("SELECT * FROM store", conn)
    conn.close()

    file = "data.xlsx"
    df.to_excel(file, index=False)

    return send_file(file, as_attachment=True)

# ---------------- RUN ----------------
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)