#!/usr/bin/env python
# coding UTF-8

# Author: Constantin Kulikov (Bad_ptr) <zxnotdead@gmail.com>
# Date: 2013/06/04 07:25:46

# License:
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.


'''
This is highly modified version of
http://wiki.python.org/moin/PythonDecoratorLibrary#Type_Enforcement_.28accepts.2Freturns.29
It was tested with Python 3.3.1
The core of this module is 'rec_type_check' function.
You can extend it by defining new subclasses to type_spec class
(and then using this subclasses in type signature).
The one thing I'm unshure is how correct the dict handling code,
couse dict is not ordered collection.

One of three degrees of enforcement may be specified by passing
the 'err_level' keyword argument to the decorator:
    0 -- NONE:   No type-checking. Decorators disabled.
    1 -- MEDIUM: Print warning message to stderr. (Default)
    2 -- STRONG: Raise TypeError with message.
If 'err_level' is not passed to the decorator, the default level(MEDIUM) is used.

Example usage:
    >>> @accepts(ts_num(int, min_num=3,max_num=3),("asd",tuple,list,[1,1],{str:int, 'a':4}))
    ... @returns(1,2,3,("asd",tuple,list,[1,1],{str:int, 'a':4}))
    ... def fun(a,b,c,d):
    ...     return a,b,c,d
    ...
    >>> fun(1,2,3,("asd",(),[],[1,1],{str:int, 'a':4}))
    (1,2,3,("asd",(),[],[1,1],{str:int, 'a':4}))
    >>>
    >>>
    >>> fun(1,2,3,("asd",(),[],[1,2],{str:int, 'a':4}))
    ''fun'' method accepts ((ts_num((<class 'int'>,), min_num=3, max_num=3), ('asd', <class 'tuple'>, <class 'list'>, [1, 1], {<class 'str'>: <class 'int'>, 'a': 4}))), but was given
    ((1, 2, 3, ('asd', (), [], [1, 2], {'asd': 1, 'a': 4})))
    TypeStack:
     Objects not equal: 1 to 2
    Type not matched: [1, 1] to [1, 2]
    Type not matched: ('asd', <class 'tuple'>, <class 'list'>, [1, 1], {<class 'str'>: <class 'int'>, 'a': 4}) to ('asd', (), [], [1, 2], {'asd': 1, 'a': 4})
    Type not matched: (ts_num((<class 'int'>,), min_num=3, max_num=3), ('asd', <class 'tuple'>, <class 'list'>, [1, 1], {<class 'str'>: <class 'int'>, 'a': 4})) to (1, 2, 3, ('asd',
    (), [], [1, 2], {'asd': 1, 'a': 4}))

    ''fun'' method returns ((1, 2, 3, ('asd', <class 'tuple'>, <class 'list'>, [1, 1], {<class 'str'>: <class 'int'>, 'a': 4}))), but result is ((1, 2, 3, ('asd', (), [], [1, 2], {'a
    sd': 1, 'a': 4})))
    TypeStack:
     Objects not equal: 1 to 2
    Type not matched: [1, 1] to [1, 2]
    Type not matched: ('asd', <class 'tuple'>, <class 'list'>, [1, 1], {<class 'str'>: <class 'int'>, 'a': 4}) to ('asd', (), [], [1, 2], {'asd': 1, 'a': 4})
    Type not matched: (1, 2, 3, ('asd', <class 'tuple'>, <class 'list'>, [1, 1], {<class 'str'>: <class 'int'>, 'a': 4})) to (1, 2, 3, ('asd', (), [], [1, 2], {'asd': 1, 'a': 4}))

    (1, 2, 3, ('asd', (), [], [1, 2], {'asd': 1, 'a': 4}))

'''

import sys

from collections import (Iterable)
from itertools import (cycle)


class stack_with_error():
    def __init__(self, msg, typ, obj):
        self.msg = msg
        self.typ = typ
        self.obj = obj

    def __repr__(self):
        return (self.msg + " "
                + repr(self.typ) + " to " + repr(self.obj))

class TypeCheckError(Exception):
    def __init__(self, stack):
        self.stack = stack

    def __str__(self):
        return repr(self.stack)

class TypeCheckLengthError(Exception):
    def __init__(self, stack):
        self.stack = stack

    def __str__(self):
        return repr(self.stack)


