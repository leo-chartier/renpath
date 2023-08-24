from renpath import renpy
from .typing import Any, Callable, TypeVar, Union

try:
    from time import perf_counter
except:
    from time import time as perf_counter



T = TypeVar('T')

def timed(name, function, *args, **kwargs):
    # type: (str, Callable[..., T], *Any, **Any) -> T
    renpy.display.log.write("==========")

    start = perf_counter()
    result = function(*args, **kwargs)
    end = perf_counter()

    dt = end - start
    h, m, s = dt // 3600, (dt // 60) % 60, dt % 60

    if h:
        renpy.display.log.write("{} took {}h {:02}m {:02.0f}s".format(name, h, m, s))
    elif m:
        renpy.display.log.write("{} took {:02}m {:05.2f}s".format(name, m, s))
    else:
        renpy.display.log.write("{} took {:06.3f}s".format(name, s))
    renpy.display.log.write("==========")
    return result

def lookup_or_none(name):
    # type: (str) -> Union[renpy.ast.Node, None]
    try:
        return renpy.game.script.lookup_or_none(name) # type: ignore
    except AttributeError:
        try:
            return renpy.game.script.lookup(name) # type: ignore
        except renpy.script.ScriptError:
            return None
