Lstail
======

[![PyPI](https://img.shields.io/pypi/v/lstail.svg)](https://pypi.org/project/lstail/)
[![Documentation Status](https://readthedocs.org/projects/lstail/badge/?version=latest)](https://lstail.org/)
[![Travis CI](https://travis-ci.org/eht16/lstail.svg?branch=master)](https://travis-ci.org/eht16/lstail)
[![Python Versions](https://img.shields.io/pypi/pyversions/lstail.svg)](https://pypi.org/project/lstail/)
[![License](https://img.shields.io/pypi/l/lstail.svg)](https://pypi.org/project/lstail/)


A command line tool to query log events from ElasticSearch,
a bit like tail for Logstash/ElasticSearch.

Lstail queries ElasticSearch for log events and displays
them on the terminal. Saved Searches from Kibana can be used
for quick access to filters and prepared column configuration.
For more details and usage examples please see the
documentation at https://lstail.org/.


Features
--------

  * Follow mode like in `tail -f`
  * CSV output / export
  * Can read Saved Searches from ElasticSearch and use their
    filters and column setup
  * Flexible configurable output of columns, colors and padding
  * Can be proxied through Kibana if not direct ElasticSearch connection is possible
  * Works with ElasticSearch 2.x - 7.x
  * Made with Python and love

![lstail usage demonstration](docs/lstail-demo.svg)


Installation
------------

Lstail requires Python 3.5 or newer.
The easiest method is to install directly from pypi using pip:

    pip install lstail


If you prefer, you can download lstail and install it
directly from source:

    python setup.py install


Get the Source
--------------

The source code is available at https://github.com/eht16/lstail/.


Setup
-----

Before using Lstail, you need to create a config file called `lstail.conf`.
Lstail will search for `lstail.conf` in the following locations (in that order):

  - /etc/lstail.conf
  - ~/.config/lstail.conf
  - lstail.conf (in current working directory)

Alternatively, you can specify the name of the config file to be read
using the `--config` command line parameter.

An example config file can be found in the sources or online
at https://raw.githubusercontent.com/eht16/lstail/master/lstail.conf.
The important part to modify in the config file is the `server` section
which must be edited to point to your ElasticSearch instance to query
data from.

For details on all configuration options, please see the documentation:
https://lstail.org/.


Usage
-----

Display events (from the configured index pattern) since ten minutes:

    lstail -r 10m

Display the last 20 events (from the configured index pattern):

    lstail -n 20

Display all events matching the given query:

    lstail -q 'host: google.com'

List Saved Searches from Kibana:

    lstail -l

Display and follow events using the Saved Search "Syslog" (use Ctrl-C to interrupt):

    lstail -s Syslog -f

Overwrite search query for Saved Search "Syslog" (i.e. ignore the query stored
in the Saved Search but use the configured columns):

    lstail -s Syslog -q program:cron


Command line options
--------------------

    usage: lstail [-h] [-V] [-d] [-v] [-c FILE] [-f] [-l] [-H] [--csv]
                  [-n NUM] [-q QUERY] [-r RANGE] [-s NAME]

    optional arguments:
      -h, --help            show this help message and exit
      -V, --version         show version and exit
      -d, --debug           enable tracebacks
      -v, --verbose         Show own log messages
      -c FILE, --config FILE
                            configuration file path
      -f, --follow          Constantly fetch new data from ElasticSearch
      -l, --list-saved-searches
                            List all saved searches from Kibana
      -H, --no-header       Do not print header line before the output
      --csv                 Use CSV (comma separated) output
      -n NUM, --lines NUM   Output the last NUM lines, instead of the last 10
      -q QUERY, --query QUERY
                            Set/Overwrite the search query (use Lucene query
                            syntax)
      -r RANGE, --range RANGE
                            Query events from the last RANGE
                            minutes(m)/hours(h)/days(d)
      -s NAME, --saved-search NAME
                            Saved search title as stored in Kibana


Contributing
------------

Found a bug or got a feature request? Please report it at
https://github.com/eht16/lstail/issues.


Author
------

Enrico Tröger <enrico.troeger@uvena.de>
