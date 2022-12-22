import logging

import requests
from bs4 import BeautifulSoup


log = logging.getLogger(__name__)
VERSION = "0.1"


class TTCMeetingsChecker:
    def __init__(self, upcoming_url: str, past_url: str):
        self.upcoming_url = upcoming_url
        self.past_url = past_url

        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Host': 'www.ttc.ca',
            'User-Agent': f'TTCMeetBot/{VERSION}',
        }
        self.session = requests.Session()

    def check_upcoming_ttc_meetings(self) -> str:
        response = self.session.get(self.upcoming_url, headers=self.headers)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            # TODO raise email alert
            log.error(err)
            return

        result = response.json()
        message = f"Found {result['Count']} new meetings"
        return message
