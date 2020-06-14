Usage
=====

Command line options
--------------------

.. code-block:: console

    usage: lstail [-h] [-V] [-d] [-v] [-c FILE] [-f] [-l] [-H] [--csv]
                  [-n NUM] [-q QUERY] [-r RANGE] [-s NAME] [--select-saved-search]

    optional arguments:
      -h, --help            show this help message and exit
      -V, --version         show version and exit (default: False)
      -d, --debug           enable tracebacks (default: False)
      -v, --verbose         Show own log messages (default: False)
      -c FILE, --config FILE
                            configuration file path (default: None)
      -f, --follow          Constantly fetch new data from ElasticSearch (default: False)
      -l, --list-saved-searches
                            List all saved searches from Kibana (default: False)
      -H, --no-header       Do not print header line before the output (default: False)
      --csv                 Use CSV (comma separated) output (default: False)
      -n NUM, --lines NUM   Output the last NUM lines, instead of the last 10 (default: None)
      -q QUERY, --query QUERY
                            Set/Overwrite the search query (use Lucene query syntax) (default: None)
      -r RANGE, --range RANGE
                            Query events from the last RANGE minutes(m)/hours(h)/days(d) (default: None)
      -s NAME, --saved-search NAME
                            Saved search title as stored in Kibana ("-" to select from a list) (default: None)
      --select-saved-search
                            Interactively select a saved search from a list (default: False)


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
