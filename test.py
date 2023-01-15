from checker import TTCMeetingsChecker


def main():
    checker = TTCMeetingsChecker(None, None)
    seen = checker.get_seen_meetings()
    archived = checker.get_archived_meetings()
    new, old, cancelled, completed = checker.get_diff_meetings(seen, archived)
    assert not old
    assert not cancelled
    assert not completed
    print("test passed")
    return


if __name__ == '__main__':
    main()
