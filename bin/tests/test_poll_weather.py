import imp
import unittest.mock  # noqa: F401

import pytest  # noqa: F401

m = imp.load_source('poll-weather', '/home/bryan/Dropbox/scripts/bin/xmonad/poll-weather')

report = m.run_weather_report('08060')


@pytest.mark.skip
def test_run_weather_report():
    report = m.run_weather_report('08060')
    assert isinstance(report, str)


params = [('([0-9]+)', 'I have 5 pigs.', '5')]


@pytest.mark.parametrize('pttrn,string,expected', params)
def test_get_group(pttrn,string,expected):
    assert expected == m.get_group(pttrn,string)


params = [('Current conditions at (.*)\n', 'Mt Holly South Jersey Rgnl, NJ'),
          (r'Temperature: ([0-9]+\.[0-9] F)', '82.0 F'),
          (r'Sky conditions: ([A-z\s]+)', 'clear'),
          (r'Wind: .*([0-9] MPH)', '5 MPH')]


@pytest.mark.parametrize('pttrn,expected', params)
def test_get_group_report(pttrn,expected):
    assert expected == m.get_group(pttrn, report)
