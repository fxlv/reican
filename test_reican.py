import datetime
import sys
import types
import pytest
import mock
import reican

# cspell:ignore reican, pytest, lzma
test_file_name = "test/test.log"
missing_test_file_name = "test/test_missing.log"

test_file_name_size = 221

#def test_get_size():
#    def mockreturn(argv):
#        return ("stuff")
#    import os
#    patch = os.stat("test/test.log")
#    monkeypatch.setattr('patch.st_size', mockreturn)
#    print reican.get_size("test/test.log")

stats = reican.Stats(test_file_name)


def test_die_1():
    """Test the die() function."""
    with pytest.raises(SystemExit):
        reican.die()


def test_die_2(capsys):
    """Test die() with optional argument."""
    with pytest.raises(SystemExit):
        reican.die("Something")
    out, err = capsys.readouterr()
    assert out == "\nSomething\n\n"


def test_get_size():
    assert reican.get_size(test_file_name) == test_file_name_size


# default test file is small so this should pass
def test_file_name_too_big():
    assert reican.file_too_big(test_file_name) == False


# change max file size to test that larger files will get rejected
def test_file_name_too_big_bigfile():
    # test file is 20 bytes
    # max size set to 20 bytes
    original_max_size = reican.MAX_FILE_SIZE
    reican.MAX_FILE_SIZE = "0.000020M"
    assert reican.file_too_big(test_file_name) == True
    # set the value back to previous
    reican.MAX_FILE_SIZE = original_max_size


#
# testing argument handling
#
def test_args(capsys):
    """Test invocation with no arguments or options specified."""
    sys.argv = ["./reican.py"]
    with pytest.raises(SystemExit) as exc:
        reican.parse_args()
    out, err = capsys.readouterr()
    assert "error: too few arguments" in err


def test_args_file_name():
    """If only one argument is passed, it must be the log file."""
    sys.argv = ["./reican.py", test_file_name]
    args = reican.parse_args()
    assert args.file_name == test_file_name


def test_args_filter_no_parameter(capsys):
    """
    Test --filter option with no parameter provided.

    If --filter is passed without a parameter,
    an error message must be returned because
    --filter is useless without the actual filtering string specified
    """
    sys.argv = ["./reican.py", "some_file_name", "--filter"]
    with pytest.raises(SystemExit) as exc:
        reican.parse_args()
    out, err = capsys.readouterr()
    print "out:", out
    print "err:", err
    assert "error: argument --filter: expected one argument" in err


def test_args_filter_with_parameter(capsys):
    """Test --filter option with a filter string provided."""
    filter_string = "something_to_filter_by"
    sys.argv = ["./reican.py", "some_file_name", "--filter", filter_string]
    args = reican.parse_args()
    assert args.filter == filter_string


def test_get_opener_type():
    opener = reican.get_opener(test_file_name, stats)
    assert isinstance(opener, types.BuiltinFunctionType)


def test_get_opener_gzip_type():
    opener = reican.get_opener(test_file_name + ".gz", stats)
    assert isinstance(opener, types.FunctionType)


def test_get_opener_lzma_type():
    opener = reican.get_opener(test_file_name + ".lzma", stats)
    assert isinstance(opener, types.FunctionType)


def test_get_opener_lzma_missing():
    """Test LZMA opener when LZMA module is missing."""
    with mock.patch.dict('sys.modules', {'backports.lzma': None}):
        with pytest.raises(SystemExit):
            opener = reican.get_opener(test_file_name + ".lzma", stats)
            assert isinstance(opener, types.FunctionType)


def test_humanize_delta():
    """Test a delta < than 1 hour."""
    expected_result = {'days': 0, 'hours': 0, 'seconds': 50, 'minutes': 2}
    delta = datetime.timedelta(minutes=2, seconds=50)
    assert expected_result == reican.humanize_delta(delta)


def test_humanize_delta_hour():
    """Test a delta > than 1 hour."""
    expected_result = {'days': 0, 'hours': 3, 'seconds': 10, 'minutes': 6}
    delta = datetime.timedelta(hours=3, minutes=6, seconds=10)
    assert expected_result == reican.humanize_delta(delta)


def test_humanize_delta_day():
    """Test a delta > than 1 day."""
    expected_result = {'days': 1, 'hours': 2, 'seconds': 25, 'minutes': 0}
    delta = datetime.timedelta(days=1, hours=2, seconds=25)
    assert expected_result == reican.humanize_delta(delta)


def test_opening_plaintext():
    opener = reican.get_opener(test_file_name, stats)
    with opener("test/test.log") as logfile:
        assert len(logfile.readlines()) == 3


def test_get_opening_gzip():
    opener = reican.get_opener(test_file_name + ".gz", stats)
    with opener("test/test.log.gz") as logfile:
        assert len(logfile.readlines()) == 3


def test_get_opening_lzma():
    opener = reican.get_opener(test_file_name + ".lzma", stats)
    with opener("test/test.log.lzma") as logfile:
        assert len(logfile.readlines()) == 3


def test_stats():
    s = reican.Stats(test_file_name)
    assert isinstance(s, types.InstanceType)


def test_stats_line_increment():
    s = reican.Stats(test_file_name)
    s.increment_line_counter()
    assert s.line_counter == 1


def test_get_timestamp_1():
    test_string = "2015-10-30T20:20:11.563278+00:00 lalala lalalalalallalalal"
    test_timestamp = "2015-10-30T20:20:11.563278+00:00"
    assert reican.get_timestamp(test_string)[0] == test_timestamp


def test_get_timestamp_2():
    test_string = "[2015-10-31 13:54:42.146481] DEBUG: Reican: Using gzip to open the file"
    test_timestamp = "2015-10-31 13:54:42.146481"
    assert reican.get_timestamp(test_string)[0] == test_timestamp


def test_get_timestamp_3():
    test_string = '''127.0.0.1 - - [31/Oct/2015:11:00:13 +0000]
    [1446314353.403] "GET /index.html HTTP/1.1" 200 54510 "-" 
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_0) 
    AppleWebKit/537.36 (KHTML,'''

    test_timestamp = "1446314353.403"
    assert reican.get_timestamp(test_string)[0] == test_timestamp


def test_get_timestamp_4():
    test_string = "2015.11.01 15:04:39 #72651112 SERVER: some stuff happened"
    test_timestamp = "2015.11.01 15:04:39"
    assert reican.get_timestamp(test_string)[0] == test_timestamp


def test_get_timestamp_5():
    test_string = "[2017/03/19 10:39:31] playlist.c:125: warn: Parsing play"
    test_timestamp = "2017/03/19 10:39:31"
    assert reican.get_timestamp(test_string)[0] == test_timestamp


def test_get_timestamp_6():
    """Testing bad timestamp."""
    test_string = "201lala5-10-30T20:20:11.563278+00:00 lalala lalalalaalalal"
    assert reican.get_timestamp(test_string) == (None, None)


#
# Test main application logic 
#
def test_main(capsys):
    """Test main application logic against test/test.log."""
    sys.argv = ["./reican.py", "test/test.log"]
    reican.main()
    out, err = capsys.readouterr()
    assert "File size: 221 bytes, 73 bytes per line" in out 
    assert "Delta: 4 hours, 14 minutes, 50 seconds." in out
