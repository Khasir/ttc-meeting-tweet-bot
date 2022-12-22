import logging

import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse, ParserError


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
            meetings: list of upcoming meeting objects
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
            for element in soup.find_all('div', class_='u-type--body'):
                # Date
                if element.text.startswith('Date:'):
                    field = element.text[len('Date:'):].strip()
                    meeting['date_raw'] = field
                    log.info(f'date_raw: {field}')
                    try:
                        meeting['date_parsed'] = parse(field, fuzzy=True).date()
                        log.info(f'date_parsed: {meeting["date_parsed"]}')
                    except ParserError:
                        log.warning(f"Could not parse date: {field}")
                # Time
                elif element.text.startswith('Start Time:'):
                    field = element.text[len('Start Time:'):].strip()
                    meeting['start_time_raw'] = field
                    try:
                        meeting['start_time_parsed'] = parse(field, fuzzy=True).time()
                        log.info(f"start_time_parsed: {meeting['start_time_parsed']}")
                    except ParserError:
                        log.warning(f"Could not parse start time: {field}")
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
                    field = element.text[len('Live Stream:'):].strip()
                    meeting['live_stream_str'] = field
                    log.info(f'live_stream_str: {field}')
                    anchor = element.find('a')
                    if anchor:
                        meeting['live_stream_url'] = anchor.get('href')
                    log.info(f"live_stream_url: {meeting.get('live_stream_url')}")

        return meetings
