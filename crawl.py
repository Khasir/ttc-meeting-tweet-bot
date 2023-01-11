"""

Features:
- Detect when new meetings are scheduled
- Detect if a meeting is scheduled for today
- Detect when scheduled meetings are cancelled
"""


import logging

import psycopg
import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse, ParserError

from helpers import Meeting


log = logging.getLogger(__name__)
VERSION = "0.1"


class TTCMeetingsChecker:
    def __init__(self, upcoming_url: str, past_url: str, base_url: str = 'https://www.ttc.ca'):
        self.upcoming_url = upcoming_url
        self.past_url = past_url
        self.base_url = base_url

        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Host': 'www.ttc.ca',
            'User-Agent': f'TTCMeetBot/{VERSION}',
        }
        self.session = requests.Session()

    def get_upcoming_meetings(self) -> list:
        """
        Get all upcoming meetings listed on the TTC website.
        Returns:
            meetings: list of the latest upcoming meetings
        """
        # Get meetings
        response = self.session.get(self.upcoming_url, headers=self.headers)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            # TODO raise email alert
            log.error(err)
            return
        result = response.json()

        # Parse the individual meeting pages for more details
        meetings = result['Results']
        for meeting in meetings:
            # Convert keys to lowercase
            to_delete = []
            for key in meeting:
                if key.lower() != key:
                    to_delete.append(key)
            for key in to_delete:
                meeting[key.lower()] = meeting[key]
                del meeting[key]

            # Convert relative URL to absolute
            url = self.base_url
            url += '/' if not meeting['url'].startswith('/') else ''
            url += meeting['url']
            meeting['url'] = url
            log.info(f"Parsing meeting: {meeting['url']}")

            response = self.session.get(url, headers=self.headers)
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as err:
                log.error(f"Could not access meeting URL: {url}")
                continue

            # Get more info
            soup = BeautifulSoup(response.text, 'html.parser')
            # Title
            field = soup.find('h1', class_='u-type--d6 field-title')
            if field:
                meeting['title'] = field.text.strip()
            for element in soup.find_all('div', class_='u-type--body'):
                # Date
                if element.text.startswith('Date:'):
                    field = element.text[len('Date:'):].strip()
                    meeting['date'] = field
                    # meeting['date_raw'] = field
                    # log.info(f'date_raw: {field}')
                    # try:
                    #     meeting['date_parsed'] = parse(field, fuzzy=True).date()
                    #     log.info(f'date_parsed: {meeting["date_parsed"]}')
                    # except ParserError:
                    #     log.warning(f"Could not parse date: {field}")
                # Time
                elif element.text.startswith('Start Time:'):
                    field = element.text[len('Start Time:'):].strip()
                    meeting['start_time'] = field
                    # meeting['start_time_raw'] = field
                    # try:
                    #     meeting['start_time_parsed'] = parse(field, fuzzy=True).time()
                    #     log.info(f"start_time_parsed: {meeting['start_time_parsed']}")
                    # except ParserError:
                    #     log.warning(f"Could not parse start time: {field}")
                # Location
                elif element.text.startswith('Location:'):
                    field = element.text[len('Location:'):].strip()
                    meeting['location'] = field
                    log.info(f'location: {field}')
                # Meeting number
                elif element.text.startswith('Meeting No:'):
                    field = element.text[len('Meeting No:'):].strip()
                    meeting['meeting_no'] = field
                    log.info(f'meeting_no: {field}')
                # Live stream info
                elif element.text.startswith('Live Stream:'):
                    meeting['live_stream'] = str(element.find('a'))
                    # field = element.text[len('Live Stream:'):].strip()
                    # meeting['live_stream_str'] = field
                    # log.info(f'live_stream_str: {field}')
                    # anchor = element.find('a')
                    # if anchor:
                    #     meeting['live_stream_url'] = anchor.get('href')
                    # log.info(f"live_stream_url: {meeting.get('live_stream_url')}")

        return [Meeting.from_dict(meeting) for meeting in meetings]

    def get_seen_meetings(self):
        """
        Query database for meetings that we've already scraped.
        Returns:
            meetings: list of previously seen meetings
        """
        query = "SELECT * FROM upcoming"
        with psycopg.connect('dbname=meetings user=postgres password=postgres', row_factory=psycopg.rows.dict_row) as conn:
            results = conn.execute(query)
        meetings = [Meeting.from_dict(r) for r in results]
        return meetings

    def get_diff_meetings(self, latest: list, previous: list) -> tuple:
        """
        Determine which meetings are:
            - new (not seen before)
            - old (already seen and still upcoming)
            - cancelled (no longer planned and whose date has not passed)
            - completed (taken place as planned)
        Params:
            latest: list of meetings from the latest scrape
            previous: list of meetings from the database
        Returns:
            new, old, cancelled, completed: lists of meetings.
        """
        latest_ids = {meeting.id for meeting in latest}
        previous_ids = {meeting.id for meeting in previous}

        new = [meeting for meeting in latest if meeting.id not in previous_ids]
        old = []
        cancelled = []
        completed = []
        for meeting in previous:
            # Add to old
            if meeting.id in latest_ids:
                old.append(meeting)
            else:
                # today = datetime.datetime.now(datetime.timezone.utc)
                # meeting_datetime = datetime.datetime.combine(meeting.date_parsed, meeting.start_time_parsed)

                # Just use date to be more lenient
                today = datetime.datetime.now(datetime.timezone.utc).date()
                # Add to cancelled
                if meeting.date_parsed > today:
                    cancelled.append(meeting)
                # Add to completed
                else:
                    completed.append(meeting)

        return new, old, cancelled, completed

    def update_database(self, new: list, cancelled: list, completed: list):
        """
        Insert new meetings and archive the cancelled or completed meetings from the database.
        """
        with psycopg.connect('dbname=meetings user=postgres password=postgres') as conn:
            # Insert new meetings
            for meeting in new:
                query = """
                    INSERT INTO upcoming (
                        id,
                        language,
                        path,
                        url,
                        name,
                        html,
                        title,
                        date_raw,
                        date_parsed_utc,
                        start_time_raw,
                        start_time_parsed_utc,
                        location,
                        meeting_no,
                        live_stream_str,
                        live_stream_url,
                        timestamp_utc
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                conn.execute(query, (
                    meeting.id,
                    meeting.language,
                    meeting.path,
                    meeting.url,
                    meeting.name,
                    meeting.html,
                    meeting.title,
                    meeting.date_raw,
                    meeting.date_parsed_utc,
                    meeting.start_time_raw,
                    meeting.start_time_parsed_utc,
                    meeting.location,
                    meeting.meeting_no,
                    meeting.live_stream_str,
                    meeting.live_stream_url,
                    meeting.timestamp_utc
                ))
            log.info(f"{len(new)} new meetings added")
            # Add cancelled and completed meetings to archive
            for meeting in cancelled:
                query = """
                    INSERT INTO archived (
                        id,
                        language,
                        path,
                        url,
                        name,
                        html,
                        title,
                        date_raw,
                        date_parsed_utc,
                        start_time_raw,
                        start_time_parsed_utc,
                        location,
                        meeting_no,
                        live_stream_str,
                        live_stream_url,
                        timestamp_utc,
                        status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'CANCELLED')
                """
                conn.execute(query, (
                    meeting.id,
                    meeting.language,
                    meeting.path,
                    meeting.url,
                    meeting.name,
                    meeting.html,
                    meeting.title,
                    meeting.date_raw,
                    meeting.date_parsed_utc,
                    meeting.start_time_raw,
                    meeting.start_time_parsed_utc,
                    meeting.location,
                    meeting.meeting_no,
                    meeting.live_stream_str,
                    meeting.live_stream_url,
                    meeting.timestamp_utc
                ))
            for meeting in completed:
                query = """
                    INSERT INTO archived (
                        id,
                        language,
                        path,
                        url,
                        name,
                        html,
                        title,
                        date_raw,
                        date_parsed_utc,
                        start_time_raw,
                        start_time_parsed_utc,
                        location,
                        meeting_no,
                        live_stream_str,
                        live_stream_url,
                        timestamp_utc,
                        status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'COMPLETED')
                """
                conn.execute(query, (
                    meeting.id,
                    meeting.language,
                    meeting.path,
                    meeting.url,
                    meeting.name,
                    meeting.html,
                    meeting.title,
                    meeting.date_raw,
                    meeting.date_parsed_utc,
                    meeting.start_time_raw,
                    meeting.start_time_parsed_utc,
                    meeting.location,
                    meeting.meeting_no,
                    meeting.live_stream_str,
                    meeting.live_stream_url,
                    meeting.timestamp_utc
                ))
            # Removed cancelled and completed meetings from upcoming
            query = """
                DELETE FROM upcoming
                WHERE id IN (
                    SELECT id FROM archived
                )
            """
            conn.execute(query)
            log.info(f"{len(cancelled)} meetings marked as cancelled")
            log.info(f"{len(completed)} meetings marked as completed")
