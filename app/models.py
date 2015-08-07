from app import db
from datetime import datetime
from config import HEROKU_MODE
import pytz


class Tweet(db.Document):
    """
    MongoDB model for Twitter Tweets.
    """

    tweet_id = db.IntField(required=True, unique=True)
    tweet_time = db.DateTimeField()
    tweet_user = db.StringField()
    tweet_user_fullname = db.StringField()
    profile_image_url = db.URLField()
    tweet_text = db.StringField()
    # Using Dic to store Latitude/Longitude because GeoLocationField not currently supported by Flask-MongoEngine ext
    location_geo = db.DictField()
    location_address = db.StringField()
    sentiment_type = db.StringField()
    sentiment_score = db.FloatField()
    keyword_search_term = db.StringField()
    location_search_term = db.StringField()
    stored_at = db.DateTimeField(default=datetime.now())


    # Define database meta settings for index and ordering of 'Tweet' documents
    meta = {
        "index": ["-stored_at", "tweet_id"],
        "ordering": ["-stored_at"]
    }

    def calc_time_ago(self):
        """
        Calculates the time past since a given 'tweet_time'.

        :return: The time in human readable format to a single precision, eg "2 hours ago".
        """

        from simpledate import SimpleDate
        from ago import human

        # Localize time to UTC using pytz
        tm = pytz.utc.localize(self.tweet_time)

        if HEROKU_MODE:
            tm = str(tm)
            tm = tm.split("+")
        else:
            # Convert to BST time using SimpleDate and remove microseconds
            tm = str(SimpleDate(tm).convert(country='GB'))
            tm = tm.split('.')

        # Convert to datetime object
        tm = datetime.strptime(tm[0], '%Y-%m-%d %H:%M:%S')

        # Use human to calculate and convert the time to an 'ago' format
        return human(tm, 1)