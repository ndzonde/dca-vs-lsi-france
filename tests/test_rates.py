from lsi_dca.rates import livret_a_rate


def test_known_schedule_points():
    cases = {
        "2009-06-01": 0.0125,   # before first entry -> flat-extended
        "2010-01-04": 0.0125,
        "2010-08-01": 0.0175,   # exact change date is inclusive
        "2011-08-01": 0.0225,
        "2013-08-01": 0.0125,
        "2015-08-01": 0.0075,
        "2020-02-01": 0.0050,
        "2023-02-01": 0.0300,
        "2025-01-01": 0.0300,   # after last entry -> flat-extended
    }
    for date, expected in cases.items():
        assert livret_a_rate(date) == expected, date


def test_rate_is_piecewise_constant_between_change_dates():
    assert livret_a_rate("2012-01-01") == livret_a_rate("2012-12-31")
