from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

app = Flask(__name__)
app.secret_key = 'event_ease_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://BhanuSathvik:new_password@localhost/event_ease_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    # New fields for venue owners
    venue_lat = db.Column(db.String(50))
    venue_lng = db.Column(db.String(50))
    venue_address = db.Column(db.String(300))
    phone = db.Column(db.String(20))
    services = db.Column(db.String(500))  # For vendors

class Event(db.Model):
    id = db.Column(db.String(100), primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    event_type = db.Column(db.String(100), nullable=False)
    user_email = db.Column(db.String(100), db.ForeignKey('user.email'))
    user_name = db.Column(db.String(100))
    vendor_email = db.Column(db.String(100))
    vendor_name = db.Column(db.String(100))
    vendor_services = db.Column(db.String(200))
    vendor_phone = db.Column(db.String(20))
    venue_owner_email = db.Column(db.String(100))
    venue_owner_name = db.Column(db.String(100))
    venue_location_lat = db.Column(db.String(50))
    venue_location_lng = db.Column(db.String(50))
    venue_address = db.Column(db.String(300))
    venue_phone = db.Column(db.String(20))
    reminder_date = db.Column(db.String(100))

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

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please use a different email.')
            return redirect(url_for('register'))

        # If venue owner, store location data
        venue_lat = request.form.get('venue_lat')
        venue_lng = request.form.get('venue_lng')
        venue_address = request.form.get('venue_address')
        phone = request.form.get('phone')
        services = request.form.get('services')

        new_user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role=role,
            venue_lat=venue_lat,
            venue_lng=venue_lng,
            venue_address=venue_address,
            phone=phone,
            services=services
        )
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please login.')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_email'] = user.email
            session['user_name'] = user.name
            session['user_role'] = user.role
            flash(f'Welcome back, {user.name}!')
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

@app.route('/select_event_type')
def select_event_type():
    if 'user_email' not in session:
        flash('Please login first.')
        return redirect(url_for('login'))
    
    return render_template('select_event_type.html')

@app.route('/select_providers', methods=['GET', 'POST'])
def select_providers():
    if 'user_email' not in session:
        flash('Please login first.')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        event_type = request.form.get('event_type')
        if not event_type:
            flash('Please select an event type.')
            return redirect(url_for('select_event_type'))
        
        session['selected_event_type'] = event_type
    
    event_type = session.get('selected_event_type')
    if not event_type:
        return redirect(url_for('select_event_type'))
    
    vendors = User.query.filter_by(role='Vendor').all()
    venue_owners = User.query.filter_by(role='Venue Owner').all()
    
    return render_template('select_providers.html', 
                         vendors=vendors, 
                         venue_owners=venue_owners,
                         event_type=event_type)

