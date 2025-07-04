import os
from google.cloud.sql.connector import Connector
import sqlalchemy

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    # Project and database configuration
    PROJECT_ID = "bbcproject-464709"
    INSTANCE_NAME = "bbc-website-instance"
    DB_NAME = "app_db"
    DB_USER = "app_user"
    DB_PASSWORD = "123"
    DB_REGION = "us-central1-c"  # Note: Should be region only (e.g., "us-central1"), not zone
    
    @property
    def SQLALCHEMY_DATABASE_URI(self):
        # First try environment variable
        env_uri = os.environ.get("SQLALCHEMY_DATABASE_URI")
        if env_uri:
            return env_uri
            
        # Fall back to Cloud SQL connection
        connector = Connector()
        
        def getconn():
            conn = connector.connect(
                f"{self.PROJECT_ID}:{self.DB_REGION}:{self.INSTANCE_NAME}",
                "pg8000",
                user=self.DB_USER,
                password=self.DB_PASSWORD,
                db=self.DB_NAME
            )
            return conn
            
        engine = sqlalchemy.create_engine(
            "postgresql+pg8000://",
            creator=getconn,
        )
        return engine.url

class Config(object):
    SECRET_KEY = os.environ.get("SECRET_KEY") or "you-will-never-guess"
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI") or \
        'postgresql://postgres:postgres@postgresdb:5432/postgres'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or "mailhog"
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 1025)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['cici@example.com']
    POSTS_PER_PAGE = 3
    LANGUAGES = ['en', 'es', 'zh']