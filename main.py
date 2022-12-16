from bs4 import BeautifulSoup


# filename = 'samples/Public meetings - true.html'
# with open(filename) as file:
# 	soup = BeautifulSoup(file.read(), 'html.parser')
# tags = soup.find('ul', class_='search-result-list')
# print(tags)

def main():
	checker = TTCMeetingsChecker('https://www.ttc.ca/public-meetings')
	found = checker.check_upcoming_ttc_meetings()
	return found


if __name__ == '__main__':
	main()
