"""
The main entrypoint for the Twitter bot.
Followed a tutorial: https://developer.twitter.com/en/docs/tutorials/creating-a-twitter-bot-with-python--oauth-2-0--and-v2-of-the-twi
"""

import argparse
import datetime
import json
import logging
import os
from zoneinfo import ZoneInfo

import requests
import tweepy

from crawl import TTCMeetingsChecker


# consumer_key = os.environ['CONSUMER_KEY']
# consumer_secret = os.environ['CONSUMER_SECRET']
# access_token = os.environ['ACCESS_TOKEN']
# access_token_secret = os.environ['ACCESS_TOKEN_SECRET']


# Logs
# logging.basicConfig(filename='logs\\ttcmeetbot.log', level=logging.INFO)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class TTCMeetBot:
    def __init__(self, consumer_key, consumer_key_secret, access_token, access_token_secret):
        auth = tweepy.OAuth1UserHandler(
            consumer_key, consumer_key_secret, access_token, access_token_secret
        )
        # Tweet object: https://developer.twitter.com/en/docs/twitter-api/v1/data-dictionary/object-model/tweet
        self.twitter_api = tweepy.API(auth)
        self.checker = TTCMeetingsChecker(
            upcoming_url='https://www.ttc.ca//sxa/search/results/?customdaterangefacet=Upcoming',
            past_url='https://www.ttc.ca//sxa/search/results/?s={5865C996-6A4C-472A-9116-C59CB3B76093}&itemid={1450DB42-0543-4C73-B159-421DF22D9460}&sig=past&p=8&o=ContentDateFacet%2CDescending&v=%7BF9A088B4-AFC4-4EE7-8649-0ACA83AB2783%7D'
        )


    def tweet_meeting_updates(self):
        log.info("checking for meeting updates")
        # Update database
        posted_meetings = self.checker.get_upcoming_meetings()
        known_meetings = self.checker.get_seen_meetings()
        new, old, cancelled, completed = self.checker.get_diff_meetings(posted_meetings, known_meetings)
        self.checker.update_database(new, cancelled, completed)

        # New meetings found
        if new:
            text = f"{len(new)} new scheduled meeting"
            text += "s" if len(new) > 1 else ""
            text += "!"
            response = self.twitter_api.update_status(text)
            log.info(f"tweeted: {text}")
            prev_tweet_id = response.id

            # Tweet each meeting
            new = sorted(new)
            for meeting in new:
                text = str(meeting)
                response = self.twitter_api.update_status(
                    text,
                    in_reply_to_status_id=prev_tweet_id,
                    auto_populate_reply_metadata=True
                )
                log.info(f"tweeted in thread: {text}")
                prev_tweet_id = response.id

        # Meetings cancelled
        if cancelled:
            text = f"{len(cancelled)} meeting"
            text += "s" if len(cancelled) > 1 else ""
            text += " cancelled :("
            response = self.twitter_api.update_status(text)
            log.info(f"tweeted: {text}")
            prev_tweet_id = response.id

            # Tweet each meeting
            cancelled = sorted(cancelled)
            for meeting in cancelled:
                text = str(meeting)
                response = self.twitter_api.update_status(
                    text,
                    in_reply_to_status_id=prev_tweet_id,
                    auto_populate_reply_metadata=True
                )
                log.info(f"tweeted in thread: {text}")
                prev_tweet_id = response.id

        if not new and not cancelled:
            log.info("no meeting updates found")

        log.info("checked for meeting updates successfully")
        return "Success", 200


    def tweet_todays_meetings(self):
        log.info("checking for today's meetings")
        meetings = self.checker.get_seen_meetings()
        meetings += self.checker.get_archived_meetings()

        # Get today's`meetings
        meets_to_tweet = []
        today = datetime.datetime.now(tz=ZoneInfo("America/Toronto")).date()
        for meeting in meetings:
            if meeting.date_parsed_et == today:
                meets_to_tweet.append(meeting)
        log.info(f"found {len(meets_to_tweet)} meetings today")

        # Tweet them, sorted by time
        meets_to_tweet = sorted(meets_to_tweet)
        for meeting in meets_to_tweet:
            text = "MEETING TODAY\n" + str(meeting)
            response = self.twitter_api.update_status(text)
            log.info(f"tweeted: {text}")

        log.info("done checking for today's meetings")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("credential_file", help='The file containing Twitter credentials')
    parser.add_argument("mode", choices=["update", "today"], help='The mode to run the bot in')
    args = parser.parse_args()

    with open(os.path.expanduser(args.credential_file), 'r', encoding='utf-8') as file:
        creds = json.load(file)

    bot = TTCMeetBot(**creds)
    if args.mode == 'update':
        bot.tweet_meeting_updates()
    elif args.mode == 'today':
        bot.tweet_todays_meetings()
