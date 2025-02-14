from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import hashlib

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # مفتاح سري لإدارة الجلسات

# تسجيل المستخدمين
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()  # تشفير كلمة المرور
        role = request.form['role']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', (username, password, role))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            conn.close()
            return "اسم المستخدم موجود مسبقًا!"
    return render_template('register.html')

# تسجيل الدخول
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['user_id'] = user[0]
            session['role'] = user[3]
            return redirect(url_for('dashboard'))
        else:
            return "اسم المستخدم أو كلمة المرور غير صحيحة!"
    return render_template('login.html')

# لوحة التحكم
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    role = session['role']
    if role == 'advertiser':
        return redirect(url_for('advertiser_dashboard'))
    elif role == 'publisher':
        return redirect(url_for('publisher_dashboard'))
    elif role == 'admin':
        return redirect(url_for('admin_dashboard'))
    else:
        return "دور غير معروف!"

# واجهة المعلنين
@app.route('/advertiser/dashboard', methods=['GET', 'POST'])
def advertiser_dashboard():
    if 'user_id' not in session or session['role'] != 'advertiser':
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        url = request.form['url']
        user_id = session['user_id']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO ads (title, content, url, user_id) VALUES (?, ?, ?, ?)', (title, content, url, user_id))
        conn.commit()
        conn.close()
        return "تم إنشاء الإعلان بنجاح!"

    # عرض الإعلانات التي أنشأها المعلن
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM ads WHERE user_id = ?', (session['user_id'],))
    ads = cursor.fetchall()
    conn.close()
    return render_template('advertiser_dashboard.html', ads=ads)

# واجهة الناشرين
@app.route('/publisher/dashboard', methods=['GET', 'POST'])
def publisher_dashboard():
    if 'user_id' not in session or session['role'] != 'publisher':
        return redirect(url_for('login'))

    if request.method == 'POST':
        site_url = request.form['site_url']
        user_id = session['user_id']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO sites (url, user_id) VALUES (?, ?)', (site_url, user_id))
        conn.commit()
        conn.close()
        return "تم إرسال الموقع للمراجعة!"

    # عرض حالة المواقع
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT sites.url, site_reviews.status 
        FROM sites 
        LEFT JOIN site_reviews ON sites.id = site_reviews.site_id 
        WHERE sites.user_id = ?
    ''', (session['user_id'],))
    sites = cursor.fetchall()
    conn.close()
    return render_template('publisher_dashboard.html', sites=sites)

# واجهة المشرفين
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    # عرض جميع المواقع المرسلة للمراجعة
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT sites.id, sites.url, users.username, site_reviews.status 
        FROM sites 
        JOIN users ON sites.user_id = users.id 
        LEFT JOIN site_reviews ON sites.id = site_reviews.site_id
    ''')
    sites = cursor.fetchall()
    conn.close()
    return render_template('admin_dashboard.html', sites=sites)

# قبول أو رفض الموقع
@app.route('/admin/review-site/<int:site_id>/<status>')
def review_site(site_id, status):
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO site_reviews (site_id, status, admin_id) VALUES (?, ?, ?)', (site_id, status, session['user_id']))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

# تسجيل الخروج
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)