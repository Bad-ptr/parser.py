#!/usr/trn/env python
# coding UTF-8

# Author: Constantin Kulikov (Bad_ptr) <zxnotdead@gmail.com>
# Date: 2013/06/24 09:42:36
# License: GPL either version 2 or any later version


from typecheck import typecheck

from common_classes import(ClsShow
                           , PStringable, thing_as_string
                           , PLengthable, thing_as_length)

from iters_readers import(BIReadable, TextReader
                          ,ReadResult , Nomatch, Fullmatch, Partialmatch)

from utils import (_or, get_from_nested_dict, merge_nested_dicts, set_to_nested_dict)

from collections import Iterable

import sys
import re



def SetRecursionLimit(n=5000):
    sys.setrecursionlimit(n)

class Grammar(ClsShow):
    def __init__(self, rules=None):
        self.name_register = {}
        self.rules = list(_or(rules,[]))
        #self._ClsShow__no_repr = ["name_register", "rules"]

    def add_rule(self, rule):
        if hasattr(rule, 'name'):
            self.name_register[rule.name] = rule
            rule.grammar = self
            self.rules.append(rule)
        return self


def gen_indentation(level=0):
    space = ""
    for i in range(level):
        space += "  "
    return space

def pprint_node_list(nlist=None, level=0, pref=None):
    if None is pref:
        pref = ""
    if None is nlist:
        nlist = []
    if isinstance(nlist, ParseNode):
        return nlist.PPrint(pref, level)
    elif isinstance(nlist, list):
        if len(nlist) < 1:
            print(pref)
            print((pref + "[]"),end="")
        else:
            space = gen_indentation(level)
            print(space + pref + "[")
            comma="  "
            for nl in nlist:
                pprint_node_list(nl, level+1, comma)
                comma=", "
            print(space + "]",end="")
    else:
        space = gen_indentation(level)
        print(space + pref + repr(nlist))


class ParseNode(ClsShow, PStringable):
    def __init__(self, name="", subnodes=None, skip=False, parent=None, Type="", priority=1, flat_eq_name=False):
        self.name = name
        self.flat_eq_name = flat_eq_name
        self.subnodes = []
        subnodes = list(_or(subnodes,[]))
        self.add_subnodes(subnodes)
        self.skip = skip
        self.parent = parent
        self.type = Type
        self.priority = priority
        self._ClsShow__no_repr = ["parent"]

    def __iter__(self):
        return iter(self.subnodes)

    def __bool__(self):
        return not self.skip

    def _as_string(self):
        return thing_as_string(self.subnodes)

    def PPrint(self, pref="", level=0):
        space = gen_indentation(level)
        print(space + pref + self.__class__.__name__ + "(" + self.name + ", ")
        pprint_node_list(nlist=self.subnodes, level=level+1, pref="")
        print(")")

    def filtered_subnodes(self):
        return filter(bool, self)

    def add_subnodes(self, subnodes):
        if not isinstance(subnodes, Iterable):
            subnodes = (subnodes,)
        for sn in subnodes:
            if isinstance(sn, ParseNode):
                if(self.flat_eq_name
                   and sn.name == self.name):
                    self.add_subnodes(sn.subnodes)
                else:
                    sn.parent = self
                    self.subnodes.append(sn)
            else:
                self.subnodes.append(sn)
        return self

    def clear(self):
        self.subnodes = []
        return self


class NotNeed(BIReadable):
    def __init__(self, thing=None):
        self.thing = thing

    def __iter__(self):
        if isinstance(self.thing, Iterable):
            return iter(self.thing)
        else:
            return iter([])

    def __bool__(self):
        return False

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


class TRef(BIReadable):
    def __init__(self, ref_name="", grammar=None, **opts):
        self.ref_name = ref_name
        self.grammar = grammar
        self.opts = {(self.ref_name + ".read_from"): opts}
        self._ClsShow__no_repr = ["grammar"]

    def unref(self, register=None):
        if None is not self.grammar:
            register = _or(register, self.grammar.name_register)
            return register.get(self.ref_name)
        return None

    def _read_from(self:object, tr:TextReader, **options) -> ReadResult:
        return tr.read_thing(self.unref(), **merge_nested_dicts(self.opts, options))


class Node(BIReadable):
    def __init__(self, name="", thing=None, skip=False, flat=False
                 , flat_eq_name=False, Type="", priority=1,
                 grammar=None, add_to_grammar=True):
        self.name = name
        self.thing = thing
        self.skip = skip
        self.flat = flat
        self.type = Type
        self.priority = priority
        self.flat_eq_name = flat_eq_name
        self.add_to_grammar = add_to_grammar
        if(None is not grammar and self.add_to_grammar):
            grammar.add_rule(self)
        self._ClsShow__no_repr = ["grammar"]

    def copy_with(self, name=None, thing=None, skip=None, flat=None
                  , flat_eq_name=None, Type=None, priority=None, grammar=None
                  , add_to_grammar=False):
        if self.name == name:
            add_to_grammar = False
        return Node(name=_or(name, self.name), thing=_or(thing, self.thing), skip=_or(skip, self.skip)
                    , flat=_or(flat, self.flat), flat_eq_name=_or(flat_eq_name, self.flat_eq_name)
                    , Type=_or(Type, self.type), priority=_or(priority, self.priority)
                    , grammar=_or(grammar, self.grammar), add_to_grammar=add_to_grammar)

    def _read_from(self:object, tr:TextReader, **options) -> ReadResult:
        rslt = tr.read_thing(self.thing, **options)
        if rslt.is_fullmatch():
            flat = _or(get_from_nested_dict(options, self.name + ".read_from", "flat")
                       , self.flat)
            skip = _or(get_from_nested_dict(options, self.name + ".read_from", "skip")
                       , self.skip)
            # set_to_nested_dict(options, None, "BIReadable.read_from", "flat")
            # set_to_nested_dict(options, None, "BIReadable.read_from", "skip")
            if not flat:
                rslt.readedlist = [ParseNode(self.name, rslt.readedlist, skip=skip, flat_eq_name=self.flat_eq_name
                                             , parent=None, Type=self.type , priority=self.priority)]
        return rslt


class Seq(BIReadable):
    def __init__(self, *thseq, seq=None):
        self.thseq = list(_or(seq, thseq))

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
