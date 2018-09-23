#!/usr/bin/env python3

import inspect

from statics import static


def statics_manual():
    a = 0
    def inner():
        nonlocal a
        a += 1
        return a
    return inner


@static(a=0)
def dynamic():
    a += 1
    return a


def function_dict(func):
    fn_code = func.__code__
    return {
        'argcount': fn_code.co_argcount,
        'kwonlyargcount': fn_code.co_kwonlyargcount,
        'nlocals': fn_code.co_nlocals,
        'stacksize': fn_code.co_stacksize,
        'flags': fn_code.co_flags,
        'codestring': fn_code.co_code,
        'constants': fn_code.co_consts,
        'names': fn_code.co_names,
        'varnames': fn_code.co_varnames,
        'filename': fn_code.co_filename,
        'name': fn_code.co_name,
        'firstlineno': fn_code.co_firstlineno,
        'lnotab': fn_code.co_lnotab,
        'freevars': fn_code.co_freevars,
        'cellvars': fn_code.co_cellvars,
    }


def diffdict(d1, d2):
    return {
        k: v for (k, v) in d2.items()
        if k not in d1 or d1[k] != v
    }


def test_single_static():
    manual = statics_manual()
    diff = diffdict(function_dict(manual), function_dict(dynamic))
    del diff['name']
    del diff['firstlineno']
    assert {'flags': diff['flags'] & ~inspect.CO_NESTED} == diff


def test_incrementing():
    assert dynamic() == 1
    assert dynamic() == 2


@static(a='hello', b='world')
def unifying(x, y):
    return a, b, x, y


def test_free_and_local():
    assert unifying(1, 2) == ('hello', 'world', 1, 2)


@static(a='hello', b='world')
def both_with_assignment(x, y):
    b = 'planet'
    z = 3
    return a, b, x, y, z


def test_free_and_local_with_assignment():
    assert both_with_assignment(1, 2) == ('hello', 'planet', 1, 2, 3)


GLOBAL = 'some global'


@static(a='hello')
def with_global_override(local):
    return a, GLOBAL, local


def test_with_global_override():
    assert with_global_override('test') == ('hello', 'some global', 'test')
