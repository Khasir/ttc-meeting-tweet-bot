import requests
from bs4 import BeautifulSoup


class TTCMeetingsChecker:
    def __init__(self, upcoming_url: str, past_url: str):
        self.upcoming_url = upcoming_url
        self.past_url = past_url
        self.session = requests.Session()

    def check_upcoming_ttc_meetings(self):
        response = self.session.get(self.upcoming_url)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(err)

        soup = BeautifulSoup(response.text, 'html.parser')
        tags = soup.find('ul', class_='search-result-list')
        return bool(tags)
