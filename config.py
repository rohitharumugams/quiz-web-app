import os

# Secret key for session management
SECRET_KEY = os.urandom(24)

# Database configuration
SQLALCHEMY_DATABASE_URI = 'sqlite:///database.db'
SQLALCHEMY_TRACK_MODIFICATIONS = False