#!/usr/trn/env python
# coding UTF-8

# Copyright 2013 Constantin Kulikov
#
# Author: Constantin Kulikov (Bad_ptr) <zxnotdead@gmail.com>
# Date: 2013/06/24 09:42:36
# License: GPL either version 2 or any later version


from typecheck      import typecheck

from common_classes import (ClsShow, gen_indentation, thing_pprint
                            , PStringable, thing_as_string
                            , PLengthable, thing_as_length)

from iters_readers  import (BIReadable, TextReader
                            , ReadResult , Nomatch, Fullmatch, Partialmatch)

from utils          import (_or, get_from_nested_dict, merge_nested_dicts, set_to_nested_dict)

from collections    import Iterable

import re


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



# def pprint_node_list(nlist=None, level=0, pref=None):
#     if None is pref:
#         pref = ""
#     if None is nlist:
#         nlist = []
#     if isinstance(nlist, ParseNode):
#         return nlist.PPrint(level, pref)
#     if isinstance(nlist, ClsShow):
#         space = gen_indentation(level)
#         print(space + pref, end="")
#         nlist.PPrint(level+1)
#     elif isinstance(nlist, list):
#         if len(nlist) < 1:
#             print(pref)
#             print((pref + "[]"),end="")
#         else:
#             space = gen_indentation(level)
#             print(space + pref + "[")
#             comma="  "
#             for nl in nlist:
#                 pprint_node_list(nl, level+1, comma)
#                 comma=", "
#             print(space + "]",end="")
#     else:
#         space = gen_indentation(level)
#         print(space + pref + repr(nlist))


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

    def PPrint(self, level=0, pref="", post="", end="\n", first_indent=True):
        space = gen_indentation(level)
        if first_indent:
            print(space, end="")
        print(pref + self.__class__.__name__ + "(" + repr(self.name))
        thing_pprint(self.subnodes, level+1, ", ", end="")
        #pprint_node_list(nlist=self.subnodes, level=level+1, pref="")
        print(")" + post, end=end)

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
