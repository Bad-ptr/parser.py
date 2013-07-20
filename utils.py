#!/usr/bin/env python
# coding UTF-8

# Author: Constantin Kulikov (Bad_ptr) <zxnotdead@gmail.com>
# Date: 2013/06/21 11:21:11
# License: GPL either version 2 or any later version


def _or(smth, defv):
    if None is smth:
        return defv
    else:
        return smth

def get_from_dictstack(name="", *dict_stack, dstack=None):
    stack = _or(dstack, dict_stack)
    for d in stack:
        try:
            return d[name]
        except KeyError:
            continue
    return None

def merge_nested_dicts(a, b):
    if(isinstance(a, dict)
       and isinstance(b, dict)):
        merged = {}
        merged.update(a)
        for (k,v) in b.items():
            merged[k] = merge_nested_dicts(merged.get(k,{}), v)
        return merged
    else:
        return b

def get_from_nested_dict(di, *path):
    if path == ():
        return di
    if not isinstance(di, dict):
        return None
    return get_from_nested_dict(di.get(path[0]), *path[1:])

def set_to_nested_dict(di, value, *path):
    if path == ():
        return value
    elif not isinstance(di, dict):
        return di
    else:
        cd = di.get(path[0])
        rest = path[1:]
        if None is not cd:
            di[path[0]] = set_to_nested_dict(cd, value, rest)
        return di

def add_hook(hook_type="", hook_name="", hook=None, hook_dict=None):
    if None is not hook:
        hook_dict = _or(hook_dict, {})
        if None is hook_dict.get(hook_type):
            hook_dict[hook_type] = {}
        hook_type_dict = hook_dict[hook_type]
        oldhs = hook_type_dict.get(hook_name, [])
        if not isinstance(oldhs, list):
            oldhs = [oldh]
        oldhs.append(hook)
        hook_type_dict[hook_name] = oldhs
        return hook_dict

def run_hooks(hook_type="", hook_name="", hook_dict=None, vargs=None, kwargs=None):
    if None is not hook_dict:
        hook_type_dict = hook_dict.get(hook_type)
        if None is not hook_type_dict:
            if hook_name == "*":
                for hooks in hook_type_dict.values():
                    for hook in hooks:
                        hook(*_or(vargs,()), **_or(kwargs,{}))
            else:
                hooks = hook_type_dict.get(hook_name)
                if None is not hooks:
                    for hook in hooks:
                        hook(*_or(vargs,()), **_or(kwargs,{}))

def run_pre_hooks(hook_name="", hook_dict=None, vargs=None, kwargs=None):
    return run_hooks(hook_type="pre", hook_name=hook_name, hook_dict=hook_dict
                     , vargs=vargs, kwargs=kwargs)

def run_post_hooks(hook_name="", hook_dict=None, vargs=None, kwargs=None):
    return run_hooks(hook_type="post", hook_name=hook_name, hook_dict=hook_dict
                     , vargs=vargs, kwargs=kwargs)
