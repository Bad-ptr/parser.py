#!/usr/bin/env python
# coding UTF-8

## Copyright 2013 Constantin Kulikov
##
## Author: Constantin Kulikov (Bad_ptr) <zxnotdead@gmail.com>
## Date: 2013/07/20 09:51:27
## License: GPL either version 2 or any later version


from collections import Iterable


class ClsShow():
    def __repr__(self):
        hide = ["_ClsShow__no_repr"]
        if hasattr(self, "_ClsShow__no_repr"):
            hide = hide + self._ClsShow__no_repr
        params = ", ".join("{!r}={!r}".format(k,v) for (k,v) in self.__dict__.items() if k not in hide)
        return self.__class__.__name__ + "(" + params + ")"

    def __str__(self):
        return "<" + self.__class__.__name__ + ">"


class PStringable():
    def as_string(self):
        return self._as_string()

    def _as_string(self):
        raise NotImplementedError("You must implement '_as_string' method"
                                  + "to use instances of " + repr(self.__class__.__name__)
                                  + " as PStringable.")


def thing_as_string(thing):
    if isinstance(thing, PStringable):
        return thing.as_string()
    elif isinstance(thing, str):
        return thing
    elif isinstance(thing, Iterable):
        #return ''.join(thing)
        ret = ""
        for th in thing:
            ret += thing_as_string(th)
        return ret
    else:
        return str(thing)


class PLengthable():
    def as_length(self):
        return self._as_length()

    def _as_length(self):
        raise NotImplementedError("You must implement '_as_length' method"
                                  + "to use instances of " + repr(self.__class__.__name__)
                                  + " as PLengthable.")


def thing_as_length(thing):
    if isinstance(thing, PLengthable):
        return thing.as_length()
    elif isinstance(thing, Iterable):
        ttl = 0
        for th in thing:
            ttl += thing_as_length(th)
        return ttl
    else:
        return 1
