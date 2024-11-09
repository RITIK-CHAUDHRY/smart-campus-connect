from flask import Flask
from config import Config
from extensions import db, bcrypt, login_manager, socketio
import sys

def create_app():
    print("Starting to create app", file=sys.stderr)
    app = Flask(__name__)
    app.config.from_object(Config)

    print("Initializing extensions", file=sys.stderr)
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))

    print("Creating app context", file=sys.stderr)
    with app.app_context():
        print("Importing routes", file=sys.stderr)
        from routes import init_routes
        init_routes(app)
        print("Routes imported", file=sys.stderr)

    return app

if __name__ == '__main__':
    print("Creating app", file=sys.stderr)
    app = create_app()
    print("App created", file=sys.stderr)
    print("Starting server", file=sys.stderr)
    socketio.run(app, debug=True, port=5001)
else:
    print("Importing app as a module", file=sys.stderr)
    app = create_app()
