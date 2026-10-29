import os
from dotenv import load_dotenv

load_dotenv()

class Config:

    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    SESSION_PERMANENT = False

    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '3306')
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_NAME = os.environ.get('DB_NAME', 'talknon')

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        f"?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SMS_ENABLED = os.environ.get('SMS_ENABLED', 'false').lower() == 'true'
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', '')

    LOCATION_CHECK_INTERVAL = int(os.environ.get('LOCATION_CHECK_INTERVAL', 600))
    DEFAULT_CAFE_RADIUS = int(os.environ.get('DEFAULT_CAFE_RADIUS', 25))

    DEFAULT_LANGUAGE = os.environ.get('DEFAULT_LANGUAGE', 'tr')
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'app/static/uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 5242880))

    WTF_CSRF_ENABLED = True

    RATELIMIT_DEFAULT = "200 per day;50 per hour"
    RATELIMIT_STORAGE_URI = "memory://"

class DevelopmentConfig(Config):

    DEBUG = True
    SQLALCHEMY_ECHO = False
    DEV_SKIP_LOCATION = True
    RATELIMIT_ENABLED = False

class ProductionConfig(Config):

    DEBUG = False
    SQLALCHEMY_ECHO = False

class TestingConfig(Config):

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
}
