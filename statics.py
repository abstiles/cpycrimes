#!/usr/bin/env python3

import inspect

from dis import opmap, Bytecode
from types import FunctionType, CodeType

from transformers import SequenceIndexer, MirrorDict


def get_cell(val=None):
    '''Create a closure cell object with initial value.'''

    # If you know a better way to do this, I'd like to hear it.
    x = val
    def closure():
        return x
    return closure.__closure__[0]


def filtered_bytecode(func, new_vars):
    added_freevars = freevar_index_map(func.__code__, new_vars)
    updated_globals = global_index_map(func.__code__, new_vars)
    updated_vars = var_index_map(func.__code__, new_vars)
    opcode_map = freevar_opcode_map()
    for instruction in Bytecode(func):
        if instruction.arg is None:
            yield bytes([instruction.opcode, 0])
        elif instruction.argval in added_freevars:
            yield bytes([
                opcode_map[instruction.opcode],
                added_freevars[instruction.argval]
            ])
        elif instruction.argval in updated_vars:
            yield bytes([
                instruction.opcode,
                updated_vars[instruction.argval]
            ])
        else:
            yield bytes([instruction.opcode, instruction.arg])


def fix_function(func, new_vars=()):
    fn_code = func.__code__
    payload = b''.join(filtered_bytecode(func, new_vars))
    new_names = tuple(var for var in fn_code.co_names if var not in new_vars)
    new_locals = tuple(var for var in fn_code.co_varnames if var not in new_vars)
    return CodeType(fn_code.co_argcount,
                    fn_code.co_kwonlyargcount,
                    len(new_locals),
                    fn_code.co_stacksize,
                    fn_code.co_flags & ~inspect.CO_NOFREE,
                    payload,
                    fn_code.co_consts,
                    new_names,
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


def var_index_map(fn_code, removed_vars):
    indexer = SequenceIndexer(fn_code.co_varnames)
    print(fn_code.co_varnames)
    for var_name in removed_vars:
        if var_name in indexer:
            del indexer[var_name]
    return indexer


def global_index_map(fn_code, removed_vars):
    indexer = SequenceIndexer(fn_code.co_varnames)
    print(fn_code.co_names)
    for var_name in removed_vars:
        if var_name in indexer:
            del indexer[var_name]
    return indexer


def freevar_opcode_map():
    return MirrorDict({
        opmap['LOAD_FAST']: opmap['LOAD_DEREF'],
        opmap['STORE_FAST']: opmap['STORE_DEREF'],
        opmap['LOAD_GLOBAL']: opmap['LOAD_DEREF'],
        opmap['STORE_GLOBAL']: opmap['STORE_DEREF'],
    })


def static(**vars):
    closure = tuple(get_cell(v) for (k, v) in vars.items())
    def wrapper(f):
        code = fix_function(f, tuple(vars.keys()))
        return FunctionType(code, f.__globals__, f.__name__, f.__defaults__,
                            (f.__closure__ or ()) + closure)
    return wrapper
