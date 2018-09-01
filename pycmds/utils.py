
"""
Miscellaneous utility classes/functions.
"""


class DotDict(dict):
    """
    A dictionary that maps attribute access to item access.
    """

    def __init__(self, *args, dynamic=True, **kwargs):
        """
        :param args: A single Python dictionary, otherwise as specified in dict's documentation.
        :param dynamic: Whether to create empty DotDicts as they are fetched, if they do not exist. E.g.
            "mydict.key1.key2.key3 = 123" would create "key1" and "key2" dynamically if they did not already exist.
        """
        # Notice we use "type" instead of "isinstance" because "type" doesn't check inheritance.
        if len(args) == 1 and type(args[0]) == dict:
            d = args[0]
            for k, v in d.items():
                if type(v) == dict:
                    # Notice we use the same value for dynamic.
                    v = DotDict(v, dynamic=dynamic)
                    d[k] = v
        super().__init__(*args, **kwargs)
        self.__dict__["dynamic"] = dynamic

    def __getitem__(self, item):
        if self.dynamic and item not in self:
            # Dynamically create a new DotDict.
            val = DotDict()
            self.__setitem__(item, val)
            return val
        # Otherwise simply attempt to return the value.
        return super().__getitem__(item)

    def __setitem__(self, key, value):
        # Make sure if we set a dictionary, we first cast it to a DotDict.
        if type(value) == dict:
            # Notice we use the same value for dynamic.
            value = DotDict(value, dynamic=self.dynamic)
        super().__setitem__(key, value)

    def __getattr__(self, item):
        try:
            return self.__getitem__(item)
        except KeyError as e:
            # This error resulted from attribute access, therefore reraise it as an AttributeError.
            # After all, getting a KeyError from getattr doesn't make any sense.
            raise AttributeError(repr(item)) from e

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    def __delattr__(self, item):
        try:
            self.__delitem__(item)
        except KeyError as e:
            # This error resulted from attribute access, therefore reraise it as an AttributeError.
            # After all, getting a KeyError from getattr doesn't make any sense.
            raise AttributeError(repr(item)) from e

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, super().__repr__())


def index_by_iterable(obj, iterable):
    """
    Index the given object iteratively with values from the given iterable.
    :param obj: the object to index.
    :param iterable: The iterable to get keys from.
    :return: The value resulting after all the indexing.
    """
    item = obj
    for i in iterable:
        item = item[i]
    return item


def nested_container_cast(obj, to, from_=list, append_func="append"):
    ancestry = [[obj, 0, to()]]
    while True:
        old_obj, idx, new_obj = ancestry[-1]
        exhausted = True
        while idx < len(old_obj):
            val = old_obj[idx]
            if isinstance(val, from_):
                ancestry[-1][1] = idx + 1
                ancestry.append([val, 0, to()])
                exhausted = False
                break
            else:
                getattr(new_obj, append_func)(val)
            idx += 1
        if exhausted:
            ancestry.pop()
            if ancestry:
                getattr(ancestry[-1][2], append_func)(new_obj)
            else:
                return new_obj


def cast(**casts):
    """
    A decorator which may be applied to a function to cast incoming arguments.
    :param casts: A dictionary in the form {<parameter_name>: <casting_function/type>}
    """
    import inspect
    import functools

    def outer(func):
        params = list(inspect.signature(func).parameters.items())
        vargs_idx = len(params)
        for idx, param in enumerate(params):
            if param[1].kind == inspect.Parameter.VAR_POSITIONAL:
                vargs_idx = idx
                break

        @functools.wraps(func)
        def inner(*args, **kwargs):
            args = list(args)
            idx = 0
            while idx < vargs_idx and idx < len(args):
                if params[idx][0] in casts:
                    args[idx] = casts[params[idx][0]](args[idx])
                idx += 1
            for kwarg in kwargs:
                if kwarg in casts:
                    kwargs[kwarg] = casts[kwarg](kwargs[kwarg])
            func(*args, **kwargs)
        return inner
    return outer
