#!/usr/bin/env python
# coding UTF-8

## Copyright 2013 Constantin Kulikov
##
## Author: Constantin Kulikov (Bad_ptr) <zxnotdead@gmail.com>
## Date: 2013/07/27 11:11:58
## License: public domain



from readable_things import (Literal, NotNeed, Seq, Num
                             , ZeroOrOne, ZeroOrMore, OneOrMore
                             , Look, Rx, Concat, Or, Not)

from infix           import Infix


OR = Infix(lambda x,y: Or(x,y))
THEN = Infix(lambda x,y: Seq(x,y))
CONCAT = Infix(lambda x,y: Concat(x,y))


class Prefix:
    def __init__(self, function):
        self.function = function
    def __or__(self, other):
        return self.function(other)
    def __lshift__(self, other):
        return self.function(other)
    def __rshift__(self, other):
        return self.function(other)
    def __call__(self, other):
        return self.function(other)
