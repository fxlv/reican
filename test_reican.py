import datetime
import sys
import types
import pytest
import reican

# cspell:ignore reican, pytest
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


def test_usage(capsys):
    """Test that Usage message is displayed correctly."""
    with pytest.raises(SystemExit):
        reican.usage()
    out, err = capsys.readouterr()
    assert len(out) > 40
    assert "Usage:" in out


def test_get_size():
    assert reican.get_size(test_file_name) == test_file_name_size


# default test file is small so this should pass
def test_file_name_too_big():
    assert reican.file_too_big(test_file_name) == False


# change max file size to test that larger files will get rejected
def test_file_name_too_big_bigfile():
    # test file is 20 bytes
    # max size set to 20 bytes
    reican.MAX_FILE_SIZE = "0.000020M"
    assert reican.file_too_big(test_file_name) == True


def test_get_file_name():
    sys.argv = ("./reican.py", test_file_name)
    assert reican.get_file_name() == test_file_name


def test_get_file_name_2():
    """get_file_name() only works of 2 arguments are passed to reican.py."""
    sys.argv = ("./reican.py")
    with pytest.raises(SystemExit):
        reican.get_file_name()


def test_get_file_name_3(capsys):
    """Test non-existing file name."""
    sys.argv = ("./reican.py", missing_test_file_name)
    with pytest.raises(SystemExit) as exc:
        reican.get_file_name()
    out, err = capsys.readouterr()
    assert out == "\nFile test/test_missing.log does not exist\n\n"


def test_get_opener_type():
    opener = reican.get_opener(test_file_name, stats)
    assert isinstance(opener, types.BuiltinFunctionType)


def test_get_opener_gzip_type():
    opener = reican.get_opener(test_file_name + ".gz", stats)
    assert isinstance(opener, types.FunctionType)


def test_get_opener_lzma_type():
    opener = reican.get_opener(test_file_name + ".lzma", stats)
    assert isinstance(opener, types.FunctionType)


def test_humanize_delta():
    expected_result = {'hours': 0, 'seconds': 50, 'minutes': 2}
    delta = datetime.timedelta(0, 170, 159069)
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
    test_string = "2015.11.01 15:04:39 #72651112 SERVER: some stuff happened here"
    test_timestamp = "2015.11.01 15:04:39"
    assert reican.get_timestamp(test_string)[0] == test_timestamp


def test_get_timestamp_5():
    """Testing bad timestamp."""
    test_string = "201lala5-10-30T20:20:11.563278+00:00 lalala lalalalalallalalal"
    assert reican.get_timestamp(test_string) == (None, None)
