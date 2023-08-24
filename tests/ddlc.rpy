init -99998 python:
    from renpath.classes.graph import Graph
    from renpath.conversion import convert
    from renpath.node_generation import _next__minimalist
    from renpath.simplification import simplify
    from renpath.utility import timed

    start_node = renpy.game.script.lookup("start")
    end_node = None

    graph = timed("Generation", convert, start_node, end_node, _next__minimalist)
    timed("Simplification", simplify, graph, simplify_menus=True)
    timed("Vizualization", Graph.vizualize, graph)

    renpy.quit()