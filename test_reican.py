import reican
import types
import sys
import datetime

test_file_name = "test/test.log"
test_file_name_size = 221

#def test_get_size():
#    def mockreturn(argv):
#        return ("kaka","mauka")
#    import os
#    patch = os.stat("test/test.log")
#    monkeypatch.setattr('patch.st_size', mockreturn)
#    print reican.get_size("test/test.log")

stats = reican.Stats(test_file_name)


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


def test_get_opener_type():
    opener = reican.get_opener("test/test.log", stats)
    assert isinstance(opener, types.BuiltinFunctionType)


def test_get_opener_gzip_type():
    opener = reican.get_opener("test/test.log.gz", stats)
    assert isinstance(opener, types.FunctionType)


def test_get_opener_lzma_type():
    opener = reican.get_opener("test/test.log.lzma", stats)
    assert isinstance(opener, types.FunctionType)


def test_humanize_delta():
    expected_result = {'hours': 0, 'seconds': 50, 'minutes': 2}
    delta = datetime.timedelta(0, 170, 159069)
    assert expected_result == reican.humanize_delta(delta)


def test_opening_plaintext():
    opener = reican.get_opener("test/test.log", stats)
    with opener("test/test.log") as logfile:
        assert len(logfile.readlines()) == 3


def test_get_opening_gzip():
    opener = reican.get_opener("test/test.log.gz", stats)
    with opener("test/test.log.gz") as logfile:
        assert len(logfile.readlines()) == 3


def test_get_opening_lzma():
    opener = reican.get_opener("test/test.log.lzma", stats)
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
    assert reican.get_timestamp(test_string) == test_timestamp


def test_get_timestamp_2():
    test_string = "[2015-10-31 13:54:42.146481] DEBUG: Reican: Using gzip to open the file"
    test_timestamp = "2015-10-31 13:54:42.146481"
    assert reican.get_timestamp(test_string) == test_timestamp


def test_get_timestamp_3():
    test_string = '''127.0.0.1 - - [31/Oct/2015:11:00:13 +0000]
    [1446314353.403] "GET /index.html HTTP/1.1" 200 54510 "-" 
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_0) 
    AppleWebKit/537.36 (KHTML,'''

    test_timestamp = "1446314353.403"
    assert reican.get_timestamp(test_string) == test_timestamp
