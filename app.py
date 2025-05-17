from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from authlib.integrations.flask_client import OAuth
from datetime import datetime
import smtplib
import pytz
import sqlite3
import pickle
import numpy as np
import os
import secrets
from flask_mail import Message
from flask import Flask
from flask_mail import Mail

def generate_reset_token():
    return secrets.token_urlsafe(32)



# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'
DATABASE = 'users.db'

# Define init_db before calling it
def init_db():
    if not os.path.exists(DATABASE):
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT
        )''')
        cursor.execute('''CREATE TABLE history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            prediction INTEGER
        )''')
        conn.commit()
        conn.close()
        print("Database initialized.")

init_db()

# Load model
with open(os.path.join(os.path.dirname(__file__), 'model.pkl'), 'rb') as model_file:
    model = pickle.load(model_file)

# --- GOOGLE AUTH SETUP ---
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id='7723684353-mihnpis45u6o4bkmvl288r0li2dved3h.apps.googleusercontent.com',
    client_secret='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',
    access_token_url='https://oauth2.googleapis.com/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    api_base_url='https://www.googleapis.com/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',
    client_kwargs={'scope': 'openid email profile'},
    redirect_uri='http://localhost:5000/google-callback'
)

# -------- ROUTES ----------
@app.route('/')
def home():
    return render_template('index.html')

# ✅ Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'prabingamerboy@gmail.com'  # your Gmail
app.config['MAIL_PASSWORD'] = 'ojbi pxif vcte inkw'       # your App Password
app.config['MAIL_DEFAULT_SENDER'] = 'prabingamerboy@gmail.com'

mail = Mail(app)


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        token = secrets.token_urlsafe(32)

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET reset_token = ? WHERE email = ?', (token, email))
        conn.commit()
        conn.close()

        reset_url = url_for('reset_token', token=token, _external=True)

        msg = Message("Reset Your Password", recipients=[email])
        msg.body = f"Click here to reset your password: {reset_url}"
        msg.html = render_template("reset_email.html", reset_url=reset_url)

        try:
            mail.send(msg)
            flash("Password reset link has been sent to your email.", "success")
        except Exception as e:
            flash("Email failed to send. Check configuration.", "danger")

        return redirect(url_for('forgot_password'))

    return render_template('forgot_password.html')


def send_reset_email(email, token):
    reset_url = url_for('reset_token', token=token, _external=True)

    msg = Message("Password Reset Request", recipients=[email])
    msg.body = f'''Hi there,

We received a request to reset your password. Click the link below to reset it:

{reset_url}

If you didn’t request this, just ignore this email.

