from flask import render_template, flash, redirect, url_for, request
from mongoengine import *
from app import app
from app.models import Tweet
from app.forms import SearchFrom
import config


@app.route("/index", methods=['GET', 'POST'])
@app.route("/", methods=['GET', 'POST'])
def index():
    """
    :return:    Rendered template for index page
    """

    page = "home"

    # Generate form
    form = SearchFrom()

    return render_template("index.html", page=page, form=form)


@app.route("/about")
def about():
    """
    :return:    Rendered template for about page
    """

    page = "about"
    return render_template("about.html", page=page)


@app.route("/contact", methods=['GET', 'POST'])
def contact():
    """
    :return:    Rendered template for contact page
    """

    page = "contact"
    return render_template("contact.html", page=page)


@app.route("/search", methods=['GET', 'POST'])
def search():
    """
    Handles post request from index page search form, processes form and calls manager functions accordingly.
    Passes results to rendered search template, or redirects user to homepage if exception occurs.

    :return:    Rendered template with search results
    """

    from app import manager
    from app import helper
    import time

    page = "search"

    if request.method == 'POST':
        # Get form data with trailing spaces removed
        keyword = request.form['keyword'].strip()
        count = request.form['count'].strip()
        location = request.form['location'].strip()

        # Check if search term has been provided
        if not keyword:
            flash("Blessed are the forgetful! Looks like you didn't enter a search parameter.")
            return redirect(url_for('index'))

        # If user hasn't specified a number of Tweets to search for, use defualt (15)
        if not count:
            count = config.TWEET_SEARCH_LIMIT_DEFAULT

        # If count provided, check to sure it does not exceed max (100)
        if int(count) > config.TWEET_SEARCH_LIMIT_MAX:
            # If exceeds max, set count to max
            count = config.TWEET_SEARCH_LIMIT_MAX

        # Check if supplied count is negative
        if int(count) <= 0:
            flash("Please enter a valid number of Tweets to search (1-100)")
            return redirect(url_for('index'))

        user_search = False
        location_search_term = None

        # Get time
        t1 = time.time()

        # Attempt to perform search, analysis and storage
        try:
            if keyword and not location:
                keyword = keyword.lower()
                # Check if searching for a user
                if keyword[0] == "@":
                    user_search = True
                    manager.analysis_supervisor(manager.search_user(keyword, count), keyword)
                else:
                    manager.analysis_supervisor(manager.search_keyword(keyword, count), keyword)
            if keyword and location:
                keyword = keyword.lower()
                location = location.lower()
                # Check if searching for a user
                if keyword[0] == "@":
                    user_search = True
                    manager.analysis_supervisor(manager.search_user(keyword, count), keyword)
                else:
                    location_search_term = location
                    location = manager.get_geo_info(location_search_term)
                    manager.analysis_supervisor(manager.search_keyword(keyword, count, location), keyword, location_search_term)
        except Exception as e:
            # Exception handling for any errors that may occur in retrieving / analyzing / saving data
            e = str(e)
            if e == "No Twitter results returned":
                if location_search_term:
                    flash("Sorry, Twitter returned no results for: \"" + keyword + "\" near " + "\"" +
                          location_search_term + "\"")
                else:
                    flash("Sorry, Twitter returned no results for: \"" + keyword + "\"")
            elif e == "Twython auth error":
                flash("Oops, it appears we're having trouble connecting to Twitter. Please try again later.")
            elif e == "AlchemyAPI auth error":
                flash("Oops, it appears we're having trouble connecting to our language processing API. "
                      "Please try again later.")
            elif e == "AlchemyAPI error":
                flash("Oops, it appears we had trouble analyzing one or more of the results for that search")
            elif e == "Not an English language user":
                flash("Sorry, it appears that account " + keyword + " is not an English language user. Presently, "
                      "Tweetvibe can only analyze English tweets.")
            elif e == "Location error":
                flash("Oops, it appears we had trouble identifying location " + "\"" + location_search_term + "\"")
            elif e == "Database error":
                flash("Oops, it appears we are experiencing a problem interacting with our database.")
            else:
                flash("Oops, something went wrong. A team of highly trained engineer monkeys have been dispatched to"
                      " fix the problem. Please try again later.")
            # Redirect to index with flash message
            return redirect(url_for('index'))

        # Attempt to get results from database
        try:
            if location:
                results = Tweet.objects(Q(keyword_search_term=keyword) & Q(location_address=location.address)).order_by('-stored_at', '-tweet_time').limit(int(count))
            else:
                results = Tweet.objects(keyword_search_term=keyword).order_by('-stored_at', '-tweet_time').limit(int(count))
        except:
            flash("Oops, it appears we are experiencing a problem querying our database.")
            return redirect(url_for('index'))

        try:
            search_aggregate = helper.aggregate_sentiment(results)
            search_avg = helper.get_query_sentiment_avg(results)
        except:
            flash("Oops, something went wrong. A team of highly trained engineer monkeys have been dispatched to"
                  " fix the problem. Please try again later.")
            return redirect(url_for('index'))

        # Calculate time taken to perform search and analysis
        t2 = time.time()
        time_taken = t2 - t1

        if location:
            # Format location latitude/longitude to 2 decimal places
            longitude = "{:.2f}".format(float(location.longitude))
            latitude = "{:.2f}".format(float(location.latitude))
            hist_avg = helper.get_historical_sentiment_avg(keyword, location.address)
            hist_data = helper.get_historical_sentiment(keyword, location.address)
            hist_predominant_sentiment = helper.predominant_sentiment(hist_data)
            return render_template(
                "search.html",
                time_taken=time_taken,
                results=results,
                page=page,
                keyword=keyword,
                location_search_term=location_search_term,
                location=location.address,
                longitude=longitude,
                latitude=latitude,
                search_count=count,
                search_aggregate=search_aggregate,
                search_avg=search_avg,
                search_stats=helper.get_query_statistics(results, search_aggregate),
                dom_sentiment=hist_predominant_sentiment,
                hist_data=hist_data,
                hist_avg=hist_avg,
                overtime_data=helper.get_sentiment_overtime(keyword, location.address)
            )
        elif user_search:
            hist_avg = helper.get_historical_sentiment_avg(keyword)
            hist_data = helper.get_historical_sentiment(keyword)
            hist_predominant_sentiment = helper.predominant_sentiment(hist_data)
            return render_template(
                "search.html",
                results=results,
                time_taken=time_taken,
                page=page,
                user=keyword,
                search_count=count,
                search_aggregate=search_aggregate,
                search_avg=search_avg,
                search_stats=helper.get_query_statistics(results, search_aggregate),
                dom_sentiment=hist_predominant_sentiment,
                hist_data=hist_data,
                hist_avg=hist_avg,
                overtime_data=helper.get_sentiment_overtime(keyword)
            )
        else:
            hist_avg = helper.get_historical_sentiment_avg(keyword)
            hist_data = helper.get_historical_sentiment(keyword)
            hist_predominant_sentiment = helper.predominant_sentiment(hist_data)
            return render_template(
                "search.html",
                results=results,
                time_taken=time_taken,
                page=page,
                keyword=keyword,
                search_count=count,
                search_aggregate=search_aggregate,
                search_avg=search_avg,
                search_stats=helper.get_query_statistics(results, search_aggregate),
                dom_sentiment=hist_predominant_sentiment,
                hist_data=hist_data,
                hist_avg=hist_avg,
                overtime_data=helper.get_sentiment_overtime(keyword)
            )
    else:
        return redirect(url_for('index'))


@app.route("/trends")
def trends():
    """
    Gets sentiment trends for the past 7 days, renders 'trends' template with data.

    :return: Rendered template with trend results
    """

    from app import helper

    page = "trends"

    # Get 7 day trends for top positive and negative sentiments
    positive_trends = helper.get_sentiment_trends(-1)
    negative_trends = helper.get_sentiment_trends(1)

    return render_template(
        "trends.html",
        page=page,
        positive_trends=positive_trends,
        negative_trends=negative_trends
    )


@app.route("/humans")
def humans():
    """
    :return:    Serves static 'humans.txt' file
    """

    return app.send_static_file("misc/humans.txt")


@app.errorhandler(404)
def page_not_found(e):
    """
    :return:    Rendered error page for 404 error (page not found)
    """

    return render_template("error.html", e=str(e)), 404


@app.errorhandler(403)
def forbidden(e):
    """
    :return:    Rendered error page for 403 error (forbidden)
    """

    return render_template("error.html", e=str(e)), 403


@app.errorhandler(500)
def internal_server_error(e):
    """
    :return:    Rendered error page for 500 error (internal server error)
    """

    return render_template("error.html", e=str(e)), 500