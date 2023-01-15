from checker import TTCMeetingsChecker


def main():
    print("START test: access database")
    checker = TTCMeetingsChecker(None, None, 'meetings', 'ubuntu', 'psql-pgpass.key')
    seen = checker.get_seen_meetings()
    archived = checker.get_archived_meetings()
    new, old, cancelled, completed = checker.get_diff_meetings(seen, archived)
    assert not old
    assert not cancelled
    assert not completed
    print("PASS test: access database")
    return


if __name__ == '__main__':
    main()
