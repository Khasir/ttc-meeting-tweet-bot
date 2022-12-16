import requests
from bs4 import BeautifulSoup


class TTCMeetingsChecker:
    def __init__(self, upcoming_url: str, past_url: str):
        self.upcoming_url = upcoming_url
        self.past_url = past_url
        self.session = requests.Session()

    def check_upcoming_ttc_meetings(self):
        __ = self.session.get('https://www.ttc.ca/public-meetings')
        response = self.session.get(self.upcoming_url, headers={
            "Content-Type": "application/json; charset=utf-8",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Content-Security-Policy": "default-src 'self' 'unsafe-inline' https://ttc.ca https://www.ttc.ca 'unsafe-eval' https://apps.sitecore.net *.azureedge.net; img-src https://ttc.ca https://www.ttc.ca *.dmtry.com *.siteimproveanalytics.io *.researchnow.com 'self' data: https://ttc.ca https://www.ttc.ca *.azureedge.net *.google.com *.google-analytics.com *.googletagmanager.com *.googleapis.com *.gstatic.com *.addthis.com *.addthisedge.com *.youtube.com *.moatads.com siteimproveanalytics.io ; style-src 'self' 'unsafe-inline' https://ttc.ca https://www.ttc.ca *.azureedge.net *.google.com *.google-analytics.com *.googletagmanager.com *.googleapis.com *.gstatic.com *.addthis.com *.addthisedge.com *.youtube.com *.moatads.com; font-src 'self' 'unsafe-inline' https://ttc.ca https://www.ttc.ca *.azureedge.net *.google.com *.google-analytics.com *.googletagmanager.com *.googleapis.com *.gstatic.com *.addthis.com *.addthisedge.com *.youtube.com *.moatads.com; connect-src * ; frame-src 'self' https://id.ttc.ca https://ttc.ca https://www.ttc.ca *.azureedge.net *.google.com *.google-analytics.com *.googletagmanager.com *.googleapis.com *.gstatic.com *.addthis.com *.addthisedge.com *.youtube.com *.moatads.com *.triplinx.ca; script-src * 'self' data: 'unsafe-inline' 'unsafe-eval' https://ttc.ca https://www.ttc.ca *.azureedge.net *.google.com *.google-analytics.com *.googletagmanager.com *.googleapis.com *.gstatic.com *.addthis.com *.addthisedge.com *.youtube.com *.moatads.com ;upgrade-insecure-requests; block-all-mixed-content; frame-ancestors 'none';"
        })
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(err)

        soup = BeautifulSoup(response.text, 'html.parser')
        tags = soup.find('ul', class_='search-result-list')
        return bool(tags)
