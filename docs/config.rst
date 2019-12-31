Configuration
=============


Setup
-----

Before using Lstail, you need to create a config file called `lstail.conf`.
Lstail will search for `lstail.conf` in the following locations (in that order):

  - /etc/lstail.conf
  - ~/.config/lstail.conf
  - lstail.conf (in current working directory)

Alternatively, you can specify the name of the config file to be read
using the ``--config`` command line parameter.

An example config file can be found below or online
at https://raw.githubusercontent.com/eht16/lstail/master/lstail.conf.
The important part to modify in the config file is the `server` section
which must be edited to point to your ElasticSearch instance to query
data from.


Configuration file
------------------

.. code-block:: ini

    [general]
    timeout = 30
    # refresh interval for use with --follow
    refresh_interval = 5.0
    initial_query_size = 10
    no_header = false
    header_color = light_yellow
    # time range from now in the past to query events initially (e.g. 2h)
    # if not specified, "1d" is used as fallback to prevent querying all documents from ElasticSearch
    # can be overridden via command line option --range
    # suffixes: m (minutes), h (hours), d (days)
    initial_time_range =
    # disable SSL certificate verification if necessary
    verify_ssl_certificates = true
    # index to be searched unless a saved Kibana search is specified
    default_index = logstash-*
    verbose = false

    # local ElasticSearch cluster
    [server_local-elastic-cluster]
    # set enable to false to ignore this server block
    enable=true
    url = http://127.0.0.1:9200

    # remote ElasticSearch cluster with Basic Auth
    [server_remote-elastic-cluster]
    enable=true
    url = https://some.host.tld
    username = foobar
    password = secret

    # Proxy ElasticSearch access through a Kibana instance
    [server_kibana-proxy]
    enable=true
    url = https://some.host.tld/kibana/elasticsearch
    username = foobar
    password = secret
    # new-line separated list(indent new lines) of additional HTTP headers to be sent,
    # e.g. useful when using Kibana as ElasticSearch proxy:
    # url = https://some.host.tld/kibana/elasticsearch and headers = kbn-xsrf: 1
    # Kibana 4.x wants: kbn-version: 4.x.y
    headers = kbn-xsrf: 1
      some-other-header: foobar


    [kibana]
    # the name of the index of Kibana (4.x or newer) in ElasticSearch
    kibana_index_name = .kibana
    # name/title of the default Saved Search from Kibana to be used for querying
    # can be overridden via command line
    #default_saved_search = Syslog lstail
    # default set of fields to display, used if no Kibana saved search is provided or found
    # these are also used for internal log messages
    default_columns: timestamp, hostname, program, message

    [parser]
    # log level names to be interpreted as warnings and errors (in lowercase, used for coloring)
    log_level_names_warning: warn, warning
    log_level_names_error: fatal, emerg, alert, crit, critical, error, err

    [format]
    timestamp = %Y-%m-%dT%H:%M:%S.%f

    # Display columns:
    # - the order of the following sections is important, the columns are displayed in that order
    # - the columns "timestamp" and "message" are essentially and should not be removed
    [display_column_timestamp]
    # This column specification is essential, do not remove it
    # "names" is a list of alternative column names which are mapped to this column if found
    names = timestamp, @timestamp, request_time
    # Available colors = blue, green, cyan, red, magenta, brown, gray, yellow, dark_gray,
    # light_blue, light_green, light_cyan, light_red, light_magenta, white, black
    # Use empty value for default terminal color
    color =
    padding = 23
    # see https://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior

    [display_column_log_level]
    names = syslog_severity, level, log_level, fail2ban_level, dj_level
    display = false
    color =
    padding =

    [display_column_hostname]
    names = hostname, host, fromhost, logsource
    color = magenta
    padding = 20

    [display_column_program]
    names = program, application, programname
    color = green
    padding = 15

    [display_column_message]
    names = message, answer
    color =
    padding =

    [display_column_http_host]
    names = http_host
    color = magenta
    padding = 20

    [display_column_http_clientip]
    names = http_clientip, client, dns.client_ip
    color = green
    padding = >39

    [display_column_http_verb]
    names = http_verb, type, dns.type
    color = light_red
    padding = 13

    [display_column_geoip.as_org]
    names = geoip.as_org
    padding = 25

    [display_column_http_code]
    names = http_code, ttl
    color = light_blue
    padding = 9

    [display_column_http_auth]
    names = http_auth
    color = light_blue
    padding = 9

    [display_column_query]
    names = query, dns.query
    color = light_green
    padding = 35

    [display_column_dns.answer]
    names = dns.answer
    color =
    padding =