class type_spec():

    def check(self, obj):
        raise NotImplementedError("You calling 'check' method of class: "
                                  + repr(self.__class__.__name__)
                                  + " but it's not implemented.")


class ts_any(type_spec):
    def __repr__(self):
        return "ts_any()"

    def check(self, obj_s):
        return obj_s[1:]


class ts_not(type_spec):
    def __init__(self, *type_sigs):
        self.type_sigs = type_sigs

    def __repr__(self):
        return "ts_not(" + repr(self.type_sigs) + ")"

    def check(self, obj_s):
        for ts in self.type_sigs:
            try:
                rec_type_check((ts,), obj_s)
            except TypeCheckError:
                continue
            else:
                raise TypeCheckError([ stack_with_error("matched.", ts, obj_s[0])
                                       , stack_with_error("ts_not not matched:", self.type_sigs, obj_s[0]) ])
        return obj_s[1:]


class ts_and(type_spec):
    def __init__(self, *type_sigs):
        self.type_sigs = type_sigs

    def __repr__(self):
        return "ts_and(" + repr(self.type_sigs) + ")"

    def check(self, obj_s):
        for ts in self.type_sigs:
            try:
                rec_type_check((ts,), obj_s)
            except TypeCheckError as err:
                lst = err.args[0]
                lst.append(stack_with_error("ts_and not matched:", self.type_sigs, obj_s[0]))
                raise TypeCheckError(lst)
        return obj_s[1:]


class ts_or(type_spec):
    def __init__(self, *type_sigs):
        self.type_sigs = type_sigs

    def __repr__(self):
        return "ts_or(" + ', '.join(map(repr, self.type_sigs)) + ")"

    def check(self, obj_s):
        for ts in self.type_sigs:
            try:
                rec_type_check((ts,), obj_s)
            except TypeCheckError:
                continue
            else:
                return obj_s[1:]
        raise TypeCheckError( [stack_with_error("ts_or not matched:", self.type_sigs, obj_s[0])] )


class ts_eq(type_spec):
    def __init__(self, obj=None):
        self.obj = obj

    def __repr__(self):
        return "ts_eq(" + repr(self.obj) + ")"

    def check(self, obj_s):
        if True is (self.obj == obj_s[0]):
            return obj_s[1:]
        else:
            raise TypeCheckError( [stack_with_error("ts_eq not matched:", self.obj, obj_s[0])] )


class ts_num(type_spec):
    def __init__(self, *type_sigs, min_num=1, max_num=-1):
        self.type_sigs = type_sigs
        self.min_num = min_num
        self.max_num = max_num

    def __repr__(self):
        return ("ts_num(" + repr(self.type_sigs) + ", min_num="
                + repr(self.min_num) + ", max_num=" + repr(self.max_num) + ")")

    def check(self, obj_s):
        num = 0
        obl = obj_s
        inn_st = []
        for typ in cycle(self.type_sigs):
            #print(self.type_sigs, " ; ", typ, " ; ", obl)
            if () == obl:
                break
            try:
                rec_type_check((typ,), obl)
            except TypeCheckLengthError:
                pass
            except TypeCheckError as err:
                inn_st = err.args[0]
                break
            num += 1
            obl = obl[1:]
        man = self.max_num
        if man < 0:
            man = num + 1
        if (num >= self.min_num and num <= man):
            return obj_s[num:]

        inn_st.append(stack_with_error("ts_num not matched: min_num=" + repr(self.min_num)
                                       + ", max_num=" + repr(self.max_num)
                                       + "; but actual_num=" + repr(num)
                                       , self.type_sigs, obj_s))
        raise TypeCheckError(inn_st)


