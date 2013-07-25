#!/usr/bin/env python
# coding UTF-8

## Copyright 2013 Constantin Kulikov
##
## Author: Constantin Kulikov (Bad_ptr) <zxnotdead@gmail.com>
## Date: 2013/07/20 14:56:03
## License: GPL either version 2 or any later version

from typecheck import typecheck

from common_classes import (ClsShow
                            , PStringable, thing_as_string
                            , PLengthable, thing_as_length)

from iters_readers  import (BufferedIterator
                            , BIReadable, BufferedReader, TextReader
                            , ReadResult, Nomatch, Fullmatch, Partialmatch)

from utils          import (_or, get_from_nested_dict, merge_nested_dicts, set_to_nested_dict)

from collections    import (deque, Iterable)

import re


def string_to_tok_by_type(string=None, tok_types=None, mode="first" #or "longer"
                          , only_fullmatch=True):
    string = _or(string, "")
    tok_types = _or(tok_types, [])
    if mode == "first":
        tr = TextReader(string)
        for tt in tok_types:
            rslt = tr.read_thing(tt)
            if rslt.is_fullmatch():
                return rslt.readedlist[0]
            #tr.inp_buf_iter.re_iter()
        return None
    elif mode == "longer":
        ml = -1
        rt = None
        tr = TextReader(string)
        for tt in tok_types:
            rslt = tr.read_thing(tt)
            if rslt.is_fullmatch():
                tok = rslt.readedlist[0]
                tl = len(tok.string)
                if tl > ml:
                    ml = tl
                    rt = tok
                tr.inp_buf_iter.re_iter()
        return rt
    else:
        return None


class Token(BIReadable, PStringable):
    def __init__(self, string=None, Type=None):
        self.string = _or(string, "")
        self.type = _or(Type, TTYPE_EOF)

    def __eq__(self, other):
        if isinstance(other, Token):
            return self.string == other.string
        elif isinstance(other, TokenType):
            return self.type == other
        elif isinstance(other, str):
            return self.string == other
        else:
            return False
            #return self.string == thing_as_string(other)

    def PPrint(self, level=0):
        typp = ""
        if None is not self.type:
            typp = self.type.name
        print(self.__class__.__name__ + "(" + repr(self.string) + ", "
              + typp + ")")

    def _as_string(self):
        return self.string

    def _read_from(self, tr, **options) -> ReadResult:
        if isinstance(tr, TextReader):
            rslt = tr.read_string(self.string, **options)
            rslt.readed_list = [self]
            rslt.readed_object = self
            return rslt
        elif isinstance(tr, TokenReader):
            rslt = tr.read_next(**options)
            if rslt.is_fullmatch():
                readed_tok = rslt.readedlist[0]
                if self == readed_tok:
                    return rslt
                else:
                    tr.push_back(rslt.readedlist)
            return Nomatch([], self)
        else:
            return Nomatch([] ,self)


class TokenType(BIReadable):
    def __init__(self, name=None, pattern=None):
        self.name = _or(name, "")
        self.pattern = pattern

    def _read_from(self, tr, **options) -> ReadResult:
        if isinstance(tr, TextReader):
            rslt = tr.read_thing(self.pattern, **options)
            if rslt.is_fullmatch():
                string = thing_as_string(rslt.readedlist)
                rslt.readedlist = [Token(string, self)]
            rslt.readed_object = self
            return rslt
        elif isinstance(tr, TokenReader):
            rslt = tr.read_next(**options)
            if rslt.is_fullmatch():
                readed_tok = rslt.readedlist[0]
                if readed_tok == self:
                    rslt.readed_object = self
                    return rslt
                else:
                    tr.push_back(rslt.readedlist)
            return Nomatch([], self)
        else:
            return Nomatch([], self)


TTYPE_EOF  = TokenType("EOF", "")
TOK_EOF = Token("", TTYPE_EOF)


