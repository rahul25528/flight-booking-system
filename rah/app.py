from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'


def init_db():
    conn = sqlite3.connect('flights.db')
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT,
        role TEXT
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS flights (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        flight_no TEXT,
        source TEXT,
        destination TEXT,
        date TEXT,
        time TEXT,
        seats INTEGER,
        price INTEGER
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        flight_id INTEGER,
        booking_date TEXT
    )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        with sqlite3.connect('flights.db') as con:
            cur = con.cursor()
            cur.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
            con.commit()
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect('flights.db') as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
            user = cur.fetchone()
            if user:
                session['user_id'] = user[0]
                session['username'] = user[1]
                session['role'] = user[3]
                return redirect('/admin' if user[3] == 'admin' else '/user')
            else:
                return "Invalid credentials"
    return render_template('login.html')

@app.route('/admin')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect('/login')
    con = sqlite3.connect('flights.db')
    cur = con.cursor()
    cur.execute("SELECT * FROM flights")
    flights = cur.fetchall()
    return render_template('admin_dashboard.html', flights=flights)

@app.route('/add_flight', methods=['GET', 'POST'])
def add_flight():
    if session.get('role') != 'admin':
        return redirect('/login')
    if request.method == 'POST':
        data = (request.form['flight_no'], request.form['source'], request.form['destination'], 
                request.form['date'], request.form['time'], request.form['seats'], request.form['price'])
        with sqlite3.connect('flights.db') as con:
            cur = con.cursor()
            cur.execute("INSERT INTO flights (flight_no, source, destination, date, time, seats, price) VALUES (?, ?, ?, ?, ?, ?, ?)", data)
            con.commit()
        return redirect('/admin')
    return render_template('add_flight.html')

@app.route('/delete_flight/<int:id>')
def delete_flight(id):
    if session.get('role') != 'admin':
        return redirect('/login')
    with sqlite3.connect('flights.db') as con:
        cur = con.cursor()
        cur.execute("DELETE FROM flights WHERE id=?", (id,))
        con.commit()
    return redirect('/admin')

@app.route('/user')
def user_dashboard():
    if session.get('role') != 'user':
        return redirect('/login')
    con = sqlite3.connect('flights.db')
    cur = con.cursor()
    cur.execute("SELECT * FROM flights")
    flights = cur.fetchall()
    return render_template('user_dashboard.html', flights=flights)

@app.route('/book_flight/<int:flight_id>')
def book_flight(flight_id):
    if session.get('role') != 'user':
        return redirect('/login')
    with sqlite3.connect('flights.db') as con:
        cur = con.cursor()
        cur.execute("SELECT seats FROM flights WHERE id=?", (flight_id,))
        seats = cur.fetchone()[0]
        if seats > 0:
            cur.execute("INSERT INTO bookings (user_id, flight_id, booking_date) VALUES (?, ?, date('now'))",
                        (session['user_id'], flight_id))
            cur.execute("UPDATE flights SET seats = seats - 1 WHERE id=?", (flight_id,))
            con.commit()
            return "Booking successful!"
        else:
            return "No seats available!"
    return redirect('/user')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


@app.route('/booking_history')
def booking_history():
    if session.get('role') != 'user':
        return redirect('/login')
    user_id = session['user_id']
    with sqlite3.connect('flights.db') as con:
        cur = con.cursor()
        cur.execute("""
            SELECT bookings.id, flights.flight_no, flights.source, flights.destination, 
                   flights.date, flights.time, flights.price, bookings.booking_date
            FROM bookings
            JOIN flights ON bookings.flight_id = flights.id
            WHERE bookings.user_id=?
        """, (user_id,))
        history = cur.fetchall()
    return render_template('booking_history.html', history=history)

if __name__ == '__main__':
    app.run(debug=True)
