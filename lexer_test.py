#!/usr/bin/env python
# coding UTF-8

## Copyright 2013 Constantin Kulikov
##
## Author: Constantin Kulikov (Bad_ptr) <zxnotdead@gmail.com>
## Date: 2013/07/22 17:33:14
## License: GPL either version 2 or any later version


from lexer           import (Token, TokenType, TokenIterator, TokenReader
                             , string_to_tok_by_type)

from iters_readers   import TextReader

from readable_things import (Literal, NotNeed, Seq, Num
                             , ZeroOrOne, ZeroOrMore, OneOrMore
                             , Look, Rx, Concat, Or, Not)


letter    = Rx('[a-zA-Z]')
digit     = Rx('[0-9]')

tt_identifier = TokenType("identifier"
                          , Concat(letter, ZeroOrMore(Or(letter, digit,))))
tt_number     = TokenType("number"
                          , Concat(OneOrMore(digit), ZeroOrOne(Seq(NotNeed("."), ZeroOrMore(digit)))))
tt_operator   = TokenType("operator"
                          , Rx('[-+@#$!~%/*=|^&\\\\]', max_chars=2))
tt_terminator = TokenType("terminator"
                          , Rx('[{}\[\]()<>,.;`\'":]'))
tt_space      = TokenType("space"
                          , Rx('[ \n\t]', max_chars=-1))
#tt_eof        = TokenType("EOF", "")

tt_comment = TokenType("comment"
                       , Seq("(", "*"
                             , ZeroOrMore(Not(Seq("*", ")")))
                             , "*", ")"))

tt_literal = TokenType("literal"
                       , Or(Seq("'", ZeroOrMore(Not("'")), "'")
                            , Seq('"', ZeroOrMore(Not('"')), '"')))

tt_list = ( tt_identifier, tt_number, tt_comment, tt_literal, tt_operator, tt_terminator, tt_space) #, tt_eof )
tt_skip_list = (tt_comment, tt_space)


tok_openbr  = string_to_tok_by_type("(", tt_list)
tok_closebr = string_to_tok_by_type(")", tt_list)

tok_opencurlybr = string_to_tok_by_type("{", tt_list)
tok_closecurlbr = Token("}", tt_terminator)

tok_opensqbr  = Token("[", tt_terminator)
tok_closesqbr = Token("]", tt_terminator)

tok_comma     = Token(".", tt_terminator)
tok_period    = Token(",", tt_terminator)
tok_colon     = Token(":", tt_terminator)
tok_semicolon = Token(";", tt_terminator)
tok_squote    = Token("'", tt_terminator)
tok_dquote    = Token('"', tt_terminator)
tok_accent    = Token("`", tt_terminator)
#tok_eof       = Token("",  tt_eof)


token_iterator = TokenIterator(TextReader(open("ebnf_test.txt"))
                               , tt_list, tt_skip_list)
token_reader = TokenReader(token_iterator)


if __name__ == '__main__':
    for tok in token_iterator:
        tok.PPrint()
    # rslt = token_reader.read_next()
    # tok = rslt.readedlist[0]
    # while tok:
    #     tok.PPrint()
    #     rslt = token_reader.read_next()
    #     tok = rslt.readedlist[0]
