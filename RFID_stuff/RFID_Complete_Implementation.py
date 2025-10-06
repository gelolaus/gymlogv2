"""
COMPLETE RFID IMPLEMENTATION - GYM LOG SYSTEM
==============================================

This file contains ALL RFID-related code from the Gym Log system in one place.
"""

# ===========================
# 1. DATABASE MODEL (models.py)
# ===========================

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class StudentData(db.Model):
    """
    Database model where RFID codes are stored and linked to Student IDs
    """
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    student_id = db.Column(db.String(15), nullable=False, unique=True)  # STUDENT ID - UNIQUE
    pe_course = db.Column(db.String(10), nullable=False)
    enrolled_block = db.Column(db.String(10), nullable=False)
    rfid = db.Column(db.String(50), nullable=False, unique=True)  # RFID CODE - UNIQUE & LINKED TO STUDENT ID
    status = db.Column(db.String(10), nullable=False, default='offline')
    last_gym = db.Column(db.DateTime, nullable=True)
    total_workout_time = db.Column(db.Float, nullable=False, default=0.0)
    last_login = db.Column(db.DateTime, nullable=True)
    completed_sessions = db.Column(db.Integer, nullable=False, default=0)

# ===========================
# 2. FORM DEFINITIONS (forms.py)
# ===========================

import wtforms
from wtforms import Form, StringField, validators

class RegGymLogForm(Form):
    """Registration form that captures RFID during student registration"""
    full_name = StringField('Full Name', [validators.Length(min=2, max=100), validators.DataRequired()])
    student_id = StringField('Student ID Number', [validators.Length(min=9, max=13), validators.DataRequired()])
    pe_course = wtforms.SelectField('PE Course', choices=[
        ('pedu1', 'PEEDU1'),
        ('pedu2', 'PEEDU2'),
        ('pedu3', 'PEEDU3'),
        ('pedu4', 'PEEDU4'),
        ('none', 'None')
    ], validators=[validators.DataRequired()])
    enrolled_block = StringField('Enrolled Block', [validators.Length(min=3, max=9), validators.DataRequired()])
    rfid = StringField('APC Identification Card', [validators.DataRequired()])  # RFID CAPTURE FIELD

class LoginForm(Form):
    """Login form that captures RFID for authentication"""
    rfid = StringField('', [validators.DataRequired()])  # RFID AUTHENTICATION FIELD

# ===========================
# 3. MAIN APPLICATION ROUTES (main.py)
# ===========================

from flask import Flask, redirect, url_for, render_template, request, flash
from datetime import datetime
from models import db, StudentData
from forms import RegGymLogForm, LoginForm
from utils import toggle_gym_status

app = Flask(__name__)

# ROUTE 1: RFID LOGIN/LOGOUT PROCESSING
@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Main RFID tapping route - handles login/logout via RFID scan
    """
    is_registered = True
    is_full = False
    if request.method == 'POST':
        rfid = request.form.get('rfid')  # GET RFID FROM FORM
        user = StudentData.query.filter_by(rfid=rfid).first()  # LOOKUP USER BY RFID
        if user:
            if user.status == "online":
                toggle_gym_status(user)  # LOG OUT USER
                return redirect(url_for('toggle_gym_status_route', user_id=user.student_id))
            else:
                if StudentData.query.filter_by(status="online").count() >= app.config['MAX_USERS']:
                    is_full = True  # GYM CAPACITY CHECK
                else:
                    toggle_gym_status(user)  # LOG IN USER
                    return redirect(url_for('toggle_gym_status_route', user_id=user.student_id))
        else:
            is_registered = False  # RFID NOT FOUND IN DATABASE

    return render_template('login.html', form=LoginForm(), is_registered=is_registered, is_full=is_full)

# ROUTE 2: STUDENT REGISTRATION WITH RFID
@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Registration route - links new RFID to Student ID
    """
    form = RegGymLogForm(request.form)
    if request.method == 'POST' and form.validate():
        # CHECK FOR DUPLICATE STUDENT ID OR RFID
        if StudentData.query.filter(
                (StudentData.student_id == form.student_id.data) | 
                (StudentData.rfid == form.rfid.data)  # RFID UNIQUENESS CHECK
            ).first():
            flash('Duplicate Student ID or RFID. Please use a different one.', 'error')
            return render_template('register.html', form=form)

        # CREATE NEW USER WITH RFID LINKED TO STUDENT ID
        new_user = StudentData(
            full_name=form.full_name.data,
            student_id=form.student_id.data,  # STUDENT ID
            pe_course=form.pe_course.data,
            enrolled_block=form.enrolled_block.data,
            rfid=form.rfid.data  # RFID CODE LINKED TO THIS STUDENT ID
        )
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('register.html', form=form)

