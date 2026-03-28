import os
from . import DB_NAME


class BaseConfig:
    '''
    Base config
    '''
    IP = os.environ.get("IP", "0.0.0.0")
    PORT = int(os.environ.get("PORT", 5000))
    SECRET_KEY = os.environ.get("SECRET_KEY", "")
    SQLALCHEMY_TRACK_MODIFICATIONS = os.environ.get("SQLALCHEMY_TRACK_MODIFICATIONS", "False").lower() == "true"
    BASE_URL = os.environ.get("BASE_URL", "")
    PROJECT_FILES_UPLOAD_FOLDER = "project_files"
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True").lower() == "true"
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.mail.me.com")
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "xxxxxxxx@kittieproductions.co.uk")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "xxxxxxxxxxx")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "xxxxxx@kittieproductions.co.uk")


class DevConfig(BaseConfig):
    '''
    Development config
    '''
    DEBUG = os.environ.get("DEBUG", "True").lower() == "true"
    DEVELOPMENT = os.environ.get("DEVELOPMENT", "True").lower() == "true"
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI", f"sqlite:///{DB_NAME}")


class ProdConfig(BaseConfig):
    '''
    Production config
    '''
    DEBUG = os.environ.get("DEBUG", "False").lower() == "true"
    DEVELOPMENT = os.environ.get("DEVELOPMENT", "False").lower() == "true"
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI", f"sqlite:///{DB_NAME}")
