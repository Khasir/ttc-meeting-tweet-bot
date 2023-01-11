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
# app.secret_key = os.urandom(50)

# # Twitter authentication
# db = redis.Redis(host='localhost', port=6379, db=0)
# client_id = os.environ['CLIENT_ID']
# client_secret = os.environ['CLIENT_SECRET']
# auth_url = "https://twitter.com/i/oauth2/authorize"
# token_url = "https://api.twitter.com/2/oauth2/token"
# redirect_uri = os.environ["REDIRECT_URI"]
# scopes = ["tweet.write", "offline.access"]
# # Code verification
# code_verifier = base64.urlsafe_b64encode(os.urandom(30)).decode("utf-8")
# code_verifier = re.sub("[^a-zA-Z0-9]+", "", code_verifier)
# # Code challenge
# code_challenge = hashlib.sha256(code_verifier.encode("utf-8")).digest()
# code_challenge = base64.urlsafe_b64encode(code_challenge).decode("utf-8")
# code_challenge = code_challenge.replace("=", "")


# def save_token(refreshed_token):
#     # Store in redis
#     db.set("token", refreshed_token)


# oauth2_user_handler = tweepy.OAuth2UserHandler(
#     client_id=client_id,
#     redirect_uri=redirect_uri,
#     scope=scopes,
#     # Client Secret is only necessary if using a confidential client
#     client_secret=client_secret,
#     Auto_refresh_url=token_url,
#     Token_updater=save_token,
# )

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


# def make_token():
#     return OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scopes)


# @app.route("/")
# def auth():
#     """
#     Enable a Twitter user to be the host of this bot.
#     """
#     # global twitter
#     # twitter = make_token()
#     authorization_url, state = twitter.authorization_url(
#         auth_url, code_challenge=code_challenge, code_challenge_method="S256"
#     )
#     session["oauth_state"] = state
#     return redirect(authorization_url)


# @app.route("/oauth/callback", methods=["GET"])
# def callback():
#     """
#     Callback for OAuth 2.0.
#     """
#     code = request.args.get("code")
#     token = twitter.fetch_token(
#         token_url=token_url,
#         client_secret=client_secret,
#         code_verifier=code_verifier,
#         code=code,
#     )
#     st_token = '"{}"'.format(token)
#     j_token = json.loads(st_token)
#     save_token(j_token)
#     # msg = check_upcoming()
#     # payload = {"text": "Hello, world!"}
#     # response = post_tweet(payload, token).json()
#     response = json.dumps({'success': True})
#     return response


# def post_tweet(payload, token):
#     log.info("Tweeting!")
#     return twitter.post(
#         "https://api.twitter.com/2/tweets",
#         json=payload,
#         headers={
#             "Authorization": "Bearer {}".format(token["access_token"]),
#             "Content-Type": "application/json",
#         },
#     )


@app.route('/', methods=['GET'])
def tweet_new_and_cancelled_meetings(refresh_token = None):
    # Update database
    checker = TTCMeetingsChecker(
        upcoming_url='https://www.ttc.ca//sxa/search/results/?customdaterangefacet=Upcoming',
        past_url='https://www.ttc.ca//sxa/search/results/?s={5865C996-6A4C-472A-9116-C59CB3B76093}&itemid={1450DB42-0543-4C73-B159-421DF22D9460}&sig=past&p=8&o=ContentDateFacet%2CDescending&v=%7BF9A088B4-AFC4-4EE7-8649-0ACA83AB2783%7D'
    )
    posted_meetings = checker.get_upcoming_meetings()
    known_meetings = checker.get_seen_meetings()
    new, old, cancelled, completed = checker.get_diff_meetings(posted_meetings, known_meetings)
    checker.update_database(new, cancelled, completed)

    # Tweet
    payload = {"text": f"Found {len(new)} meetings!"}
    # post_tweet(payload, refresh_token)
    twitter_api.update_status(payload['text'])
    return "Success", 200


# @app.route("/run", methods=["GET"])
# def run():
#     # auth_client = OAuth2Session(client_id, client=oauthlib.oauth2.BackendApplicationClient(client_id), redirect_uri=redirect_uri, scope=scopes)
#     # Load OAuth token from redis
#     t = db.get("token")
#     bb_t = t.decode("utf8").replace("'", '"')
#     data = json.loads(bb_t)

#     token_url = "https://api.twitter.com/2/oauth2/token"

#     # Refresh token lasts 6 months
#     # refreshed_token = auth_client.refresh_token(
#     #     client_id=client_id,
#     #     client_secret=client_secret,
#     #     token_url=token_url,
#     #     refresh_token=data["refresh_token"],
#     #     # grant_type='client_credentials',
#     #     # access_token=data['access_token'],
#     #     headers={
#     #         "Authorization": "Basic RmKADOeccwyXwTI1rH9WTFoLH:NPQsLLyj72NSOEmNJt6uQ0m9b4rPx7ZfAiNUFYZ87IV54zVdi9",
#     #         "Content-Type": "application/x-www-form-urlencoded",
#     #     }
#     # )
#     refreshed_token = requests.post(
#         token_url,
#         data={
#             'client_id': client_id,
#             'refresh_token': data['refresh_token'],
#             'grant_type': 'refresh_token',
#         },
#         headers={
#             'Content-Type': 'application/x-www-form-urlencoded',
#             'Authorization': f'Bearer {data["access_token"]}'
#         },
#     )
#     breakpoint()
#     if not refreshed_token.ok:
#         pass  # TODO
#     refreshed_token = refreshed_token.text
#     # Store in redis
#     st_refreshed_token = '"{}"'.format(refreshed_token)
#     j_refreshed_token = json.loads(st_refreshed_token)
#     save_token(refreshed_token)

#     # extra = {
#     #     'client_id': client_id,
#     #     'client_secret': client_secret
#     # }
#     # client = OAuth2Session(
#     #     client_id, token=data, auto_refresh_url=token_url,
#     #     auto_refresh_kwargs=extra, token_updater=save_token
#     # )
#     # refresh_token = client.get()

#     tweet_new_and_cancelled_meetings(refreshed_token)


if __name__ == '__main__':
    app.run()
