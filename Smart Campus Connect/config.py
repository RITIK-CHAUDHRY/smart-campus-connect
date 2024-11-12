
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb+srv://RITIK_CHAUDHRY:0LNbZFYM7aHC0wWm@cluster0.sm38b.mongodb.net/'
