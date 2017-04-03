# Reican

Reican goes and finds stuff from your logs.
Not much here yet but soon the Reican will be able to do useful stuff.

## Timestamps

Supported formats:

* 2015-10-30T20:20:11.563278+00:00
* 2015-10-31 11:13:43.541912
* 1446236678.247

## Virtualenv

For the first time:
```
sudo pip install virtualenv
virtualenv venv
```
Then Every time:
```
source venv/bin/activate
```

## Dependencies

Inside the virtualenv you might want to have:
* pytest
* backports.lzma 
* monkeypatch

Install them using
```
pip install -r requirements.txt
```

Note, that you'll need at least `lzma` headers to build `arrow`.
On a Debian based system you' ll want to do something like:

```
sudo apt-get install liblzma-dev
```


