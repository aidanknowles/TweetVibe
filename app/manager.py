from twython import Twython, TwythonAuthError
from app.alchemyapi import AlchemyAPI
from app.models import Tweet
from datetime import datetime
import config


def save_tweets(tweets, search_term, location_search_term=None):
    """
    Saves given tweet data in MongoDB database.

    :param tweets: Tweet data
    :param search_term: Search term entered by user
    :param location_search_term: Location search term entered by user (optional)
    """

    try:
        if location_search_term:
            # Cycle through list of Tweets
            for status in tweets:
                tweet_id = status['tweet_id']
                # Check if tweet already exists in db, skip this iteration if it does
                id_query = len(Tweet.objects(tweet_id=tweet_id))
                if id_query >= 1:
                    continue
                # Define record to save to db
                record = Tweet(
                    tweet_id=status['tweet_id'],
                    tweet_time=status['created_at'],
                    tweet_text=status['text'],
                    tweet_user=status['user'],
                    tweet_user_fullname=status['user_fullname'],
                    profile_image_url=status['profile_image_url'],
                    sentiment_type=status['sentiment'],
                    sentiment_score=status['sentimentScore'],
                    location_geo=status['location_geo'],
                    location_address=status['location_address'],
                    keyword_search_term=search_term,
                    location_search_term=location_search_term
                )
                # Save to DB
                record.save()
        else:
            # Cycle through list of processed Tweets
            for status in tweets:
                tweet_id = status['tweet_id']
                # Check if tweet already exists in db, skip this iteration if it does
                id_query = len(Tweet.objects(tweet_id=tweet_id))
                if id_query >= 1:
                    continue
                # Define record to save to db
                record = Tweet(
                    tweet_id=status['tweet_id'],
                    tweet_time=status['created_at'],
                    tweet_text=status['text'],
                    tweet_user=status['user'],
                    tweet_user_fullname=status['user_fullname'],
                    profile_image_url=status['profile_image_url'],
                    sentiment_type=status['sentiment'],
                    sentiment_score=status['sentimentScore'],
                    keyword_search_term=search_term
                )
                # Save to DB
                record.save()
    except Exception:
        raise Exception("Database error")


def twitter_auth():
    """
    Imports Twitter API credentials from config file and performs OAuth2 using app credentials from config.py

    :return: Authorized instance of Twython
    """

    # Pulling Twitter API credentials from config.py
    key = config.TWITTER_CONSUMER_KEY
    key_secret = config.TWITTER_CONSUMER_SECRET
    token = config.TWITTER_ACCESS_TOKEN
    token_secret = config.TWITTER_ACCESS_TOKEN_SECRET

    # Attempting OAuth connection to Twitter using Twython with API credentials
    try:
        twitter = Twython(key, key_secret, token, token_secret)
    except TwythonAuthError:
        raise Exception("Twython auth error")

    return twitter


def get_geo_info(place_name):
    """
    Gets coordinates and address for a given place name using geopy.

    :param place_name: Name of place to search for, eg "San Francisco"
    :return: Location object with latitude, longitude and name attributes
    """

    from geopy.geocoders import Nominatim

    # Create geo_locator object instance
    geo_locator = Nominatim()

    # Attempt to obtain geo data for given place name
    try:
        location = geo_locator.geocode(place_name)
    except Exception:
        raise Exception("Location error")

    if not location:
        raise Exception("Location error")

    return location


def search_keyword(keyword, count, location=None):
    """
    Performs a Twitter search for a given keyword.
    Will restrict keyword search to within 10 miles radius of given location (if provided).

    :param keyword: Keyword to search
    :param location: Location object from geopy to restrict results to (optional)
    :param count: Number of Tweets to search for
    :return: List of dictionaries containing parsed Tweet data from search
    """

    # Perform OAuth connection to Twitter, creates instance of Twython
    twitter = twitter_auth()

    is_location_search = False
    in_db = False

    # List to store our data
    tweets = []

    # Attempt to query Twitter REST API using Twython
    try:
        if location is None:
            search_result = twitter.search(q=keyword, lang="en", count=count)
        else:
            is_location_search = True
            search_result = twitter.search(q=keyword, lang="en", geocode="%s,%s,10mi" % (location.latitude, location.longitude), count=count)
    except Exception:
        raise Exception("No Twitter results returned")

    # Cycle through results and parse the data we want, save as dictionary and store in 'tweets' list
    for status in search_result['statuses']:
        tweet_id = status['id']
        # Check if Tweet is already in DB
        id_query = len(Tweet.objects(tweet_id=tweet_id))
        if id_query >= 1:
            in_db = True
            continue
        tweet = {}
        tweet['tweet_id'] = tweet_id
        tweet['text'] = status['text'].strip()
        tm = status['created_at']
        tm = datetime.strptime(tm, '%a %b %d %H:%M:%S +0000 %Y')
        tweet['created_at'] = tm
        tweet['user'] = status['user']['screen_name'].strip()
        tweet['user_fullname'] = status['user']['name']
        tweet['profile_image_url'] = status['user']['profile_image_url']
        if is_location_search:
            tweet['location_geo'] = {"latitude": location.latitude, "longitude": location.longitude}
            tweet['location_address'] = location.address
        # Append parsed tweet data dictionary to results list
        tweets.append(tweet)

    # If no search results returned and data is not in our database, raise exception
    if not tweets and not in_db:
        raise Exception("No Twitter results returned")

    return tweets


