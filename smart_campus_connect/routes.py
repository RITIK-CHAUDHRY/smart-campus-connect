from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import User, Announcement, Event, Resource, Message, Notification
from extensions import db, bcrypt
import sys

def init_routes(app):
    @app.route('/')
    @app.route('/home')
    def home():
        return render_template('index.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        # Login logic here
        return render_template('login.html')

    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
        # Signup logic here
        return render_template('signup.html')

    @app.route('/profile')
    @login_required
    def profile():
        # Profile logic here
        return render_template('profile.html')

    # Add other routes as needed

    print("Routes initialized", file=sys.stderr)