def rec_type_check(type_sig, objs):
    inner_stack = []
    state = True

    typ, obj = None,None

    if () == type_sig:
        typ = type_sig
        if () == objs:
            return objs
        else:
            state = False
            inner_stack = [stack_with_error("Type length not matched:", type_sig, objs)]
            raise TypeCheckLengthError(inner_stack)
            #raise TypeCheckError(inner_stack)
    elif () == objs:
        typ = type_sig[0]
        obj = objs
    else:
        typ = type_sig[0]
        obj = objs[0]

    #print(typ, " ; ", obj)

    if isinstance(typ, type_spec):
        try:
            objs = typ.check(objs)
        except TypeCheckError as err:
            state = False
            inner_stack = err.args[0]
    elif isinstance(typ, type):
        if False is isinstance(obj, typ):
            state = False
            inner_stack = [stack_with_error("Object is not instance of:", typ, obj)]
        else:
            objs = objs[1:]
    elif isinstance(typ, Iterable):
        if type(type_sig) != type(objs):
            state = False
            inner_stack = [stack_with_error("Type not matched:", type_sig, objs)]
        elif 0 == len(type_sig):
            if 0 == len(obj):
                objs = objs[1:]
            else:
                state = False
                inner_stack = [stack_with_error("Type length not matched:", type_sig, objs)]
        if isinstance(typ, str):
            if typ != obj:
                state = False
                inner_stack = [stack_with_error("Strings not equal:", typ, obj)]
            else:
                objs = objs[1:]
        elif isinstance(typ, dict):
            try:
                rec_type_check(tuple(typ.items()), tuple(obj.items()))
            except TypeCheckLengthError as err:
                state = False
                inner_stack = err.args[0]
            except TypeCheckError as err:
                state = False
                inner_stack = err.args[0]
            objs = objs[1:]
        else:
            try:
                rec_type_check(tuple(typ), tuple(obj))
            except TypeCheckLengthError as err:
                state = False
                inner_stack = err.args[0]
            except TypeCheckError as err:
                state = False
                inner_stack = err.args[0]
            objs = objs[1:]
    else:
        if typ != objs[0]:
            state = False
            inner_stack = [stack_with_error("Objects not equal:", typ, objs[0])]
        else:
            objs = objs[1:]
    if False is state:
        inner_stack.append(stack_with_error("Type not matched:", type_sig, objs))
        raise TypeCheckError(inner_stack)
    return rec_type_check(type_sig[1:], objs)


def accepts(*type_sig, **kw):
    '''Function decorator. Checks decorated function's arguments are
    of the expected type signature.

    Parameters:
    type_sig -- The expected type of the inputs to the decorated function.
    kw       -- Optional specification of 'err_level' level (this is the only
                valid keyword argument, no other should be given).
                err_level = ( 0 | 1 | 2 )
    '''
    if not kw:
        # default level: MEDIUM
        err_level = 1
    else:
        err_level = kw['err_level']
    try:
        def decorator(f):
            def newf(*args):
                if err_level is 0:
                    return f(*args)
                try:
                    rec_type_check(type_sig, args)
                except TypeCheckError as err:
                    if err_level > 0:
                        print(info(f.__name__, type_sig, args, 0),file=sys.stderr)
                        print("TypeStack: \n"
                              ,"\n".join(map(str,err.args[0])), "\n"
                              ,file=sys.stderr)
                    elif err_level > 1:
                        raise
                return f(*args)
            newf.__name__ = f.__name__
            return newf
        return decorator
    except KeyError as err:
        raise KeyError(repr(err.args[0]) + " is not a valid keyword argument")
    except TypeError:
        raise


def returns(*type_sig, **kw):
    '''Function decorator. Checks decorated function's return value
    is of the expected type.

    Parameters:
    type_sig -- The expected type of the decorated function's return value.
    kw       -- Optional specification of 'err_level' level (this is the only
                valid keyword argument, no other should be given).
                err_level=( 0 | 1 | 2 )
    '''
    try:
        if not kw:
            # default level: MEDIUM
            err_level = 1
        else:
            err_level = kw['err_level']

        def decorator(f):
            def newf(*args):
                result = f(*args)
                if err_level is 0:
                    return result
                try:
                    if not isinstance(result,tuple):
                        rec_type_check(type_sig, (result,))
                    else:
                        rec_type_check(type_sig, result)
                except TypeCheckError as err:
                    if err_level > 0:
                        print(info(f.__name__, type_sig, result, 1), file=sys.stderr)
                        print("TypeStack: \n", "\n".join(map(str, err.args[0])), "\n"
                              , file=sys.stderr)
                    elif err_level > 1:
                        raise
                return result
            newf.__name__ = f.__name__
            return newf
        return decorator

    except KeyError as err:
        raise KeyError(repr(err.args[0])  + " is not a valid keyword argument")
    except TypeError:
        raise


def info(fname, expected, actual, flag):
    '''Convenience function returns nicely formatted error/warning msg.'''
    msg = "'{}' method ".format(repr(fname))\
          + ("accepts", "returns")[flag] + " ({}),\nbut ".format(repr(expected))\
          + ("was given", "result is")[flag] + " ({})".format(repr(actual))
    return msg