@app.route('/create_event', methods=['GET', 'POST'])
def create_event():
    if 'user_email' not in session:
        flash('Please login first.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        event_id = str(uuid.uuid4())
        title = request.form.get('title')
        description = request.form.get('description')
        event_type = session.get('selected_event_type')
        vendor_email = session.get('selected_vendor_email')
        venue_owner_email = session.get('selected_venue_owner_email')
        reminder_date = request.form.get('reminder_date')

        vendor = User.query.filter_by(email=vendor_email).first()
        venue_owner = User.query.filter_by(email=venue_owner_email).first()

        new_event = Event(
            id=event_id,
            title=title,
            description=description,
            event_type=event_type,
            user_email=session['user_email'],
            user_name=session['user_name'],
            vendor_email=vendor_email,
            vendor_name=vendor.name if vendor else 'Unknown',
            vendor_services=vendor.services if vendor else '',
            vendor_phone=vendor.phone if vendor else '',
            venue_owner_email=venue_owner_email,
            venue_owner_name=venue_owner.name if venue_owner else 'Unknown',
            venue_location_lat=venue_owner.venue_lat if venue_owner else '',
            venue_location_lng=venue_owner.venue_lng if venue_owner else '',
            venue_address=venue_owner.venue_address if venue_owner else '',
            venue_phone=venue_owner.phone if venue_owner else '',
            reminder_date=reminder_date
        )
        db.session.add(new_event)
        db.session.commit()

        # Clear session data
        session.pop('selected_event_type', None)
        session.pop('selected_vendor_email', None)
        session.pop('selected_venue_owner_email', None)

        flash('Event created successfully!')
        return redirect(url_for('my_events'))

    # Check if providers are selected
    if not session.get('selected_vendor_email') or not session.get('selected_venue_owner_email'):
        flash('Please select vendor and venue owner first.')
        return redirect(url_for('select_event_type'))

    event_type = session.get('selected_event_type')
    vendor = User.query.filter_by(email=session.get('selected_vendor_email')).first()
    venue_owner = User.query.filter_by(email=session.get('selected_venue_owner_email')).first()

    return render_template('create_event.html', 
                         event_type=event_type,
                         vendor=vendor,
                         venue_owner=venue_owner)

@app.route('/select_provider', methods=['POST'])
def select_provider():
    if 'user_email' not in session:
        flash('Please login first.')
        return redirect(url_for('login'))
    
    vendor_email = request.form.get('vendor_email')
    venue_owner_email = request.form.get('venue_owner_email')
    
    if vendor_email:
        session['selected_vendor_email'] = vendor_email
    if venue_owner_email:
        session['selected_venue_owner_email'] = venue_owner_email
    
    # Check if both are selected
    if session.get('selected_vendor_email') and session.get('selected_venue_owner_email'):
        return redirect(url_for('create_event'))
    
    return redirect(url_for('select_providers'))

@app.route('/my_events')
def my_events():
    if 'user_email' not in session:
        flash('Please login first.')
        return redirect(url_for('login'))

    events = Event.query.filter_by(user_email=session['user_email']).all()
    return render_template('my_events.html', events=events)

@app.route('/vendor_bookings')
def vendor_bookings():
    if 'user_email' not in session:
        flash('Please login first.')
        return redirect(url_for('login'))

    if session['user_role'] != 'Vendor':
        flash('Only vendors can view vendor bookings.')
        return redirect(url_for('home'))

    events = Event.query.filter_by(vendor_email=session['user_email']).all()
    return render_template('vendor_bookings.html', events=events)

@app.route('/venue_bookings')
def venue_bookings():
    if 'user_email' not in session:
        flash('Please login first.')
        return redirect(url_for('login'))

    if session['user_role'] != 'Venue Owner':
        flash('Only venue owners can view venue bookings.')
        return redirect(url_for('home'))

    events = Event.query.filter_by(venue_owner_email=session['user_email']).all()
    return render_template('venue_bookings.html', events=events)

@app.route('/event/<event_id>')
def view_event(event_id):
    if 'user_email' not in session:
        flash('Please login first.')
        return redirect(url_for('login'))

    event = Event.query.filter_by(id=event_id).first()

    if not event:
        flash('Event not found.')
        return redirect(url_for('home'))

    user_email = session['user_email']
    if (user_email != event.user_email and 
        user_email != event.vendor_email and 
        user_email != event.venue_owner_email):
        flash('You do not have permission to view this event.')
        return redirect(url_for('home'))

    return render_template('view_event.html', event=event)

@app.route('/event/<event_id>/delete', methods=['POST'])
def delete_event(event_id):
    if 'user_email' not in session:
        flash('Please login first.')
        return redirect(url_for('login'))

    event = Event.query.filter_by(id=event_id).first()

    if not event:
        flash('Event not found.')
        return redirect(url_for('home'))

    if session['user_email'] != event.user_email:
        flash('You do not have permission to delete this event.')
        return redirect(url_for('home'))

    db.session.delete(event)
    db.session.commit()

    flash('Event deleted successfully.')
    return redirect(url_for('my_events'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)