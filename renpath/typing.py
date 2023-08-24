# type: ignore
try:
    from typing import Any, Callable, Dict, Iterator, List, Protocol, Tuple, Type, TypeVar, Union, Optional
except ImportError:
    # Typing not available in renpy, use placeholders
    Any = object()
    class Callable:
        pass
    Dict = dict()
    class Iterator:
        pass
    List = list()
    class Protocol:
        pass
    class Tuple:
        pass
    class Type:
        pass
    class TypeVar:
        def __init__(self, name):
            pass
    class Union:
        pass
    class Optional:
        pass
