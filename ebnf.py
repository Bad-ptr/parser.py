#!/usr/bin/env python
# coding UTF-8

## Copyright 2013 Constantin Kulikov
##
## Author: Constantin Kulikov (Bad_ptr) <zxnotdead@gmail.com>
## Date: 2013/07/19 06:44:38
## License: public domain

"""
This is translated and slightly modified version of EBNF grammar
  from https://en.wikipedia.org/wiki/Ebnf#Examples
"""

from utils           import SetRecursionLimit
from iters_readers   import TextReader
from parser          import (Grammar, Node, TRef, pprint_node_list)
from readable_things import (Literal, NotNeed, Seq, Num
                             , ZeroOrOne, ZeroOrMore, OneOrMore
                             , Look, Rx, Concat, Or, Not)


cur_grammar = Grammar()


letter = Rx('[a-zA-Z]')
digit = Rx('[0-9]')
symbol = Or("[", "]", "(", ")", "{", "}", "<", ">", "'", "'", "=", "|", ".", ",", ";")
character = Or(letter, digit, symbol)

identifier = Node("identifier", Concat(letter, ZeroOrMore(Or(letter, digit,))), grammar=cur_grammar)
terminal = Node("terminal" , Concat(Or(Seq(NotNeed("'"), ZeroOrMore(Not("'")), NotNeed("'"))
                                       , Seq(NotNeed('"'), ZeroOrMore(Not('"')), NotNeed('"'))))
                , grammar=cur_grammar)

ident_or_term = Or(identifier, terminal)

lhs = Node("lhs", identifier, grammar=cur_grammar)

option = Node("option"
              , Seq(NotNeed("["), TRef("rhs",grammar=cur_grammar, flat=True), NotNeed("]"))
              , grammar=cur_grammar)
repetition = Node("repetition"
                  , Seq(NotNeed("{"), TRef("rhs",grammar=cur_grammar, flat=True), NotNeed("}"))
                  , grammar=cur_grammar)
grouping = Node("group"
                , Seq(NotNeed("("), TRef("rhs",grammar=cur_grammar, flat=True), NotNeed(")"))
                , grammar=cur_grammar)

negation = Node("negation"
                , Seq(NotNeed("^"), TRef("rhs",grammar=cur_grammar, flat=True), NotNeed("^"))
                , grammar=cur_grammar)

regexp = Node("regexp"
              , Seq(NotNeed("rx"), TRef("terminal",grammar=cur_grammar))
              , grammar=cur_grammar)

groups = Or(option, repetition, grouping, negation, regexp)

ident_or_term_or_groups = Or(ident_or_term, groups)

concatenation = Node("concatenation"
                     , Seq(ident_or_term_or_groups, NotNeed(","), TRef("rhs", grammar=cur_grammar, flat=True))
                     , flat_eq_name=True, grammar=cur_grammar)

alteration = Node("alteration"
                  , Seq(ident_or_term_or_groups, NotNeed("|"), TRef("rhs", grammar=cur_grammar, flat=True))
                  , flat_eq_name=True, grammar=cur_grammar)

rhs = Node("rhs", Or( concatenation
                    , alteration
                    , groups
                    , ident_or_term)
           , grammar=cur_grammar)

rule = Node("rule", Seq(lhs, NotNeed("="), rhs, NotNeed(";")), grammar=cur_grammar)
grammar = Node("ebnf_grammar", ZeroOrMore(rule), grammar=cur_grammar)


if __name__ == '__main__':
    space = Node("space", Concat(OneOrMore(Or(" ", "\t", "\n"))), skip=True)
    comment = Node("comment", Seq("(", "*"
                                  , Node("text", Concat(ZeroOrMore(Not(Seq("*", ")")))))
                                  , "*", ")")
                   , skip=True)
    skip_pattern = OneOrMore(Or(space, comment))

    tr = TextReader(open("ebnf_test.txt"), skip_pattern=skip_pattern)

    SetRecursionLimit(5000)

    rslt = grammar.read_from(tr)
    pprint_node_list(rslt.readedlist)
