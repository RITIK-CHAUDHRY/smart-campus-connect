
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import mongo, login_manager
from bson.objectid import ObjectId
from datetime import datetime

class User(UserMixin):
    def __init__(self, username, email, password, reg_number, department, year, is_admin=False):
        self.username = username
        self.email = email
        self.password_hash = generate_password_hash(password)
        self.reg_number = reg_number
        self.department = department
        self.year = year
        self.is_admin = is_admin

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def save(self):
        user_data = {
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'reg_number': self.reg_number,
            'department': self.department,
            'year': self.year,
            'is_admin': self.is_admin
        }
        return mongo.db.users.insert_one(user_data)

    @staticmethod
    def get_by_id(user_id):
        user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        if user_data:
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                password='',
                reg_number=user_data['reg_number'],
                department=user_data['department'],
                year=user_data['year'],
                is_admin=user_data.get('is_admin', False)
            )
            user.id = str(user_data['_id'])
            return user
        return None

    @staticmethod
    def get_all_users():
        users = mongo.db.users.find()
        return [User.get_by_id(user['_id']) for user in users]

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)

class Announcement:
    def __init__(self, title, content, author, created_at=None, _id=None):
        self.title = title
        self.content = content
        self.author = author
        self.created_at = created_at or datetime.utcnow()
        self._id = _id or ObjectId()

    def save(self):
        announcement_data = {
            'title': self.title,
            'content': self.content,
            'author': self.author,
            'created_at': self.created_at,
        }
        if self._id:
            mongo.db.announcements.update_one({'_id': self._id}, {'$set': announcement_data})
        else:
            result = mongo.db.announcements.insert_one(announcement_data)
            self._id = result.inserted_id

    @staticmethod
    def get_all():
        announcements = mongo.db.announcements.find().sort('created_at', -1)
        return [Announcement(**announcement) for announcement in announcements]

    @staticmethod
    def get_by_id(announcement_id):
        announcement = mongo.db.announcements.find_one({'_id': ObjectId(announcement_id)})
        return Announcement(**announcement) if announcement else None

class Event:
    def __init__(self, title, description, start_time, end_time, location, organizer, _id=None):
        self.title = title
        self.description = description
        self.start_time = start_time
        self.end_time = end_time
        self.location = location
        self.organizer = organizer
        self._id = _id or ObjectId()

    def save(self):
        event_data = {
            'title': self.title,
            'description': self.description,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'location': self.location,
            'organizer': self.organizer,
        }
        if self._id:
            mongo.db.events.update_one({'_id': self._id}, {'$set': event_data})
        else:
            result = mongo.db.events.insert_one(event_data)
            self._id = result.inserted_id

    @staticmethod
    def get_all():
        events = mongo.db.events.find().sort('start_time', 1)
        return [Event(**event) for event in events]

    @staticmethod
    def get_by_id(event_id):
        event = mongo.db.events.find_one({'_id': ObjectId(event_id)})
        return Event(**event) if event else None

    @staticmethod
    def get_upcoming_events(limit=5):
        current_time = datetime.utcnow()
        events = mongo.db.events.find({'start_time': {'$gte': current_time}}).sort('start_time', 1).limit(limit)
        return [Event(**event) for event in events]

class Message:
    def __init__(self, sender, recipient, content, timestamp=None, _id=None):
        self.sender = sender
        self.recipient = recipient
        self.content = content
        self.timestamp = timestamp or datetime.utcnow()
        self._id = _id or ObjectId()

    def save(self):
        message_data = {
            'sender': self.sender,
            'recipient': self.recipient,
            'content': self.content,
            'timestamp': self.timestamp,
        }
        if self._id:
            mongo.db.messages.update_one({'_id': self._id}, {'$set': message_data})
        else:
            result = mongo.db.messages.insert_one(message_data)
            self._id = result.inserted_id

    @staticmethod
    def get_conversation(user1, user2):
        messages = mongo.db.messages.find({
            '$or': [
                {'sender': user1, 'recipient': user2},
                {'sender': user2, 'recipient': user1}
            ]
        }).sort('timestamp', 1)
        return [Message(**message) for message in messages]

    @staticmethod
    def get_user_conversations(user):
        conversations = mongo.db.messages.aggregate([
            {'$match': {'$or': [{'sender': user}, {'recipient': user}]}},
            {'$sort': {'timestamp': -1}},
            {'$group': {
                '_id': {
                    '$cond': [
                        {'$eq': ['$sender', user]},
                        '$recipient',
                        '$sender'
                    ]
                },
                'last_message': {'$first': '$$ROOT'}
            }}
        ])
        return [conversation['last_message'] for conversation in conversations]

class Resource:
    def __init__(self, title, description, file_path, uploaded_by, upload_date=None, _id=None):
        self.title = title
        self.description = description
        self.file_path = file_path
        self.uploaded_by = uploaded_by
        self.upload_date = upload_date or datetime.utcnow()
        self._id = _id or ObjectId()

    def save(self):
        resource_data = {
            'title': self.title,
            'description': self.description,
            'file_path': self.file_path,
            'uploaded_by': self.uploaded_by,
            'upload_date': self.upload_date,
        }
        if self._id:
            mongo.db.resources.update_one({'_id': self._id}, {'$set': resource_data})
        else:
            result = mongo.db.resources.insert_one(resource_data)
            self._id = result.inserted_id

    @staticmethod
    def get_all():
        resources = mongo.db.resources.find().sort('upload_date', -1)
        return [Resource(**resource) for resource in resources]

    @staticmethod
    def get_by_id(resource_id):
        resource = mongo.db.resources.find_one({'_id': ObjectId(resource_id)})
        return Resource(**resource) if resource else None


from datetime import datetime
from bson import ObjectId

class Notification:
    def __init__(self, user_id, message, is_read=False, created_at=None, _id=None):
        self.user_id = user_id
        self.message = message
        self.is_read = is_read
        self.created_at = created_at or datetime.utcnow()
        self._id = _id or ObjectId()

    def save(self):
        notification_data = {
            'user_id': self.user_id,
            'message': self.message,
            'is_read': self.is_read,
            'created_at': self.created_at,
        }
        if self._id:
            mongo.db.notifications.update_one({'_id': self._id}, {'$set': notification_data})
        else:
            result = mongo.db.notifications.insert_one(notification_data)
            self._id = result.inserted_id

    @staticmethod
    def get_user_notifications(user_id):
        notifications = mongo.db.notifications.find({'user_id': user_id}).sort('created_at', -1)
        return [Notification(**notification) for notification in notifications]

    @staticmethod
    def mark_as_read(notification_id):
        mongo.db.notifications.update_one({'_id': ObjectId(notification_id)}, {'$set': {'is_read': True}})

    @staticmethod
    def get_unread_count(user_id):
        return mongo.db.notifications.count_documents({'user_id': user_id, 'is_read': False})





