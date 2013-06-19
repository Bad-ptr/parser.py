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
The core of this module is 'rec_type_check' function.
You can extend it by defining new subclasses to type_spec class
(and then using this subclasses in type signature).
The one thing I'm unshure is how correct the dict handling code,
couse dict is not ordered collection.
It was tested with Python 3.3.1

Level of error reporting is controlled via __typecheck_error_level variable:
  NOTHING   = -1
  WARNING   = 0
  EXCEPTION = 1
Which could be set by set_typecheck_error_level function.

Example usage:
>>> from typecheck import (typecheck,accepts,returns, ts_num, set_typecheck_error_level
                           , NOTHING, WARNING, EXCEPTION)

>>> @accepts(ts_num(int, min_num=3,max_num=3),("asd",tuple,list,[int,1]),bool)
... def fun(a,b,c,d,test=False):
...     print("test =", test)
...     return a,b,c,d

>>> fun(1,2,3,("asd",(),[],[2,1]),True)
# test = True
# (1, 2, 3, ('asd', (), [], [2, 1]))

>>> fun(1,2,3,("asd",(),[],[3,1]))
# test = False
# (1, 2, 3, ('asd', (), [], [3, 1]))

>>> returns(1,2,3,(str,(),[ts_num(int)],[1,1]))(fun)

>>> set_typecheck_error_level(EXCEPTION)

>>> fun(1,2,3,("asd",(),[],[1,1]),True)
# 'fun' method returns ((1, 2, 3, ('asd', (), [ts_num((<class 'int'>,), min_num=1, max_num=-1)], [1, 1]))),
# but result is (((1, 2, 3, ('asd', (), [], [1, 1])),))
# TypeStack:
#  ts_num not matched: min_num=1, max_num=-1; but actual_num=0 (<class 'int'>,) to ()
# Type not matched: (ts_num((<class 'int'>,), min_num=1, max_num=-1),) to ()
# Type not matched: ([ts_num((<class 'int'>,), min_num=1, max_num=-1)], [1, 1]) to ([], [1, 1])
# Type not matched: (('asd', (), [ts_num((<class 'int'>,), min_num=1, max_num=-1)], [1, 1]),) to (('asd',(), [], [1, 1]),)
#
# Traceback...

>>> @typecheck()
... def foo(a:int,b:bool, *vargs:((1,2),)) -> 'ret_string':
...     return 'ret_string'

