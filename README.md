gdb-buildbot
============

gdb buildbot configuration


This is a buildbot configuration for gdb.

Currently it is a bit out of date.  For example, native-gdbserver.exp
is now in-tree and doesn't need any special configuration.

This configuration makes it easy to deploy slaves that test gdb in
different scenarios.  For example there is a canned way to run the
test suite using gdbserver.  It is also easy to add new
configurations.  This is important because gdb can be used in many
different ways.

It collects the .sum files and establishes a baseline.  The baselines
are then "ratcheted": new PASSes are automatically added to the
baseline for a given slave configuration, and any regressions are
flagged as build failures.

This also provides a way to retrieve the .sum files for any given
revision and configuration.  This can be handy for doing local
comparisons.


To do items include:

* Add more configurations.  For example, dwz, split debuginfo, etc.

* Store the .sum files in a nicer way.  Right now they accumulate and
  are not de-duplicated.  Just de-duplicating would help a bit, but
  perhaps a real database of some form would be nicer.

* Provide a way to do nice web-based comparisons across different
  configurations.

* Host it somewhere :-)
