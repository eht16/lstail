Usage
=====

Command line options
--------------------

.. code-block:: console

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


Examples
--------

Display events (from the configured index pattern) since ten minutes::

    lstail -r 10m

Display the last 20 events (from the configured index pattern)::

    lstail -n 20

Display all events matching the given query::

    lstail -q 'host: google.com'

List Saved Searches from Kibana::

    lstail -l

Display and follow events using the Saved Search "Syslog" (use Ctrl-C to interrupt)::

    lstail -s Syslog -f

Overwrite search query for Saved Search "Syslog" (i.e. ignore the query stored
in the Saved Search but use the configured columns)::

    lstail -s Syslog -q program:cron
