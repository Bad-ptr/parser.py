#!/usr/bin/env python
# coding UTF-8

# Author: Constantin Kulikov (Bad_ptr) <zxnotdead@gmail.com>
# Date: 2013/06/21 11:21:11
# License: GPL either version 2 or any later version


from collections import (deque, Iterable, Mapping)
from typecheck import typecheck
from itertools import islice
import re


NOMATCH = -1
FULLMATCH = 0
PARTIALMATCH = 1


def _or(smth, defv):
    if None is smth:
        return defv
    else:
        return smth

def get_from_dictstack(name="", *dict_stack, dstack=None):
    stack = _or(dstack, dict_stack)
    for d in stack:
        try:
            return d[name]
        except KeyError:
            continue
    return None

def merge_nested_dicts(a, b):
    if(isinstance(a, dict)
       and isinstance(b, dict)):
        merged = {}
        merged.update(a)
        for (k,v) in b.items():
            merged[k] = merge_nested_dicts(merged.get(k,{}), v)
        return merged
    else:
        return b

def get_from_nested_dict(di, *path):
    if path == ():
        return di
    if not isinstance(di, dict):
        return None
    return get_from_nested_dict(di.get(path[0]), *path[1:])

def set_to_nested_dict(di, value, *path):
    if path == ():
        return value
    elif not isinstance(di, dict):
        return di
    else:
        cd = di.get(path[0])
        rest = path[1:]
        if None is not cd:
            di[path[0]] = set_to_nested_dict(cd, value, rest)
        return di

def add_hook(hook_type="", hook_name="", hook=None, hook_dict=None):
    if None is not hook:
        hook_dict = _or(hook_dict, {})
        if None is hook_dict.get(hook_type):
            hook_dict[hook_type] = {}
        hook_type_dict = hook_dict[hook_type]
        oldhs = hook_type_dict.get(hook_name, [])
        if not isinstance(oldhs, list):
            oldhs = [oldh]
        oldhs.append(hook)
        hook_type_dict[hook_name] = oldhs
        return hook_dict

def run_hooks(hook_type="", hook_name="", hook_dict=None, vargs=None, kwargs=None):
    if None is not hook_dict:
        hook_type_dict = hook_dict.get(hook_type)
        if None is not hook_type_dict:
            if hook_name == "*":
                for hooks in hook_type_dict.values():
                    for hook in hooks:
                        hook(*_or(vargs,()), **_or(kwargs,{}))
            else:
                hooks = hook_type_dict.get(hook_name)
                if None is not hooks:
                    for hook in hooks:
                        hook(*_or(vargs,()), **_or(kwargs,{}))

def run_pre_hooks(hook_name="", hook_dict=None, vargs=None, kwargs=None):
    return run_hooks(hook_type="pre", hook_name=hook_name, hook_dict=hook_dict
                     , vargs=vargs, kwargs=kwargs)

def run_post_hooks(hook_name="", hook_dict=None, vargs=None, kwargs=None):
    return run_hooks(hook_type="post", hook_name=hook_name, hook_dict=hook_dict
                     , vargs=vargs, kwargs=kwargs)


class ClsShow():
    def __repr__(self):
        hide = ["_ClsShow__no_repr"]
        if hasattr(self, "_ClsShow__no_repr"):
            hide = hide + self._ClsShow__no_repr
        params = ", ".join("{!r}={!r}".format(k,v) for (k,v) in self.__dict__.items() if k not in hide)
        return self.__class__.__name__ + "(" + params + ")"

    def __str__(self):
        return "<" + self.__class__.__name__ + ">"


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
            dstack = [_or(options.get("hooks"), {}), self.hooks]
            hdict = {}
            hdict.update(self.hooks)
            hdict.update(_or(options.get("hooks"), {}))
            run_pre_hooks("read_raw_next", hdict, (self, None))
        return next(self.inp_buf_iter)

    def read_next(self, **options):
        if not bool(options.get("nohooks")):
            hdict = {}
            hdict.update(self.hooks)
            hdict.update(_or(options.get("hooks"), {}))
            run_pre_hooks("read_next", hdict, (self, None))
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
