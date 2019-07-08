from flask import Flask
from config import Config
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from app.extensions import mongo

app = Flask(__name__)
moment = Moment(app)
app.config.from_object(Config)
mongo.init_app(app)
bootstrap = Bootstrap(app)
app.jinja_env.filters['zip'] = zip

from app import routes