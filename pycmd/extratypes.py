
"""
TODO
"""

import click
from utils import index_by_iterable


class CollectionParamType(click.ParamType):
    """
    TODO
    """

    name = "collection"

    def __init__(self, enclosing_chars="", require_enclosing_chars=False, item_sep_char=","):
        if len(enclosing_chars) not in (0, 2):
            raise ValueError("invalid enclosing_chars specification {!r}; must be of length zero or two"
                             .format(enclosing_chars))
        self.enclosing_chars = enclosing_chars
        self.require_enclosing_chars = require_enclosing_chars
        self.item_sep_char = item_sep_char

    def convert(self, value, param, ctx):
        raise NotImplementedError("{} class 'convert' method must be overridden.".format(self.__class__.__name__))

    def itemize(self, value: str):
        if value.startswith(self.enclosing_chars[0]) and value.endswith(self.enclosing_chars[1]):
            value = value[1:-1]
        elif self.require_enclosing_chars:
            self.fail("invalid syntax for {} parameter type; expected enclosing characters to be {!r} and {!r}"
                      .format(self.__class__.__name__, self.enclosing_chars[0], self.enclosing_chars[1]))

        items = []
        for item in value.split(self.item_sep_char):
            items.append(self.item_hook(item))
        if items[-1] == "":
            del items[-1]
        return items

    def item_hook(self, item):
        return item


class ListParamType(CollectionParamType):
    """
    TODO
    """

    name = "list"

    def convert(self, value, param, ctx):
        return self.itemize(value)


class DictParamType(CollectionParamType):
    """
    TODO
    """

    name = "dict"

    def __init__(self, kv_sep_char=":", **kwargs):
        super().__init__(**kwargs)
        self.kv_sep_char = kv_sep_char

    def convert(self, value, param, ctx):
        ret = {}
        for item in self.itemize(value):
            try:
                key, val = item.split(self.kv_sep_char)
            except ValueError:
                self.fail("invalid syntax for {} parameter type; invalid key-value pair {!r}"
                          .format(self.__class__.__name__, item))
            key = self.key_hook(key)
            val = self.value_hook(val)
            ret[key] = val
        return ret

    def key_hook(self, key):
        return key

    def value_hook(self, value):
        return value


class VariableParamType(click.ParamType):
    """
    TODO
    """

    name = "variable"

    RETURN_KEYS = "keys"
    RETURN_VALUE = "value"
    RETURN_KEYS_AND_VALUE = "keys and value"

    def __init__(self, var_bank=None, key_sep=".", error_on_unknown=False, return_type=RETURN_VALUE):
        self.var_bank = var_bank
        self.key_sep = key_sep
        self.error_on_unknown = error_on_unknown
        self.return_type = return_type

    def convert(self, value, param, ctx):
        if not (self.var_bank or hasattr(ctx.obj, "variables")):
            raise click.ClickException("cannot fetch variables without assigned variable bank")
        keys = self.decompose_var_name(value)
        bank = self.var_bank or ctx.obj.variables
        try:
            data = index_by_iterable(bank, keys)
            if self.return_type == self.RETURN_KEYS:
                return keys
            elif self.return_type == self.RETURN_VALUE:
                return data
            else:  # if self.return_type == self.RETURN_KEYS_AND_VALUE
                return keys, data
        except KeyError:
            if self.error_on_unknown:
                self.fail("cannot find variable {!r}".format(value), param, ctx)
            return ""  # returning None yields a BadParameter exception

    def decompose_var_name(self, var_name):
        return var_name.split(self.key_sep)


LIST = ListParamType(enclosing_chars="[]")
DICT = DictParamType(enclosing_chars="{}")
VARIABLE = VariableParamType()