Thanks,
Your App Team
'''

    msg.html = render_template("reset_email.html", reset_url=reset_url)
    mail.send(msg)



@app.route('/reset/<token>', methods=['GET', 'POST'])
def reset_token(token):
    if request.method == 'POST':
        password = request.form['password']

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT email FROM users WHERE reset_token = ?', (token,))
        result = cursor.fetchone()

        if result:
            cursor.execute('UPDATE users SET password = ?, reset_token = NULL WHERE reset_token = ?', (password, token))
            conn.commit()
            flash("Password updated successfully. You can now log in.", "success")
            return redirect(url_for('signin'))
        else:
            flash("Invalid or expired token.", "danger")

        conn.close()

    return render_template('reset_password.html')






@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                           (username, email, password))
            conn.commit()
            flash('Sign up successful. Please log in.')
            return redirect(url_for('signin'))
        except sqlite3.IntegrityError:
            flash('Email already registered.')
        conn.close()
    return render_template('signup.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email=?', (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[3], password):
            session['email'] = email
            return redirect(url_for('predict'))
        else:
            flash('Invalid credentials.')
    return render_template('signin.html')

@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        email = request.form['email']
        new_password = generate_password_hash(request.form['new_password'])

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET password=? WHERE email=?', (new_password, email))
        conn.commit()
        conn.close()

        flash('Password reset successfully.')
        return redirect(url_for('signin'))

    return render_template('forgot.html')

# --- CORRECTED PREDICT ROUTE ---
from datetime import datetime
import pytz

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if 'email' not in session:
        return redirect(url_for('signin'))

    if request.method == 'POST':
        gender = request.form['gender']
        age = request.form['age']
        hypertension = request.form['hypertension']
        heart_disease = request.form['heart_disease']
        smoking_history = request.form['smoking_history']
        bmi = request.form['bmi']
        hba1c_level = request.form['hba1c_level']
        blood_glucose = request.form['blood_glucose']

        # ✅ Input Validation
        try:
            age = float(age)
            bmi = float(bmi)
            hba1c_level = float(hba1c_level)
            blood_glucose = float(blood_glucose)
            hypertension = int(hypertension)
            heart_disease = int(heart_disease)

            if not (1 <= age <= 120):
                return "Age must be between 18 and 100", 400
            if not (10 <= bmi <= 60):
                return "BMI must be between 10 and 60", 400
            if not (3.5 <= hba1c_level <= 14.0):
                return "HbA1c level must be between 3.5 and 14.0", 400
            if not (40 <= blood_glucose <= 500):
                return "Blood Glucose level must be between 40 and 500", 400
            if hypertension not in (0, 1):
                return "Hypertension must be 0 or 1", 400
            if heart_disease not in (0, 1):
                return "Heart Disease must be 0 or 1", 400

        except ValueError:
            return "Invalid input: Please enter correct numeric values.", 400

        # ✅ Gender Encoding
        gender_val = 1 if gender.lower() == 'male' else 0

        # ✅ Smoking History Mapping
        smoking_map = {
            'never': 0,
            'former': 1,
            'current': 2,
            'not current': 3,
            'ever': 4,
            'no info': 5
        }
        smoking_val = smoking_map.get(smoking_history.lower(), -1)
        if smoking_val == -1:
            return "Invalid smoking history value.", 400

        # ✅ Prepare input for prediction
        input_data = np.array([
            gender_val,
            age,
            hypertension,
            heart_disease,
            smoking_val,
            bmi,
            hba1c_level,
            blood_glucose
        ]).reshape(1, -1)

        prediction = model.predict(input_data)[0]

        if prediction == 'No Diabetic':
            prediction = 'Non-Diabetic'

        label_to_number = {
            'Non-Diabetic': 0,
            'Pre-Diabetic': 1,
            'Diabetic': 2
        }

        session['prediction'] = label_to_number.get(prediction, -1)

        # ✅ Save to history with IST timestamp
        tz = pytz.timezone('Asia/Kolkata')
        timestamp = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO history (email, prediction, timestamp)
            VALUES (?, ?, ?)
        ''', (session['email'], session['prediction'], timestamp))
        conn.commit()
        conn.close()

        return redirect(url_for('result'))

    return render_template('predict.html')


# --------------------------
# New /result route

@app.route('/result')
def result():
    if 'prediction' not in session:
        return redirect(url_for('predict'))

    prediction = session['prediction']

    # Only allow expected prediction values
    if prediction == 0:
        prediction_text = "Non-Diabetic"
    elif prediction == 1:
        prediction_text = "Pre-Diabetic"
    elif prediction == 2:
        prediction_text = "Diabetic"
    else:
        # If prediction is unexpected, redirect to predict page or show error
        return redirect(url_for('predict'))

    return render_template('result.html', prediction_text=prediction_text) 


@app.route('/history')
def history():
    if 'email' not in session:
        return redirect(url_for('signin'))

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT prediction, timestamp FROM history WHERE email = ? ORDER BY timestamp DESC', (session['email'],))
    data = cursor.fetchall()
    conn.close()

    # Define both numeric and string label mappings
    label_mapping = {
        0: 'Non-Diabetic',
        1: 'Pre-Diabetic',
        2: 'Diabetic',
        '0': 'Non-Diabetic',
        '1': 'Pre-Diabetic',
        '2': 'Diabetic',
        'Non-Diabetic': 'Non-Diabetic',
        'Pre-Diabetic': 'Pre-Diabetic',
        'Diabetic': 'Diabetic'
    }

    history = []
    for row in data:
        prediction_raw = row[0]
        timestamp = row[1]

        prediction_text = label_mapping.get(prediction_raw, 'Unknown')

        history.append({
            'prediction': prediction_text,
            'timestamp': timestamp
        })

    return render_template('history.html', history=history)


@app.route('/delete_history', methods=['POST'])
def delete_history():
    if 'email' not in session:
        return redirect(url_for('signin'))

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM history WHERE email = ?', (session['email'],))
    conn.commit()
    conn.close()

    return redirect(url_for('history'))



