import requests
from bs4 import BeautifulSoup


class TTCMeetingsChecker:
    def __init__(self, root_url: str):
        self.root_url = root_url

    def check_upcoming_ttc_meetings(self, suffix="?tab=0#upcoming_e=0&past_CustomDateRangeFacet=Past&upcoming_CustomDateRangeFacet=Upcoming"):
        response = requests.get(self.root_url + suffix)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(err)
