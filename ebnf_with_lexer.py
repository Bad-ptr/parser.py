#!/usr/bin/env python
# coding UTF-8

## Copyright 2013 Constantin Kulikov
##
## Author: Constantin Kulikov (Bad_ptr) <zxnotdead@gmail.com>
## Date: 2013/07/23 11:37:31
## License: GPL either version 2 or any later version


from lexer_test      import (tt_identifier, tt_number, tt_operator, tt_terminator
                             , tt_space, tt_comment, tt_literal, tt_list, tt_skip_list
                             , tok_openbr, tok_closebr, tok_opencurlybr, tok_closecurlbr
                             , tok_opensqbr, tok_closesqbr, tok_squote, tok_dquote
                             , tok_comma, tok_period, tok_colon, tok_semicolon
                             , tok_accent

                             , token_iterator, token_reader)

from parser          import (Grammar, Node, TRef, pprint_node_list)

from lexer           import (TokenIterator, TokenReader)

from iters_readers   import TextReader

from readable_things import (Literal, NotNeed, Seq, Num
                             , ZeroOrOne, ZeroOrMore, OneOrMore
                             , Look, Rx, Concat, Or, Not)

from utils import SetRecursionLimit


cur_grammar = Grammar()

pn_identifier = Node("pn_identifier", OneOrMore(tt_identifier), grammar=cur_grammar)
pn_terminal = Node("terminal", OneOrMore(tt_literal), grammar=cur_grammar)
pn_ident_or_term = Or(pn_identifier, pn_terminal)

pn_lhs = Node("pn_lhs", pn_identifier, grammar=cur_grammar)

pn_option = Node("pn_option"
                 , Seq(NotNeed(tok_opensqbr), TRef("pn_rhs", grammar=cur_grammar, flat=True), NotNeed(tok_closesqbr))
                 , grammar=cur_grammar)
pn_repetition = Node("pn_repetition"
                     , Seq(NotNeed(tok_opencurlybr), TRef("pn_rhs", grammar=cur_grammar, flat=True), NotNeed(tok_closecurlbr))
                     , grammar=cur_grammar)
pn_grouping = Node("group"
                   , Seq(NotNeed(tok_openbr), TRef("pn_rhs", grammar=cur_grammar, flat=True), NotNeed(tok_closebr))
                   , grammar=cur_grammar)
pn_negation = Node("pn_negation"
                   , Seq(NotNeed("^"), TRef("pn_rhs", grammar=cur_grammar, flat=True), NotNeed("^"))
                   , grammar=cur_grammar)
pn_regexp = Node("pn_regexp"
                 , Seq(NotNeed("rx"), tt_literal)
                 , grammar=cur_grammar)

pn_groups = Or(pn_option, pn_repetition, pn_grouping, pn_negation, pn_regexp)

pn_ident_or_term_or_pn_groups = Or(pn_ident_or_term, pn_groups)

pn_concatenation = Node("pn_concatenation"
                        , Seq(pn_ident_or_term_or_pn_groups, NotNeed(","), TRef("pn_rhs", grammar=cur_grammar, flat=True))
                        , flat_eq_name=True, grammar=cur_grammar)

pn_alteration = Node("pn_alteration"
                     , Seq(pn_ident_or_term_or_pn_groups, NotNeed("|"), TRef("pn_rhs", grammar=cur_grammar, flat=True))
                     , flat_eq_name=True, grammar=cur_grammar)

pn_rhs = Node("pn_rhs", Or(pn_concatenation
                           , pn_alteration
                           , pn_groups
                           , pn_ident_or_term)
              , grammar=cur_grammar)

pn_rule = Node("pn_rule", Seq(pn_lhs, NotNeed("="), pn_rhs, NotNeed(";")), grammar=cur_grammar)
pn_grammar = Node("ebnf_grammar", ZeroOrMore(pn_rule), grammar=cur_grammar)


#token_iterator = TokenIterator(TextReader(open("test1.txt"))
#                               , tt_list, tt_skip_list)
#token_reader = TokenReader(token_iterator)
#token_reader = TokenReader(TokenIterator(TextReader(open("test1.txt")), tt_list, tt_skip_list))


if __name__ == '__main__':
    #SetRecursionLimit(5000)
    # lexer reducing recursion level
    rslt = pn_grammar.read_from(token_reader)
    pprint_node_list(rslt.readedlist)
