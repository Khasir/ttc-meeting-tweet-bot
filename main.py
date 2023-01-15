"""
The main entrypoint for the Twitter bot.
Followed a tutorial: https://developer.twitter.com/en/docs/tutorials/creating-a-twitter-bot-with-python--oauth-2-0--and-v2-of-the-twi
"""

import argparse
import datetime
import json
import logging
import os
import sys
from zoneinfo import ZoneInfo

import requests
import tweepy

from checker import TTCMeetingsChecker


# Logs
#os.makedirs(os.path.expanduser("~/logs"), exist_ok=True)
#logging.basicConfig(filename=os.path.expanduser('~/logs/ttcmeetbot.log'), encoding='utf-8', level=logging.INFO, format='%(asctime)s|%(levelname)s|%(name)s|%(message)s')
logging.basicConfig(stream=sys.stdout, encoding='utf-8', level=logging.INFO, format='%(asctime)s|%(levelname)s|%(name)s|%(message)s')
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


    def tweet_meeting_updates(self, dry_run=False):
        """
        Check TTC website for any meeting updates and tweet them.

        Params:
            dry_run: (bool=False) whether this is a dry run (ie. test without tweeting or making any state changes).
        """
        log.info("checking for meeting updates")
        # Update database
        posted_meetings = self.checker.get_upcoming_meetings()
        known_meetings = self.checker.get_seen_meetings()
        new, old, cancelled, completed = self.checker.get_diff_meetings(posted_meetings, known_meetings)

        if not dry_run:
            self.checker.update_database(new, cancelled, completed)

        # New meetings found
        if new:
            text = f"{len(new)} new scheduled meeting"
            text += "s" if len(new) > 1 else ""
            text += "!"
            if not dry_run:
                response = self.twitter_api.update_status(text)
                prev_tweet_id = response.id
            log.info(f"tweeted: {text}")

            # Tweet each meeting
            new = sorted(new)
            for meeting in new:
                text = str(meeting)
                if not dry_run:
                    response = self.twitter_api.update_status(
                        text,
                        in_reply_to_status_id=prev_tweet_id,
                        auto_populate_reply_metadata=True
                    )
                    prev_tweet_id = response.id
                log.info(f"tweeted in thread: {text}")

        # Meetings cancelled
        if cancelled:
            text = f"{len(cancelled)} meeting"
            text += "s" if len(cancelled) > 1 else ""
            text += " cancelled :("
            if not dry_run:
                response = self.twitter_api.update_status(text)
                prev_tweet_id = response.id
            log.info(f"tweeted: {text}")

            # Tweet each meeting
            cancelled = sorted(cancelled)
            for meeting in cancelled:
                text = str(meeting)
                if not dry_run:
                    response = self.twitter_api.update_status(
                        text,
                        in_reply_to_status_id=prev_tweet_id,
                        auto_populate_reply_metadata=True
                    )
                    prev_tweet_id = response.id
                log.info(f"tweeted in thread: {text}")

        if not new and not cancelled:
            log.info("no meeting updates found")

        log.info("checked for meeting updates successfully")
        return "Success", 200


    def tweet_todays_meetings(self, dry_run=False):
        """
        Check internal database for any meetings today and tweet them.

        Params:
            dry_run: (bool=False) whether this is a dry run (ie. test without tweeting or making any state changes).
        """
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
            if not dry_run:
                response = self.twitter_api.update_status(text)
            log.info(f"tweeted: {text}")

        log.info("done checking for today's meetings")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["update", "today"], help='The mode to run the bot in')
    parser.add_argument("twitter_credential_file", help='The file containing Twitter credentials')
    parser.add_argument("db_name")
    parser.add_argument("db_username")
    parser.add_argument("db_credential_file", help="The file containing the postgreSQL database credentials")
    parser.add_argument("--dry-run", action="store_true", help="Run without tweeting", dest='dry_run')
    args = parser.parse_args()

    with open(os.path.expanduser(args.twitter_credential_file), 'r', encoding='utf-8') as file:
        creds = json.load(file)

    bot = TTCMeetBot(**creds, dbname=args.db_name, dbuser=args.db_username, dbpassfile=args.db_credential_file)
    if args.mode == 'update':
        bot.tweet_meeting_updates(dry_run=args.dry_run)
    elif args.mode == 'today':
        bot.tweet_todays_meetings(dry_run=args.dry_run)
