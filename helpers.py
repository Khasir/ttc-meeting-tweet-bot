import datetime
import logging
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
from dateutil.parser import parse, ParserError

log = logging.getLogger(__name__)


class Meeting:
    def __init__(
            self,
            id: str,
            language: str = None,
            path: str = None,
            url: str = None,
            name: str = None,
            html: str = None,
            title: str = None,
            date: str = None,
            start_time: str = None,
            location: str = None,
            meeting_no: str = None,
            live_stream: str = None):
        self.id = id
        self.language = language[:2] if language else None
        self.path = path
        self.url = url
        self.name = name
        self.html = html
        self.title = title
        self.date_raw = date
        self.date_parsed_et = self.parse_date(date) if date else None
        self.start_time_raw = start_time
        self.start_time_parsed_et = self.parse_time(start_time) if start_time else None
        self.location = location
        self.meeting_no = meeting_no
        self.live_stream_html = live_stream
        self.live_stream_str, self.live_stream_url = self.parse_live_stream(live_stream) if live_stream else (None, None)
        self.timestamp_utc = datetime.datetime.now(datetime.timezone.utc)

    @staticmethod
    def parse_date(date: str):
        parsed = None
        try:
            parsed = parse(date, fuzzy=True).replace(tzinfo=ZoneInfo("America/Toronto")).date()
            log.info(f'date parsed: {date} -> {parsed}')
        except ParserError:
            log.warning(f"could not parse date: {date}")
        return parsed

    @staticmethod
    def parse_time(time: str):
        """
        Assumes time is in the America/Toronto timezone.
        """
        parsed = None
        try:
            parsed = parse(time, fuzzy=True).replace(tzinfo=ZoneInfo("America/Toronto")).time()
            log.info(f"time parsed: {time} -> {parsed}")
        except ParserError:
            log.warning(f"could not parse start time: {time}")
        return parsed

    @staticmethod
    def parse_live_stream(html: str):
        text = None
        url = None
        soup = BeautifulSoup(html, 'html.parser')
        anchor = soup.find('a')
        if anchor:
            url = anchor.get('href')
            log.info(f"live stream url found: {url}")
        return soup.text, url

    @classmethod
    def from_dict(cls, meeting: dict, parse: bool = True):
        """
        Create a Meeting from a dictionary.
        Params:
            meeting: dictionary to parse
            parse: leave meeting as is
        """
        if parse:
            ret = Meeting(
                id=meeting['id'],
                language=meeting.get('language'),
                path=meeting.get('path'),
                url=meeting.get('url'),
                name=meeting.get('name'),
                html=meeting.get('html'),
                title=meeting.get('title'),
                date=meeting.get('date'),
                start_time=meeting.get('start_time'),
                location=meeting.get('location'),
                meeting_no=meeting.get('meeting_no'),
                live_stream=meeting.get('live_stream')
            )
        else:
            ret = Meeting(meeting['id'])
            ret.language = meeting['language']
            ret.path = meeting['path']
            ret.url = meeting['url']
            ret.name = meeting['name']
            ret.html = meeting['html']
            ret.title = meeting['title']
            ret.date_raw = meeting['date_raw']
            ret.date_parsed_et = meeting['date_parsed_et']
            ret.start_time_raw = meeting['start_time_raw']
            ret.start_time_parsed_et = meeting['start_time_parsed_et']
            ret.location = meeting['location']
            ret.meeting_no = meeting['meeting_no']
            ret.live_stream_str = meeting['live_stream_str']
            ret.live_stream_url = meeting['live_stream_url']
            ret.timestamp_utc = meeting['timestamp_utc']
        return ret

    def __str__(self) -> str:
        text = self.title + '\n'
        text += self.start_time_raw + '\n'
        text += self.location + '\n'
        text += self.url
        return text

    def __repr__(self) -> str:
        return str(self.__dict__)

    def __lt__(self, other) -> bool:
        """
        Compare based on date and time.
        """
        if not self.date_parsed_et:
            return False
        if not other.date_parsed_et:
            return True
        if self.date_parsed_et < other.date_parsed_et:
            return True
        if self.date_parsed_et == other.date_parsed_et:
            if not self.start_time_parsed_et:
                return False
            if not other.start_time_parsed_et:
                return True
            if self.start_time_parsed_et < other.start_time_parsed_et:
                return True
        return False
