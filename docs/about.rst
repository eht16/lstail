About
=====


Features
--------

Lstail queries ElasticSearch for log events and displays
them on the terminal. Saved Searches from Kibana can be used
for quick access to filters and prepared column configuration.


  * Follow mode like in `tail -f`
  * CSV output / export
  * Can read Saved Searches from ElasticSearch and use their
    filters and column setup
  * Flexible configurable output of columns, colors and padding
  * Can be proxied through Kibana if not direct ElasticSearch connection is possible
  * Works with ElasticSearch 2.x - 7.x
  * Made with Python and love

.. image:: lstail-demo.svg
  :alt: lstail usage demonstration


Source code
------------

See https://github.com/eht16/lstail/.


License
-------

.. literalinclude:: ../LICENSE
    :language: none


ChangeLog
---------

1.0.0 (Dec 31, 2019)
++++++++++++++++++++

  * Initial release
