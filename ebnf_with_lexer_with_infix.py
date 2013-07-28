#!/usr/bin/env python
# coding UTF-8

## Copyright 2013 Constantin Kulikov
##
## Author: Constantin Kulikov (Bad_ptr) <zxnotdead@gmail.com>
## Date: 2013/07/23 11:37:31
## License: GPL either version 2 or any later version


from common_classes  import thing_pprint

from lexer_test      import (tt_identifier, tt_number, tt_operator, tt_terminator
                             , tt_space, tt_comment, tt_literal, tt_list, tt_skip_list
                             , tok_openbr, tok_closebr, tok_opencurlybr, tok_closecurlbr
                             , tok_opensqbr, tok_closesqbr, tok_squote, tok_dquote
                             , tok_comma, tok_period, tok_colon, tok_semicolon
                             , tok_accent

                             , token_iterator, token_reader)

from parser          import (Grammar, Node, TRef)

from lexer           import (TokenIterator, TokenReader)

from iters_readers   import TextReader

from readable_things import (Literal, NotNeed, Seq, Num
                             , ZeroOrOne, ZeroOrMore, OneOrMore
                             , Look, Rx, Concat, Or, Not)

from x_operators import (OR, THEN, CONCAT)

from utils import SetRecursionLimit


cur_grammar = Grammar()

pn_identifier = Node("pn_identifier", OneOrMore(tt_identifier), grammar=cur_grammar)
pn_terminal = Node("terminal", OneOrMore(tt_literal), grammar=cur_grammar)
pn_ident_or_term = (pn_identifier
                    |OR| pn_terminal)

pn_lhs = Node("pn_lhs", pn_identifier, grammar=cur_grammar)

pn_option = Node("pn_option"
                 , (NotNeed(tok_opensqbr)
                    <<THEN>> TRef("pn_rhs", grammar=cur_grammar, flat=True)
                    <<THEN>> NotNeed(tok_closesqbr))
                 , grammar=cur_grammar)
pn_repetition = Node("pn_repetition"
                     , (NotNeed(tok_opencurlybr)
                        <<THEN>> TRef("pn_rhs", grammar=cur_grammar, flat=True)
                        <<THEN>> NotNeed(tok_closecurlbr))
                     , grammar=cur_grammar)
pn_grouping = Node("group"
                   , (NotNeed(tok_openbr)
                      <<THEN>> TRef("pn_rhs", grammar=cur_grammar, flat=True)
                      <<THEN>> NotNeed(tok_closebr))
                   , grammar=cur_grammar)
pn_negation = Node("pn_negation"
                   , (NotNeed("^")
                      <<THEN>> TRef("pn_rhs", grammar=cur_grammar, flat=True)
                      <<THEN>> NotNeed("^"))
                   , grammar=cur_grammar)
pn_regexp = Node("pn_regexp"
                 , (NotNeed("rx")
                    <<THEN>> tt_literal)
                 , grammar=cur_grammar)

pn_groups = (pn_option
             |OR| pn_repetition
             |OR| pn_grouping
             |OR| pn_negation
             |OR| pn_regexp)

pn_ident_or_term_or_pn_groups = pn_ident_or_term |OR| pn_groups

pn_concatenation = Node("pn_concatenation"
                        , (pn_ident_or_term_or_pn_groups
                           <<THEN>> NotNeed(",")
                           <<THEN>> TRef("pn_rhs", grammar=cur_grammar, flat=True))
                        , flat_eq_name=True, grammar=cur_grammar)

pn_alteration = Node("pn_alteration"
                     , (pn_ident_or_term_or_pn_groups
                        <<THEN>> NotNeed("|")
                        <<THEN>> TRef("pn_rhs", grammar=cur_grammar, flat=True))
                     , flat_eq_name=True, grammar=cur_grammar)

pn_rhs = Node("pn_rhs", pn_concatenation
              |OR| pn_alteration
              |OR| pn_groups
              |OR| pn_ident_or_term
              , grammar=cur_grammar)

pn_rule = Node("pn_rule", (pn_lhs
                           <<THEN>> NotNeed("=")
                           <<THEN>> pn_rhs
                           <<THEN>> NotNeed(";")), grammar=cur_grammar)
pn_grammar = Node("ebnf_grammar", ZeroOrMore(pn_rule), grammar=cur_grammar)


if __name__ == '__main__':
    rslt = pn_grammar.read_from(token_reader)
    thing_pprint(rslt.readedlist)
