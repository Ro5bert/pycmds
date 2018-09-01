
"""
Extra Click parameter types.
"""

import click
from .utils import index_by_iterable


class CollectionParamType(click.ParamType):
    """
    A base collection (as in collection of objects) parameter type. This class allows the breaking down of a string
    value into a list of items according to an item separation character (default is a comma.) A pair of enclosing
    characters--say, opening and closing parentheses--may be specified--and, further, even required--for the sake of
    readability.
    """

    name = "collection"

    def __init__(self, enclosing_chars="", require_enclosing_chars=False, item_sep_char=","):
        """
        :param enclosing_chars: A two-length string, tuple, etc. specifying the opening then closing characters, or an
            empty string, tuple, etc. for no enclosing characters.
        :param require_enclosing_chars: Whether or not the enclosing characters must be present when a string is
            itemized.
        :param item_sep_char: The delimiting character between items.
        """
        if len(enclosing_chars) not in (0, 2):
            raise ValueError("invalid enclosing_chars specification {!r}; must be of length zero or two"
                             .format(enclosing_chars))
        if not enclosing_chars and require_enclosing_chars:
            raise ValueError("invalid configuration: enclosing_chars must be specified if require_enclosing_chars is")
        self.enclosing_chars = enclosing_chars
        self.require_enclosing_chars = require_enclosing_chars
        self.item_sep_char = item_sep_char

    def convert(self, value, param, ctx):
        raise NotImplementedError("{} class 'convert' method must be overridden.".format(self.__class__.__name__))

    def itemize(self, value):
        """
        Break down the given string into items.
        :param value: The string to itemize.
        :return: The resultant list of items.
        """
        if self.enclosing_chars and value.startswith(self.enclosing_chars[0])\
                and value.endswith(self.enclosing_chars[1]):
            # Remove enclosing chars.
            value = value[1:-1]
        elif self.require_enclosing_chars:
            # Raise a Click error if we require enclosing chars and there weren't any.
            self.fail("invalid syntax for {} parameter type; expected enclosing characters to be {!r} and {!r}"
                      .format(self.__class__.__name__, self.enclosing_chars[0], self.enclosing_chars[1]))

        # Populate a list with the items.
        items = []
        for item in value.split(self.item_sep_char):
            items.append(self.item_hook(item))
        # If the given string ends in the item_sep_char, the last list element will be an empty string; delete it.
        if items[-1] == "":
            del items[-1]
        return items

    # noinspection PyMethodMayBeStatic
    def item_hook(self, item):
        """
        Called in itemize whenever an item is generated. Allows for user modifications to the item (e.g. casting).
        :param item: The unmodified item string.
        :return: The item after user modification. Defaults to the original, unmodified string.
        """
        return item


class ListParamType(CollectionParamType):
    """
    A list parameter type. Parses a string of comma (by default)-separated string values and returns them in a Python
    list.
    """

    name = "list"

    def convert(self, value, param, ctx):
        return self.itemize(value)


class DictParamType(CollectionParamType):
    """
    A dictionary parameter type. Converts a string of comma (by default)-separated key-value pairs--which are themselves
    separated by (by default) colons--into a Python dictionary.
    """

    name = "dict"

    def __init__(self, kv_sep_char=":", **kwargs):
        """
        :param kv_sep_char: The key-value separation character. (Not to be confused with item_sep_char.)
        """
        super().__init__(**kwargs)
        self.kv_sep_char = kv_sep_char

    def convert(self, value, param, ctx):
        ret = {}
        for item in self.itemize(value):
            try:
                key, val = item.split(self.kv_sep_char)
            except ValueError:
                # This happens if we unpack the wrong amount of values.
                self.fail("invalid syntax for {} parameter type; invalid key-value pair {!r}"
                          .format(self.__class__.__name__, item))
            key = self.key_hook(key)
            val = self.value_hook(val)
            ret[key] = val
        return ret

    # noinspection PyMethodMayBeStatic
    def key_hook(self, key):
        """
        Called in convert whenever a key is generated. Allows for user modifications to the key (e.g. casting).
        :param key: The unmodified key string.
        :return: The key after user modification. Defaults to the original, unmodified string.
        """
        return key

    # noinspection PyMethodMayBeStatic
    def value_hook(self, value):
        """
        Called in convert whenever a value is generated. Allows for user modifications to the value (e.g. casting).
        :param value: The unmodified value string.
        :return: The value after user modification. Defaults to the original, unmodified string.
        """
        return value


class VariableParamType(click.ParamType):
    """
    A variable parameter type. Takes a given variable name string and attempts to convert it into its corresponding
    value by looking for a dictionary entry in, first, a given variable bank and then, if that fails, the "variables"
    dictionary on the user object "obj" on the context, should it exist. If neither location is provided/exists, a Click
    exception is generated. Nested values may be specified using the key_sep_char (defaults to a period). E.g.
    "key1.key2" would attempt to return the value corresponding to "key2" which is inside "key1" which is, in turn,
    inside the variable bank.
    """

    name = "variable"

    # These constants specify the format of the return value of the convert method.
    RETURN_KEYS = "keys"
    RETURN_VALUE = "value"  # Default
    RETURN_KEYS_AND_VALUE = "keys and value"

    def __init__(self, var_bank=None, key_sep_char=".", error_on_unknown=False, return_type=RETURN_VALUE):
        """
        :param var_bank: A dictionary-like object to look in for variables. If not provided, then a dictionary named
            "variables" is searched for on the context object.
        :param key_sep_char: What character to split the input string into keys on.
        :param error_on_unknown: Whether to fail when the specified variable cannot be found.
        :param return_type: What should be returned from the convert function: the keys representing the path to the
            variable, the value of the variable, or both.
        """
        self.var_bank = var_bank
        self.key_sep_char = key_sep_char
        self.error_on_unknown = error_on_unknown
        self.return_type = return_type

    def convert(self, value, param, ctx):
        if not (self.var_bank or hasattr(ctx.obj, "variables")):
            raise click.ClickException("cannot fetch variables without assigned variable bank")
        keys = self.dismantle_var_name(value)
        bank = self.var_bank or ctx.obj.variables
        try:
            data = index_by_iterable(bank, keys)
        except KeyError:
            if self.error_on_unknown:
                self.fail("cannot find variable {!r}".format(value), param, ctx)
            return ""  # Returning None yields a BadParameter exception, so return an empty string instead.
        if self.return_type == self.RETURN_KEYS:
            return keys
        elif self.return_type == self.RETURN_VALUE:
            return data
        else:  # if self.return_type == self.RETURN_KEYS_AND_VALUE
            return keys, data

    def dismantle_var_name(self, var_name):
        """
        Break the given input string/variable name into keys.
        :param var_name: The input variable name.
        :return: A list of keys.
        """
        return var_name.split(self.key_sep_char)


# Below are instances of all the instantiable parameter types defined above with sensible defaults for all their
# arguments.
LIST = ListParamType(enclosing_chars="[]")
DICT = DictParamType(enclosing_chars="{}")
VARIABLE = VariableParamType()
