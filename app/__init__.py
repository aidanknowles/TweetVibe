from flask import Flask
from flask.ext.mongoengine import MongoEngine
from mongoengine import connect
import config


# Define instance of Flask
app = Flask(__name__)

# Add ChartKicks to Jinja
app.jinja_env.add_extension("chartkick.ext.charts")

# Configure app from config.py file
app.config.from_object("config")

# Connect to MongoDB db using credentials from config.py
connect(config.MONGODB_DB, host=config.MONGODB_HOST + config.MONGODB_USERNAME + ":" + config.MONGODB_PASSWORD
        + "@" + config.MONGODB_HOST_ADDRESS)

# Declare database for MongoEngine
db = MongoEngine(app)

# Configure logging if not running in debug mode
if config.DEBUG_MODE is False:
    import logging
    stream_handler = logging.StreamHandler()
    app.logger.addHandler(stream_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info("TweetVibe start")

# Import views and models
from app import views, models
