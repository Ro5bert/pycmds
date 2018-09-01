
"""
TODO
"""

import sys
import os
import shlex
from prompt_toolkit.document import Document
from prompt_toolkit.completion import Completer, Completion
import click
from core import AliasGroup


class CmdCompleter(Completer):
    """
    Prompt-toolkit completer for click commands.
    A few important notes:
        Only POSIX-style arguments (with single and double dashes) are supported.
        Only context settings specified on the root/top-level command will be considered (by necessity).
        Incompatible with "allow_interspersed_args" on the Context.
        Incompatible with "ignore_unknown_opts" on the Context.
        Incompatible with "chain" on MultiCommands.
    """

    def __init__(self, root_cmd: click.Command, prog_name=None, use_cmd_aliases=True):
        if prog_name is None:
            prog_name = os.path.basename(sys.argv[0])
        self.root_cmd = root_cmd
        self.use_cmd_aliases = use_cmd_aliases
        self.dummy_context = click.Context(root_cmd, info_name=prog_name, **root_cmd.context_settings)

    def get_completions(self, document: Document, complete_event):
        try:
            words = shlex.split(document.text)
        except ValueError:
            return []
        curr_word = words[-1] if words and document.is_cursor_at_the_end and document.text.rstrip() == document.text \
            else ""
        curr_cmd = self.root_cmd
        curr_params = self.get_options(curr_cmd)
        curr_subcmds = self.get_subcommand_names(curr_cmd)
        curr_used_params = set()
        complete_more_short = None
        n_vals_needed = 0
        for word in words:
            if n_vals_needed:
                n_vals_needed -= 1
                continue
            if word.startswith("--"):
                used, n_vals_needed = self.parse_long_flag(word, curr_params)
                if used is None and not word == curr_word:
                    return []
                curr_used_params.add(used)
            elif word.startswith("-"):
                used, n_vals_needed, complete_more_short = self.parse_short_flags(word, curr_params)
                if used is None:
                    return []
                curr_used_params.update(used)
            elif word in curr_subcmds:
                curr_cmd = curr_cmd.get_command(self.dummy_context, word)
                curr_params = self.get_options(curr_cmd)
                curr_subcmds = self.get_subcommand_names(curr_cmd)
                curr_used_params = set()
            elif not word == curr_word:  # arguments
                return []
        if n_vals_needed:
            return []
        param_completions = [k for k, v in curr_params.items()
                             if v in set(curr_params.values()).difference(curr_used_params)]
        if self.is_short_flag(curr_word):
            if complete_more_short:
                return self.filter_and_format_short_flags(param_completions)
            return []
        return self.filter_and_format_startswith(param_completions+curr_subcmds, curr_word)

    def get_subcommand_names(self, cmd):
        if isinstance(cmd, click.MultiCommand):
            ret = cmd.list_commands(self.dummy_context)[:]
            if self.use_cmd_aliases and isinstance(cmd, AliasGroup):
                ret.extend(cmd.list_aliases(self.dummy_context))
            return ret
        return []

    def get_options(self, cmd):
        params = cmd.get_params(self.dummy_context)
        return {name: param for param in params for name in param.opts + param.secondary_opts
                if isinstance(param, click.Option)}

    def filter_and_format_short_flags(self, flags):
        return [Completion(flag[1]) for flag in flags if self.is_short_flag(flag)]

    @staticmethod
    def parse_long_flag(string, params):
        used_param = None
        n_vals_needed = 0
        try:
            param = params[string]
        except KeyError:
            return None, None
        if not (param.multiple or param.count):
            used_param = param
        if not (param.is_flag or param.count):
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
                return None, None, None
            if not (param.multiple or param.count):
                used_params.add(param)
            if param.is_flag or param.count:
                continue
            else:
                complete_more_short = False
                if idx == len(string) - 2:
                    n_vals_needed = param.nargs
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
