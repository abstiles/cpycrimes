#!/usr/bin/env python3

import inspect

from dis import opmap, Bytecode
from types import FunctionType, CodeType

def get_cell(val=None):
    '''Create a closure cell object with initial value.'''

    # If you know a better way to do this, I'd like to hear it.
    x = val
    def closure():
        return x
    return closure.__closure__[0]


def filtered_bytecode(f, added_freevars):
    # I hate everything about this. Fix it.
    for instruction in Bytecode(f):
        if instruction.argval in added_freevars:
            if instruction.opname == 'LOAD_FAST':
                yield bytes([opmap['LOAD_DEREF'], added_freevars[instruction.argval]])
            elif instruction.opname == 'STORE_FAST':
                yield bytes([opmap['STORE_DEREF'], added_freevars[instruction.argval]])
            else:
                yield bytes([instruction.opcode, instruction.arg or 0])
        else:
            yield bytes([instruction.opcode, instruction.arg or 0])
    # TODO: Fix the LOAD/STORE FAST instructions for the other variables,
    # which will need their indices adjusted to compensate for the removal of
    # the free vars from their tuple.


def fix_function(func, new_vars=()):
    fn_code = func.__code__
    idx_map = freevar_index_map(fn_code, new_vars)
    payload = b''.join(filtered_bytecode(func, idx_map))
    new_locals = tuple(var for var in fn_code.co_varnames if var not in new_vars)
    return CodeType(fn_code.co_argcount,
                    fn_code.co_kwonlyargcount,
                    len(new_locals),
                    fn_code.co_stacksize,
                    fn_code.co_flags & ~inspect.CO_NOFREE,
                    payload,
                    fn_code.co_consts,
                    fn_code.co_names,
                    new_locals,
                    fn_code.co_filename,
                    fn_code.co_name,
                    fn_code.co_firstlineno,
                    fn_code.co_lnotab,
                    fn_code.co_freevars + tuple(new_vars),
                    fn_code.co_cellvars,)


def freevar_index_map(fn_code, new_freevars):
    first_idx = len(fn_code.co_freevars or ())
    return {var: idx for (idx, var) in enumerate(new_freevars, first_idx)}


def static(**vars):
    closure = tuple(get_cell(v) for (k, v) in vars.items())
    def wrapper(f):
        code = fix_function(f, tuple(vars.keys()))
        return FunctionType(code, f.__globals__, f.__name__, f.__defaults__,
                            (f.__closure__ or ()) + closure)
    return wrapper
