#!/usr/bin/env python3

import inspect

from dis import opmap, Bytecode
from types import FunctionType, CodeType


def static(**vars):
    '''Decorator to inject static variables into a function.'''

    closure = tuple(get_cell(v) for (k, v) in vars.items())
    def wrapper(f):
        code = inject_closure_vars(f, vars.keys())
        return FunctionType(code, f.__globals__, f.__name__, f.__defaults__,
                            (f.__closure__ or ()) + closure)
    return wrapper


def get_cell(val=None):
    '''Create a closure cell object with initial value.'''

    # If you know a better way to do this, I'd like to hear it.
    x = val
    def closure():
        return x  # pragma: no cover
    return closure.__closure__[0]


def inject_closure_vars(func, new_vars=()):
    '''Get the code for a closure of the new vars into the given function'''

    fn_code = func.__code__
    new_freevars = fn_code.co_freevars + tuple(new_vars)
    new_globals = [var for var in fn_code.co_names if var not in new_vars]
    new_locals = [var for var in fn_code.co_varnames if var not in new_vars]
    payload = b''.join(
        filtered_bytecode(func, new_freevars, new_globals, new_locals))
    return CodeType(fn_code.co_argcount,
                    fn_code.co_kwonlyargcount,
                    len(new_locals),
                    fn_code.co_stacksize,
                    fn_code.co_flags & ~inspect.CO_NOFREE,
                    payload,
                    fn_code.co_consts,
                    tuple(new_globals),
                    tuple(new_locals),
                    fn_code.co_filename,
                    fn_code.co_name,
                    fn_code.co_firstlineno,
                    fn_code.co_lnotab,
                    fn_code.co_freevars + tuple(new_vars),
                    fn_code.co_cellvars,)


def filtered_bytecode(func, freevars, globals, locals):
    '''Get the bytecode for a function with adjusted closed variables

    Any references to globlas or locals in the bytecode which exist in the
    freevars are modified to reference the freevars instead.

    '''
    opcode_map = {
        opmap['LOAD_FAST']: opmap['LOAD_DEREF'],
        opmap['STORE_FAST']: opmap['STORE_DEREF'],
        opmap['LOAD_GLOBAL']: opmap['LOAD_DEREF'],
        opmap['STORE_GLOBAL']: opmap['STORE_DEREF']
    }
    freevars_map = {var: idx for (idx, var) in enumerate(freevars)}
    globals_map = {var: idx for (idx, var) in enumerate(globals)}
    locals_map = {var: idx for (idx, var) in enumerate(locals)}

    for instruction in Bytecode(func):
        if instruction.opcode not in opcode_map:
            yield bytes([instruction.opcode, instruction.arg or 0])
        elif instruction.argval in freevars_map:
            yield bytes([opcode_map[instruction.opcode],
                         freevars_map[instruction.argval]])
        elif 'GLOBAL' in instruction.opname:
            yield bytes([instruction.opcode,
                         globals_map[instruction.argval]])
        elif 'FAST' in instruction.opname:
            yield bytes([instruction.opcode,
                         locals_map[instruction.argval]])
