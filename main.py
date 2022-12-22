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

import redis
from bs4 import BeautifulSoup
from flask import Flask, session, redirect, request
from requests_oauthlib import OAuth2Session, TokenUpdated

from crawl import TTCMeetingsChecker


# Web server
app = Flask(__name__)
app.secret_key = os.urandom(50)

# Twitter authentication
db = redis.Redis(host='localhost', port=6379, db=0)
client_id = os.environ['CLIENT_ID']
client_secret = os.environ['CLIENT_SECRET']
auth_url = "https://twitter.com/i/oauth2/authorize"
token_url = "https://api.twitter.com/2/oauth2/token"
redirect_uri = os.environ["REDIRECT_URI"]
scopes = ["tweet.read", "users.read", "tweet.write", "offline.access"]
# Code verification
code_verifier = base64.urlsafe_b64encode(os.urandom(30)).decode("utf-8")
code_verifier = re.sub("[^a-zA-Z0-9]+", "", code_verifier)
# Code challenge
code_challenge = hashlib.sha256(code_verifier.encode("utf-8")).digest()
code_challenge = base64.urlsafe_b64encode(code_challenge).decode("utf-8")
code_challenge = code_challenge.replace("=", "")

# Logs
# logging.basicConfig(filename='logs\\ttcmeetbot.log', level=logging.INFO)
log = logging.getLogger(__name__)


def make_token():
    return OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scopes)


def check_upcoming():
    checker = TTCMeetingsChecker(
        upcoming_url='https://www.ttc.ca//sxa/search/results/?customdaterangefacet=Upcoming',
        past_url='https://www.ttc.ca//sxa/search/results/?s={5865C996-6A4C-472A-9116-C59CB3B76093}&itemid={1450DB42-0543-4C73-B159-421DF22D9460}&sig=past&p=8&o=ContentDateFacet%2CDescending&v=%7BF9A088B4-AFC4-4EE7-8649-0ACA83AB2783%7D'
    )
    found = checker.check_upcoming_ttc_meetings()
    return found


def post_tweet(payload, token):
    print("Tweeting!")
    logger.info("Tweeting!")
    return requests.post(
        "https://api.twitter.com/2/tweets",
        json=payload,
        headers={
            "Authorization": "Bearer {}".format(token["access_token"]),
            "Content-Type": "application/json",
        },
    )


@app.route("/")
def auth():
    global twitter
    twitter = make_token()
    authorization_url, state = twitter.authorization_url(
        auth_url, code_challenge=code_challenge, code_challenge_method="S256"
    )
    session["oauth_state"] = state
    return redirect(authorization_url)


@app.route("/oauth/callback", methods=["GET"])
def callback():
    code = request.args.get("code")
    token = twitter.fetch_token(
        token_url=token_url,
        client_secret=client_secret,
        code_verifier=code_verifier,
        code=code,
    )
    st_token = '"{}"'.format(token)
    j_token = json.loads(st_token)
    db.set("token", j_token)
    msg = check_upcoming()
    payload = {"text": "{}".format(msg)}
    response = post_tweet(payload, token).json()
    return response


if __name__ == '__main__':
    app.run()
