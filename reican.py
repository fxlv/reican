#!/usr/bin/env python
import sys
import os
import gzip
import re
import argparse
import time
import arrow
from logbook import Logger
from logbook import FileHandler


# import ptvsd
# ptvsd.enable_attach("supersecret", address = ('0.0.0.0', 8000))
# ptvsd.wait_for_attach()


# I use cspell plugin for spell checking, and I want it to ignore few words
# cspell:ignore reican lzma isdir

# max file size in lines (10M by default)
MAX_LINES_TO_READ = 10000000
# max file size in megabytes
MAX_FILE_SIZE = "50M"
# where to write application log
LOG_FILE_NAME = "reican.log"

TIMESTAMP_FORMAT = "YYYY-MM-DD HH:mm:ss"

log_handler = FileHandler(LOG_FILE_NAME)
log_handler.push_application()
log = Logger("Reican")
log.info("Logging started")


def func_log(function_name):
    """Decorator for logging and timing function execution."""

    def log_it(*args, **kwargs):
        """Log function and its args, execute the function and return the result."""
        t_start = time.time()
        result = function_name(*args, **kwargs)
        t_end = time.time() - t_start
        msg = "Function call: {}".format(function_name.__name__)
        if args:
            msg += " with args: {}".format(args)
        if kwargs:
            msg += " with kwargs {}".format(args, kwargs)
        msg += " executed in: {:5.5f} sec".format(t_end)
        log.debug(msg)
        return result

    return log_it


@func_log
def die(msg=None):
    """Print a message and exit."""
    if msg:
        print
        print msg
        print
        log.critical(msg)
    sys.exit(1)


@func_log
def is_readable(file_name):
    """Check if we have permissions to read the file."""
    return os.access(file_name, os.R_OK)


