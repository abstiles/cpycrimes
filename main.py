#!/usr/bin/env python3

import inspect

from dis import dis, opmap, Bytecode
from types import FunctionType, CodeType

from IPython import embed

gl = 0


def assigns_static(static_name):
    def assigns_name(instruction):
        if instruction.opname != 'STORE_FAST':
            return False
        if instruction.argval != static_name:
            return False
        return True
    return assigns_name


def fetches_static(static_name):
    def fetches_name(instruction):
        if instruction.opname != 'LOAD_FAST':
            return False
        if instruction.argval != static_name:
            return False
        return True
    return fetches_name


def filtered_bytecode(f):
    assigns_a = assigns_static('a')
    fetches_a = fetches_static('a')
    for instruction in Bytecode(f):
        if assigns_a(instruction):
            yield bytes([opmap['STORE_DEREF'], instruction.arg])
        elif fetches_a(instruction):
            yield bytes([opmap['LOAD_DEREF'], instruction.arg])
        else:
            yield bytes([instruction.opcode, instruction.arg or 0])


def fix_function(func):
    fn_code = func.__code__
    payload = b''.join(filtered_bytecode(func))
    return CodeType(fn_code.co_argcount,
                    fn_code.co_kwonlyargcount,
                    fn_code.co_nlocals,
                    fn_code.co_stacksize,
                    fn_code.co_flags & ~inspect.CO_NOFREE,
                    payload,
                    fn_code.co_consts,
                    fn_code.co_names,
                    fn_code.co_varnames,
                    fn_code.co_filename,
                    fn_code.co_name,
                    fn_code.co_firstlineno,
                    fn_code.co_lnotab,
                    fn_code.co_freevars + ('a',),
                    fn_code.co_cellvars,)


def static(a):
    def closed():
        nonlocal a
        pass
    def wrapper(f):
        code = fix_function(f)
        return FunctionType(code, f.__globals__, f.__name__, f.__defaults__,
                            (f.__closure__ or ()) + closed.__closure__)
    return wrapper


def statics_manual():
    a = 1
    def inner():
        nonlocal a
        print(a)
        a += 1
        print(a)
    return inner


@static(1)
def dynamic():
    print(a)
    a += 1
    print(a)


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


def get_cell(val=None):
    '''Create a closure cell object with initial value.'''

    # If you know a better way to do this, I'd like to hear it.
    x = val
    def closure():
        return x
    return closure.__closure__[0]


manual = statics_manual()
print('Manual')
dis(manual)
print('Dynamic')
dis(dynamic)

print(diffdict(function_dict(manual), function_dict(dynamic)))
embed()
