
"""
Prompt-toolkit completer for click commands.
"""

import sys
import os
import shlex
from prompt_toolkit.completion import Completer, Completion
import click
from .core import AliasGroup


class CmdCompleter(Completer):
    """
    Prompt-toolkit completer for click commands.
    A few important notes:
        Only POSIX-style arguments (with single and double dashes) are supported.
        Only context settings specified on the root/top-level command will be considered (by necessity).
        Incompatible with "allow_interspersed_args" on the Context.
        Incompatible with "ignore_unknown_opts" on the Context.
        Incompatible with "chain" on MultiCommands.
        The split character for parameters with nargs>1 is expected to be a space.
    """

    NONE_USED = object()

    def __init__(self, root_cmd, prog_name=None, use_cmd_aliases=True):
        """
        :param root_cmd: The root click Command.
        :param prog_name: The program name to show in help message, etc. Defaults to file name from sys.argv.
        :param use_cmd_aliases: Whether to complete command aliases from AliasGroups.
        """
        if prog_name is None:
            prog_name = os.path.basename(sys.argv[0])
        self.root_cmd = root_cmd
        self.use_cmd_aliases = use_cmd_aliases
        self.dummy_context = click.Context(root_cmd, info_name=prog_name, **root_cmd.context_settings)

    def get_completions(self, document, complete_event):
        try:
            # shlex.split splits strings like they would be on the command line.
            words = shlex.split(document.text)
        except ValueError:
            # This happens when quotes aren't closed or an invalid escape sequence is encountered.
            return []
        # document.get_word_under_cursor only finds actual english words it seems... thus we define our own requirements
        # on what is the "current word."
        curr_word = words[-1] if words and document.is_cursor_at_the_end and document.text.rstrip() == document.text \
            else ""
        # Some state variables:
        curr_cmd = self.root_cmd
        curr_options = self.get_options(curr_cmd)
        curr_subcmds = self.get_subcommand_names(curr_cmd)
        curr_used_options = set()
        # complete_more_short is a state variable set to indicate if we should complete more single dash options on the
        # current word if it is a group of short options. If the last option in the group is a flag, then we may;
        # otherwise we're expecting a value, or the value is appended to the end of the group.
        complete_more_short = None
        # Added to as need to indicate how many words (which are assumed to be values) to skip.
        n_vals_needed = 0
        # Loop through each word and classify it.
        for word in words:
            # Skip words if needed.
            if n_vals_needed:
                n_vals_needed -= 1
                continue
            # Parse long options.
            if word.startswith("--"):
                used, n_vals_needed = self.parse_long_flag(word, curr_options)
                # "used is None" indicates parse_long_flag failed to match word with a option, but we should only yield
                # no completions if this word is the last word, since the user may still be editing/correcting it.
                if used is None and not word == curr_word:
                    return []
                elif used is not self.NONE_USED:
                    curr_used_options.add(used)
            # Parse short options.
            elif word.startswith("-"):
                used, n_vals_needed, complete_more_short = self.parse_short_flags(word, curr_options)
                if used is None:
                    return []
                curr_used_options.update(used)
            elif word in curr_subcmds:
                curr_cmd = curr_cmd.get_command(self.dummy_context, word)
                curr_options = self.get_options(curr_cmd)
                curr_subcmds = self.get_subcommand_names(curr_cmd)
                curr_used_options = set()
            # If this word is not an option or subcommand and its not the current (i.e. still being edited) word, it
            # ought to be an argument, which we can't auto-complete for.
            elif not word == curr_word:
                return []
        # If we ended the above loop still looking for values, we can't auto-complete.
        if n_vals_needed:
            return []
        # Establish a list of option names that may still be used (and thus should be shown in the completion menu).
        option_completions = [k for k, v in curr_options.items()
                              if v in set(curr_options.values()).difference(curr_used_options)]
        if self.is_short_flag(curr_word):
            # Only permit grouping more short options if complete_more_short is set.
            if complete_more_short:
                return self.filter_and_format_short_flags(option_completions)
            # Otherwise we don't complete anything.
            return []
        # If the current word isn't a group of short options, complete simply based on what each candidate (all option
        # names and subcommands for the right-most identified command in the document text) starts with.
        return self.filter_and_format_startswith(option_completions + curr_subcmds, curr_word)

    def get_subcommand_names(self, cmd):
        # Commands only have subcommands if they're MultiCommands
        if isinstance(cmd, click.MultiCommand):
            # Create a shallow copy of the return list from list_commands,
            # just in case the implementation doesn't for us.
            ret = cmd.list_commands(self.dummy_context)[:]
            # Also include aliases if we can.
            if self.use_cmd_aliases and isinstance(cmd, AliasGroup):
                ret.extend(cmd.list_aliases(self.dummy_context))
            return ret
        return []

    def get_options(self, cmd):
        params = cmd.get_params(self.dummy_context)
        # Format the dict so that each option name/alias is a distinct key/value pair for easy access.
        return {name: param for param in params for name in param.opts + param.secondary_opts
                if isinstance(param, click.Option)}

    def filter_and_format_short_flags(self, flags):
        return [Completion(flag[1]) for flag in flags if self.is_short_flag(flag)]

    @staticmethod
    def parse_long_flag(string, params):
        # We use None to indicate failure, so we must use a different object to indicate success when the matched
        # option has "multiple" or "count" set.
        used_param = CmdCompleter.NONE_USED
        n_vals_needed = 0
        try:
            param = params[string]
        except KeyError:
            # We couldn't match the given string to a option!
            return None, None
        if not (param.multiple or param.count):
            # This means this option should not be given again.
            used_param = param
        if not (param.is_flag or param.count):
            # Remove one from the values needed if one of the values needed for this option (there may only be one) is
            # clustered with this option already.
            compressed = len(string.split("=")) == 2
            n_vals_needed = param.nargs - compressed
        return used_param, n_vals_needed

    @staticmethod
    def parse_short_flags(string, params):
        used_params = set()
        n_vals_needed = 0
        complete_more_short = True
        for idx, char in enumerate(string[1:]):
            try:
                param = params["-"+char]
            except KeyError:
                # We couldn't match the char to a option!
                return None, None, None
            if not (param.multiple or param.count):
                # This means this option should not be given again.
                used_params.add(param)
            if param.is_flag or param.count:
                # We can keep looping and grouping (short options) baby.
                continue
            else:
                complete_more_short = False
                # If we're at the end of the given string and thus no value is appended to the right...
                if idx == len(string) - 2:
                    n_vals_needed = param.nargs
                # Otherwise one of the needed values (there may only be one) is clustered on this option,
                # hence the minus one.
                else:
                    n_vals_needed = param.nargs - 1
            break
        return used_params, n_vals_needed, complete_more_short

    @staticmethod
    def is_short_flag(flag):
        return flag.startswith("-") and not flag.startswith("--")

    @staticmethod
    def filter_and_format_startswith(strings, prefix):
        ret = []
        prefix_len = len(prefix)
        for string in strings:
            if string.startswith(prefix):
                ret.append(Completion(string[prefix_len:]))
        return ret
