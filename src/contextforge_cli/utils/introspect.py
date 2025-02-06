"""
contextforge_cli/utils/introspect.py

Defines built in contextforge_cli functions to aid in introspection
"""
# SOURCE: https://github.com/hugapi/hug/blob/e4a3fa40f98487a67351311d0da659a6c9ce88a6/hug/introspect.py#L33

# from __future__ import absolute_import
from __future__ import annotations

from types import MethodType


def is_method(function):
    """Returns True if the passed in function is identified as a method (NOT a function)"""
    return isinstance(function, MethodType)


def is_coroutine(function):
    """Returns True if the passed in function is a coroutine"""
    return function.__code__.co_flags & 0x0080 or getattr(
        function, "_is_coroutine", False
    )


def name(function):
    """Returns the name of a function"""
    return function.__name__


def arguments(function, extra_arguments=0):
    """Returns the name of all arguments a function takes"""
    if not hasattr(function, "__code__"):
        return ()

    return function.__code__.co_varnames[
        : function.__code__.co_argcount + extra_arguments
    ]


def takes_kwargs(function):
    """Returns True if the supplied function takes keyword arguments"""
    return bool(function.__code__.co_flags & 0x08)


def takes_args(function):
    """Returns True if the supplied functions takes extra non-keyword arguments"""
    return bool(function.__code__.co_flags & 0x04)


def takes_arguments(function, *named_arguments):
    """Returns the arguments that a function takes from a list of requested arguments"""
    return set(named_arguments).intersection(arguments(function))


def takes_all_arguments(function, *named_arguments):
    """Returns True if all supplied arguments are found in the function"""
    return takes_arguments(function, *named_arguments) == set(named_arguments)


def generate_accepted_kwargs(function, *named_arguments):
    """
    Dynamically creates a function that when called with dictionary of arguments will produce a kwarg that's
    compatible with the supplied function
    """
    if hasattr(function, "__code__") and takes_kwargs(function):
        function_takes_kwargs = True
        function_takes_arguments = []
    else:
        function_takes_kwargs = False
        function_takes_arguments = takes_arguments(function, *named_arguments)

    def accepted_kwargs(kwargs):
        if function_takes_kwargs:
            return kwargs
        elif function_takes_arguments:
            return {
                key: value
                for key, value in kwargs.items()
                if key in function_takes_arguments
            }
        return {}

    return accepted_kwargs
