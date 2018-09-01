
"""
Core functionality/Click addons.
"""

import shlex
import click
from .utils import DotDict


class Commander:
    """
    A simplified way to execute Click commands from an existing Python instance (i.e. not from the command line).
    """

    def __init__(self, root_cmd, name=None, obj=None, print_click_exceptions=True,
                 suppress_aborts=False, suppress_exits=True):
        """
        :param root_cmd: The root Click command object.
        :param name: The program name
        :param obj: The user object to place on the context. Defaults to a DotDict.
        :param print_click_exceptions: Whether to print Click exceptions when they occur or simply reraise them.
        :param suppress_aborts: Whether to suppress Abort exceptions or reraise them.
        :param suppress_exits: Whether to suppress SystemExit exceptions or reraise them.
        """
        self.root_cmd = root_cmd
        self.name = name
        self.obj = obj or DotDict(dynamic=False)
        self.print_click_exceptions = print_click_exceptions
        self.suppress_aborts = suppress_aborts
        self.suppress_exits = suppress_exits

    def exec(self, cmd, **ctx_settings):
        """
        Execute the given command string or list of command tokens.
        :param cmd: Command to execute as a string or list of tokens.
        :param ctx_settings: Additional context settings.
        :return: The result of the command.
        """
        try:
            if isinstance(cmd, str):
                # Try to split the command if it's a string.
                try:
                    # shlex.split splits a command like the command line would.
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
            # Always reraise KeyboardInterrupts even though click turns them into Aborts.
            if isinstance(e.__context__, KeyboardInterrupt):
                raise KeyboardInterrupt from e
            elif not self.suppress_aborts:
                raise


class AliasGroup(click.Group):
    """
    A command group capable of using aliases for its members. Otherwise identical to click.Group.
    """

    def __init__(self, name=None, commands=None, aliases=None, **kwargs):
        """
        :param aliases: A dictionary in the form {<cmd(_name)>: <iterable of aliases>, ...}.
        """
        super().__init__(name, commands, **kwargs)
        self.aliases = {}
        if aliases:
            # Iterate through the aliases and add each one.
            for cmd_name, cmd_aliases in aliases.items():
                for alias in cmd_aliases:
                    self.add_alias(cmd_name, alias)

    def add_command(self, cmd, name=None, aliases=None):
        """
        Same as click.Group.add_command but with the option to add aliases.
        :param cmd: The Command object.
        :param name: Command name to override the default in the Command object.
        :param aliases: An iterable of aliases for the given command.
        """
        super().add_command(cmd, name)
        if aliases:
            for alias in aliases:
                self.add_alias(cmd, alias)

    def add_alias(self, cmd, alias):
        """
        Add an alias for the given command.
        :param cmd: Command name or click.Command object.
        :param alias: A single alias to add.
        """
        # Disallow duplicate names.
        if alias in self.commands or alias in self.aliases:
            raise ValueError("cannot add a non-distinct alias ({!r})".format(alias))
        if isinstance(cmd, str):
            # Try to convert the command name string to a command object.
            try:
                cmd = self.commands[cmd]
            except KeyError:
                raise ValueError("cannot add alias {!r}; command {!r} is not a member of this group"
                                 .format(alias, cmd))
        # We cannot add an alias to a command which is not in this group already!
        elif cmd not in self.commands.values():
            cmd_name = cmd.name if isinstance(cmd, click.Command) else str(cmd)
            raise ValueError("cannot add alias {!r}; command {!r} is not a member of this group"
                             .format(alias, cmd_name))
        self.aliases[alias] = cmd

    def get_command(self, ctx, cmd_name):
        # First try to return a command according to its name, then its aliases.
        return super().get_command(ctx, cmd_name) or self.aliases.get(cmd_name)

    def list_aliases(self, ctx):
        """
        List all the aliases for all the commands in this group.
        :param ctx: Not used by default, but a subclass may desire access to the context.
        :return: A sorted list of aliases.
        """
        return sorted(self.aliases)
