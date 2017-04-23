#!/usr/bin/env python
import sys
import os
import gzip
import re
import arrow
from logbook import Logger
from logbook import FileHandler

# I use cspell plugin for spell checking, and I want it to ignore few words
# cspell:ignore reican lzma isdir

# max file size in lines (10M by default)
MAX_LINES_TO_READ = 10000000
# max file size in megabytes
MAX_FILE_SIZE = "500M"
# where to write application log
LOG_FILE_NAME = "reican.log"

TIMESTAMP_FORMAT = "YYYY-MM-DD HH:mm:ss"

log_handler = FileHandler(LOG_FILE_NAME)
log_handler.push_application()
log = Logger("Reican")
log.info("Logging started")


def die(msg=None):
    """Print a message and exit."""
    if msg:
        print
        print msg
        print
        log.critical(msg)
    sys.exit(1)


def usage():
    """Display usage information."""
    print
    print "Usage:"
    print "{} <filename>".format(sys.argv[0])
    print
    die(None)


def is_readable(file_name):
    """Check if we have permissions to read the file."""
    return os.access(file_name, os.R_OK)


def get_opener(file_name, stats):
    """
    Return opener function based on extension fo the file.

    Support for different types of files based on their extension.
    Return 'open' object that can afterwards be iterated.
    """
    if file_name.endswith("gz"):
        log.debug("Using gzip to open the file")
        opener = gzip.open
        stats.compressed = True
    elif file_name.endswith("lzma"):
        try:
            import backports.lzma as lzma
        except:
            die("LZMA module not installed. Cannot open the file")
        log.debug("Using lzma to open the file")
        opener = lzma.open
        stats.compressed = True
    else:
        opener = open
    return opener


def get_file_name():
    """
    Handle args and return log file name
    that is passed as the first argument
    """
    if len(sys.argv) != 2:
        usage()
    else:
        file_name = sys.argv[1]
        if not os.path.exists(file_name):
            die("File {} does not exist".format(file_name))
    return file_name


class Stats:
    """Maintain some statistics."""

    def __init__(self, file_name):
        self.line_counter = 0
        self.log_start_time = None
        self.log_end_time = None
        self.size = get_size(file_name)
        self.compressed = False

    def max_lines_reached(self):
        if self.line_counter > MAX_LINES_TO_READ:
            return True
        return False

    def increment_line_counter(self):
        self.line_counter += 1


def get_timestamp(line):
    """
    Find the timestamp in a log line.

    If needed, timestamp format is also returned
    that can be later used by 'arrow'

    Returns a tuple of (timestamp, timestamp_format)
    """
    # Currently supported timestamps
    # 2015-10-30T20:20:11.563278+00:00
    # [2015-10-31 11:13:43.541912]
    # [1446314353.403]
    # 2015.11.01 15:04:39
    # [2017/03/19 10:39:31]

    regexes = {
        "([0-9]{4}\-[0-9]{2}\-[0-9]{2}\s[0-9:]+\.[0-9]+)": None,
        "^([0-9]{4}\-[0-9]{2}\-[0-9]{2}T[0-9:\.\+_-]+) ": None,
        "([0-9]{10}\.[0-9]{3})": None,
        "^([0-9]{4}\.[0-9]{2}\.[0-9]{2}\s[0-9:]{2}:[0-9]{2}:[0-9]{2})":
        "YYYY.MM.DD HH:mm:ss",
        "([0-9]{4}/[0-9]{2}/[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2})": "YYYY/MM/DD HH:mm:ss"
    }
    time_format = None
    for regex in regexes:
        r = re.search(regex, line)
        if r:
            # if match is found, exit the loop
            log.debug("Timestamp found")
            time_format = regexes[regex]
            break
    else:
        log.error("Could not match the timestamp")
        log.error(line)
        # if timestamp was not macthed, None will be returned
        # and  the line will be skipped
        return None, None
    if len(r.groups()) == 1:
        return r.groups()[0], time_format
    else:
        return False, False


def get_time(log_line):
    """Parse log line and return timestamp."""
    # use arrow module to translate timestamp to python datetime object
    timestamp, time_format = get_timestamp(log_line)
    # some time formats are not recognized by arrow,
    # therefore, if needed, a 'time_format' string is passed to arrow
    if time_format:
        time = arrow.get(timestamp, time_format)
    else:
        time = arrow.get(timestamp)
    return time


