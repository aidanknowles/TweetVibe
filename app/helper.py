from mongoengine import *
from app.models import *
from datetime import datetime, timedelta


def tweet_collection_size():
    """
    :return: Number total number of documents in the database's Tweet collection
    """

    return len(Tweet.objects())


def count_tweets(search_term, location=None):
    """
    Finds number of documents in the Tweet collection matching a given search_term (and location, if provided).

    :param search_term: A given search term
    :param location: A given location address (optional)
    :return: The number of documents in the db matching the specified parameters
    """

    if location:
        return len(Tweet.objects(Q(keyword_search_term=search_term) & Q(location_address=location)))
    else:
        return len(Tweet.objects(keyword_search_term=search_term))


def get_historical_sentiment(search_term, location=None):
    """
    Calculates a keyword's historical sentiment (restricted within a location, if provided).

    :param search_term: A given search term
    :param location: A given location address (optional)
    :return: List with number of positive, negative and neutral results matching the query parameters
    """

    if location:
        positive = len(Tweet.objects(Q(keyword_search_term=search_term) & Q(location_address=location) & Q(sentiment_type="positive")))
        negative = len(Tweet.objects(Q(keyword_search_term=search_term) & Q(location_address=location) & Q(sentiment_type="negative")))
        neutral = len(Tweet.objects(Q(keyword_search_term=search_term) & Q(location_address=location) & Q(sentiment_type="neutral")))
    else:
        positive = len(Tweet.objects(Q(keyword_search_term=search_term) & Q(sentiment_type="positive")))
        negative = len(Tweet.objects(Q(keyword_search_term=search_term) & Q(sentiment_type="negative")))
        neutral = len(Tweet.objects(Q(keyword_search_term=search_term) & Q(sentiment_type="neutral")))

    result = [["Positive", positive], ["Neutral", neutral], ["Negative", negative]]
    return result


def get_historical_sentiment_avg(search_term, location=None):
    """
    Calculates the average sentiment score for a given keyword (restricted within a location, if provided).

    :param search_term: A given search term
    :param location: A given location address (optional)
    :return: Average sentiment score for all tweets matching the query parameters
    """

    total = 0

    if location:
        tweets = Tweet.objects(Q(keyword_search_term=search_term) & Q(location_address=location))
        count = len(tweets)
    else:
        tweets = Tweet.objects(Q(keyword_search_term=search_term))
        count = len(tweets)

    for tweet in tweets:
        total += tweet.sentiment_score

    # Calculate average
    avg = total / count
    avg = float("{0:.2f}".format((float(avg))))

    return avg


def get_query_sentiment_avg(tweets):
    """
    Calculates the average sentiment score in a given query set of Tweets.

    :param tweets: A query set of tweet data
    :return: The average sentiment score in the query set
    """

    total = 0
    count = len(tweets)

    for tweet in tweets:
        total += tweet.sentiment_score

    # Calculate average
    avg = total / count
    avg = float("{0:.2f}".format((float(avg))))

    return avg


def get_query_statistics(tweets, sentiment_aggregate_list):
    """
    Generates basic statistics for a given query set of Tweets.

    :param tweets: A query set of Tweets
    :param sentiment_aggregate_list: A list with number of positive, negative and neutral Tweets in the query set
    :return: Dictionary with total number of tweets and percentage break down of sentiment types
    """

    total = len(tweets)
    positive_percentage = float("{0:.2f}".format((float(sentiment_aggregate_list[0][1]/total*100))))
    neutral_percentage = float("{0:.2f}".format((float(sentiment_aggregate_list[1][1]/total*100))))
    negative_percentage = float("{0:.2f}".format((float(sentiment_aggregate_list[2][1]/total*100))))

    result = {"%Positive": positive_percentage, "%Neutral": neutral_percentage, "%Negative": negative_percentage, "Total": total}
    return result


def aggregate_sentiment(tweets):
    """
    Aggregates sentiment types for a given tweet collection.

    :param tweets: A query set of pre-analyzed Tweets
    :return: List with number of positive, negative and neutral Tweets
    """

    positive = 0
    negative = 0
    neutral = 0

    for tweet in tweets:
        if tweet.sentiment_type == "positive":
            positive += 1
        elif tweet.sentiment_type == "negative":
            negative += 1
        else:
            neutral += 1

    result = [["Positive", positive], ["Neutral", neutral], ["Negative", negative]]
    return result


def predominant_sentiment(sentiment_aggregate_list):
    """
    Gets the predominant sentiment type from a list of sentiments.
    (Eg [[positive, 3],[neutral, 10],[negative,15]])

    :param sentiment_aggregate_list: A list of sentiments with corresponding frequency values
    :return: The predominant sentiment type
    """

    positive = int(sentiment_aggregate_list[0][1])
    neutral = int(sentiment_aggregate_list[1][1])
    negative = int(sentiment_aggregate_list[2][1])

    if positive > neutral and positive > negative:
        return "positive"
    elif neutral > positive and neutral > negative:
        return "neutral"
    elif negative > positive and negative > neutral:
        return "negative"
    else:
        return "mixed"


def get_sentiment_overtime(keyword, location=None):
    """
    Gets sentiment statistics for average sentiment for a given keyword (and location, if specified) over the past 10 days.

    :param keyword: A given search keyword
    :param location: A given location address (optional)
    :return: List containing results
    """

    # Get date 10 days ago
    ten_days_ago = datetime.now() - timedelta(days=10)

    # Get raw PyMongo collection
    collection = Tweet._get_collection()

    if location:
        match = {
            "$match":
                {
                    "keyword_search_term": keyword,
                    "location_address": location,
                    "tweet_time": {"$gt": ten_days_ago}
                }
            }
    else:
        match = {
            "$match":
                {
                    "keyword_search_term": keyword,
                    "tweet_time": {"$gt": ten_days_ago}
                }
            }

    project = {
            "$project":
                {
                    "sentiment_score": 1,
                    "day":
                    {
                        "$substr": ["$tweet_time", 0, 10]
                    }
                }
            }

    group = {
            "$group":
                {
                    "_id": "$day",
                    "average":
                    {
                        "$avg": "$sentiment_score"
                    }
                }
            }

    limit = {"$limit": 10}

    # Perform aggregate query
    result = collection.aggregate([match, project, group, limit])

    # Add query results to list
    l = []
    for i in result['result']:
        average = "{0:.2f}".format(i['average'])
        t = [i['_id'], average]
        l.append(t)

    return l


def get_sentiment_trends(order):
    """
    Gets the top 10 most positive / negative sentiment triggers from the past 7 days.

    :param order: Indicate whether to return most positive (-1) or most negative (1) tweets
    :return: Query set of results
    """

    # Get date seven days ago
    seven_days_ago = datetime.now() - timedelta(days=7)

    # Get raw PyMongo collection
    collection = Tweet._get_collection()

    # Perform aggregate query
    result = collection.aggregate([
        {
            "$match":
                {
                    "tweet_time": {"$gt": seven_days_ago}
                }
        },
        {
            "$group":
                {
                    "_id": "$keyword_search_term",
                    "average":
                    {
                        "$avg": "$sentiment_score"
                    }
                }
        },
        {
            "$sort":
                {
                    "average": order
                }
        },
        {
            "$limit": 10
        }
    ])

    return result