# ROUTE 3: STATS LOOKUP VIA RFID
@app.route('/stats_route', methods=['GET', 'POST'])
def stats_route():
    """
    Stats route - lookup student stats using RFID
    """
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        user = StudentData.query.filter_by(rfid=form.rfid.data).first()  # RFID LOOKUP
        if user:
            return redirect(url_for('individual_stats', user_id=user.student_id))
        flash('RFID not recognized. Please try again.', 'error')
    return render_template('stats_forms.html', form=form)

# ===========================
# 4. UTILITY FUNCTIONS (utils.py)
# ===========================

def toggle_gym_status(user):
    """
    Toggle user gym status based on RFID tap
    """
    now = datetime.now()
    if user.status == 'offline':
        user.status = 'online'
        user.last_login = now
        print(f"User {user.full_name} (RFID: {user.rfid}) logged in.")
    else:
        user.status = 'offline'
        user.last_gym = now.replace(microsecond=0)
        if user.last_login:
            workout_duration = round((now - user.last_login).total_seconds() / 60, 2)
            user.total_workout_time += workout_duration
        user.completed_sessions += 1
        print(f"User {user.full_name} (RFID: {user.rfid}) logged out.")
    db.session.commit()

# ===========================
# 5. FRONTEND JAVASCRIPT (formHandler.js)
# ===========================

"""
// Auto-focus RFID input field for card scanning
function autoFocusInput() {
    const inputField = document.getElementById('rfid');
    inputField.focus();
    setInterval(function() {
        inputField.focus();  // Keep RFID input focused
    }, 1000);
}

// Commented out auto-submit (causes double submission with RFID scanners)
// function autoSubmitForm() {
//     const inputField = document.getElementById('rfid');
//     inputField.addEventListener('input', function() {
//         if (inputField.value.length >= 10) {
//             document.getElementById('autoSubmitInput').submit();
//         }
//     });
// }

document.addEventListener('DOMContentLoaded', function() {
    autoFocusInput();
});
"""

# ===========================
# 6. DATABASE SEEDER (commands.py)
# ===========================

def seeder_db():
    """
    Seeds database with test RFID codes linked to Student IDs
    """
    json_file_path = 'seeders/database/test_students.json'
    
    with open(json_file_path, 'r') as file:
        test_data = json.load(file)

    for data in test_data:
        student = StudentData(
            full_name=data["full_name"],
            student_id=data["student_id"],  # STUDENT ID
            enrolled_block=data["enrolled_block"],
            pe_course=data["pe_course"],
            rfid=data["rfid"],  # RFID LINKED TO STUDENT ID
            status='offline',
            total_workout_time=0.0,
            completed_sessions=0
        )
        db.session.add(student)

    db.session.commit()

# ===========================
# 7. HTML TEMPLATES
# ===========================

"""
LOGIN TEMPLATE (login.html):
-----------------------------
<h2>Tap your APC Identification ID here to log-in or log-out!</h2>
<form method="post" id="autoSubmitInput" action="{{ url_for('login') }}">
    <dl>
        {{ render_field(form.rfid, class='...') }}  <!-- RFID INPUT FIELD -->
    </dl>
    <input type="submit" value="">
</form>

REGISTER TEMPLATE (register.html):
---------------------------------
<div class="mb-5">
    {{ render_field(form.rfid, id="rfid", placeholder="Tap your APC ID Here!") }}  <!-- RFID CAPTURE -->
</div>

STATS TEMPLATE (stats_forms.html):
---------------------------------
<form method="post" action="{{ url_for('stats_route') }}">
    <dl>
        {{ render_field(form.rfid, class='...') }}  <!-- RFID INPUT FOR STATS -->
    </dl>
</form>

GYM INFO TEMPLATE (gym_info.html):
---------------------------------
<form action="{{ url_for('login') }}" method="POST">
    <input type="hidden" name="rfid" value="{{ log.rfid }}">  <!-- HIDDEN RFID FOR MANUAL TOGGLE -->
    <button type="submit">Toggle Status</button>
</form>
"""

# ===========================
# SUMMARY OF RFID-STUDENT ID MAPPING
# ===========================

"""
HOW RFID CODES ARE LINKED TO STUDENT IDs:
=========================================

1. STORAGE LOCATION: StudentData table in database (models.py line 17)
   - Each record has both 'student_id' and 'rfid' fields
   - Both fields are UNIQUE constraints
   - One-to-one relationship between Student ID and RFID

2. REGISTRATION PROCESS: 
   - Student provides both Student ID and taps RFID card
   - Both values stored in same database record
   - Creates permanent link between Student ID and RFID

3. AUTHENTICATION PROCESS:
   - RFID scanned → Database lookup by RFID → Student record retrieved
   - System knows Student ID, name, and all other details from RFID alone

4. EXAMPLE DATABASE RECORD:
   {
     "id": 1,
     "student_id": "2023-140022",     ← STUDENT ID
     "full_name": "Jose H. Nunez", 
     "rfid": "1920983678",           ← RFID CODE
     "status": "offline",
     ...
   }

The RFID code acts as a physical key that maps to the Student ID in the database.
"""