>>> foo(0,False,(1,2))
# 'ret_string'
'''


import sys

from collections import (Iterable, OrderedDict)
from itertools import (cycle)
from functools import (wraps)
import inspect


NOTHING   = -1
WARNING   = 0
EXCEPTION = 1
__typecheck_error_level = WARNING

def set_typecheck_error_level(err_level=WARNING):
    global __typecheck_error_level
    __typecheck_error_level = err_level

class stack_with_error():
    def __init__(self, msg, typ, obj):
        self.msg = msg
        self.typ = typ
        self.obj = obj

    def __repr__(self):
        return (self.msg + " "
                + repr(self.typ) + " to " + repr(self.obj))


class TypeCheckError(TypeError):
    def __init__(self, stack=[], num_matched=0):
        self.stack = stack
        self.num_matched = num_matched

    def __str__(self):
        return repr(self.stack)

class TypeCheckLengthError(TypeCheckError):
    def __init__(self, stack=[], num_matched=0, objs=[]):
        super().__init__(stack, num_matched)
        self.objs = objs


class type_spec():
    def check(self, obj):
        raise NotImplementedError("You calling 'check' method of class: "
                                  + repr(self.__class__.__name__)
                                  + " but it's not implemented.")


class ts_any(type_spec):
    def __repr__(self):
        return "ts_any()"

    def check(self, obj_s):
        return 1


class ts_not(type_spec):
    def __init__(self, *type_sigs):
        self.type_sigs = type_sigs

    def __repr__(self):
        return "ts_not(" + repr(self.type_sigs) + ")"

    def check(self, obj_s):
        for ts in self.type_sigs:
            try:
                n = rec_type_check((ts,), obj_s)
            except TypeCheckError as err:
                continue
            else:
                raise TypeCheckError([stack_with_error("matched.", ts, obj_s[0])
                                      , stack_with_error("ts_not not matched:", self.type_sigs, obj_s) ])
        return 1


class ts_and(type_spec):
    def __init__(self, *type_sigs, tt='min'):
        self.type_sigs = type_sigs

    def __repr__(self):
        return "ts_and(" + repr(self.type_sigs) + ")"

    def check(self, obj_s):
        ll = 0
        for ts in self.type_sigs:
            try:
                n = rec_type_check((ts,), obj_s)
                if n > ll:
                    ll = n
            except TypeCheckError as err:
                lst = err.stack
                lst.append(stack_with_error("ts_and not matched:", self.type_sigs, obj_s[0]))
                raise TypeCheckError(lst)
        return ll


class ts_or(type_spec):
    def __init__(self, *type_sigs, tt='min'):
        self.type_sigs = type_sigs
        self.tt = tt

    def __repr__(self):
        return "ts_or(" + ', '.join(map(repr, self.type_sigs)) + ")"

    def check(self, obj_s):
        ll = []
        for ts in self.type_sigs:
            try:
                n = rec_type_check((ts,), obj_s)
                ll.append(n)
            except TypeCheckError:
                continue
            else:
                n = 0
                if self.tt == 'min':
                    n = min(n, *ll)
                elif self.tt == 'max':
                    n = max(n, *ll)
                elif self.tt == 'single':
                    n = 1
                return n
        raise TypeCheckError( [stack_with_error("ts_or not matched:", self.type_sigs, obj_s[0])] )


class ts_eq(type_spec):
    def __init__(self, obj=None):
        self.obj = obj

    def __repr__(self):
        return "ts_eq(" + repr(self.obj) + ")"

    def check(self, obj_s):
        if True is (self.obj == obj_s[0]):
            return 1
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
        n = 1
        for typ in cycle(self.type_sigs):
            if () == obl:
                break
            try:
                n = rec_type_check((typ,), obl)
            except TypeCheckLengthError:
                pass
            except TypeCheckError as err:
                inn_st = err.stack
                break
            num += n
            obl = obl[n:]
        man = self.max_num
        if man < 0:
            man = num + 1
        if (num >= self.min_num and num <= man):
            return num

        inn_st.append(stack_with_error("ts_num not matched: min_num=" + repr(self.min_num)
                                       + ", max_num=" + repr(self.max_num)
                                       + "; but actual_num=" + repr(num)
                                       , self.type_sigs, obj_s))
        raise TypeCheckError(inn_st)


def rec_type_check(type_sig, objs, match_num=0):
    inner_stack = []
    state = True
    mn = 1

    typ, obj = None,None

    if () == type_sig:
        typ = type_sig
        if () == objs:
            return match_num + mn
        else:
            state = False
            inner_stack = [stack_with_error("Type length not matched:", type_sig, objs)]
            raise TypeCheckLengthError(inner_stack, match_num, objs)
    elif () == objs:
        typ = type_sig[0]
        obj = objs
    else:
        typ = type_sig[0]
        obj = objs[0]

    if isinstance(typ, type_spec):
        try:
            mn = typ.check(objs)
        except TypeCheckError as err:
            state = False
            inner_stack = err.stack
    elif isinstance(typ, type):
        if False is isinstance(obj, typ):
            state = False
            inner_stack = [stack_with_error("Object is not instance of:", typ, obj)]
    elif isinstance(typ, Iterable):
        if type(typ) != type(obj):
            state = False
            inner_stack = [stack_with_error("Type not matched:", typ, obj)]
        elif isinstance(typ, str):
            if typ != obj:
                state = False
                inner_stack = [stack_with_error("Strings not equal:", typ, obj)]
        elif isinstance(typ, dict):
            try:
                rec_type_check(tuple(typ.items()), tuple(obj.items()))
            except TypeCheckError as err:
                state = False
                inner_stack = err.stack
        else:
            try:
                rec_type_check(tuple(typ), tuple(obj))
            except TypeCheckError as err:
                state = False
                inner_stack = err.stack
    else:
        if typ != obj:
            state = False
            inner_stack = [stack_with_error("Objects not equal:", typ, obj)]
    if False is state:
        inner_stack.append(stack_with_error("Type not matched:", type_sig, objs))
        raise TypeCheckError(inner_stack, match_num)
    return rec_type_check(type_sig[1:], objs[mn:], match_num + mn)



class __empty_arg():
    def __str__(self):
        return "<empty>"
    def __iter__(self):
        return self
    def __next__(self):
        raise StopIteration
    def __bool__(self):
        return False
__EARG = __empty_arg()


def sigs_from_spec(argspec):
    if hasattr(argspec, 'annotations'):
        annots = argspec.annotations
        pos_args_list = (argspec.args or [])
        try:
            retsig = annots['return']
        except KeyError:
            retsig = __EARG
        else:
            if not isinstance(retsig, tuple):
                retsig = (retsig,)

        pargsig = []
        try:
            for n in pos_args_list:
                pargsig.append(annots[n])
            varargs_name = argspec.varargs
            if None is not varargs_name:
                var_sig = annots[varargs_name]
                if not isinstance(var_sig, Iterable):
                    pargsig.append(var_sig)
                else:
                    pargsig.extend(list(var_sig))
        except KeyError:
            pargsig = __EARG
        else:
            pargsig = tuple(pargsig)

        kwargsig = {}
        try:
            for n in argspec.kwonlyargs:
                kwargsig[n] = annots[n]
        except KeyError:
            kwargsig = __EARG

        return pargsig, kwargsig, retsig
    else:
        return __EARG, __EARG, __EARG

def args_dict_from_spec(argspec):
    pos_args_list     = (argspec.args           or [])
    pos_args_defaults = (argspec.defaults       or ())

    args_dict = OrderedDict([])

    for n in pos_args_list[:-len(pos_args_defaults)]:
        args_dict[n] = __EARG
    for (n, v) in zip(pos_args_list[-len(pos_args_defaults):], pos_args_defaults):
        args_dict[n] = v

    return args_dict

def build_positional_parameters_tuple(tparams, args, kws):
    pargs = []
    nn = 0
    for (n, v) in zip(tparams['args_dict'].keys(), args):
        pargs.append(v)
        nn += 1
    for n in list(tparams['args_dict'].keys())[nn:]:
        if n in kws:
            pargs.append(kws[n])
            del kws[n]
        else:
            pargs.append(tparams['args_dict'][n])
    pargs.extend(args[nn:])
    return tuple(pargs)

def get_typecheck_decor_or_func(f):
    def rec_get(fu):
        if hasattr(fu, '__bptr_typecheck_wrapper_parameters'):
            return fu
        else:
            if hasattr(fu, '__wrapped__'):
                return rec_get(fu.__wrapped__)
            else:
                return None
    return (rec_get(f) or f)

def typecheck(pos_args_sig=__EARG, kw_args_sig=__EARG, return_sig=__EARG):
    '''Function decorator. Checks decorated function's arguments and return value
    are of the expected type signature.

    Parameters:
    pos_args_sig -- The expected types of the positional arguments. (tuple)
    kw_args_sig  -- The expected types of the keyword arguments.    (dict)
    return_sig   -- The expected type of return value.              (tuple)

    If no arguments are given -- try to build type signatures from annotations.
    '''
    def decorator(f):
        nonlocal pos_args_sig, kw_args_sig, return_sig

        f = get_typecheck_decor_or_func(f)

        if hasattr(f, '__bptr_typecheck_wrapper_parameters'):
            if pos_args_sig is not __EARG:
                f.__bptr_typecheck_wrapper_parameters['pos_args_sig'] = pos_args_sig
            if kw_args_sig is not __EARG:
                f.__bptr_typecheck_wrapper_parameters['kw_args_sig'] = kw_args_sig
            if return_sig is not __EARG:
                f.__bptr_typecheck_wrapper_parameters['return_sig'] = return_sig

            return f

        else:

            argspec = inspect.getfullargspec(f)

            args_dict = args_dict_from_spec(argspec)

            if (pos_args_sig is __EARG and kw_args_sig is __EARG and return_sig is __EARG):
                pargsig, kwargsig, retsig = sigs_from_spec(argspec)
                if pargsig is __EARG and kwargsig is __EARG and retsig is __EARG:
                    return f
                else:
                    pos_args_sig, kw_args_sig, return_sig = pargsig, kwargsig, retsig

            @wraps(f)
            def newf(*args, **kws):
                global __typecheck_error_level
                if __typecheck_error_level < 0:
                    return f(*args, **kws)
                else:
                    tparams = newf.__bptr_typecheck_wrapper_parameters
                    pargs = build_positional_parameters_tuple(tparams, args, kws)

                    try:
                        if tparams['pos_args_sig'] is not __EARG:
                            rec_type_check(tparams['pos_args_sig'], pargs)
                        if tparams['kw_args_sig'] is not __EARG:
                            for (n,v) in kws.items():
                                if not isinstance(v, tuple):
                                    v = (v,)
                                try:
                                    s = tparams['kw_args_sig'][n]
                                except KeyError:
                                    raise TypeCheckError([stack_with_error("Unknown keyword argument:"
                                                                           , n, v)], 0)
                                if not isinstance(s, tuple):
                                    s = (s,)
                                rec_type_check(s, v)
                    except TypeCheckError as err:
                            print(info(f.__name__
                                       , ("positional: " + repr(tparams['pos_args_sig'])
                                          + " and keyword: " + repr(tparams['kw_args_sig']))
                                       , repr(args), 0),file=sys.stderr)
                            print("TypeStack: \n"
                                  ,"\n".join(map(str,err.stack)), "\n"
                                  ,file=sys.stderr)
                            if __typecheck_error_level > 0:
                                raise
                    result = f(*args, **kws)
                    if tparams['return_sig'] is not __EARG:
                        try:
                            if not isinstance(result, tuple):
                                rec_type_check(tparams['return_sig'], (result, ))
                            else:
                                rec_type_check(tparams['return_sig'], result)
                        except TypeCheckError as err:
                            print(info(f.__name__
                                       , repr(tparams['return_sig'])
                                       , repr((result, )), 1),file=sys.stderr)
                            print("TypeStack: \n"
                                  ,"\n".join(map(str,err.stack)), "\n"
                                  ,file=sys.stderr)
                            if __typecheck_error_level > 0:
                                raise
                        else:
                            return result
                    else:
                        return result
            newf.__bptr_typecheck_wrapper_parameters = {
                'args_dict'     : args_dict
                ,'pos_args_sig' : pos_args_sig
                ,'kw_args_sig'  : kw_args_sig
                ,'return_sig'   : return_sig
            }
            return newf
    return decorator


def accepts(*pos_args_sig, **kw_args_sig):
    '''Function decorator. Checks decorated function's arguments are
    of the expected type signature.

    Parameters:
    pos_args_sig -- The expected types of the positional arguments.
    kw_args_sig  -- The expected types of the keyword arguments.
    '''
    return typecheck(pos_args_sig, kw_args_sig)


def returns(*type_sig):
    '''Function decorator. Checks decorated function's return value
    is of the expected type.

    Parameters:
    type_sig -- The expected type of the decorated function's return value.
    '''
    return typecheck(return_sig=type_sig)


def info(fname_str, expected_str, actual_str, flag):
    '''Convenience function returns nicely formatted error/warning msg.'''
    msg = "'{}' method ".format(str(fname_str))\
        + ("accepts", "returns")[flag] + " ({}),\nbut ".format(str(expected_str))\
        + ("was given", "result is")[flag] + " ({})".format(str(actual_str))
    return msg
