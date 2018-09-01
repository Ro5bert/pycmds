
"""
TODO
"""


class DotDict(dict):

    def __init__(self, *args, dynamic=True, **kwargs):
        if len(args) == 1 and type(args[0]) == dict:
            d = args[0]
            for k, v in d.items():
                if type(v) == dict:
                    v = DotDict(v, dynamic=dynamic)
                    d[k] = v
        super().__init__(*args, **kwargs)
        self.__dict__["dynamic"] = dynamic

    def __getitem__(self, item):
        if self.dynamic and item not in self:
            val = DotDict()
            self.__setitem__(item, val)
            return val
        return super().__getitem__(item)

    def __setitem__(self, key, value):
        if type(value) == dict:
            value = DotDict(value, dynamic=self.dynamic)
        super().__setitem__(key, value)

    def __getattr__(self, item):
        try:
            return self.__getitem__(item)
        except KeyError as e:
            raise AttributeError(repr(item)) from e

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    def __delattr__(self, item):
        try:
            self.__delitem__(item)
        except KeyError as e:
            raise AttributeError(repr(item)) from e

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, super().__repr__())


def index_by_iterable(obj, iterable):
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
    import inspect

    def outer(func):
        params = list(inspect.signature(func).parameters.items())
        vargs_idx = len(params)
        for idx, param in enumerate(params):
            if param[1].kind == inspect.Parameter.VAR_POSITIONAL:
                vargs_idx = idx
                break

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
