
from flask import Flask, render_template, redirect, url_for, flash, request, send_file
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from config import Config
from extensions import mongo, login_manager
from datetime import datetime
from bson import ObjectId

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
mongo.init_app(app)
login_manager.init_app(app)

# Import models after initializing extensions
from models import User, Announcement, Event, Message, Resource, Notification

@app.route('/')
def index():
    return render_template('index.html', title='Home')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        reg_number = request.form['reg_number']
        department = request.form['department']
        year = request.form['year']
        
        if mongo.db.users.find_one({'email': email}):
            flash('Email already registered')
            return redirect(url_for('register'))
        
        user = User(username, email, password, reg_number, department, year)
        user.save()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user_data = mongo.db.users.find_one({'email': email})
        if user_data and User.check_password(user_data['password_hash'], password):
            user = User.get_by_id(user_data['_id'])
            login_user(user)
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('index')
            return redirect(next_page)
        flash('Invalid email or password')
    return render_template('login.html', title='Sign In')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', title='Profile')

@app.route('/announcements')
def announcements():
    announcements = Announcement.get_all()
    return render_template('announcements.html', announcements=announcements)

@app.route('/announcement/<announcement_id>')
def announcement_detail(announcement_id):
    announcement = Announcement.get_by_id(announcement_id)
    if announcement:
        return render_template('announcement_detail.html', announcement=announcement)
    flash('Announcement not found')
    return redirect(url_for('announcements'))

@app.route('/create_announcement', methods=['GET', 'POST'])
@login_required
def create_announcement():
    if not current_user.is_admin:
        flash('You do not have permission to create announcements')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        announcement = Announcement(title=title, content=content, author=current_user.username)
        announcement.save()
        flash('Announcement created successfully')
        return redirect(url_for('announcements'))
    return render_template('create_announcement.html')

@app.route('/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('index'))
    
    # Search for users
    users = mongo.db.users.find({'$or': [
        {'username': {'$regex': query, '$options': 'i'}},
        {'email': {'$regex': query, '$options': 'i'}},
        {'department': {'$regex': query, '$options': 'i'}}
    ]})

    # Search for announcements
    announcements = mongo.db.announcements.find({
        '$or': [
            {'title': {'$regex': query, '$options': 'i'}},
            {'content': {'$regex': query, '$options': 'i'}}
        ]
    })

    return render_template('search_results.html', query=query, users=users, announcements=announcements)

@app.route('/events')
def events():
    events = Event.get_all()
    return render_template('events.html', events=events)

@app.route('/event/<event_id>')
def event_detail(event_id):
    event = Event.get_by_id(event_id)
    if event:
        return render_template('event_detail.html', event=event)
    flash('Event not found')
    return redirect(url_for('events'))

@app.route('/create_event', methods=['GET', 'POST'])
@login_required
def create_event():
    if not current_user.is_admin:
        flash('You do not have permission to create events')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        start_time = datetime.strptime(request.form['start_time'], '%Y-%m-%dT%H:%M')
        end_time = datetime.strptime(request.form['end_time'], '%Y-%m-%dT%H:%M')
        location = request.form['location']
        organizer = current_user.username
        
        event = Event(title, description, start_time, end_time, location, organizer)
        event.save()
        flash('Event created successfully')
        return redirect(url_for('events'))
    return render_template('create_event.html')

@app.route('/upcoming_events')
def upcoming_events():
    events = Event.get_upcoming_events()
    return render_template('upcoming_events.html', events=events)

@app.route('/messages')
@login_required
def messages():
    conversations = Message.get_user_conversations(current_user.username)
    return render_template('messages.html', conversations=conversations)

@app.route('/messages/<recipient>')
@login_required
def conversation(recipient):
    messages = Message.get_conversation(current_user.username, recipient)
    return render_template('conversation.html', messages=messages, recipient=recipient)

@app.route('/send_message', methods=['POST'])
@login_required
def send_message():
    recipient = request.form['recipient']
    content = request.form['content']
    message = Message(sender=current_user.username, recipient=recipient, content=content)
    message.save()
    return redirect(url_for('conversation', recipient=recipient))

import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/resources')
def resources():
    resources = Resource.get_all()
    return render_template('resources.html', resources=resources)

@app.route('/resource/<resource_id>')
def resource_detail(resource_id):
    resource = Resource.get_by_id(resource_id)
    if resource:
        return render_template('resource_detail.html', resource=resource)
    flash('Resource not found')
    return redirect(url_for('resources'))

@app.route('/upload_resource', methods=['GET', 'POST'])
@login_required
def upload_resource():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            title = request.form['title']
            description = request.form['description']
            resource = Resource(title, description, file_path, current_user.username)
            resource.save()
            
            flash('Resource uploaded successfully')
            return redirect(url_for('resources'))
    return render_template('upload_resource.html')

@app.route('/download_resource/<resource_id>')
@login_required
def download_resource(resource_id):
    resource = Resource.get_by_id(resource_id)
    if resource:
        return send_file(resource.file_path, as_attachment=True)
    flash('Resource not found')
    return redirect(url_for('resources'))

@app.route('/notifications')
@login_required
def notifications():
    notifications = Notification.get_user_notifications(current_user.id)
    return render_template('notifications.html', notifications=notifications)

@app.route('/mark_notification_read/<notification_id>')
@login_required
def mark_notification_read(notification_id):
    Notification.mark_as_read(notification_id)
    return redirect(url_for('notifications'))

@app.context_processor
def inject_unread_notifications_count():
    if current_user.is_authenticated:
        unread_count = Notification.get_unread_count(current_user.id)
        return {'unread_notifications_count': unread_count}
    return {'unread_notifications_count': 0}


from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You do not have permission to access this page.')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    return render_template('admin/dashboard.html')

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.get_all_users()
    return render_template('admin/users.html', users=users)

@app.route('/admin/toggle_admin/<user_id>')
@login_required
@admin_required
def toggle_admin(user_id):
    user = User.get_by_id(user_id)
    if user:
        user.is_admin = not user.is_admin
        mongo.db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'is_admin': user.is_admin}})
        flash(f"Admin status for {user.username} has been {'granted' if user.is_admin else 'revoked'}.")
    return redirect(url_for('admin_users'))


if __name__ == '__main__':
    app.run(debug=True)
