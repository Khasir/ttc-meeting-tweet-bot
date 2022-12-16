from bs4 import BeautifulSoup

from crawl import TTCMeetingsChecker


# filename = 'samples/Public meetings - true.html'
# with open(filename) as file:
#   soup = BeautifulSoup(file.read(), 'html.parser')
# tags = soup.find('ul', class_='search-result-list')
# print(tags)

def main():
    checker = TTCMeetingsChecker(
        upcoming_url='https://www.ttc.ca//sxa/search/results/?customdaterangefacet=Upcoming',
        past_url='https://www.ttc.ca//sxa/search/results/?s={5865C996-6A4C-472A-9116-C59CB3B76093}&itemid={1450DB42-0543-4C73-B159-421DF22D9460}&sig=past&p=8&o=ContentDateFacet%2CDescending&v=%7BF9A088B4-AFC4-4EE7-8649-0ACA83AB2783%7D'
    )
    found = checker.check_upcoming_ttc_meetings()
    return found


if __name__ == '__main__':
    print(main())
