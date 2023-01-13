"""
The main entrypoint for the Twitter bot.
Followed a tutorial: https://developer.twitter.com/en/docs/tutorials/creating-a-twitter-bot-with-python--oauth-2-0--and-v2-of-the-twi
"""

import base64
import hashlib
import json
import logging
import os
import re

import oauthlib
import redis
import requests
import tweepy
from bs4 import BeautifulSoup
from flask import Flask, session, redirect, request
from requests_oauthlib import OAuth2Session, TokenUpdated

from crawl import TTCMeetingsChecker


# Web server
app = Flask(__name__)

consumer_key = os.environ['CONSUMER_KEY']
consumer_secret = os.environ['CONSUMER_SECRET']
access_token = os.environ['ACCESS_TOKEN']
access_token_secret = os.environ['ACCESS_TOKEN_SECRET']
auth = tweepy.OAuth1UserHandler(
    consumer_key, consumer_secret, access_token, access_token_secret
)
twitter_api = tweepy.API(auth)

# Logs
# logging.basicConfig(filename='logs\\ttcmeetbot.log', level=logging.INFO)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


@app.route('/', methods=['GET'])
def tweet_meeting_updates(refresh_token = None):
    log.info("checking for meeting updates")
    # Update database
    checker = TTCMeetingsChecker(
        upcoming_url='https://www.ttc.ca//sxa/search/results/?customdaterangefacet=Upcoming',
        past_url='https://www.ttc.ca//sxa/search/results/?s={5865C996-6A4C-472A-9116-C59CB3B76093}&itemid={1450DB42-0543-4C73-B159-421DF22D9460}&sig=past&p=8&o=ContentDateFacet%2CDescending&v=%7BF9A088B4-AFC4-4EE7-8649-0ACA83AB2783%7D'
    )
    posted_meetings = checker.get_upcoming_meetings()
    known_meetings = checker.get_seen_meetings()
    new, old, cancelled, completed = checker.get_diff_meetings(posted_meetings, known_meetings)
    checker.update_database(new, cancelled, completed)

    # New meetings found
    if len(new):
        text = f"{len(new)} new scheduled meeting"
        text += "s" if len(new) > 1 else ""
        text += "!"
        response = twitter_api.update_status(text)
        log.info(f"tweeted: {text}")
        prev_tweet_id = response.id

        # Tweet each meeting
        for meeting in new:
            text = str(meeting)
            response = twitter_api.update_status(
                text,
                in_reply_to_status_id=prev_tweet_id,
                auto_populate_reply_metadata=True
            )
            log.info(f"tweeted in thread: {text}")
            prev_tweet_id = response.id

    else:
        log.info("no meeting updates found")

    log.info("checked for meeting updates successfully")
    return "Success", 200


if __name__ == '__main__':
    app.run()