@app.route('/diet', methods=['GET', 'POST'])
def diet():
    if request.method == 'POST':
        diet_type = request.form['diet_type']
        condition = session.get('condition', 'Non Diabetic')  # Set this after prediction!

        full_diet = {
            "Non Diabetic - Vegetarian Diet Plan": [
                {"day": "Monday", "breakfast": "Oats with fruits", "lunch": "Paneer curry, chapati, salad", "dinner": "Vegetable khichdi, curd"},
                {"day": "Tuesday", "breakfast": "Idli with sambhar", "lunch": "Mixed veg sabzi, rice", "dinner": "Rajma curry, roti"},
                {"day": "Wednesday", "breakfast": "Poha with peanuts", "lunch": "Chole, chapati", "dinner": "Lauki sabzi, rice"},
                {"day": "Thursday", "breakfast": "Upma and curd", "lunch": "Palak paneer, rice", "dinner": "Kadhi, roti"},
                {"day": "Friday", "breakfast": "Vegetable sandwich", "lunch": "Dal, chapati, sabzi", "dinner": "Vegetable pulao, raita"},
                {"day": "Saturday", "breakfast": "Paratha with curd", "lunch": "Baingan bharta, roti", "dinner": "Tinda curry, rice"},
                {"day": "Sunday", "breakfast": "Dosa with chutney", "lunch": "Mixed dal, rice", "dinner": "Aloo gobi, chapati"},
            ],
            "Non Diabetic - Non-Vegetarian Diet Plan": [
                {"day": "Monday", "breakfast": "Boiled eggs, toast", "lunch": "Grilled chicken, rice", "dinner": "Egg curry, roti"},
                {"day": "Tuesday", "breakfast": "Oats with milk", "lunch": "Fish curry, rice", "dinner": "Chicken soup, bread"},
                {"day": "Wednesday", "breakfast": "Paneer sandwich", "lunch": "Chicken biryani", "dinner": "Omelette, paratha"},
                {"day": "Thursday", "breakfast": "Idli and eggs", "lunch": "Egg bhurji, chapati", "dinner": "Fish fry, rice"},
                {"day": "Friday", "breakfast": "Cornflakes and banana", "lunch": "Grilled fish, veggies", "dinner": "Chicken curry, rice"},
                {"day": "Saturday", "breakfast": "Dosa and eggs", "lunch": "Prawns masala, rice", "dinner": "Boiled eggs, salad"},
                {"day": "Sunday", "breakfast": "Poha and egg", "lunch": "Chicken curry, rice", "dinner": "Fish tikka, roti"},
            ],
            "Pre Diabetic - Vegetarian Diet Plan": [
                {"day": "Monday", "breakfast": "Multigrain toast, milk", "lunch": "Lentil soup, salad", "dinner": "Vegetable stew"},
                {"day": "Tuesday", "breakfast": "Vegetable oats", "lunch": "Tofu curry, roti", "dinner": "Bajra khichdi"},
                {"day": "Wednesday", "breakfast": "Sprouts with fruits", "lunch": "Paneer bhurji, salad", "dinner": "Mixed veg, chapati"},
                {"day": "Thursday", "breakfast": "Moong dal chilla", "lunch": "Vegetable rice, curd", "dinner": "Stuffed paratha, raita"},
                {"day": "Friday", "breakfast": "Low-fat poha", "lunch": "Bhindi, roti", "dinner": "Vegetable soup, bread"},
                {"day": "Saturday", "breakfast": "Idli with sambhar", "lunch": "Lauki kofta, rice", "dinner": "Dal tadka, roti"},
                {"day": "Sunday", "breakfast": "Upma and nuts", "lunch": "Chole, salad", "dinner": "Khichdi, curd"},
            ],
            "Pre Diabetic - Non-Vegetarian Diet Plan": [
                {"day": "Monday", "breakfast": "Boiled eggs, oats", "lunch": "Chicken salad", "dinner": "Egg curry, rice"},
                {"day": "Tuesday", "breakfast": "Egg sandwich", "lunch": "Fish curry, rice", "dinner": "Chicken soup"},
                {"day": "Wednesday", "breakfast": "Oats and milk", "lunch": "Grilled chicken", "dinner": "Boiled egg, chapati"},
                {"day": "Thursday", "breakfast": "Toast and egg", "lunch": "Chicken stew", "dinner": "Fish tikka, salad"},
                {"day": "Friday", "breakfast": "Smoothie, eggs", "lunch": "Grilled prawns", "dinner": "Egg curry, veg soup"},
                {"day": "Saturday", "breakfast": "Sprouts and egg", "lunch": "Fish pulao", "dinner": "Grilled chicken, roti"},
                {"day": "Sunday", "breakfast": "Upma, boiled egg", "lunch": "Fish curry, salad", "dinner": "Chicken roast, rice"},
            ],
            "Diabetic - Vegetarian Diet Plan": [
                {"day": "Monday", "breakfast": "Oats with chia seeds", "lunch": "Bitter gourd sabzi, roti", "dinner": "Lentil soup, salad"},
                {"day": "Tuesday", "breakfast": "Sprouts, tea", "lunch": "Low oil dal, brown rice", "dinner": "Vegetable curry, chapati"},
                {"day": "Wednesday", "breakfast": "Low GI fruits", "lunch": "Lauki sabzi, roti", "dinner": "Palak dal, rice"},
                {"day": "Thursday", "breakfast": "Moong dal chilla", "lunch": "Vegetable khichdi", "dinner": "Stuffed tinda, roti"},
                {"day": "Friday", "breakfast": "Vegetable upma", "lunch": "Tofu sabzi, rice", "dinner": "Methi dal, salad"},
                {"day": "Saturday", "breakfast": "Low-fat poha", "lunch": "Mixed veg, roti", "dinner": "Cabbage curry, soup"},
                {"day": "Sunday", "breakfast": "Paratha with curd", "lunch": "Pumpkin sabzi, roti", "dinner": "Dalia, salad"},
            ],
            "Diabetic - Non-Vegetarian Diet Plan": [
                {"day": "Monday", "breakfast": "Boiled eggs, tea", "lunch": "Grilled fish, salad", "dinner": "Egg whites, soup"},
                {"day": "Tuesday", "breakfast": "Oats and egg", "lunch": "Chicken breast, brown rice", "dinner": "Boiled egg, veggies"},
                {"day": "Wednesday", "breakfast": "Sprouts, egg", "lunch": "Fish curry, low oil", "dinner": "Chicken stew"},
                {"day": "Thursday", "breakfast": "Idli and boiled egg", "lunch": "Grilled prawns", "dinner": "Egg curry"},
                {"day": "Friday", "breakfast": "Low-fat toast, egg", "lunch": "Chicken salad", "dinner": "Fish fry, salad"},
                {"day": "Saturday", "breakfast": "Upma, egg whites", "lunch": "Fish pulao", "dinner": "Boiled chicken, roti"},
                {"day": "Sunday", "breakfast": "Vegetable oats, egg", "lunch": "Grilled chicken", "dinner": "Chicken soup, veggies"},
            ],
        }

        key = f"{condition} - {diet_type} Diet Plan"
        plan = full_diet.get(key, [])

        return render_template("diet.html", plan=plan, diet_type=diet_type)

    return render_template("diet.html", plan=None)


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('signin'))

