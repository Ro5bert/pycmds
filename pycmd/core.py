
"""
TODO: Fix usage string -- filename listed at front
"""

import shlex
import click
from utils import DotDict


class Commander:
    """
    TODO
    """

    def __init__(self, root_cmd: click.Command, name=None, obj=None, print_click_exceptions=True,
                 suppress_aborts=False, suppress_exits=True):
        self.root_cmd = root_cmd
        self.name = name
        self.obj = obj or DotDict(dynamic=False)
        self.print_click_exceptions = print_click_exceptions
        self.suppress_aborts = suppress_aborts
        self.suppress_exits = suppress_exits

    def exec(self, cmd, **ctx_settings):
        try:
            if isinstance(cmd, str):
                try:
                    cmd = shlex.split(cmd)
                except ValueError as e:
                    raise click.UsageError(str(e)) from e
            return self.root_cmd.main(args=cmd, prog_name=self.name, standalone_mode=False,
                                      obj=self.obj, **ctx_settings)
        except SystemExit:
            if not self.suppress_exits:
                raise
        except click.ClickException as e:
            if not self.print_click_exceptions:
                raise
            e.show()
        except click.Abort as e:
            if isinstance(e.__context__, KeyboardInterrupt):
                raise KeyboardInterrupt from None
            elif not self.suppress_aborts:
                raise


class AliasGroup(click.Group):
    """
    TODO
    """

    def __init__(self, name=None, commands=None, aliases=None, **kwargs):
        super().__init__(name, commands, **kwargs)
        self.aliases = {}
        if aliases:
            for cmd_name, cmd_aliases in aliases.items():
                for alias in cmd_aliases:
                    self.add_alias(cmd_name, alias)

    def add_command(self, cmd, name=None, aliases=None):
        super().add_command(cmd, name)
        if aliases:
            for alias in aliases:
                self.add_alias(cmd, alias)

    def add_alias(self, cmd, alias):
        if alias in self.commands or alias in self.aliases:
            raise ValueError("cannot add a non-distinct alias ({!r})".format(alias))
        if isinstance(cmd, str):
            try:
                cmd = self.commands[cmd]
            except KeyError:
                raise ValueError("cannot add alias {!r}; command {!r} is not a member of this group"
                                 .format(alias, cmd))
        elif cmd not in self.commands.values():
            cmd_name = cmd.name if isinstance(cmd, click.Command) else str(cmd)
            raise ValueError("cannot add alias {!r}; command {!r} is not a member of this group"
                             .format(alias, cmd_name))
        self.aliases[alias] = cmd

    def get_command(self, ctx, cmd_name):
        cmd = super().get_command(ctx, cmd_name)
        if cmd is not None:
            return cmd
        return self.aliases.get(cmd_name)

    def list_aliases(self, ctx):
        return sorted(self.aliases)
