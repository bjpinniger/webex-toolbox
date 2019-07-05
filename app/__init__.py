from flask import Flask
from config import Config
from flask_bootstrap import Bootstrap
from app.extensions import mongo

app = Flask(__name__)
app.config.from_object(Config)
mongo.init_app(app)
bootstrap = Bootstrap(app)
app.jinja_env.filters['zip'] = zip

from app import routes