class TokenIterator(BufferedIterator):
    def __init__(self, tr:TextReader=None, token_types=None, tokens_skip=None
                 , mode="first", n_prelook=25):
        self.text_reader = tr
        if isinstance(self.text_reader, BufferedIterator):
            self.text_reader = TextReader(self.text_reader)
        self.token_types = _or(token_types, [])
        self.tokens_skip = _or(tokens_skip, [])
        self.mode = mode # "first" or "longer"
        self.n_prelook = n_prelook
        self.buffer, self.backbuffer = deque([]), deque([])
        self.at_end = False

    def __iter__(self):
        return self

    def __next__(self):
        if self.at_end:
            raise StopIteration
        ret = TOK_EOF
        try:
            ret = self.buffer.popleft()
        except IndexError:
            self.refillbuffer()
            try:
                ret = self.buffer.popleft()
            except IndexError:
                self.at_end = True
                raise StopIteration
            else:
                self.backbuffer.append(ret)
        else:
            self.backbuffer.append(ret)
        if ret == TOK_EOF:
            self.at_end = True
        if ret in self.tokens_skip:
            ret = next(self)
        return ret

    def re_iter(self):
        self.text_reader.inp_buf_iter.re_iter()
        return self

    def refillbuffer(self):
        for n in range(self.n_prelook):
            if self.mode == "first":
                for tt in self.token_types:
                    rslt = self.text_reader.read_thing(tt)
                    if rslt.is_fullmatch():
                        self.push_forward(rslt.readedlist[0])
                        break
            elif self.mode == "longer":
                ml = -1
                rt = None
                for tt in self.token_types:
                    rslt = self.text_reader.read_thing(tt)
                    if rslt.is_fullmatch():
                        tok = rslt.readedlist[0]
                        tl = len(tok.string)
                        if tl > ml:
                            ml = tl
                            rt = tok
                        self.text_reader.push_back(rslt.readedlist)
                if None is not rt:
                    rslt = self.text_reader.read_thing(rt)
                    if rslt.is_fullmatch():
                        self.push_forward(rslt.readedlist[0])
            else:
                break
        return self

    def push_forward(self, el=None):
        if el is not None:
            if isinstance(el, str):
                tok = string_to_tok_by_type(el, self.token_types)
                if None is tok:
                    tok = Token(el)
                self.push_forward(tok)
            elif isinstance(el, Iterable):
                for e in el:
                    self.push_forward(e)
            else:
                self.at_end = False
                self.buffer.append(el)
        return self

    def push_back(self, el=None):
        if el is not None:
            if isinstance(el, str):
                tok = string_to_tok_by_type(el, self.token_types)
                if None is tok:
                    tok = Token(el)
                self.push_back(tok)
            elif isinstance(el, Iterable):
                seq = reversed(list(el))
                for e in seq:
                    self.push_back(e)
            else:
                self.at_end = False
                be = self.backbuffer.pop()
                if el != be:
                    self.backbuffer.append(be)
                self.buffer.appendleft(el)
        return self


class TokenReader(BufferedReader):
    def __init__(self, inp_buf_iter : TokenIterator=None, hooks=None):
        super().__init__(inp_buf_iter, hooks)
        if(isinstance(self.inp_buf_iter, Iterable)
           and not isinstance(self.inp_buf_iter, TokenIterator)):
            self.inp_buf_iter = TextReader(self.inp_buf_iter)
        if isinstance(self.inp_buf_iter, TextReader):
            self.inp_buf_iter = TokenIterator(self.inp_buf_iter)

    def read_thing(self, thing, **options):
        if isinstance(thing, (TokenType, Token, str)):
            rslt = self.read_next(**options)
            if rslt.is_fullmatch():
                tok = rslt.readedlist[0]
                if tok == thing:
                    return Fullmatch([tok], thing)
                else:
                    self.push_back(rslt.readedlist)
            return Nomatch([], thing)
        elif isinstance(thing, BIReadable):
            return thing.read_from(self, **options)
        elif isinstance(thing, Iterable):
            return self.read_thing_seq(thing, **options)
        else:
            return Nomatch([], thing)
            #return self.read_thing(thing_as_string(thing), **options)