@func_log
def get_opener(file_name, stats):
    """
    Return opener function based on extension of the file.

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


class Stats:
    """Maintain some statistics."""

    def __init__(self, file_name):
        self.file_name = file_name
        self.line_counter = 0
        self.log_start_time = None
        self.log_end_time = None
        self.size = get_size(file_name)
        self.compressed = False
        self.bytes_per_line = None
        self.times = {'start': None, 'stop': None, 'delta': None}
        self.per_hour_aggregation = {}
        self.lines = {}
        self.filter_string = None
        self.filter_date = None

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
        "([0-9]{4}/[0-9]{2}/[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2})":
        "YYYY/MM/DD HH:mm:ss"
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


def is_same_day(date1, date2):
    """Compare two dates in arrow format and return True if they are the same day."""
    return date1.date() == date2.date()


@func_log
def get_size(file_name):
    """Return file size in bytes."""
    size_bytes = os.stat(file_name).st_size
    log.debug("File size for {} is {} bytes".format(file_name, size_bytes))
    return size_bytes


@func_log
def file_too_big(file_name):
    """Convert MAX_FILE_SIZE to bytes and check against the given file."""
    max_file_size_bytes = float(MAX_FILE_SIZE.replace("M", "")) * 1024 * 1024
    log.debug("Max file size is: {} bytes".format(max_file_size_bytes))
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


@func_log
def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument('file_name', help="Log file to parse")
    parser.add_argument('--filter', help="Filter string to search for")
    parser.add_argument('--date', help="Date string to search for")

    args = parser.parse_args()
    # try to parse the provided date, but if that die()'
    if args.date:
        try:
            args.date = arrow.get(args.date)
        except (arrow.parser.ParserError, TypeError) as exc:
            log.warn("Exception while parsing date '{}'".format(exc))
            log.warn("Could not parse date '{}'".format(args.date))
            die("Invalid date specified")
    return args


def check_if_file_is_valid(file_name):
    """
    Verify if a valid file name has been provided.

    Do several tests to see if file exists, is readable and so on.
    """
    if not os.path.exists(file_name):
        die("File {} does not exist".format(file_name))

    if not is_readable(file_name):
        die("File is not readable. Check permissions?")
    if os.path.isdir(file_name):
        die("This appears to be a directory.")

    if not is_ascii(file_name):
        die("This does not appear to be a text file.")

    if file_too_big(file_name):
        die("File {} is too big".format(file_name))
    return True


def print_summary(stats):
    """Print human readable summary of the log analysis."""
    print "-" * 80
    print "Summary:"
    if stats.filter_string:
        print "Filtering by string: '{}'".format(stats.filter_string)
    print "File: {}".format(stats.file_name),

    if stats.compressed:
        print ""
    else:
        print "."
    print "{} lines parsed".format(stats.line_counter)
    print "File size: {} bytes, {} bytes per line".format(stats.size,
                                                          stats.bytes_per_line)
    print "Start time: {}".format(stats.times['start'])
    print "Stop time: {}".format(stats.times['stop'])

    print "Delta: {}".format(
        human_delta_string(humanize_delta(stats.times['delta'])))
    keys = stats.per_hour_aggregation.keys()
    keys.sort()
    for hour in keys:
        print hour.format(TIMESTAMP_FORMAT), stats.per_hour_aggregation[hour]


@func_log
def get_line_count(file_handle):
    """Return line count in an already open file handle."""
    # first, count the lines in file, this will come in handy in reporting progress
    line_count = 0
    for line in file_handle:
        line_count += 1
    # return back to beginning of file
    if file_handle.tell() > 0:
        file_handle.seek(0)
    return line_count


class ProgressTracker:
    @func_log
    def __init__(self, logfile_handle):
        self.line_count = get_line_count(logfile_handle)
        self.one_percent = self.line_count / float(100)
        self.current_line = 0
        self.current_percentage = 0
        self.new_percentage = 0
        self.time_last = time.time()

    @func_log
    def increment(self):
        self.current_line += 1

    @func_log
    def report(self):
        # if one percent increment is reached 
        if self.current_line % self.one_percent < 3:
            self.new_percentage = int(self.current_line / self.one_percent)
            # and this is a new percentage point
            if self.new_percentage > self.current_percentage:
                # and at least 2 seconds have passed since previous % progress update
                next_update = self.time_last + 1
                if time.time() > next_update:
                    print "{}% done. Processed: {} out of {} lines".format(
                        self.current_percentage, self.current_line,
                        self.line_count)
                    self.time_last = time.time()
                self.current_percentage = self.new_percentage


def analyze_stats(stats):
    # iterate over all the lines from 'stats'
    start_hour = None
    end_hour = None
    for line in stats.lines:
        time = stats.lines[line]
        # save first timestamp found so that delta can be calculated later
        if not stats.times['start']:
            stats.times['start'] = time
        # hours are parsed one by one
        # first determine the first hour and that will be the first bucket
        # when the time overflows the hour, move on to next one
        if not start_hour or time > end_hour:
            start_hour = time.replace(minute=0, second=0, microsecond=0)
            end_hour = start_hour.replace(hours=+1)
            log.debug("Start hour: {}".format(start_hour))
            log.debug("End hour: {}".format(end_hour))
            stats.per_hour_aggregation[start_hour] = 0
        # line analysis and aggregation happens here
        log.debug("Stats line #{} time: {}".format(line, time))
        stats.increment_line_counter()
        # increment the per hour line stats
        stats.per_hour_aggregation[start_hour] += 1
        # every line could be the last one, so save the time every time
        stats.times['stop'] = time
    stats.bytes_per_line = stats.size / stats.line_counter
    stats.times['delta'] = stats.times['stop'] - stats.times['start']
    if stats.max_lines_reached():
        print "Max lines limit was reached, parsing incomplete"
        die()
    return stats


@func_log
def parse_file(file_name, stats):
    opener = get_opener(file_name, stats)
    with opener(file_name) as logfile:
        progress = ProgressTracker(logfile)
        # start iterating over lines, initially aim is to filter-out anything that can be skipped
        # such as, lines not containing required string, 
        # not containing timestamps or not mathing the date that was requested
        for line in logfile:
            progress.increment()
            progress.report()
            if stats.filter_string:
                if stats.filter_string not in line:
                    # if filtering string is specified,
                    # skip any lines that don't contain that string
                    continue
            if stats.max_lines_reached():
                log.error("MAX_LINES_TO_READ reached")
                break
            line = line.strip()
            # parse line and get the timestamp
            time = get_time(line)
            log.debug("Got time: {}".format(time))
            # if date has been specified, discard any lines that do not match it
            if stats.filter_date:
                stats.filter_date = arrow.get(stats.filter_date)
                if not is_same_day(time, stats.filter_date):
                    log.debug("Skipping non-matching date {}".format(time))
                    continue
            if not time:
                # skip the line if there's no timestamp
                pass
            # add the extracted line number and timestamp to stats object for later analysis
            stats.lines[progress.current_line] = time
    return stats


def main():
    """Main application logic goes here."""
    args = parse_args()
    file_name = args.file_name
    stats = Stats(file_name)
    check_if_file_is_valid(file_name)
    stats.filter_string = args.filter
    stats.filter_date = args.date

    stats = parse_file(file_name, stats)    
    stats = analyze_stats(stats)
    print_summary(stats)


if __name__ == "__main__":
    main()
