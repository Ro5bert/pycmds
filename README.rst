PyCmds
======

A wrapper around the `Click <http://click.pocoo.org/5/>`_
library for Python. PyCmds makes it easier to use Click's command execution
framework independently of the command line (i.e. executing Click
``Command``s in an existing Python instance.)

To accompany this, PyCmds adds a ``CmdCompleter`` class which implements the
``Completer`` interface from the
`python-prompt-toolkit <(https://github.com/jonathanslenders/python-prompt-toolkit)>`_.
Using this class, one may create a python-prompt-toolkit interface with
intelligent (see below) autocompletion for Click ``Command``s and ``Option``s.

Also, PyCmds adds an ``AliasGroup`` class to allow the assignment of aliases
to Click ``Command``s.

``CmdCompleter`` Features
-------------------------

- Only displays completion menu when the completer is certain of what
  options or subcommands are valid. (E.g. no naive option or subcommand
  suggestions when Click is expecting a value for a previous option.)
- Considers ``click.Option.is_flag`` and ``click.Parameter.nargs`` to
  decide how many values a option should consume.
- Considers ``click.Option.count`` and ``click.Option.multiple`` to decide
  if more than one instance of the same option should be permitted.
- Smart autocompletion for grouped short flags with or without a value
  clustered on the end.

Important Notes About ``CmdCompleter``
--------------------------------------

- Designed primarily for POSIX-style options.
- Only context settings specified on the root/top-level ``Command`` will
  be considered (by necessity).
- Incompatible with ``click.Context.allow_interspersed_args``.
- Incompatible with ``click.Context.ignore_unknown_opts``.
- Incompatible with ``click.MultiCommand.chain``.
- The split character for parameters with nargs > 1 is expected to be a
  space.
