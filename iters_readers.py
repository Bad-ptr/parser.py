#!/usr/bin/env python
# coding UTF-8

## Copyright 2013 Constantin Kulikov
##
## Author: Constantin Kulikov (Bad_ptr) <zxnotdead@gmail.com>
## Date: 2013/07/20 09:48:24
## License: GPL either version 2 or any later version


from typecheck import typecheck

from common_classes import (ClsShow
                            , PStringable, thing_as_string
                            , PLengthable, thing_as_length)

from utils import (_or, merge_nested_dicts, get_from_nested_dict, set_to_nested_dict
                   , add_hook, run_pre_hooks)

from collections import (deque, Iterable)
from itertools import islice

import re


NOMATCH = -1
FULLMATCH = 0
PARTIALMATCH = 1


class ReadResult(ClsShow):
    def __init__(self, state=NOMATCH, readedlist=None, readed_object=None):
        self.state = state
        self.readedlist = _or(readedlist, [])
        if not isinstance(self.readedlist, list):
            self.readedlist = [self.readedlist]
        self.readed_object = readed_object

    def __iter__(self):
        return iter(self.readedlist)

    def __bool__(self):
        return self.state == FULLMATCH

    def is_fullmatch(self):
        return bool(self)

    def is_partialmatch(self):
        return self.state == PARTIALMATCH

    def is_nomatch(self):
        return self.state == NOMATCH


def Nomatch(readedlist=None, readed_object=None):
    return ReadResult(NOMATCH, readedlist, readed_object)
def Fullmatch(readedlist=None, readed_object=None):
    return ReadResult(FULLMATCH, readedlist, readed_object)
def Partialmatch(readedlist=None, readed_object=None):
    return ReadResult(PARTIALMATCH, readedlist, readed_object)


class BufferedIterator(ClsShow):
    def __init__(self, input_iterable=None, n_prelook=25):
        self.input_iterable = _or(input_iterable, ())
        self.n_prelook = n_prelook
        self.buffer = deque([])
        self.at_end = False
        self.re_iter()

    def __iter__(self):
        return self

    def __next__(self):
        ret = None
        try:
            ret = self.buffer.popleft()
        except IndexError:
            self.refillbuffer()
            try:
                ret = self.buffer.popleft()
            except IndexError:
                self.at_end = True
                raise StopIteration
        return ret

    def re_iter(self):
        self.input_iterator = iter(self.input_iterable)
        return self

    def refillbuffer(self):
        for (el, n) in zip(self.input_iterator
                           , range(self.n_prelook)):
            self.push_forward(el)
        return self

    def push_forward(self, el=None):
        if el is not None:
            self.at_end = False
            self.buffer.append(el)
        return self

    def push_back(self, el=None):
        if el is not None:
            self.at_end = False
            self.buffer.appendleft(el)
        return self


class BufferedReader(ClsShow):
    def __init__(self, inp_buf_iter=None, hooks=None):
        self.inp_buf_iter = _or(inp_buf_iter, BufferedIterator(tuple()))
        self.hooks = _or(hooks, {})

    def push_back(self, thms=None):
        self.inp_buf_iter.push_back(thms)
        return self

    def slice(self, n=1):
        return islice(self.inp_buf_iter, n)

    def read_raw_next(self, **options):
        if not bool(options.get("nohooks")):
            run_pre_hooks("read_raw_next"
                          , merge_nested_dicts(self.hooks, _or(options.get("hooks"), {}))
                          , (self, None))
        return next(self.inp_buf_iter)

    def read_next(self, **options):
        if not bool(options.get("nohooks")):
            run_pre_hooks("read_next"
                          , merge_nested_dicts(self.hooks, _or(options.get("hooks"), {}))
                          , (self, None))
        state = FULLMATCH
        el = None
        try:
            el = self.read_raw_next(**options)
        except StopIteration:
            state = NOMATCH
        return ReadResult(state, el, el)

    def read_el(self, el, **options):
        cel = self.read_next(**options)
        if FULLMATCH == cel.state:
           if el != cel.readedlist[0]:
               self.push_back(cel.readedlist)
               return Nomatch(cel.readedlist, el)
           else:
               return Fullmatch(cel.readedlist, el)
        else:
            return Nomatch([], el)

    def can_read_el(self, el):
        reslt = self.read_el(el, dry_run=True)
        if reslt.state == FULLMATCH:
            self.push_back(reslt.readedlist)
        return reslt

    def read_thing(self, thing, **options):
        if isinstance(thing, BIReadable):
            return thing.read_from(self, **options)
        elif (isinstance(thing, Iterable)
              and ((not isinstance(thing, str)) or len(thing) > 1)):
            return self.read_thing_seq(thing, **options)
        else:
            return self.read_el(thing, **options)

    def can_read_thing(self, thing):
        reslt = self.read_thing(thing, dry_run=True)
        if reslt.state == FULLMATCH:
            self.push_back(reslt.readedlist)
        return reslt

    def read_thing_seq(self, thseq, **options):
        if((not isinstance(thseq, Iterable))
           or (isinstance(thseq, str) and len(thseq) < 2)):
            thseq = (thseq,)
        acc = []
        state = FULLMATCH
        for th in thseq:
            reslt = self.read_thing(th, **options)
            if FULLMATCH == reslt.state:
                acc.extend(reslt.readedlist)
            else:
                #self.push_back(reslt.readedlist)
                self.push_back(acc)
                state = reslt.state
                break
        return ReadResult(state, acc, thseq)

    def can_read_thing_seq(self, thseq):
        reslt = self.read_thing_seq(thseq, dry_run=True)
        if reslt.state == FULLMATCH:
            self.push_back(reslt.readedlist)
        return reslt


