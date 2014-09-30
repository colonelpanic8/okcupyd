import datetime

from okcupyd import helpers


def test_parse_date_updated_day_of_the_week():
    day_to_spellings = {
        'Monday': ['M', 'Monday', 'monday', 'MONDAY'],
        'Saturday': ['Sat', 'Saturday', 'saturday']
    }
    for best_spelling, spellings in day_to_spellings.items():
        expected_date = helpers.parse_date_updated(best_spelling)
        for spelling in spellings:
            assert expected_date == helpers.parse_date_updated(spelling)

def test_parse_date_updated_handles_slash_dates():
    assert helpers.parse_date_updated('11/22/99') == datetime.datetime(
        year=1999, day=22, month=11
    )


def test_parse_date_updated_handles_times():
    assert helpers.parse_date_updated('10:11pm').date()
    assert helpers.parse_date_updated('11:59pm').date()
    assert helpers.parse_date_updated('12:00am').date()


def test_parse_date_handles_month_abbreviation_day_pairs():
    assert helpers.parse_date_updated('Jan 12').date()
    assert helpers.parse_date_updated('Jan 31').date()
    assert helpers.parse_date_updated('Feb 29').date()
