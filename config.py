import os

class Config(object):
    MONGO_URI = os.environ.get('MONGO_URI')
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    clientID = os.environ.get('CLIENT_ID')
    secretID = os.environ.get('SECRET_ID')
    redirectURI = os.environ.get('REDIRECT_URI')
    webhookURI = os.environ.get('WEBHOOK_URI')
    webex_admin = os.environ.get('WEBEX_ADMIN')
    webex_pwd = os.environ.get('WEBEX_PWD')
    webex_site = os.environ.get('WEBEX_SITE')
    WTF_CSRF_ENABLED = True