def get_size(file_name):
    """Return file size in bytes."""
    size_bytes = os.stat(file_name).st_size
    return size_bytes


def file_too_big(file_name):
    """Convert MAX_FILE_SIZE to bytes and check against the given file."""
    max_file_size_bytes = float(MAX_FILE_SIZE.replace("M", "")) * 1024 * 1024
    if float(max_file_size_bytes) < get_size(file_name):
        return True
    return False


def is_ascii(file_name):
    """Check if a file is a text file."""
    f = open(file_name)
    content = f.read(100)
    try:
        content.decode()
        return True
    except UnicodeDecodeError:
        return False


def humanize_delta(delta):
    """Interpret the delta in human friendly units."""
    seconds = int(delta.total_seconds())
    days = 0
    minutes = 0
    hours = 0
    if seconds > 86400:
        days = seconds / 86400
    # calculate remaining seconds
    seconds = seconds - (days * 86400)
    if seconds > 3600:
        hours = seconds / 3600
    # calculate remaining seconds
    seconds = seconds - (hours * 3600)
    if seconds > 60:
        minutes = seconds / 60
    # calculate remaining seconds
    seconds = seconds - (minutes * 60)
    return {
        'days': days,
        'hours': hours,
        'minutes': minutes,
        'seconds': seconds
    }


def human_delta_string(delta):
    """Return a string representation of the delta."""
    delta_string = ""
    if delta['days'] > 0:
        delta_string += "{} days, ".format(delta['days'])
    if delta['hours'] > 0:
        delta_string += "{} hours, ".format(delta['hours'])
    if delta['minutes'] > 0:
        delta_string += "{} minutes, ".format(delta['minutes'])
    if delta['seconds'] > 0:
        delta_string += "{} seconds.".format(delta['seconds'])
    return delta_string


def main():
    file_name = get_file_name()
    stats = Stats(file_name)

    if not is_readable(file_name):
        die("File is not readable. Check permissions?")
    if os.path.isdir(file_name):
        die("This appears to be a directory.")

    if not is_ascii(file_name):
        die("This does not appear to be a text file.")

    if file_too_big(file_name):
        die("File is too big")

    opener = get_opener(file_name, stats)
    times = {'start': None, 'stop': None, 'delta': None}
    start_hour = None
    end_hour = None
    per_hour_aggregation = {}
    with opener(file_name) as logfile:
        for line in logfile:
            if stats.max_lines_reached():
                log.error("MAX_LINES_TO_READ reached")
                break
            line = line.strip()
            # parse line and get the timestamp
            time = get_time(line)
            if not time:
                # skip the line if there's no timestamp
                pass
            # save first timestamp found so that delta can be calculated later
            if not times['start']:
                times['start'] = time
            # hours are parsed one by one
            # first determine the first hour and that will be the first bucket
            # when the time overflows the hour, move on to next one
            if not start_hour or time > end_hour:
                start_hour = time.replace(minute=0, second=0, microsecond=0)
                end_hour = start_hour.replace(hours=+1)
                log.debug("Start hour: {}".format(start_hour))
                log.debug("End hour: {}".format(end_hour))
                per_hour_aggregation[start_hour] = 0
            # line analysis and aggregation happens here
            log.info(time, line)
            stats.increment_line_counter()
            # increment the per hour line stats
            per_hour_aggregation[start_hour] += 1
            # every line could be the last one, so save the time every time
            times['stop'] = time

    bytes_per_line = stats.size / stats.line_counter
    times['delta'] = times['stop'] - times['start']
    if stats.max_lines_reached():
        print "Max lines limit was reached, parsing incomplete"
        die()
    print "-" * 80
    print "Summary:"
    print "File: {}".format(file_name),
    if stats.compressed:
        print ""
    else:
        print "."
    print "{} lines parsed".format(stats.line_counter)
    print "File size: {} bytes, {} bytes per line".format(stats.size,
                                                          bytes_per_line)
    print "Start time: {}".format(times['start'])
    print "Stop time: {}".format(times['stop'])

    print "Delta: {}".format(human_delta_string(humanize_delta(times['delta'])))
    keys = per_hour_aggregation.keys()
    keys.sort()
    for hour in keys:
        print hour.format(TIMESTAMP_FORMAT), per_hour_aggregation[hour]


if __name__ == "__main__":
    main()