class CharIterator(BufferedIterator):
    def push_forward(self, el=None):
        if el is not None:
            el = thing_as_string(el)
            if len(el) > 0:
                if len(el) < 2:
                    super().push_forward(el)
                else:
                    for e in el:
                        super().push_forward(e)
        return self

    def push_back(self, el=None):
        if el is not None:
            el = thing_as_string(el)
            if len(el) > 0:
                if len(el) < 2:
                    super().push_back(el)
                else:
                    seq = reversed(list(el))
                    for e in seq:
                        super().push_back(e)
        return self

    def __next__(self):
        return thing_as_string(super().__next__())


class TextReader(BufferedReader):
    def __init__(self, chiter=None, hooks=None, skip_pattern=None):
        hooks = _or(hooks, {})
        self.skip_pattern = _or(skip_pattern, [])
        add_hook("pre", "read_el"
                 , lambda br, el: br.read_thing(self.skip_pattern, nohooks=True)
                 , hooks)
        add_hook("pre", "read_next"
                 , lambda br, el: br.read_thing(self.skip_pattern, nohooks=True)
                 , hooks)
        super().__init__(chiter, hooks)
        if not isinstance(self.inp_buf_iter, CharIterator):
            self.inp_buf_iter = CharIterator(self.inp_buf_iter)

    def read_next_char(self, **options):
        return self.read_next(**options)

    def read_ch(self, ch, **options):
        return self.read_el(ch, **options)

    def can_read_ch(self, ch):
        return self.can_read_el(ch)

    def read_string(self, string, **options):
        acc = []
        state = FULLMATCH
        for ch in string:
            rslt = self.read_ch(ch, **options)
            if FULLMATCH == rslt.state:
                acc.extend(rslt.readedlist)
            else:
                state = rslt.state
                self.push_back(acc)
                break
        return ReadResult(state, [''.join(acc)], string)

    def can_read_string(self, string):
        rslt = self.read_string(string, dry_run=True)
        if rslt.state == FULLMATCH:
            self.push_back(rslt.readedlist)
        return rslt

    def read_chars_by_regexp(self, regexp, **options):
        acc = ""
        state = NOMATCH
        while True:
            rslt = read_next_char(**options)
            if rslt.state == FULLMATCH:
                if None is not re.match(regexp, rslt.readedlist[0]):
                    state = FULLMATCH
                    acc += rslt.readedlist[0]
                else:
                    self.push_back(rslt.readedlist)
            else:
                break
        return ReadResult(state, acc, regexp)

    def read_string_by_regexp(self, regexp, **options):
        acc = ""
        state = NOMATCH
        while True:
            rslt = read_next_char(**options)
            if rslt.state == FULLMATCH:
                if None is not re.match(regexp, acc + rslt.readedlist[0]):
                    state = FULLMATCH
                    acc += rslt.readedlist[0]
                else:
                    self.push_back(rslt.readedlist)
            else:
                break
        return ReadResult(state, [''.join(acc)], regexp)

    def read_thing(self, thing, **options):
        if isinstance(thing, BIReadable):
            return thing.read_from(self, **options)
        elif isinstance(thing, str):
            return self.read_string(thing, **options)
        elif isinstance(thing, Iterable):
            return self.read_thing_seq(thing, **options)
        else:
            return self.read_el(thing, **options)




class BIReadable(ClsShow):
    @typecheck(allow_unknown_keywords=True)
    def can_read_from(self:object, br:BufferedReader) -> ReadResult:
        return self._can_read_from(br)

    @typecheck(allow_unknown_keywords=True)
    def read_from(self:object, br:BufferedReader, **options) -> ReadResult:
        return self._read_from(br, **options)

    def _read_from(self, br, **options):
        raise NotImplementedError("You must implement '_read_from' method"
                                  + "to use instances of " + repr(self.__class__.__name__)
                                  + " as BIReadable.")

    @typecheck()
    def _can_read_from(self:object, br:BufferedReader) -> ReadResult:
        reslt = self.read_from(br, dry_run=True)
        if reslt.state == FULLMATCH:
            br.push_back(reslt.readedlist)
        return reslt
