# Reican

Reican goes and finds stuff from your logs.
Not much here yet but soon the Reican will be able to do useful stuff.

Idea is to write something that helps getting immediate, but basic, understanding
of what is happening in a specific log file.

For example, has the log volume always been like this?
Easy way to check is to run Reican with no filter - this will gove you sort of a breakdown per hour.

If there's something more specific you're looking for, filtering by string provides the same per-hour bucketing, but this time only for lines that match your filter string.

Hopefully this will grow into something useful eventually, but for now I use this project to learn more about testing and TDD.

## Getting started

Just clone and run `./setup.sh` to handle the dependencies.
Afterwards `./reican.py <log_file_name>` is all you need to get going.

## Timestamps

Supported formats:

* 2015-10-30T20:20:11.563278+00:00
* 2015-10-31 11:13:43.541912
* 1446236678.247
* 2017/03/19 10:39:31

## Dependencies

Inside the virtualenv you might want to have:
* pytest
* backports.lzma 
* monkeypatch
* mock
* arrow

Install them using
```
pip install -r requirements.txt
```

Note, that you'll need at least `lzma` headers to build `arrow`.
On a Debian based system you' ll want to do something like:

```
sudo apt-get install liblzma-dev
```