# ---- GOOGLE AUTH ROUTES ----
@app.route('/google-login')
def google_login():
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/google-callback')
def google_callback():
    token = google.authorize_access_token()
    resp = google.get('userinfo')
    user_info = resp.json()

    email = user_info['email']
    name = user_info.get('name', 'Google User')

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email=?', (email,))
    user = cursor.fetchone()

    if not user:
        cursor.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', (name, email, ''))
        conn.commit()

    conn.close()
    session['email'] = email
    return redirect(url_for('predict'))


@app.route('/exercise/<category>')
def exercise_plan(category):
    plans = {
        "diabetic": {
            "title": "Exercise Plan for Diabetic",
            "exercises": [
                {"icon": "fa-sun", "text": "Gentle Morning Stretching"},
                {"icon": "fa-walking", "text": "30 min Brisk Walking"},
                {"icon": "fa-heartbeat", "text": "Low-impact Aerobics"},
                {"icon": "fa-dumbbell", "text": "Light Resistance Training (2–3x/week)"},
                {"icon": "fa-spa", "text": "Yoga & Breathing Exercises"}
            ]
        },
        "pre-diabetic": {
            "title": "Exercise Plan for Pre-Diabetic",
            "exercises": [
                {"icon": "fa-bicycle", "text": "Cycling or Swimming (45 min/day)"},
                {"icon": "fa-running", "text": "Jogging or Power Walking"},
                {"icon": "fa-dumbbell", "text": "Moderate Weight Training"},
                {"icon": "fa-stopwatch", "text": "HIIT (2x/week under guidance)"},
                {"icon": "fa-leaf", "text": "Mindful Meditation & Cool Down"}
            ]
        },
        "non-diabetic": {
            "title": "Exercise Plan for Non-Diabetic",
            "exercises": [
                {"icon": "fa-running", "text": "Daily Jogging or Outdoor Games"},
                {"icon": "fa-dumbbell", "text": "Strength Training (3–4x/week)"},
                {"icon": "fa-bicycle", "text": "Cardio Activities (Cycling, Hiking)"},
                {"icon": "fa-water", "text": "Swimming or Dance Fitness"},
                {"icon": "fa-heart", "text": "Stretching & Heart-Health Exercises"}
            ]
        }
    }

    plan = plans.get(category.lower())
    if not plan:
        return "Category not found", 404

    return render_template('exercise_details.html', category=category.title(), plan=plan)

if __name__ == '__main__':
    app.run(debug=True)