def search_user(screen_name, count):
    """
    Performs a Twitter search for a given username.

    :param screen_name: Username of Twitter user to search for
    :param count: Number of the user's Tweets to return
    :return: List of dictionaries containing parsed Tweet data from search
    """

    # Perform OAuth connection to Twitter, creates instance of Twython
    twitter = twitter_auth()

    in_db = False

    # List to store our results
    tweets = []

    # Attempt to query Twitter REST API using Twython
    try:
        search_result = twitter.get_user_timeline(screen_name=screen_name, count=count)
    except Exception:
        raise Exception("No Twitter results returned")

    if search_result[0]['user']['lang'] != "en":
        # If not English, we can't perform sentiment analysis (limitation of AlchemyAPI)
        raise Exception("Not an English language user")

    # Cycle through results and parse the data we want, save as dictionary and store in 'tweets' list
    for status in search_result:
        tweet_id = status['id']
        # Check if Tweet is already in DB
        id_query = len(Tweet.objects(tweet_id=tweet_id))
        if id_query >= 1:
            in_db = True
            continue
        tweet = {}
        tweet['tweet_id'] = tweet_id
        tweet['text'] = status['text'].strip()
        tm = status['created_at']
        tm = datetime.strptime(tm, '%a %b %d %H:%M:%S +0000 %Y')
        tweet['created_at'] = tm
        tweet['user'] = screen_name[1:]
        tweet['user_fullname'] = status['user']['name']
        tweet['profile_image_url'] = status['user']['profile_image_url']
        # Add parsed tweet data dictionary to results list
        tweets.append(tweet)

    # If no search results returned and data is not in our database, raise exception
    if not tweets and not in_db:
        raise Exception("No Twitter results returned")

    return tweets


def analysis_worker(in_queue, out_queue):
    """
    Performs sentiment analysis on Tweet data using AlchemyAPI.

    :param in_queue: Shared input queue of Tweet data to analyze
    :param out_queue: Shared output queue of Tweet data to analyze
    """

    # Attempt to create new AlchemyAPI instance
    try:
        alchemy = AlchemyAPI()
    except:
        raise Exception("AlchemyAPI auth error")

    while not in_queue.empty():
        # Get Tweet from the queue
        tweet = in_queue.get()
        tweet['sentiment'] = {}

        # Attempt to call AlchemyAPI to perform document level sentiment of the Tweet text
        try:
            sentiment = alchemy.sentiment("text", tweet['text'], {"showSourceText": 1})
        except:
            raise Exception("AlchemyAPI error")

        # Add sentiment data (score + sentiment type) to Tweet dictionary
        try:
            tweet['sentiment'] = sentiment['docSentiment']['type']
            if tweet['sentiment'] != 'neutral':
                tweet['sentimentScore'] = float("{0:.2f}".format((float(sentiment['docSentiment']['score'])*100)))
            else:
                tweet['sentimentScore'] = 0
        except KeyError:
            tweet['sentiment'] = "neutral"
            tweet['sentimentScore'] = 0
        except:
            raise Exception("Classification error")

        # Signal task has been complete
        in_queue.task_done()
        # Add analyzed Tweet to output queue
        out_queue.put(tweet)


def analysis_supervisor(tweets, search_term, location_search_term=None):
    """
    Spawns and manages threads (concurrency limit defined in config.py) to perform analysis of gathered Tweet data.
    Passes Tweet data (with newly added analysis info) to 'save_tweets' function to save to database.

    :param tweets: Parsed tweet data to analyze
    :param search_term: Term associated with this search
    """

    import queue
    import threading

    # Set concurrent thread limit
    limit = config.ALCHEMY_THREAD_LIMIT

    # Create queues
    in_queue = queue.Queue()
    out_queue = queue.Queue()

    # List to store threads
    threads = []

    # Add Tweets to queue
    for tweet in tweets:
        in_queue.put(tweet)

    # Get size of full queue
    in_size = in_queue.qsize()

    # Spawn threads up to concurrency limit
    for i in range(limit):
        # Set target for thread
        t = threading.Thread(target=analysis_worker, args=(in_queue, out_queue))
        # Set as daemon
        t.daemon = True
        # Append to threads list
        threads.append(t)
        # Put thread to work
        t.start()

    # Wait for threads to finish
    in_queue.join()

    while True:
        # Check if all Tweets have been processed
        if in_size == out_queue.qsize():
            break

    # List to store our analyzed Tweet data
    output = []

    # Add processed results to list
    while not out_queue.empty():
        output.append(out_queue.get())

    # Pass processed Tweets list to 'save_tweets' function to save to database
    save_tweets(output, search_term, location_search_term)
