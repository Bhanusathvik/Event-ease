from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
import json
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'event_ease_secret_key'

# Ensure data directory exists
if not os.path.exists('data'):
    os.makedirs('data')

# File paths for data storage
USERS_FILE = 'data/users.json'
EVENTS_FILE = 'data/events.json'

# Initialize empty data files if they don't exist
def initialize_data_files():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump([], f)
    if not os.path.exists(EVENTS_FILE):
        with open(EVENTS_FILE, 'w') as f:
            json.dump([], f)

initialize_data_files()

# Helper functions
def load_users():
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def load_events():
    with open(EVENTS_FILE, 'r') as f:
        return json.load(f)

def save_events(events):
    with open(EVENTS_FILE, 'w') as f:
        json.dump(events, f, indent=4)

def get_user_by_email(email):
    return next((user for user in load_users() if user['email'] == email), None)

def get_users_by_role(role):
    return [user for user in load_users() if user['role'] == role]

@app.route('/')
def index():
    if 'user_email' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        users = load_users()

        if any(user['email'] == email for user in users):
            flash('Email already registered. Please use a different email.')
            return redirect(url_for('register'))

        new_user = {
            'name': name,
            'email': email,
            'password': generate_password_hash(password),
            'role': role
        }
        users.append(new_user)
        save_users(users)

        flash('Registration successful! Please login.')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = get_user_by_email(email)

        if user and check_password_hash(user['password'], password):
            session['user_email'] = user['email']
            session['user_name'] = user['name']
            session['user_role'] = user['role']
            flash(f'Welcome back, {user["name"]}!')
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password. Please try again.')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/home')
def home():
    if 'user_email' not in session:
        flash('Please login first.')
        return redirect(url_for('login'))

    return render_template('home.html', 
                           user_name=session['user_name'], 
                           user_role=session['user_role'])

@app.route('/create_event', methods=['GET', 'POST'])
def create_event():
    if 'user_email' not in session:
        flash('Please login first.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        vendor_email = request.form.get('vendor')
        venue_owner_email = request.form.get('venue_owner')
        vendor_services = request.form.get('vendor_services')
        vendor_phone = request.form.get('vendor_phone')
        venue_location_lat = request.form.get('venue_location_lat')
        venue_location_lng = request.form.get('venue_location_lng')
        venue_phone = request.form.get('venue_phone')
        reminder_date = request.form.get('reminder_date')

        events = load_events()
        new_event = {
            'title': title,
            'description': description,
            'user_email': session['user_email'],
            'user_name': session['user_name'],
            'vendor_email': vendor_email,
            'venue_owner_email': venue_owner_email,
            'vendor_services': vendor_services,
            'vendor_phone': vendor_phone,
            'venue_location_lat': venue_location_lat,
            'venue_location_lng': venue_location_lng,
            'venue_phone': venue_phone,
            'reminder_date': reminder_date
        }
        events.append(new_event)
        save_events(events)

        flash('Event created successfully!')
        return redirect(url_for('my_events'))

    vendors = get_users_by_role('Vendor')
    venue_owners = get_users_by_role('Venue Owner')
    return render_template('create_event.html', vendors=vendors, venue_owners=venue_owners)

@app.route('/my_events')
def my_events():
    if 'user_email' not in session:
        flash('Please login first.')
        return redirect(url_for('login'))

    events = load_events()
    user_events = [event for event in events if event['user_email'] == session['user_email']]
    return render_template('my_events.html', events=user_events)

@app.route('/vendor_bookings')
def vendor_bookings():
    if 'user_email' not in session:
        flash('Please login first.')
        return redirect(url_for('login'))

    if session['user_role'] != 'Vendor':
        flash('Only vendors can view vendor bookings.')
        return redirect(url_for('home'))

    events = load_events()
    vendor_events = [event for event in events if event['vendor_email'] == session['user_email']]
    return render_template('vendor_bookings.html', events=vendor_events)

@app.route('/venue_bookings')
def venue_bookings():
    # Check if the user is logged in
    if 'user_email' not in session:
        flash('Please login first.')
        return redirect(url_for('login'))

    # Check if the user is a Venue Owner
    if session['user_role'] != 'Venue Owner':
        flash('Only venue owners can view venue bookings.')
        return redirect(url_for('home'))

    # Load all events (Assuming `load_events()` is a function that loads all events)
    events = load_events()

    # Filter events based on the logged-in venue owner's email
    venue_events = [event for event in events if event['venue_owner_email'] == session['user_email']]

    # Render the 'venue_bookings.html' template and pass the filtered events
    return render_template('venue_bookings.html', events=venue_events)

if __name__ == '__main__':
    app.run(debug=True)
