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


class type_spec():

    def check(self, obj):
        raise NotImplementedError("You calling 'check' method of class: "
                                  + self.__class__.__name__
                                  + " but it's not implemented.")


class ts_any(type_spec):
    def __repr__(self):
        return "ts_any()"

    def check(self, obj):
        return True


class ts_not(type_spec):
    def __init__(self, *type_sigs):
        self.type_sigs = type_sigs

    def __repr__(self):
        return "ts_not(" + repr(self.type_sigs) + ")"

    def check(self, obj):
        for ts in self.type_sigs:
            try:
                rec_type_check(ts, obj)
            except TypeError:
                continue
            else:
                raise TypeError([ stack_with_error("matched.", ts, obj)
                                , stack_with_error("ts_not not matched:", self.type_sigs, obj) ])
        return True


class ts_and(type_spec):
    def __init__(self, *type_sigs):
        self.type_sigs = type_sigs

    def __repr__(self):
        return "ts_and(" + repr(self.type_sigs) + ")"

    def check(self, obj):
        for ts in self.type_sigs:
            try:
                rec_type_check(ts, obj)
            except TypeError as err:
                lst = err.args[0]
                lst.append(stack_with_error("ts_and not matched:", self.type_sigs, obj))
                raise TypeError(lst)
        return True


class ts_or(type_spec):
    def __init__(self, *type_sigs):
        self.type_sigs = type_sigs

    def __repr__(self):
        return "ts_or(" + ', '.join(map(repr, self.type_sigs)) + ")"

    def check(self, obj):
        for ts in self.type_sigs:
            try:
                rec_type_check(ts, obj)
            except TypeError:
                continue
            else:
                return True
        raise TypeError( [stack_with_error("ts_or not matched:", self.type_sigs, obj)] )


class ts_eq(type_spec):
    def __init__(self, obj=None):
        self.obj = obj

    def __repr__(self):
        return "ts_eq(" + repr(self.obj) + ")"

    def check(self, obj):
        if True is (self.obj == obj):
            return True
        else:
            raise TypeError( [stack_with_error("ts_eq not matched:", self.obj, obj)] )


class ts_num(type_spec):
    def __init__(self, *type_sigs, min_num=1, max_num=-1):
        self.type_sigs = type_sigs
        self.min_num = min_num
        self.max_num = max_num
        self.num = 0

    def __repr__(self):
        return ("ts_num(" + repr(self.type_sigs) + ", min_num="
                + repr(self.min_num) + ", max_num=" + repr(self.max_num) + ")")

    def check(self, objs):
        self.num = 0
        for (typ, obj) in zip(cycle(self.type_sigs), objs):
            try:
                rec_type_check(typ, obj)
            except TypeError:
                break
            self.num += 1
        man = self.max_num
        if man < 0:
            man = self.num + 1
        if (self.num >= self.min_num and self.num <= man):
            return True
        raise TypeError( [stack_with_error("ts_num not matched: min_num=" + repr(self.min_num)
                                           + ", max_num=" + repr(self.max_num)
                                           + "; but actual_num=" + repr(self.num)
                                           , self.type_sigs, objs)] )


def rec_type_check(type_sig, objs):
    inner_stack = []
    state = True
    if not isinstance(type_sig, Iterable):
        type_sig = (type_sig,)
    if not isinstance(objs, Iterable):
        objs = (objs,)
    t_sig, ob_s = tuple(type_sig), tuple(objs)
    while True:
        if () == t_sig:
            if () != ob_s:
                state = False
                raise TypeError( [stack_with_error("Type signature length not matched:"
                                                   , type_sig, objs)] )
            break
        elif () == ob_s:
            state = False
            raise TypeError( [stack_with_error("Type signature length not matched:"
                                               , type_sig, objs)] )
            break

        typ = t_sig[0]
        obj = ob_s[0]

        if(isinstance(typ, type_spec)):
            if(isinstance(typ, ts_num)):
                try:
                    typ.check(ob_s)
                except TypeError as err:
                    state = False
                    inner_stack = err.args[0]
                    break
                else:
                    ob_s = ob_s[typ.num:]
                    t_sig = t_sig[1:]
                    continue
            else:
                try:
                    typ.check(obj)
                except TypeError as err:
                    state = False
                    inner_stack = err.args[0]
                    break
        elif(isinstance(typ, type)):
            if False is isinstance(obj, typ):
                state = False
                inner_stack = [stack_with_error("Object is not instance of:", typ, obj)]
                break
        elif(isinstance(typ, Iterable)):
            if type(typ) != type(obj):
                state = False
                inner_stack = [stack_with_error("Type not matched:", typ, obj)]
                break
            if(isinstance(typ, str)):
                if typ != obj:
                    state = False
                    inner_stack = [stack_with_error("Strings not equal:", typ, obj)]
                    break
            elif(isinstance(typ, dict)):
                #for (tk, tv), (ok, ov) in zip(typ, obj):
                # if False == (rec_type_check(typ.keys(), obj.keys())
                #              and rec_type_check(typ.values(), obj.values())):
                try:
                    rec_type_check(typ.items(), obj.items())
                except TypeError as err:
                    state = False
                    inner_stack = err.args[0]
                    break
            else:
                try:
                    rec_type_check(typ, obj)
                except TypeError as err:
                    state = False
                    inner_stack = err.args[0]
                    break
        else:
            if typ != obj:
                state = False
                inner_stack = [stack_with_error("Objects not equal:", typ, obj)]
                break

        t_sig = t_sig[1:]
        ob_s = ob_s[1:]

    if False is state:
        inner_stack.append( stack_with_error("Type not matched:" , type_sig, objs) )
        raise TypeError(inner_stack)
    return state


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
                except TypeError as err:
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
                    rec_type_check(type_sig, result)
                except TypeError as err:
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
          + ("accepts", "returns")[flag] + " ({}), but ".format(repr(expected))\
          + ("was given", "result is")[flag] + " ({})".format(repr(actual))
    return msg
