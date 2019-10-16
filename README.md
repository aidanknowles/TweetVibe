# TweetVibe

### What is  TweetVibe ?

TweetVibe is an experimental opinion mining web application which retrieves, processes, classifies and tracks the sentiment of English language Twitter tweets.

The tool can be used to disocver the sentiment for a given keyword, hashtag (within a location radius, if desired) or to analyze a specific user's tweet history.

### Who is behind it?

The application was created by a former MSc Computer Science student at the School of Computer Science and Informatics, University College Dublin, Ireland.

Produced as a final project for a graduate class in Software Engineering.


### How does it work?

Behind the scenes, Tweetvibe is powered primarily by the Python 3 programming language.

It incorporates the Twython library, a pure Python wrapper for the Twitter REST API v1.1, in combination with AlchemyAPI - a popular, advanced machine learning based natural language processing web service - to perform the retrieval, keyword/entity extraction and sentiment analysis of the tweets.

For rapid web development, deployment and responsive design - the Flask Python microframework (with several extensions), Twitter's own Bootstrap frontend HTML/CSS/JS framework and Highcharts visualization graphics API are utilized.

To store data, the application adopts MongoDB - a popular document oriented NoSQL database.

Application/Database platform hosting is provided in the cloud by Heroku and MongoLab.

For more technology info, check out the project's humans.txt file.


### Sentiment analysis?

(from Wikipedia)

Sentiment analysis (also known as 'opinion mining') refers to the use of natural language processing, text analysis and computational linguistics to identify and extract subjective information in source materials.

Generally speaking, sentiment analysis aims to determine the attitude of a speaker or a writer with respect to some topic or the overall contextual polarity of a document.

The attitude may be his or her judgment or evaluation, affective state (the emotional state of the author when writing), or the intended emotional communication (the emotional effect the author wishes to have on the reader).
