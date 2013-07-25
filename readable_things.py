#!/usr/bin/env python
# coding UTF-8

## Copyright 2013 Constantin Kulikov
##
## Author: Constantin Kulikov (Bad_ptr) <zxnotdead@gmail.com>
## Date: 2013/07/20 17:07:20
## License: GPL either version 2 or any later version


from common_classes import (ClsShow
                            , PStringable, thing_as_string
                            , PLengthable, thing_as_length)

from iters_readers  import (BIReadable, TextReader
                            ,ReadResult , Nomatch, Fullmatch, Partialmatch)

from utils          import (_or, get_from_nested_dict, merge_nested_dicts, set_to_nested_dict)

from collections    import Iterable

import sys
import re


class NotNeed(PStringable, BIReadable):
    def __init__(self, thing=None):
        self.thing = thing

    def __iter__(self):
        if isinstance(self.thing, Iterable):
            return iter(self.thing)
        else:
            return iter([])

    def __bool__(self):
        return False

    def PPrint(self, level=0):
        print(self.__class__.__name__ + "(", end="")
        if isinstance(self.thing, ClsShow):
            self.thing.PPrint(level)
        else:
            print(str(self.thing), end="")
        print(")")

    def _as_string(self):
        return thing_as_string(self.thing)

    def _read_from(self, tr, **options):
        rslt = tr.read_thing(self.thing, **options)
        if rslt.is_fullmatch():
            rslt.readedlist = [NotNeed(rslt.readedlist)]
        return rslt


class Literal(BIReadable):
    def __init__(self, string=""):
        self.string = string

    def _read_from(self:object, tr:TextReader, **options) -> ReadResult:
        return tr.read_thing(self.string, **options)


class Seq(BIReadable):
    def __init__(self, *thseq, seq=None):
        self.thseq = _or(seq, thseq)

    def _read_from(self:object, tr:TextReader, **options) -> ReadResult:
        rslt = Fullmatch([], self)
        acc = []
        for th in self.thseq:
            rslt = tr.read_thing(th, **options)
            if rslt.is_fullmatch():
                acc.extend(rslt.readedlist)
            else:
                tr.push_back(acc)
                break
        #print(repr(rslt))
        if rslt.is_fullmatch():
            return Fullmatch(acc, self)
        else:
            return ReadResult(rslt.state, acc, self)


class Num(BIReadable):
    def __init__(self, thing=None, min_num=1, max_num=-1):
        self.thing = thing
        self.min_num = min_num
        self.max_num = max_num

    def _read_from(self:object, tr:TextReader, **options) -> ReadResult:
        rslt = Fullmatch([],self)
        acc = []
        n = 0
        while True:
            if self.max_num >= 0 and n >= self.max_num:
                break
            rslt = tr.read_thing(self.thing, **options)
            if rslt.is_fullmatch():
                acc.extend(rslt.readedlist)
            else:
                break
            n += 1
        if not rslt.is_fullmatch():
            if n >= self.min_num:
                return Fullmatch(acc, self)
            else:
                tr.push_back(acc)
                return ReadResult(rslt.state, acc, self)
        else:
            return Fullmatch(acc, self)

def ZeroOrOne(thing=None):
    return Num(thing, min_num=0, max_num=1)

def ZeroOrMore(thing=None):
    return Num(thing, min_num=0, max_num=-1)

def OneOrMore(thing=None):
    return Num(thing, min_num=1, max_num=-1)


class Look(BIReadable):
    def __init__(self, thing=None):
        self.thing = thing

    def _read_from(self:object, tr:TextReader, **options) -> ReadResult:
        rslt = tr.read_thing(self.thing, **options)
        if rslt.is_fullmatch():
            tr.push_back(rslt.readedlist)
        rslt.readedlist = []
        rslt.readed_object = self
        return rslt


class Rx(BIReadable):
    def __init__(self, regexp=r'', mode='char', min_chars=1, max_chars=1):
        self.regexp = regexp
        self.mode = mode
        self.min_chars = min_chars
        self.max_chars = max_chars

    #@typecheck(allow_unknown_keywords=True)
    def _read_from(self:object, tr:TextReader, **options) -> ReadResult:
        n_chars = 0
        acc = ""
        if 'char' == self.mode:
            while True:
                if self.max_chars >= 0 and n_chars >= self.max_chars:
                    break
                ch = tr.read_next(**options)
                if not ch.is_fullmatch():
                    break
                if None is not re.match(self.regexp, thing_as_string(ch.readedlist)):
                    acc += thing_as_string(ch.readedlist)
                else:
                    tr.push_back(ch.readedlist)
                    break
                n_chars += 1
        elif 'string' == self.mode:
            acc = ""
            while True:
                if self.max_chars >= 0 and n_chars >= self.max_chars:
                    break
                ch = tr.read_next(**options)
                if not ch.is_fullmatch():
                    break
                if None is re.match(self.regexp, acc + thing_as_string(ch.readedlist)):
                    tr.push_back(ch.readedlist)
                    break
                else:
                   acc += thing_as_string(ch.readedlist)
                n_chars += 1
        else:
            return Nomatch([], self)

        if n_chars >= self.min_chars:
            return Fullmatch(thing_as_string(acc), self)
        else:
            tr.push_back(acc)
            return Nomatch(thing_as_string(acc), self)


class Concat(BIReadable):
    def __init__(self, *thseq):
        self.thseq = thseq

    #@typecheck(allow_unknown_keywords=True)
    def _read_from(self:object, tr:TextReader, **options) -> ReadResult:
        acc = ""
        for th in self.thseq:
            rslt = tr.read_thing(th, **options)
            if rslt.is_fullmatch():
                acc += thing_as_string(rslt.readedlist)
            else:
                tr.push_back(acc)
                return ReadResult(rslt.state, acc, self)
                break
        return Fullmatch(acc, self)


class Or(BIReadable):
    def __init__(self, *thseq, mode=None):
        self.thseq = thseq
        self.mode = _or(mode, "first")

    def _read_from(self:object, tr:TextReader, **options) -> ReadResult:
        if self.mode == "first":

            for th in self.thseq:
                rslt = tr.read_thing(th, **options)
                if rslt.is_fullmatch():
                    return rslt
            return Nomatch([], self)

        elif self.mode == "longer":
            maxl = -1
            mid = -1
            i = 0
            for th in self.thseq:
                rslt = tr.read_thing(th, **options)
                if rslt.is_fullmatch():
                    l = len(thing_as_string(rslt.readedlist))
                    if l > maxl:
                        maxl = l
                        mid = i
                    tr.push_back(rslt.readedlist)
                i += 1

            if mid < 0:
                return Nomatch([], self)
            else:
                rslt = tr.read_thing(self.thseq[mid])
                return rslt


class Not(BIReadable):
    def __init__(self, *thseq, escape_char="\\", allow_escaped=True):
        self.thseq = thseq
        self.escape_char = escape_char
        self.allow_escaped = allow_escaped

    def _read_from(self:object, tr:TextReader, **options) -> ReadResult:
        escaped = False
        while True:
            for th in self.thseq:
                rslt = tr.read_thing(th, **options)
                if rslt.is_fullmatch():
                    tr.push_back(rslt.readedlist)
                    if not escaped:
                        return Nomatch()
            rslt = tr.read_next_char(**options)
            if escaped:
                escaped = False
                return rslt
            else:
                if self.escape_char == rslt.readedlist[0]:
                    escaped = True
                    continue
                else:
                    return rslt
            #rslt.readed_object = self
